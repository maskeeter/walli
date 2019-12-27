import logging
import traceback
from signal import pause

from gpiozero import DistanceSensor, Button

from tj_frame import screen
from tj_frame.streaming import get_active_player, extract_playlist
from tj_frame.streaming import validate_channel_config, play_outage_footage, stream
from tj_frame.utils import read_config, kill_app

CHANNELS = ['pl', 'live']
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
GLOBAL_CONFIG = read_config("config/global_config.json")


def toggle_channel():
    current_player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if current_player:
        current_player.pause()
    toggle_channel.current_channel_id = toggle_channel.current_channel_id + 1 \
        if toggle_channel.current_channel_id < len(CHANNELS) - 1 else 0
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if player:
        player.play()
    else:
        stream_channel(toggle_channel.current_channel_id)


toggle_channel.current_channel_id = 0


def stream_channel(channel_id: int):
    channel = CHANNELS[channel_id]
    ch_config = GLOBAL_CONFIG.get(channel)
    if GLOBAL_CONFIG:
        try:
            if not validate_channel_config(ch_config, channel):
                play_outage_footage(channel, "invalid config")
            else:
                stream(channel, ch_config)
                screen.turn_on()
                outage = get_active_player('outage')
                if outage and outage.is_playing():
                    outage.pause()
        except Exception as e:
            traceback.print_exc()
            main_channel = get_active_player(channel)
            if main_channel and main_channel.is_playing():
                main_channel.pause()
            play_outage_footage(channel, 'streaming failed')
    else:
        kill_app("No configuration exists!")


# TODO : account for OMXPlayerDeadError('Process is no longer alive, can\'t run command')

def wakeup():
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if player:
        player.play()
        screen.turn_on()
    else:
        stream_channel(toggle_channel.current_channel_id)
    logging.info("play mode ...")


def standby():
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if player:
        player.pause()
    else:
        logging.warning("doesn't have any player")
    screen.turn_off()
    logging.info("standby mode ...")


def mark_held(btn):
    btn.was_held = True
    logging.info('hold marked')


def switch_button_action(btn):
    if not btn.was_held:
        toggle_channel()
        logging.info(f'button just pressed')
    else:
        logging.info(f'button held sensor')
        if btn.sensor:
            if btn.sensor.closed:
                btn.sensor = start_sensor()
            else:
                btn.sensor.close()
    btn.was_held = False


Button.was_held = False


def start_sensor():
    logging.info('Sensor Enabled ....')
    d_sensor = DistanceSensor(echo=23, trigger=24, max_distance=1, threshold_distance=0.2, partial=True)
    d_sensor.when_in_range = wakeup
    d_sensor.when_out_of_range = standby
    return d_sensor


def stop_sensor(d_sensor: DistanceSensor):
    logging.info('Sensor Disabled ....')
    d_sensor.close()


Button.sensor = None


def initialize_extractor():
    pl_config = GLOBAL_CONFIG.get('pl')
    t = extract_playlist(pl_config.get('list_id'), pl_config.get('extractor_config'), pl_config.get('playlist_target'))
    t.join()


if __name__ == '__main__':
    try:
        initialize_extractor()
        sensor = start_sensor()
        button = Button(4, hold_time=3)
        button.sensor = sensor
        button.when_held = mark_held
        button.when_released = switch_button_action
        pause()
    except KeyboardInterrupt:
        standby()
        logging.info("goodbye ....")
        exit(1)

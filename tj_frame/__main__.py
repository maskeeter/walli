import logging
from signal import pause

from gpiozero import DistanceSensor, Button

from tj_frame import screen
from tj_frame.player import get_channel_player
from tj_frame.streaming import validate_channel_config, play_outage_channel, stream
from tj_frame.utils import read_config, kill_app

CHANNELS = ['pl', 'gif', 'live']
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
GLOBAL_CONFIG = read_config("config/global_config.json")


def toggle_channel():
    current_player = get_channel_player(CHANNELS[toggle_channel.current_channel_id])
    if current_player and current_player.is_playing():
        current_player.pause()
    toggle_channel.current_channel_id = toggle_channel.current_channel_id + 1 \
        if toggle_channel.current_channel_id < len(CHANNELS) - 1 else 0
    player = get_channel_player(CHANNELS[toggle_channel.current_channel_id])
    if player:
        player.play()
    else:
        stream_channel(toggle_channel.current_channel_id)


toggle_channel.current_channel_id = 2  # live is default channel


def stream_channel(channel_id: int):
    channel = CHANNELS[channel_id]
    ch_config = GLOBAL_CONFIG.get(channel)
    if GLOBAL_CONFIG:
        try:
            if not validate_channel_config(ch_config, channel):
                play_outage_channel(channel, "invalid config")
            else:
                outage = get_channel_player('outage')
                if outage and outage.is_playing():
                    outage.pause()
                stream(channel, ch_config)
        except Exception as e:
            main_channel = get_channel_player(channel)
            if main_channel and main_channel.is_playing():
                main_channel.pause()
            play_outage_channel(channel, 'streaming failed')
    else:
        kill_app("No configuration exists!")


# TODO : account for OMXPlayerDeadError('Process is no longer alive, can\'t run command')

def wakeup():
    player = get_channel_player(CHANNELS[toggle_channel.current_channel_id])
    if player:
        screen.turn_on()
        player.play()
    else:
        stream_channel(toggle_channel.current_channel_id)
    logging.info("play mode ...")


def standby():
    player = get_channel_player(CHANNELS[toggle_channel.current_channel_id])
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
    d_sensor = DistanceSensor(echo=23, trigger=24, max_distance=1, threshold_distance=0.5, queue_len=20)
    d_sensor.when_in_range = wakeup
    d_sensor.when_out_of_range = standby
    return d_sensor


def stop_sensor(d_sensor: DistanceSensor):
    logging.info('Sensor Disabled ....')
    d_sensor.close()


Button.sensor = None

if __name__ == '__main__':
    sensor = start_sensor()
    button = Button(4, hold_time=3)
    button.sensor = sensor
    button.when_held = mark_held
    button.when_released = switch_button_action
    pause()

import logging
from gpiozero import DistanceSensor, Button
from signal import pause

from tj_frame import screen
from tj_frame.player import get_channel_player
from tj_frame.streaming import validate_channel_config, play_outage_channel, stream
from tj_frame.utils import read_config, kill_app

CHANNELS = ['pl', 'gif', 'live']
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
GLOBAL_CONFIG = read_config("config/global_config.json")


def toggle_channel():
    toggle_channel.current_channel_id = toggle_channel.current_channel_id + 1 \
        if toggle_channel.current_channel_id < len(CHANNELS) - 1 else 0
    if stream_channel.current_player:
        stream_channel.current_player.pause()
        print('toggle: stopping {}'.format(stream_channel.current_player))
        print('toggle: is playing {}'.format(stream_channel.current_player.is_playing()))
    player = get_channel_player(CHANNELS[toggle_channel.current_channel_id])
    print('toggle: starting {}'.format(player))
    if player:
        player.play()
        stream_channel.current_player = player
    else:
        print('new stream .......')
        stream_channel(toggle_channel.current_channel_id)


toggle_channel.current_channel_id = 2  # live is default channel


def stream_channel(channel_id: int):
    channel = CHANNELS[channel_id]
    ch_config = GLOBAL_CONFIG.get(channel)
    if GLOBAL_CONFIG:
        try:
            if not validate_channel_config(ch_config, channel):
                stream_channel.current_player = play_outage_channel(channel, "invalid config")
            else:
                stream_channel.current_player = stream(channel, ch_config)
        except Exception as e:
            if stream_channel.current_player and stream_channel.current_player.is_playing():
                print(f'stopping player {stream_channel.current_player} to play outage ...')
                stream_channel.current_player.pause()
            play_outage_channel(channel, 'streaming failed')
    else:
        kill_app("No configuration exists!")


stream_channel.current_player = None


def wakeup():
    player = stream_channel.current_player
    if player:
        screen.turn_on()
        player.play()
    else:
        stream_channel(toggle_channel.current_channel_id)
    logging.info("play mode ...")


def standby():
    player = stream_channel.current_player
    if player:
        player.pause()
    else:
        logging.warning("doesn't have any player")
    screen.turn_off()
    logging.info("standby mode ...")


def mark_held(btn):
    btn.was_held = True
    print('hold marked')


def switch_button_action(btn):
    if not btn.was_held:
        toggle_channel()
        logging.info(f'button just pressed')
    else:
        logging.info(f'button held')
        # btn.close()
    btn.was_held = False


Button.was_held = False

if __name__ == '__main__':
    sensor = DistanceSensor(echo=23, trigger=24, max_distance=1, threshold_distance=0.5, partial=True)
    sensor.when_in_range = wakeup
    sensor.when_out_of_range = standby
    button = Button(4, hold_time=3)
    button.when_held = mark_held
    button.when_released = switch_button_action
    pause()

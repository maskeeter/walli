import logging
import sys
import traceback
from signal import pause

from gpiozero import DistanceSensor, Button

from tj_frame import screen
from tj_frame.streaming import get_active_player, play_outage, stop_outage
from tj_frame.streaming import validate_channel_config, stream
from tj_frame.utils import read_config, kill_app, toggle

CHANNELS = ['pl', 'live']
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def read_global_config(key: str):
    global_config = read_config("config/global_config.json")
    return global_config[key] if global_config and key in global_config else None


def toggle_channel():
    stop_outage()
    current_player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if current_player and current_player.is_playing():
        current_player.pause()
    toggle_channel.current_channel_id = toggle(CHANNELS, toggle_channel.current_channel_id)
    wakeup()


toggle_channel.current_channel_id = 0


def stream_channel(channel_id: int):
    config = read_global_config('channels')
    channel = CHANNELS[channel_id]
    if config and channel and validate_channel_config(config[channel], channel):
        try:
            stream(channel, config[channel])
        except Exception as e:
            traceback.print_exc()
            play_outage(channel, f'streaming failed')
        finally:
            return
    kill_app("No configuration exists!")


def wakeup():
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    try:
        player.play()
    except Exception as e:
        logging.warning("no player found!")
        stream_channel(toggle_channel.current_channel_id)
    finally:
        screen.turn_on()
        logging.info("play mode ...")


def standby():
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    try:
        player.pause()
    except Exception as e:
        logging.warning("doesn't have any player")
    finally:
        screen.turn_off()
        logging.info("standby mode ...")


def mark_held(btn):
    btn.was_held = True


def switch_button_action(btn):
    if not btn.was_held:
        toggle_channel()
        logging.info(f'button pressed!')
    else:
        logging.info(f'button held!')
        if btn.sensor:
            if btn.sensor.closed:
                btn.sensor = start_sensor()
            else:
                btn.sensor.close()
    btn.was_held = False


Button.was_held = False


def start_sensor():
    config = read_global_config('sensor')
    try:
        if config:
            d_sensor = DistanceSensor(echo=24, trigger=23, max_distance=config.get('max_distance'),
                                      threshold_distance=config.get('threshold'), queue_len=(config.get('delay') * 40))
            d_sensor.when_in_range = wakeup
            d_sensor.when_out_of_range = standby
            logging.info('Sensor Enabled ....')
            return d_sensor
        kill_app("No configuration exists!")
    except Exception as e:
        logging.error("loading sensor failed, check configuration!")
        raise e


def stop_sensor(d_sensor: DistanceSensor):
    logging.info('Sensor Disabled ....')
    d_sensor.close()


Button.sensor = None

if __name__ == '__main__':
    try:
        screen.turn_off()
        sensor = start_sensor()
        button = Button(4, hold_time=3)
        button.sensor = sensor
        button.when_held = mark_held
        button.when_released = switch_button_action
        pause()
    except KeyboardInterrupt:
        standby()
        logging.info("goodbye ....")
        sys.exit()

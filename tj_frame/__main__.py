import logging
import sys
from signal import pause

from gpiozero import DistanceSensor, Button

from tj_frame import screen
from tj_frame.streaming import get_active_player, play_outage, stop_outage
from tj_frame.streaming import validate_channel_config, stream
from tj_frame.utils import read_config, kill_app, toggle, reboot_device

CHANNELS = ['pl', 'live']
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def toggle_channel():
    current_player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    if current_player:
        current_player.pause()
    toggle_channel.current_channel_id = toggle(CHANNELS, toggle_channel.current_channel_id)
    wakeup()


toggle_channel.current_channel_id = 0


def stream_channel(channel_id: int):
    config = read_config("config/global_config.json")
    channel = CHANNELS[channel_id]
    if config and channel and validate_channel_config(config[channel], channel):
        try:
            stop_outage()
            stream(channel, config[channel])
        except Exception as e:
            play_outage(channel, f'streaming failed')
        finally:
            return
    kill_app("No configuration exists!")


def wakeup():
    player = get_active_player(CHANNELS[toggle_channel.current_channel_id])
    try:
        player.play()
    except Exception as e:
        logging.error("player is disfunctional, reason: ", e)
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
        if btn.held_time > 10:
            reboot_device()
        else:
            if btn.sensor:
                if btn.sensor.closed:
                    btn.sensor = start_sensor()
                else:
                    btn.sensor.close()
    btn.was_held = False


Button.was_held = False


def start_sensor():
    logging.info('Sensor Enabled ....')
    d_sensor = DistanceSensor(echo=24, trigger=23, max_distance=1, threshold_distance=0.5, partial=True)
    d_sensor.when_in_range = wakeup
    d_sensor.when_out_of_range = standby
    return d_sensor


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

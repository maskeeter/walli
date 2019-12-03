import os


def turn_on():
    os.popen('vcgencmd display_power 1')


def turn_off():
    os.popen('vcgencmd display_power 0')

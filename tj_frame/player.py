import logging
import sys
from time import sleep

from omxplayer.player import OMXPlayer

from tj_frame.utils import get_file_logger, id_generator

this = sys.modules[__name__]
DEFAULT_CONFIG = ['--aspect-mode', 'Letterbox']


def add_player_log(player: OMXPlayer, name: str):
    player_log = get_file_logger('omxplayer')
    player.playEvent += lambda _: player_log.info(f"{name} : Play")
    player.pauseEvent += lambda _: player_log.info(f"{name} : Pause")
    player.stopEvent += lambda _: player_log.info(f"{name} : Stop")
    player.exitEvent += lambda _, exit_code: player_log.info(f"{name} : Exit: {exit_code}")


def prepare_player(player: OMXPlayer, name: str = "player"):
    player.playEvent += lambda _: player.show_video()
    player.pauseEvent += lambda _: player.hide_video()
    add_player_log(player, name)


def run_omx_player_stream(stream: str, options: list = None, pause: bool = False):
    if options is None:
        options = DEFAULT_CONFIG
    player_name = f'org.mpris.MediaPlayer2.omxplayer.{id_generator()}'
    player = OMXPlayer(stream, args=options, dbus_name=player_name, pause=pause)
    sleep(3)
    logging.info(f'player created: {player_name}')
    if player:
        prepare_player(player)
        return player
    raise Exception('player not available')

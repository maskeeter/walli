import logging
import sys
from itertools import cycle
from time import sleep

from omxplayer.player import OMXPlayer, OMXPlayerDeadError

from tj_frame.extractors import run_youtube_dl_extract_stream
from tj_frame.utils import get_file_logger, id_generator, run_in_thread

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


def run_omx_player_stream(stream: str, options: list = None):
    if options is None:
        options = DEFAULT_CONFIG
    player_name = f'org.mpris.MediaPlayer2.omxplayer.{id_generator()}'
    player = OMXPlayer(stream, args=options, dbus_name=player_name)
    logging.info(f'player created: {player_name}')
    if player:
        prepare_player(player)
        return player
    raise Exception('player not available')


def shuffle_player(first, second, extractor_config, url):
    first.play()
    shuffle_player.next = run_youtube_dl_extract_stream(url, extractor_config)
    second.load(shuffle_player.next.get('url'), pause=True)
    sleep(shuffle_player.next.get('duration') - 5)
    first.pause()


shuffle_player.next = {}


def initialize_players(init_video: dict, player_options: str):
    player_1 = OMXPlayer(init_video.get('url'), args=player_options,
                         dbus_name='org.mpris.MediaPlayer2.omxplayer.playlistone', pause=True)
    player_2 = OMXPlayer(init_video.get('url'), args=player_options,
                         dbus_name='org.mpris.MediaPlayer2.omxplayer.playlisttwo', pause=True)
    shuffle_player.next = init_video
    prepare_player(player_1, "1")
    prepare_player(player_2, "2")
    return player_1, player_2


@run_in_thread
def run_omx_player_juggle_play_extract(player_1: OMXPlayer, player_2: OMXPlayer, extractor_config: dict, pl: list):
    playlist = cycle(pl)
    while True:
        try:
            shuffle_player(player_1, player_2, extractor_config, next(playlist).get('webpage_url'))
            shuffle_player(player_2, player_1, extractor_config, next(playlist).get('webpage_url'))
        except OMXPlayerDeadError as e:
            logging.error(e)
            continue

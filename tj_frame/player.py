from itertools import cycle

from omxplayer.player import OMXPlayer

from tj_frame.utils import get_file_logger, read_options

DEFAULT_CONFIG = ['--aspect-mode', 'Letterbox']


def add_player_log(player: OMXPlayer):
    player_log = get_file_logger('omxplayer')
    player.playEvent += lambda _: player_log.info("Play")
    player.pauseEvent += lambda _: player_log.info("Pause")
    player.stopEvent += lambda _: player_log.info("Stop")
    player.exitEvent += lambda _, exit_code: player_log.info(f"Exit: {exit_code}")


def prepare_player(player):
    player.playEvent += lambda _: player.show_video()
    player.pauseEvent += lambda _: player.hide_video()
    add_player_log(player)


def run_omx_player_playlist(playlist: list, config_path: str):
    options = read_options(config_path)
    options.append('--refresh')
    cyc_list = cycle(playlist)
    player = run_omx_player_stream(next(cyc_list).get('url'), options)
    player.exitEvent += lambda _, exit_code: player.load(next(cyc_list).get('url'))
    return player


def run_omx_player_stream(stream: str, options: list = None):
    if options is None:
        options = DEFAULT_CONFIG
    player = OMXPlayer(stream, args=options,
                       dbus_name='org.mpris.MediaPlayer2.omxplayer.live')  # TODO: different name for each bsu
    if player:
        prepare_player(player)
        return player
    raise Exception('player not available')

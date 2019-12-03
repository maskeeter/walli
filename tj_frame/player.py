import sys
from multiprocessing import connection
from tj_frame.utils import get_file_logger, run_in_separate_process
from omxplayer.player import OMXPlayer
from time import sleep

DEFAULT_CONFIG = []
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.players = {}


def get_channel_player(channel: str):
    print(channel)
    print(this.players)
    print(this.players.get(channel))
    if channel in this.players.keys():
        return this.players[channel]
    return None


def add_player_log(player: OMXPlayer):
    player_log = get_file_logger('omxplayer')
    player.playEvent += lambda _: player_log.info("Play")
    player.pauseEvent += lambda _: player_log.info("Pause")
    player.stopEvent += lambda _: player_log.info("Stop")


def extract_options(config: str):
    return [arg for arg in config if len(arg) and arg[0] != '#']


def run_omx_player_live(url: str, config: str):
    options = extract_options(config) if config else DEFAULT_CONFIG
    options.append('--live')
    player = OMXPlayer(url, args=options, dbus_name='org.mpris.MediaPlayer2.omxplayer.live')
    add_player_log(player)
    sleep(2.5)
    if player.is_playing():
        this.players['live'] = player
        return player
    raise Exception('player not available')


def run_omx_player_file_loop(filename: str, config: str):
    options = extract_options(config) if config else DEFAULT_CONFIG
    options.append('--loop')
    player = OMXPlayer(filename, args=options, dbus_name='org.mpris.MediaPlayer2.omxplayer.live')
    add_player_log(player)
    sleep(2.5)
    if player.is_playing():
        return player
    raise Exception('player not available')


def prepare_player(player):
    player.playEvent += lambda _: player.show_video()
    player.pauseEvent += lambda _: player.hide_video()
    add_player_log(player)


def juggle(player_1: OMXPlayer, player_2: OMXPlayer, playlist: list):
    while True:
        for i in range(0, len(playlist), 2):
            player_1.load(playlist[i].get('url'), pause=False)
            player_2.load(playlist[i + 1].get('url'), pause=True)
            sleep(playlist[i].get('duration') - 0.1)
            player_1.pause()
            player_2.play()
            sleep(playlist[i + 1].get('duration') - 0.1)
            player_2.pause()


def run_omx_player_playlist(playlist: list, config: str):
    options = extract_options(config)
    if not playlist or len(playlist) < 2:
        raise Exception('too short playlist!')
    player_1 = OMXPlayer(playlist[0].get('url'), pause=True, args=options + ['--layer', '1'],
                         dbus_name='org.mpris.MediaPlayer2.omxplayer.pl.1')
    player_2 = OMXPlayer(playlist[1].get('url'), pause=True, args=options + ['--layer', '2'],
                         dbus_name='org.mpris.MediaPlayer2.omxplayer.pl.2')
    sleep(2.5)
    prepare_player(player_1)
    prepare_player(player_2)
    juggle(player_1, player_2, playlist)
    # TODO: implement players as shared state so as to be able to control them over a separate process


@run_in_separate_process
def run_gif_tv(url: str, hashtags: list, c_connection: connection):
    # run and handle i/o of gif-tv-tool with configuration passed and signal back
    flogging = get_file_logger('giftv')
    # http://tv.giphy.com/?username=kimmyschmidt show sources and recreate slideshow using api calls
    return None

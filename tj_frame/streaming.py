import json
import logging
import sys

from omxplayer import OMXPlayer

from tj_frame.extractors import run_streamlink
from tj_frame.player import run_omx_player_stream, run_omx_player_juggle_play_extract, initialize_players
from tj_frame.utils import read_config, validate_url, read_options

this = sys.modules[__name__]
this.active_players = {}
INTRO_VIDEO = {'url': 'distributor_20th_century_fox-DWEU.mkv', 'duration': 22}


def get_active_player(channel: str):
    if channel in this.active_players.keys():
        return this.active_players[channel]
    return None


def set_active_player(player: OMXPlayer, channel: str):
    logging.info(f"Set active player {player} for channel {channel}")
    this.active_players[channel] = player


def play_playlist(player_config_path: str, extractor_config_path: str, playlist_path: str):
    extractor_config = read_config(extractor_config_path).get('youtube-dl')
    options = read_options(player_config_path) + ['--refresh']
    try:
        with open(playlist_path, 'rt') as playlist_file:
            pl = json.load(playlist_file)
        if len(pl):
            player_1, player_2 = initialize_players(INTRO_VIDEO, options)
            player_1.playEvent += lambda p: set_active_player(p, 'pl')
            player_2.playEvent += lambda p: set_active_player(p, 'pl')
            run_omx_player_juggle_play_extract(player_1, player_2, extractor_config, pl)
    except (ValueError, FileNotFoundError) as e:
        raise Exception('invalid playlist', e)


def play_live_stream(url: str, config_path: str):
    if url:
        options = read_options(config_path)
        player = run_omx_player_stream(url, options)
        if player:
            set_active_player(player, 'live')
            return
    raise Exception(f'cannot play live stream {url}')


def play_outage_footage(channel: str, message: str):
    logging.warning(f"{channel} is unavailable, error: {message}")
    options = ['--loop', '--aspect-mode', 'fill']
    player = run_omx_player_stream('file_example_MP4_1280_10MG.mp4', options)
    if player:
        set_active_player(player, 'outage')
        return
    raise Exception(f'cannot play outage footage')


def stream(channel: str, ch_config: dict):
    logging.info('streaming ...')
    try:
        player_config_path = ch_config.get('player_config')
        if channel == 'pl':
            ytdl_config_path = ch_config.get('extractor_config')
            playlist_path = ch_config.get('playlist_target')
            play_playlist(player_config_path, ytdl_config_path, playlist_path)
        elif channel == 'live':
            streamlink_config = read_config(ch_config.get('extractor_config')).get('streamlink')
            stream_url = validate_url(ch_config.get('url'), 'www.youtube.com')
            video_stream = run_streamlink(stream_url, streamlink_config)
            logging.info(f'stream extracted ...')
            play_live_stream(video_stream, player_config_path)
        else:
            logging.exception(f'invalid channel: {channel}')
    except Exception as e:
        # TODO: when failed, retry streaming the channel here
        raise e


def validate_channel_config(config: dict, channel: str):
    if channel == 'pl' and (
            "list_id" and "extractor_config" and "config_file" and "playlist_path" and "playlist_target" in config) \
            or channel == 'live' and ("url" and "player_config" in config):
        return True
    return False

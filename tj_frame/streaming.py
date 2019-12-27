import json
import logging
import sys
from time import sleep

from omxplayer import OMXPlayer

from tj_frame.extractors import run_streamlink, run_youtube_dl
from tj_frame.player import run_omx_player_playlist, run_omx_player_stream
from tj_frame.utils import read_config, validate_url, read_options, run_in_thread

this = sys.modules[__name__]
this.active_players = {}


def get_active_player(channel: str):
    if channel in this.active_players.keys():
        return this.active_players[channel]
    return None


def set_active_player(player: OMXPlayer, channel: str):
    if player.is_playing():
        this.active_players[channel] = player


@run_in_thread
def extract_playlist(list_id: str, config_path: str, playlist_path: str):
    config = read_config(config_path)
    if config:
        config = config.get('youtube-dl')
        playlist_data = run_youtube_dl(list_id, config)
        logging.info(f'playlist extracted ...')
        with open(playlist_path, 'wt+') as playlist:
            playlist.write(json.dumps(playlist_data))
    sleep(3 * 60 * 60)


def read_playlist(playlist_path: str):
    try:
        with open(playlist_path, 'rt') as playlist_file:
            return json.load(playlist_file)
    except (ValueError, FileNotFoundError) as e:
        raise Exception('invalid playlist', e)


def play_playlist(config_path: str, playlist_path: str):
    playlist = read_playlist(playlist_path)
    if len(playlist):
        player = run_omx_player_playlist(playlist, config_path)
        if player:
            set_active_player(player, 'pl')
            return
    raise Exception("cannot play playlist")


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
            playlist_path = ch_config.get('playlist_target')
            play_playlist(player_config_path, playlist_path)
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

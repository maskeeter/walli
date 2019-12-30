import json
import logging
import sys
from itertools import cycle

from omxplayer import OMXPlayer

from tj_frame.extractors import run_streamlink, run_youtube_dl_extract_stream
from tj_frame.player import run_omx_player_stream
from tj_frame.utils import read_config, validate_url, read_options

this = sys.modules[__name__]
this.active_players = {}


def get_active_player(channel: str):
    if channel in this.active_players.keys():
        return this.active_players[channel]
    return None


def set_active_player(player: OMXPlayer, channel: str):
    if player.is_playing():
        this.active_players[channel] = player


def playlist(playlist_path: str):
    try:
        # TODO: replace with extract playlist
        with open(playlist_path, 'rt') as playlist_file:
            pl = json.load(playlist_file)
        if len(pl):
            playlist.entries = cycle(pl)
    except (ValueError, FileNotFoundError) as e:
        raise Exception('invalid playlist', e)


playlist.entries = None


def play_and_prepare_next_video(current_player, config, exit_code):
    logging.info(f"Exit: {exit_code}")
    if current_player:
        print('before load')
        current_player.load(play_playlist.next)
        print('after load')
        print(next(playlist.entries))
        print(current_player.can_play())
        play_playlist.next = run_youtube_dl_extract_stream(next(playlist.entries).get('webpage_url'), config)
        print('after extractt')


def play_playlist(player_config_path: str, extractor_config_path: str):
    extractor_config = read_config(extractor_config_path).get('youtube-dl')
    if playlist.entries:
        options = read_options(player_config_path) + ['--refresh']
        print(f'hi: {options}')
        play_playlist.next = run_youtube_dl_extract_stream(next(playlist.entries).get('webpage_url'), extractor_config)
        player = run_omx_player_stream(play_playlist.next, options)
        print('\nbefore adding exit')
        player.exitEvent += lambda current_player, exit_code: play_and_prepare_next_video(current_player,
                                                                                          extractor_config, exit_code)
        print('\nafter adding exit')
        if player:
            set_active_player(player, 'pl')
            return
    raise Exception("cannot play playlist")


play_playlist.next = ''


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
            playlist(playlist_path)
            play_playlist(player_config_path, ytdl_config_path)
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

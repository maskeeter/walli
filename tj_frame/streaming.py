import json
import logging

from tj_frame import screen
from tj_frame.extractors import run_streamlink, run_youtube_dl
from tj_frame.player import run_omx_player_file_loop, run_omx_player_live, run_gif_tv, run_omx_player_playlist
from tj_frame.utils import read_config, list_updated, validate_url


def extract_playlist(list_id: str, config_path: str):
    if list_updated(list_id):
        ytdl_config = read_config(config_path)
        if ytdl_config:
            playlist_data = run_youtube_dl(list_id, ytdl_config)
            with open(ytdl_config.get('playlist_target'), 'w') as playlist:
                playlist.write(json.dumps(playlist_data))


def play_playlist(playlist_path: str, pl_config_path: str):
    pl_config = read_config(pl_config_path)
    if pl_config:
        try:
            playlist = json.loads(playlist_path)
        except ValueError as e:
            raise Exception('invalid playlist', e)
        player = run_omx_player_playlist(playlist, pl_config)
        return player
    raise Exception("unable to find playlis config")


def play_live_stream(url: str, config_path: str):
    if url:
        with open(config_path) as config:
            return run_omx_player_live(url, config.read())
    raise Exception(f'cannot extract live stream link {url}')


def play_outage_channel(channel: str, message: str):
    logging.warning(f"{channel} is unavailable, error: {message}")
    return run_omx_player_file_loop('file_example_MP4_1280_10MG.mp4', '')


def stream(channel: str, ch_config: dict):
    logging.info('streaming ...')
    player = None
    screen.turn_on()
    try:
        if channel == 'pl':
            extract_playlist(ch_config.get('list_id'), ch_config.get('extractor_config').get('youtube-dl'))
            logging.info('playlist extracted ...')
            play_playlist(ch_config.get('player_config'), ch_config.get('playlist_target'))
        elif channel == 'gif':
            player = play_gif_tv(ch_config.get('url'), ch_config.get('hashtags'))
        elif channel == 'live':
            streamlink_config = read_config(ch_config.get('extractor_config')).get('streamlink')
            video_stream = run_streamlink(validate_url(ch_config.get('url'), 'www.youtube.com'), streamlink_config)
            logging.info(f'stream extracted ...{video_stream}')
            player = play_live_stream(video_stream, ch_config.get('player_config'))
        else:
            logging.exception(f'invalid channel: {channel}')
        return player
    except Exception as e:
        # TODO: when failed, retry streaming the channel here
        raise e


def play_gif_tv(url: str, hashtags: list = None):
    return run_gif_tv(url, hashtags)


def validate_channel_config(config: dict, channel: str):
    if channel == 'pl' and (
            "list_id" and "extractor_config" and "config_file" and "playlist_path" and "playlist_target" in config) or channel == 'gif' and (
            "url" and "hashtags" in config) or channel == 'live' and ("url" and "player_config" in config):
        return True
    return False

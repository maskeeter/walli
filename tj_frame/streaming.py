import logging
import os
import re
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from omxplayer import OMXPlayer

from tj_frame import screen
from tj_frame.extractors import run_streamlink, extract_playlist
from tj_frame.player import run_omx_player_stream
from tj_frame.utils import read_config, validate_url, read_options

this = sys.modules[__name__]
this.active_players = {}
INTRO_VIDEO = {'url': 'distributor_20th_century_fox-DWEU.mp4', 'duration': 22}


def get_active_player(channel: str):
    if channel in this.active_players.keys():
        return this.active_players[channel]
    return None


def set_active_player(player: OMXPlayer, channel: str):
    logging.info(f"Set active player {player} for channel {channel}")
    this.active_players[channel] = player


def play_playlist(player_options: list, extractor_config: dict, list_id: str, playlist_target: str,
                  pause: bool):
    youtube_dl_config = extractor_config.get('youtube-dl')
    options = player_options + ['--loop']
    videos_folder = re.search(r'./(.*)/', youtube_dl_config.get("outtmpl")).group(1)
    try:
        if not os.path.isfile(f'{playlist_target}.mp4'):
            extract_playlist(list_id, videos_folder, playlist_target, youtube_dl_config)
        player = run_omx_player_stream(f'{playlist_target}.mp4', options, pause)
        if player:
            set_active_player(player, 'pl')
            return
    except (ValueError, FileNotFoundError) as e:
        raise Exception('invalid playlist', e)


def schedule_change_tapes(player_options: list, extractor_config: dict, list_id: str, playlist_target: str):
    cron = extractor_config.get("cron")
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(change_tape, 'cron', day_of_week=cron.get("day_of_week"), hour=cron.get("hour"),
                      minute=cron.get("minute"),
                      args=(player_options, extractor_config, list_id, playlist_target),
                      name='playlist download job')


def change_tape(player_options: list, extractor_config: dict, list_id: str, playlist_target: str):
    playlist_player = get_active_player('pl')
    if playlist_player and playlist_player.can_play() and playlist_player.is_playing():
        playlist_player.pauseEvent += lambda _: change_tape(player_options, extractor_config, list_id, playlist_target)
        return
    playlist_player.quit()
    os.remove(f'{playlist_target}.mp4')
    play_playlist(player_options, extractor_config, list_id, playlist_target, True)


def play_live_stream(url: str, config_path: str):
    if url:
        options = read_options(config_path)
        player = run_omx_player_stream(url, options)
        if player:
            set_active_player(player, 'live')
            return
    raise Exception(f'cannot play live stream {url}')


def stream(channel: str, ch_config: dict):
    logging.info('streaming ...')
    try:
        player_config_path = ch_config.get('player_config')
        if channel == 'pl':
            player_options = read_options(player_config_path)
            extractor_config_path = ch_config.get('extractor_config')
            extractor_config = read_config(extractor_config_path)
            list_id = ch_config.get('list_id')
            playlist_target = ch_config.get('playlist_target')
            play_playlist(player_options, extractor_config, list_id, playlist_target, False)
            schedule_change_tapes(player_options, extractor_config, list_id, playlist_target)
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


def stop_outage():
    player = get_active_player('outage')
    if player and player.is_playing():
        player.pause()


def play_outage(channel: str, message: str):
    if message:
        logging.warning(f"{channel} is unavailable, error: {message}")
    channel_player = get_active_player(channel)
    if channel_player and channel_player.is_playing():
        channel_player.quit()
    try:
        options = ['--loop', '--aspect-mode', 'fill']
        player = run_omx_player_stream('outage.mp4', options)
        if player:
            set_active_player(player, 'outage')
            return
    except Exception as e:
        logging.error(e)
        screen.turn_off()


def handle_player_error(channel: str, exit_status: int):
    pass

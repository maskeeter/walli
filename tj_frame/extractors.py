from __future__ import unicode_literals

import os
import traceback
from importlib import reload
from os import listdir
from subprocess import call

import youtube_dl
from streamlink import Streamlink

from tj_frame.utils import get_file_logger


def run_streamlink(url: str, config: dict):
    session = Streamlink()
    if config:
        for key in config.keys():
            session.set_option(key, config[key])
    flogging = get_file_logger('streamlink')
    streams = session.streams(url)
    if streams:
        resolutions = list(streams.keys())[:-2]
        flogging.info(f'found resolutions {resolutions}')
        if '720' in resolutions:
            return streams.get('720p').url
        if '480' in resolutions:
            return streams.get('480p').url
        return streams.get('best').url


def extract_playlist(playlist_id: str, videos_folder: str, target: str, config: dict):
    run_youtube_dl(playlist_id, config, videos_folder)
    with open('vids.txt', 'wt+') as list_file:
        list_file.writelines([f'file \'{videos_folder}/{f}\'\n' for f in listdir(videos_folder) if f.endswith(".mp4")])
    os.system(f'ffmpeg -loglevel quiet -y -f concat -safe 0 -i vids.txt -c copy {target}.mp4')
    os.remove(f'{videos_folder}/*.mp4')


def renew_playlist_every_day_at(renew_hour: int):
    # TODO: register a cron to re-extract file if not playing, if playing snooze
    pass


def run_youtube_dl(list_id: str, config: dict, videos_path: str):
    flogging = get_file_logger('youtube-dl')
    if config:
        config['logger'] = flogging
        upgrade_youtube_dl()
        with youtube_dl.YoutubeDL(config) as ytdl:
            flogging.info('start downloading files ...')
            try:
                if not os.path.exists(videos_path):
                    os.mkdir(videos_path)
                ytdl.extract_info(list_id, download=True)
            except Exception as e:
                traceback.print_exc()
                flogging.warning('failed to extract list')


def upgrade_youtube_dl():
    call(['pip', 'install', '--upgrade', 'youtube-dl'])
    reload(youtube_dl)

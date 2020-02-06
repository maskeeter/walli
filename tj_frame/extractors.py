from __future__ import unicode_literals

import os
import shutil
import traceback
from importlib import reload
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
    videos_path = f"./{videos_folder}"
    run_youtube_dl(playlist_id, config, videos_path)
    post_process_videos(videos_path, target)


def post_process_videos(videos_path: str, target: str):
    flogging = get_file_logger('youtube-dl')
    flogging.info("converting files to intermediate format")
    videos = [v.split('.')[0] for v in os.listdir(videos_path)]
    for video in videos:
        os.system(
            f'ffmpeg -y -loglevel panic -i {videos_path}/{video}.mp4 -c copy -bsf h264_mp4toannexb -an {videos_path}/{video}.ts')
        if os.path.exists(f'{video}.mp4'):
            os.remove(f'{video}.mp4')
    flogging.info("merging files to output")
    inputs = [f'{videos_path}/{v}.ts' for v in videos]
    os.system(f'ffmpeg -y -loglevel panic -i "concat:{"|".join(inputs)}" -c copy -bsf:a aac_adtstoasc {target}.mp4')
    shutil.rmtree(videos_path, ignore_errors=True)


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

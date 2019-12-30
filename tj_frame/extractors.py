from __future__ import unicode_literals

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


def run_youtube_dl_extract_stream(url: str, config: dict):
    flogging = get_file_logger('youtube-dl')
    print(f"\nhi: {url}")
    if config:
        config['logger'] = flogging
        if not run_youtube_dl_extract_stream.extractor:
            run_youtube_dl_extract_stream.extractor = youtube_dl.YoutubeDL(config)
        try:
            video_data = run_youtube_dl_extract_stream.extractor.extract_info(url, download=False)
            flogging.info(f'stream_extracted [{url}]')
            return video_data['url']
        except Exception as e:
            traceback.print_exc()
            flogging.warning('failed to extract url')
            upgrade_youtube_dl()


run_youtube_dl_extract_stream.extractor = None


def upgrade_youtube_dl():
    call(['pip', 'install', '--upgrade', 'youtube-dl'])
    reload(youtube_dl)

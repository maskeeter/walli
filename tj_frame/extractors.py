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


def run_youtube_dl(list_id: str, config: dict):
    flogging = get_file_logger('youtube-dl')
    if config:
        config['logger'] = flogging
        upgrade_youtube_dl()
        with youtube_dl.YoutubeDL(config) as ytdl:
            flogging.info('start extracting streams ...')
            pl_data = {}
            try:
                pl_data = ytdl.extract_info(list_id, download=False)
            except Exception as e:
                traceback.print_exc()
                flogging.warning('failed to extract list')
            items = pl_data.get('entries')
            if items and len(items) > 0:
                return list(map(lambda video: {k: video[k] for k in ('playlist_index', 'duration', 'url')}, items))
            flogging.warning('list is empty')


def upgrade_youtube_dl():
    call(['pip', 'install', '--upgrade', 'youtube-dl'])
    reload(youtube_dl)

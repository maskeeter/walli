# Walli

a raspberry pi mini tv with youtube channels that will turn on only when you're standing in front of it.

The application uses [streamlink](https://streamlink.github.io/) to extract live channel stream.
and uses [youtube-dl](https://github.com/ytdl-org/youtube-dl) to download playlist files using preconfigured [cron](https://opensource.com/article/17/11/how-use-cron-linux) jobs then merge them using (ffmpeg)[http://ffmpeg.org/]
and uses [omxplayer](https://github.com/popcornmix/omxplayer) to play both.


## Installation
Use pipenv to build the Environment and run the application:

```
pipenv install /project/path
pipenv run python -m tj_frame
```

Use walli.service with debian systemctl to autorun the script everytime the device restarts:
``` 
sudo systemctl daemon-reload
sudo systemctl enable walli.service
```

**Note:** Add an _outage.mp4_ file to working directory to play as an outage footage when one of the channels is not available (currently not configurable).

## Configuration
- **global configuration:**
  
  contains for each channel:
  - target playlist / livestream 
  - player configuration file used
  - _for playlist:_ filename used to merge downloaded files.
  
- **extractotr configuration**
    
    contains configuration for python wrappers of both [streamlink](https://streamlink.github.io/api.html#streamlink.Streamlink.set_option) and [youtube_dl](https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312), and the cron used by scheduler to schedule playlist downloads.
    
- **player configuration:**
    
    contains omxplayer configuratiton (read more about it [here](https://github.com/popcornmix/omxplayer#synopsis))

## Usage

- sensor will wake up the player when anybody is standing closer than threshold (currently hardcoded to 0.8m)
- button press will either be:
  **short** will toggle the channel
  **long** will enable/disable the sensor (and keep player at current state.)

## Circuit
![Alt text](circuit.png?raw=true "Title")

Licensed under GNU General Public License v3.0

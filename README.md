# TrackTales

A narrator for Music Player Daemon (MPD) using the OpenAI APIs.

An AI presenter for your MPD playlist. TrackTales collects data about the currently playing and queued tracks, including album art and embedded pictures, and passes this information to the gpt-4-vision-preview model from OpenAI to generate a track announcement. This announcement is synthesized with the OpenAI TTS API and inserted into the MPD playlist so that the presentation track plays between the current and next track.

Optionally, you can configure the latitude and longitude of your listener's position, and also include celestial events like sunrise and sunset, as well as weather information provided to the model.

## Prerequisites

* An OpenAI API key.
* Optionally, an OpenWeatherMap API key.
* Python.
* FFmpeg.

## Installation

```bash
pipx install git+https://github.com/mlang/tracktales
```

## Configuration

TrackTales reads its configuration from `~/.config/tracktales/tracktales.cfg`.

Here is a sample:

```
[DEFAULT]
clips-directory = openai-speech
max-prompt-tokens = 7000
min-remaining-seconds = 100
personality = nova
openai-api-key = sk-<REDACTED>
openweathermap-api-key = <REDACTED>
station = Radio Mario
max-tokens = 777
image-required = no
language = Austrian German
location = Graz
region = Austria
timezone = Europe/Vienna
latitude = 47.06
longitude = 15.45
elevation = 300

[nova]
tts-model = tts-1-hd
voice = nova
speed = 1.23
name = Nova
```

`clips-directory` is a subdirectory of the MPD `music_directory` and needs to be writable by the user who is running TrackTales.

`max-prompt-tokens` is the upper limit of the context.  If a request requires more then this amount of prompt tokens, the context is reset to the system prompt.

If `image-required` is on, tracktales will only generate a track announcements if visual artwork was found. Depending on your music collection, setting this can help to reduce anoyance and costs.

### Advanced

You can also create different personalities by adding a file to `~/.config/tracktales/<NAME>.txt`, which contains a Jinja2 template to generate the initial system prompt. Look at `nova.txt` for inspiration.

## Usage

Since TrackTales needs to place files in the MPD `music_directory`, it currently needs to be run on the same machine where MPD is running. This could theoretically be extended to support copying the files to a remote machine before performing an MPD update. However, for simplicity's sake, this isn't implemented yet.

Also, you should be aware that using TrackTales for prolonged periods of time can generate non-trivial costs. Depending on how much album art your music collection contains, an hour of usage can cost around $1.

To start generating track announcements, simply launch the `tracktales` executable.

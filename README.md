# tracktales

A narrator for Music Player Daemon (MPD) using the OpenAI APIs.

A AI presenter for your MPD playlist.
tracktales collects data about the currently playing and queued track,
including albumart and embedded pictures, and passes this information to
the gpt-4-vision-preview model from OpenAI to generate a track announcement.
This announcement is synthesized with the OpenAI TTS API and inserted
into the MPD playlist such that the presentation track plays between the
current and next track.

Optionally, you can configure the latitude and longitude of your
listeners position, and also have celestial events like sunrise and sunset,
as well as weather information provided to the model.

## Prerequisites

* You need an OpenAI API key
* Optionally, an OpenWeatherMap API key
* Python
* FFmpeg

## Installation

```bash
pipx install git+https://github.com/mlang/tracktales
```

## Configuration

tracktales reads its configuration from `~/.config/tracktales/tracktales.cfg`.

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
language = Austrian german
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

`clips-directory` is a subdirectory of MPD music_directory and needs
to be writable by the user who is running tracktales.

### Advanced

You can also create different personalities by adding a file
`~/.config/tracktales/<NAME>.txt> which contains a Jinja2 template to generate
the initial system prompt.  Look for `nova.txt` for inspiration.

## Usage

Since tracktales needs to place files in the MPD music_directory,
it currently needs to be run on the same machine where MPD is running.
This could theoretically be extended to support copying the files to a remote
machine before performing MPD update, however, for simplicities sake, this
isn't implemented yet.

Also, you should probably be warned that using tracktales for prolonged amounts
of time can generate non-trivial costs.  Depending on how much
albumart your music collection contains, a hour of usage can cost around $1.

To start generating track announcements, simply launch the tracktales executable.


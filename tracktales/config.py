from configparser import ConfigParser
from datetime import datetime, timedelta
from os import makedirs, path
from xdg import XDG_CONFIG_HOME
from zoneinfo import ZoneInfo

__all__ = ["dir", "env", "vars", "personality"]

config = ConfigParser(
    {
        "chat-model": "gpt-4-vision-preview",
        "prompt-kilotoken-price": 0.01,
        "completion-kilotoken-price": 0.03,
        "clips-directory": "openai-speech",
        "max-prompt-tokens": 7000,
        "max-tokens": 777,
        "min-remaining-seconds": 120,
        "mpd-socket": "/run/mpd/socket",
        "personality": "nova",
        "image-required": False
    }
)

dir = path.join(XDG_CONFIG_HOME, "tracktales")

files = config.read([path.join(dir, "tracktales.cfg")])



def personality():
    return config.get("DEFAULT", "personality")


if not config.has_section(personality()):
    config.add_section(personality())
    section = config[personality()]
    section["tts-model"] = "tts-1-hd"
    section["voice"] = "nova"
    section["speed"] = "1.23"
    section["name"] = "Nova"
    section["age"] = 35
    section["station"] = "Radio Mario"
    section["location"] = "Graz"
    section["region"] = "Austria"
    section["language"] = "Austrian german"

if len(files) == 0:
    if not config.has_option("DEFAULT", "openai-api-key"):
        config.set("DEFAULT", "openai-api-key", input("OpenAI API Key: "))
    if not path.isdir(dir):
        makedirs(dir)
    with open(path.join(dir, "tracktales.cfg"), "w") as file:
        config.write(file)

vars = config[personality()]


def env():
    result = dict(vars)
    for key in ("openai-api-key", "openweathermap-api-key"):
        if key in result:
            del result[key]

    return result

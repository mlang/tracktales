from datetime import datetime, timedelta
import ffmpeg
from jinja2 import Environment, ChoiceLoader, FileSystemLoader, PackageLoader
import logging
from mpd import MPDClient
from mutagen.flac import FLAC, Picture
from openai import OpenAI
import os
import requests
from signal import signal, SIGINT, SIG_IGN
import subprocess
from time import sleep
from tracktales import config
from tracktales import sensors
from wand.image import Image

logging.basicConfig(level=config.vars.get("log-level", logging.INFO))
openai = OpenAI(
    api_key=config.vars.get("openai-api-key", os.environ.get("OPENAI_API_KEY"))
)
mpd = MPDClient()
mpd.connect(config.vars.get("mpd-socket"))
music_directory = mpd.config()
clips_directory = config.vars.get("clips-directory")
template = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    loader=ChoiceLoader([
        FileSystemLoader(config.dir),
        PackageLoader("tracktales", "templates")
    ])
).get_template
messages = []
prompt_tokens = 0
completion_tokens = 0
done = False


def track_info(dict):
    if "artist" in dict and "title" in dict:
        return f"{dict['artist']} - {dict['title']}"
    return dict["file"]


def system_prompt():
    env = config.env()
    env.update(sensors.env())
    return {
        "role": "system",
        "content": template(config.personality() + ".txt").render(env)
    }


def image_url(image):
    img = Image(image=image)

    w, h = img.width, img.height

    def shrink(f, n):
        nonlocal w, h
        x = f(w, h)
        if x > n:
            factor = n / x
            h = h * factor
            w = w * factor

    shrink(max, 2000)
    shrink(min, 768)

    if (w, h) != (image.width, image.height):
        logging.info(f"Resizing {image.width}x{image.height} -> {w}x{h}")
        img.resize(round(w), round(h))

    if img.format != "jpeg":
        img.format = "jpeg"

    return {
        "type": "image_url",
        "image_url": {"url": img.data_url(), "detail": "high"}
    }


def mpd_insert(file):
    subprocess.run(["mpc", "insert", file], check=True)
    logging.info(f"Inserted {file}")
    # id = mpd.addid(file)
    # mpd.prioid(min(mpd.currentsong().get('prio', 0) + 1, 255), id)


def speech(text, time, title,
           volume=2.0, padding=1,
           model="tts-1-hd", voice="nova", speed=1.23
          ):
    format = "flac"
    timestamp = time.strftime("%Y%m%dT%H%M%S")
    filename = os.path.join(
        music_directory, clips_directory, f"{voice}-{timestamp}.{format}"
    )
    response = openai.audio.speech.create(
        input=text, speed=speed, model=model, voice=voice, response_format=format
    )
    logging.info("Adjusting audio")
    (
        ffmpeg.input("pipe:", f=format)
        .filter("volume", volume)
        .filter(
            "compand",
            attacks=0,
            points="-80/-169|-54/-80|-49.5/-64.6|-41.1/-41.1|-25.8/-15|-10.8/-4.5|0/0|20/8.3",
        )
        .filter("adelay", str(padding) + "s", all=True)
        .filter("apad", pad_dur=padding)
        .output(filename)
        .run(input=response.read(), quiet=True, overwrite_output=True)
    )

    tags = FLAC(filename)
    tags["artist"] = "OpenAI"
    tags["title"] = f"Presenting: {title}"
    tags["model"] = model
    tags["voice"] = voice
    tags["speed"] = speed
    tags["text"] = text
    tags.save()

    logging.info("Updating MPD database...")
    job = mpd.update(clips_directory)
    while mpd.status().get("updating_db") == job:
        sleep(1)

    mpd_insert(os.path.relpath(filename, music_directory))


def clean_info(info):
    for key in ("last-modified", "format", "pos", "id", "time"):
        del info[key]
    info["duration"] = datetime.utcfromtimestamp(
        float(info["duration"])
    ).time().isoformat(timespec='seconds')
    for key in ("albumart", "picture"):
        if key in info:
            del info[key]

    return info


def ctrl_c(signal, frame):
    global done

    done = True


def generate(date, prev, next, padding):
    global messages
    global prompt_tokens, completion_tokens

    image = next.get("picture", next.get("albumart"))
    env = {
        "date": date,
        "previous": clean_info(prev),
        "next": clean_info(next),
    }
    env.update(config.env())
    env.update(sensors.env())

    content = [{"type": "text", "text": template("song.txt").render(env)}]
    if image is not None:
        content.append(image_url(image))
    logging.info(content[0]['text'])
    messages.append({"role": "user", "content": content})

    int_handler = signal(SIGINT, ctrl_c)

    result = openai.chat.completions.create(
        messages=messages,
        model=config.vars.get("chat-model"),
        max_tokens=int(config.vars.get("max-tokens")),
    )

    message = result.choices[0].message
    messages.append(message)
    speech(
        message.content,
        date,
        track_info(env["next"]),
        padding=padding,
        model=config.vars.get("tts-model", "tts-1-hd"),
        voice=config.vars.get("voice", "nova"),
        speed=config.vars.get("speed", "1.0"),
    )

    prompt_tokens += result.usage.prompt_tokens
    completion_tokens += result.usage.completion_tokens

    if result.usage.prompt_tokens > int(config.vars.get("max-prompt-tokens")):
        messages = [system_prompt()]

    signal(SIGINT, int_handler)


def is_ours(info):
    return info["file"].startswith(clips_directory)


def try_generate():
    status = mpd.status()
    if "updating_db" not in status and status["state"] == "play":
        prev = mpd.currentsong()
        if "nextsongid" in status:
            next = mpd.playlistid(status["nextsongid"])[0]
            if not is_ours(prev) and not is_ours(next):
                remaining = float(status["duration"]) - float(status["elapsed"])
                if remaining >= int(config.vars.get("min-remaining-seconds")):
                    date = datetime.now() + timedelta(seconds=remaining)
                    padding = int(status.get("xfade", "0"))

                    try:
                        next["albumart"] = Image(
                            blob=mpd.albumart(next["file"])["binary"]
                        )
                    except:
                        pass
                    try:
                        next["picture"] = Image(
                            blob=mpd.readpicture(next["file"])["binary"]
                        )
                    except:
                        pass

                    generate(date, prev, next, padding)
                else:
                    logging.info("Not enough time, not generating speech.")


def estimate_cost():
    prompt = float(config.vars.get("prompt-kilotoken-price"))
    completion = float(config.vars.get("completion-kilotoken-price"))

    price = (prompt_tokens / 1000) * prompt
    price += (completion_tokens / 1000) * completion

    return price


def main():
    global messages
    global done

    messages = [system_prompt()]
    logging.info(messages[0]['content'])

    while not done:
        try_generate()
        if not done:
            try:
                logging.debug("Waiting for next track...")
                mpd.idle("player")
            except KeyboardInterrupt:
                done = True

    logging.info(f"Estimated cost = ~${estimate_cost()}")


if __name__ == "__main__":
    main()

from astral import LocationInfo
from astral.moon import moonrise, moonset, phase
from astral.sun import midnight, sun
from configparser import NoOptionError
from datetime import datetime, timedelta
import requests
from tracktales import config
from zoneinfo import ZoneInfo

__all__ = ["env"]

def celestial_events():
    try:
        location = LocationInfo(
            name=config.vars.get("location"),
            region=config.vars.get("region"),
            timezone=config.vars.get("timezone"),
            latitude=config.vars.get("latitude"),
            longitude=config.vars.get("longitude"),
        )
        observer = location.observer
        if "elevation" in config.vars:
            observer.elevation = config.vars.get("elevation")
        tomorrow = datetime.now() + timedelta(days=1)
        events = list(sun(observer, tzinfo=location.timezone).items()) + list(
            sun(observer, date=tomorrow, tzinfo=location.timezone).items()
        )
        events += [
            ("moonrise", moonrise(observer, tzinfo=location.timezone)),
            ("moonrise", moonrise(observer, date=tomorrow, tzinfo=location.timezone)),
        ]
        events += [
            ("moonset", moonset(observer, tzinfo=location.timezone)),
            ("moonset", moonset(observer, date=tomorrow, tzinfo=location.timezone)),
        ]
        events += [
            ("midnight", midnight(observer, tzinfo=location.timezone)),
            ("midnight", midnight(observer, date=tomorrow, tzinfo=location.timezone)),
        ]
        now = datetime.now(tz=ZoneInfo(key=location.timezone))
        events = sorted(
            ((label, time) for (label, time) in events if time >= now),
            key=lambda x: x[1],
        )[:8]
        return {
            "celestial_events": list(
                map(
                    lambda x: (
                        x[0],
                        x[1].replace(tzinfo=None).isoformat(timespec="minutes"),
                    ),
                    events
                )
            )
        }
    except NoOptionError:
        return {}


def owm_params():
    return {
        "lat": config.vars.get('latitude'),
        "lon": config.vars.get('longitude'),
        "units": "metric",
        "appid": config.vars.get('openweathermap-api-key', "1f68a06a8735f02c7dd2e52f8a60a9fe")
    }


def weather():
    if "latitude" in config.vars and "longitude" in config.vars:
        result = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=owm_params()
        ).json()
        for key in ("coord", "base", "sys", "dt", "timezone", "id", "name", "cod"):
            del result[key]

        main = result["main"]
        del result["main"]
        main.update(result)

        main["temp"] = int(main["temp"])
        main["phenomena"] = list(map(lambda x: x["description"], main["weather"]))
        del main["weather"]
        main["uv-index"] = requests.get(
            "https://api.openweathermap.org/data/2.5/uvi",
            params=owm_params()
        ).json()["value"]

        return {"weather": main}
    else:
        return {}

def env():
    dict = {}
    dict.update(celestial_events())
    dict.update(weather())

    return dict

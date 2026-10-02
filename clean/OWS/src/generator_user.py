
from random import choice, choices, randint, sample
from typing import TypedDict

from .user_data import DEVICES, CATEGORIES, COUNTRIES_LANGUAGES, DEVICE_WEIGHTS

class UserProfile(TypedDict):
    device: str
    channel: str
    categories: list[str]
    ad_size: tuple[int, int] | None
    region: str
    languages: list[str]
    local_hour: int

def generate_user() -> UserProfile:
    """
    Generate a random user profile. The profile is sampled as follows: 
    - 'device' is chosen from 'DEVICES' keys, weighted by 'DEVICE_WEIGHTS'.
    - 'channel' is a uniformly random channel belonging to the chosen device. 
    - 'categories' is a random non-empty subset (unique, order-undefined) of 'CATEGORIES'. 
    - 'ad_size' is a uniformly random '(width, height)' tuple for the chosen device.
    - 'region' is a uniformly random key of 'COUNTRIES_LANGUAGES'. 
    - 'languages' is a random non-empty subset of the languages belonging to the chosen region. 
    - 'local_hour' is an integer in '[0, 23]'. Hours 19–23 are three times as likely as hours
    0–18, so the hour distribution is biased toward the evening. 
    """
    
    device = choices(list(DEVICES.keys()), weights=DEVICE_WEIGHTS, k=1)[0]
    channel = choice(DEVICES[device]["channels"])
    categories = sample(CATEGORIES, k=randint(1, len(CATEGORIES)))
    ad_size = choice(DEVICES[device]["ad_sizes"])
    region = choice(list(COUNTRIES_LANGUAGES.keys()))
    languages = sample(
        COUNTRIES_LANGUAGES[region],
        k=randint(1, len(COUNTRIES_LANGUAGES[region]))
    )
    local_hour = choices(
        list(range(24)),
        weights=[1] * 19 + [3] * 5,
        k=1,
    )[0] # we generate more hours between 19 and 23

    user_info = {
            "device": device,
            "channel": channel,
            "categories": categories,
            "ad_size": ad_size,
            "region": region,
            "languages": languages,
            "local_hour": local_hour,
    }
    
    return user_info

def main() -> dict:
   return  generate_user()

if __name__ == "__main__":
    main()


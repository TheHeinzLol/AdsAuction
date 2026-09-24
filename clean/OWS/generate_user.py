
from random import choice, choices, randint, sample

from .user_data import DEVICES, CATEGORIES, COUNTRIES_LANGUAGES, DEVICE_WEIGHTS

def main() -> dict:

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

if __name__ == "__main__":
    main()


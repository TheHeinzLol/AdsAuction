
import logging

from random import choice, choices, randint, sample

logger = logging.getLogger(__name__)

CHANNELS = [
    "audio streaming",
    "maps",
    "search",
    "social",
    "video streaming",
]

CATEGORIES = [
    "technology",
    "beauty",
    "gaming",
    "sports",
    "finance",
    "fashion",
    "health",
    "food",
    "pets",
    "movies",
    "music"
]

PLACEMENT_TYPES = [
    "banner",
    "sidebar",
    "interstitial",
    "rewarded video",
    "native",
    "audio",
    "preroll",
    "midroll",
    "billboard"
]

AD_SIZES = [
    [300, 250],
    [728, 90],
    [160, 600],
    [1920, 1080],
    [1080, 1920]
]
countries_languages = {
    "IND": ["Hindi", "English"],
    "CHN": ["Mandarin Chinese", "English"],
    "USA": ["English", "Spanish"],
    "IDN": ["Indonesian"],
    "PAK": ["Urdu", "English"],
    "NGA": ["English", "Hausa", "Yoruba", "Igbo"],
    "BRA": ["Portuguese", "English"],
    "BGD": ["Bengali"],
    "RUS": ["Russian"],
    "MEX": ["Spanish", "English"],
    "JPN": ["Japanese", "English"],
    "ETH": ["Amharic"],
    "PHL": ["Filipino", "English"],
    "EGY": ["Arabic"],
    "COD": ["French", "Lingala", "Swahili"],
}
country_list = list(countries_languages.keys())

# helper functions
def check_argument_length(channels, categories, placement_types) -> None:
    if not (channels and categories and placement_types):
        raise ValueError(f"""channels, categories, and placement types must be greater than 0.
        Got: channels len = {len(channels)},
        categories len = {len(categories)},
        placements_type len = {len(placement_types)}""")

def generate_base() -> dict:
    """Returns basic user info: local time, region, and language"""
    # generate local time
    local_hour = randint(0, 23)
    # generate region
    region = choice(country_list)
    # take languages of generated region
    languages_set =  list({lang for lang in countries_languages[region]})
    # and pick random number of those
    languages = sample(languages_set, k=randint(1, len(languages_set)))

    ssp_user = {
            'local_hour': local_hour,
            'region': region,
            'languages': languages
            }
    return ssp_user
   
def weighted_sample_without_replacement(items: list, weights: list[float], k: int):
    """
    Select k unique items from a list with weighted probability without replacement.
    
    Each item's chance of being selected is proportional to its corresponding weight.
    Once an item is selected, it is removed from consideration for subsequent picks.
    
    Args:
        items: List of elements to sample from.
        weights: List of non-negative numeric weights corresponding to each item.
            Must be same length as items.
        k: Number of unique items to select. Must be <= len(items).
    
    Returns:
        A list of k unique items selected from the original list in the order they were chosen.
    
    Raises:
        ValueError: If items and weights have different lengths, if k exceeds the number of items,
            or if any weight is negative.
    """
    if len(items) != len(weights):
        raise ValueError(f"Items and weights must have same length. Got {len(items)} and {len(weights)}")
    if k > len(items):
        raise ValueError(f"k must be not greater than length of item list. Got k={k},"\
                f"item list length={len(items)}")
    # copy so that original lists are not edited
    items = items[:]
    weights = weights[:]
    selected = []

    for _ in range(k):
        chosen = choices(items, weights=weights, k=1)[0]

        idx = items.index(chosen)

        selected.append(chosen)

        items.pop(idx)
        weights.pop(idx)

    return selected

# generation
def generate_portable_screen_user(
                                channels: list[str], 
                                categories: list[str],
                                placement_types: list[str],
                                ad_sizes: list[list[int]]
) -> dict:
    check_argument_length(channels, categories, placement_types)
    # weights to base generation on
    weights_channels = [0.1, 0.1, 0.3, 0.3, 0.1] 
    # generating user info
    ssp_user_info = generate_base()
    ssp_user_info['device'] = choices(
            ["pc", "phone", "TV"],
            weights=[0.4, 0.5, 0.1],
            k=1
        )[0]
    ssp_user_info["channel"] = weighted_sample_without_replacement(
                items=channels,
                weights=weights_channels,
                k=1
                )[0]
    ssp_user_info["categories"] = sample(
            categories, 
            k=randint(1, len(categories)))
    ssp_user_info["ad_size"] = choice(ad_sizes)

    logger.debug(f"Generated portable screen user info: {ssp_user_info}")
    return ssp_user_info

def generate_speaker_user(categories: list[str]) -> dict:

    ssp_user_info = generate_base()
    ssp_user_info["device"] = "smart speaker"
    ssp_user_info["channel"] = "audio streaming"
    ssp_user_info["categories"] = sample(categories, k=randint(1, len(categories)))
    ssp_user_info["ad_size"]= None
    logger.debug(f"Generated speaker user info: {ssp_user_info}")
    return ssp_user_info

def generate_billboard_user(
        categories: list[str],
        ad_sizes: list[list[int]]
) -> dict:
    ssp_user_info = generate_base()
    ssp_user_info["device"] = "billboard"
    ssp_user_info["channel"] = "billboard display"
    ssp_user_info["categories"] = sample(categories, k=randint(1, len(categories)))
    ssp_user_info["ad_size"]= choice(ad_sizes)
    logger.debug(f"Generated billboard user info: {ssp_user_info}")
    return ssp_user_info

def generate_ssp_user(idx: int):
    # this is needed so that python does not run all generate_*_user 
    # functions before random.choices chooses one
    generators = [
        lambda: generate_portable_screen_user(CHANNELS, CATEGORIES, PLACEMENT_TYPES, AD_SIZES),
        lambda: generate_speaker_user(CATEGORIES),
        lambda: generate_billboard_user(CATEGORIES, AD_SIZES)
    ]
    chosen_generator = choices(generators, weights=[0.8, 0.1, 0.1], k=1)[0]
    ssp_user_info = chosen_generator()
    ssp_user_info['id'] = idx
    return ssp_user_info

if __name__ == "__main__":
    print(generate_ssp_user())


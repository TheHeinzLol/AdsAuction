
import logging

from datetime import datetime, timedelta, timezone
from random import choice, randint, sample

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

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
                "item list length={len(items)}")
    items = items[:]
    weights = weights[:]

    selected = []

    for _ in range(k):
        choice = random.choices(items, weights=weights, k=1)[0]

        idx = items.index(choice)

        selected.append(choice)

        items.pop(idx)
        weights.pop(idx)

    return selected

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
devices = ["pc", "phone", "display"]
channels = ["social", "search", "streaming_video", "streaming_audio"]
categories = ["technology", "pets", "beauty", "healthcare", "games", \
        "food", "automobiles"]

def generate_ssp_user_info() -> dict:
    target_time = timezone(timedelta(hours=randint(-12, 12)))

    target_regions = sample(list(country_list), k=randint(1, len(country_list)))

    languages_set =  list({lang for region in target_regions
                      for lang in countries_languages[region]})
    target_languages = sample(languages_set, k=randint(1, len(languages_set)))

    target_devices = weighted_sample_without_replacement(
                items=devices,
                weights=[0.4, 0.4, 0.2],
                k=randint(1, len(devices))
                )

    # This choise of target channels means that there might be a situation when
    # the only devise is display but channels are filled with unusable options.
    # Although this might sound like a bug or a waste of memory, there is an option
    # when bidder did not update his targets of interest, but updated the 
    # strategy in DSP service
    target_channels = weighted_sample_without_replacement(
                items=channels,
                weights=[0.4, 0.4, 0.1, 0.1],
                k=randint(1, len(channels))
                )
    # since the only channel for "display" device is "display" itself,
    # we add it if such device is in target list
    if ("display" in target_devices and "display" not in target_channels):
        target_channels.append("display")

    target_categories = sample(
            categories, 
            k=randint(1, len(categories)))

    ssp_user_info = {
            'is_active': choice([True, False], weights=[0.9, 0.1]),
            'target_regions': target_regions,
            'target_languages': target_languages,
            'target_devices': target_devices,
            'target_channels': target_channels,
            'target_categories': target_categories,
            }

    logger.debug(f"Generated user info: {ssp_user_info}")
    return ssp_user_info


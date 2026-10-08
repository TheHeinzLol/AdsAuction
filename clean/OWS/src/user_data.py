
COUNTRIES_LANGUAGES = {
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

CATEGORIES = list({
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
})

DEVICES = {
    "pc": {
            "channels": ["audio streaming", "maps", "search", "social", "video streaming"],
            "ad_sizes": [(300, 250), (728, 90), (160, 600), (1920, 1080), (1080, 1920)]
    },
    "phone": {
            "channels": ["audio streaming", "maps", "search", "social", "video streaming"],
            "ad_sizes": [(300, 250), (728, 90), (160, 600)]
    },
    "tablet": {
            "channels": ["audio streaming", "maps", "search", "social", "video streaming"],
            "ad_sizes": [(300, 250), (728, 90), (160, 600), (768, 1024)]
    },
    "billboard": {
            "channels": ["billboard"],
            "ad_sizes": [(1920, 1080), (3840, 2160)]
    },
    "speaker": {
            "channels": ["audio streaming"],
            "ad_sizes":[None]
    }
}

DEVICE_WEIGHTS = [0.35, 0.50, 0.10, 0.04, 0.01]

# ===== VALIDATION =====
# Fail fast if data is invalid

assert len(CATEGORIES) > 0, "CATEGORIES is empty"
assert len(COUNTRIES_LANGUAGES) > 0, "COUNTRIES_LANGUAGES is empty"
assert len(DEVICES) > 0, "DEVICES is empty"
assert len(DEVICE_WEIGHTS) == len(DEVICES), "DEVICE_WEIGHTS length mismatch"

# Validate languages per country
for country, langs in COUNTRIES_LANGUAGES.items():
    assert len(langs) > 0, f"{country} has no languages"
    assert len(langs) == len(set(langs)), f"{country} has duplicate languages"

# Validate devices
for device, data in DEVICES.items():
    channels = data["channels"]
    sizes = data["ad_sizes"]
    
    assert len(channels) > 0, f"{device} has no channels"
    assert len(channels) == len(set(channels)), f"{device} has duplicate channels"
    
    assert len(sizes) > 0, f"{device} has no ad_sizes"
    assert len(sizes) == len(set(sizes)), f"{device} has duplicate ad sizes"


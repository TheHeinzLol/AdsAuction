
from prometheus_client import Counter

AD_REQUESTS_SENT = Counter(
        "ows_ad_requests_sent_total",
        "Total number of ad requests",
        ["status"],  # success | error
)

RENDERS_CONFIRMED = Counter(
        "ows_renders_confirmed_total",
        "Total number of confirmed renders",
)

RENDERS_SKIPPED = Counter(
        "ows_renders_skipped_total",
        "Total number of skipped renders",
)


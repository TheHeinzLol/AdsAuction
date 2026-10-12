from prometheus_client import Counter, Histogram

AD_REQUEST_DURATION = Histogram(
        "ows_ad_request_duration",
        "Response time for ad request in ms",
        ['status'],
        buckets=(10, 25, 50, 75, 90, 100, 110, 125, 150, 175, 200, "+inf")
)

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


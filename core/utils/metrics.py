from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

# /auth/me cache metrics
AUTHME_REQUESTS = Counter(
    "authme_cache_requests_total",
    "Total /auth/me cache requests by outcome",
    labelnames=("outcome",),
)

AUTHME_INVALIDATIONS = Counter(
    "authme_cache_invalidations_total",
    "Total /auth/me cache invalidations by reason",
    labelnames=("reason",),
)

AUTHME_BUILD_LATENCY = Histogram(
    "authme_cache_build_latency_seconds",
    "/auth/me build (no-cache) latency",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2)
)

AUTHME_ENTRIES = Gauge(
    "authme_cache_entries",
    "Current number of /auth/me cache entries (memory mode)",
)

AUTHME_AGE = Histogram(
    "authme_cache_age_seconds",
    "Age of cached /auth/me entries served",
    buckets=(0.5, 1, 2, 4, 8, 16, 32, 60, 120)
)

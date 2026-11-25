import logging

from django.core.cache import cache

from .models import Topic

logger = logging.getLogger(__name__)

TOPICS_CACHE_KEY = "topics:list"
TOPICS_CACHE_TIMEOUT = 300


def get_topics():
    """Return topics and the source they came from.

    The list is cached in Valkey for five minutes. A cache hit avoids a
    PostgreSQL query; a miss reads PostgreSQL and fills the cache.
    """
    topics = cache.get(TOPICS_CACHE_KEY)
    if topics is not None:
        logger.info("TOPICS_CACHE hit key=%s", TOPICS_CACHE_KEY)
        return topics, "cache"

    logger.info("TOPICS_CACHE miss key=%s", TOPICS_CACHE_KEY)
    topics = list(
        Topic.objects.order_by("order", "id").values(
            "id", "name", "slug", "description"
        )
    )
    cache.set(TOPICS_CACHE_KEY, topics, timeout=TOPICS_CACHE_TIMEOUT)
    return topics, "database"

"""In-memory cache shared between tap streams during a single sync run."""

CACHE = {}


def add(key, val):
    """Store *val* under *key* in the shared cache."""
    CACHE[key] = val


def get(key):
    """Return the cached value for *key*, or None if not present."""
    return CACHE.get(key)

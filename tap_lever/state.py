"""State management helpers for Singer bookmarks."""

import json
import singer

from dateutil.parser import parse

LOGGER = singer.get_logger()


def get_last_record_value_for_table(state, table):
    """Return the last bookmarked datetime for *table*, or None if not yet set."""
    last_value = state.get('bookmarks', {}) \
                      .get(table, {}) \
                      .get('last_record')

    if last_value is None:
        return None

    return parse(last_value)


def incorporate(state, table, field, value):
    """Advance the bookmark for *table*/*field* to *value* if it is more recent."""
    if value is None:
        return state

    new_state = state.copy()

    parsed = parse(value).strftime("%Y-%m-%dT%H:%M:%SZ")

    if 'bookmarks' not in new_state:
        new_state['bookmarks'] = {}

    if(new_state['bookmarks'].get(table, {}).get('last_record') is None or
       new_state['bookmarks'].get(table, {}).get('last_record') < value):
        new_state['bookmarks'][table] = {
            'field': field,
            'last_record': parsed,
        }

    return new_state


def save_state(state):
    """Write current state to stdout via singer.write_state."""
    if not state:
        return

    LOGGER.info('Updating state.')

    singer.write_state(state)


def load_state(filename):
    """Load state from *filename* and return as a dict; returns {} when filename is None."""
    if filename is None:
        return {}

    try:
        with open(filename, encoding='utf-8') as handle:
            return json.load(handle)
    except Exception as exc:
        LOGGER.fatal("Failed to decode state file. Is it valid json?")
        raise RuntimeError("Failed to decode state file") from exc

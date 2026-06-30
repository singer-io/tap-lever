import singer

from tap_lever.client import LeverForbiddenError

LOGGER = singer.get_logger()  # noqa


def discover(client, config, state, available_streams):
    """
    Check stream access, build and return the catalog dict.
    Inaccessible parent streams (and their children) are excluded.
    Raises LeverForbiddenError if no parent stream is accessible.
    """
    inaccessible_tables = _get_inaccessible_tables(client, config, state, available_streams)

    accessible_parents = [
        s for s in available_streams
        if s.PARENT is None and s.TABLE not in inaccessible_tables
    ]
    if not accessible_parents:
        raise LeverForbiddenError(
            "HTTP-error-code: 403, Error: The credentials do not have "
            "'read' access to any supported streams."
        )

    if inaccessible_tables:
        LOGGER.warning(
            "No 'read' access to stream(s): %s. Excluded from catalog.",
            ", ".join(sorted(inaccessible_tables)),
        )

    return {"streams": _build_catalog_entries(config, state, available_streams, inaccessible_tables)}


def _get_inaccessible_tables(client, config, state, available_streams):
    inaccessible = set()
    for stream_cls in available_streams:
        stream = stream_cls(config, state, None, client)
        if not stream.check_access():
            inaccessible.add(stream_cls.TABLE)
    return inaccessible


def _build_catalog_entries(config, state, available_streams, inaccessible_tables):
    catalog = []
    for stream_cls in available_streams:
        if stream_cls.TABLE in inaccessible_tables:
            continue
        if stream_cls.PARENT and stream_cls.PARENT in inaccessible_tables:
            LOGGER.warning(
                "Stream '%s' excluded from catalog because its parent stream '%s' is not accessible.",
                stream_cls.TABLE, stream_cls.PARENT,
            )
            continue

        stream = stream_cls(config, state, None, None)
        for entry in stream.generate_catalog():
            replication_method = entry.get("replication_method")
            replication_keys = entry.get("replication_keys", [])

            if replication_method == "FULL_TABLE":
                entry.pop("replication_keys", None)
            elif replication_method == "INCREMENTAL" and not replication_keys:
                raise ValueError(
                    f"Stream '{entry.get('stream')}' is marked as INCREMENTAL "
                    f"but has no replication_keys defined."
                )

            catalog.append(entry)
    return catalog

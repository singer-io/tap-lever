#!/usr/bin/env python3

import json
import singer
import sys

from tap_lever.client import LeverClient, LeverForbiddenError
from tap_lever.streams import AVAILABLE_STREAMS
from tap_lever.state import save_state
from tap_lever.streams.base import is_stream_selected

LOGGER = singer.get_logger()  # noqa


class LeverRunner:

    def __init__(self, args, client, available_streams):
        self.config = args.config
        self.state = args.state
        self.catalog = args.catalog
        self.client = client
        self.available_streams = available_streams

    def do_discover(self):
        LOGGER.info("Starting discovery.")

        # Check read access for each stream; child streams always pass.
        inaccessible_tables = set()
        for available_stream in self.available_streams:
            stream = available_stream(self.config, self.state, None, self.client)
            if not stream.check_access():
                inaccessible_tables.add(available_stream.TABLE)

        # Fail fast if no parent stream is reachable.
        accessible_parents = [
            s for s in self.available_streams
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

        catalog = []
        for available_stream in self.available_streams:
            if available_stream.TABLE in inaccessible_tables:
                continue
            if available_stream.PARENT and available_stream.PARENT in inaccessible_tables:
                LOGGER.warning(
                    "Stream '%s' excluded from catalog because its parent stream '%s' is not accessible.",
                    available_stream.TABLE, available_stream.PARENT,
                )
                continue

            stream = available_stream(self.config, self.state, None, None)

            for entry in stream.generate_catalog():
                replication_method = entry.get("replication_method")
                replication_keys = entry.get("replication_keys", [])

                if replication_method == "FULL_TABLE":
                    entry.pop("replication_keys", None)
                elif replication_method == "INCREMENTAL":
                    if not replication_keys:
                        raise ValueError(
                            f"Stream '{entry.get('stream')}' is marked as INCREMENTAL "
                            f"but has no replication_keys defined."
                        )

                catalog.append(entry)

        json.dump({'streams': catalog}, sys.stdout, indent=4)

    def get_streams_to_replicate(self):
        streams = []
        opportunity_child_catalogs = {}

        if not self.catalog:
            return streams, opportunity_child_catalogs
        for stream_catalog in self.catalog.streams:
            if not is_stream_selected(stream_catalog):
                LOGGER.info("'{}' is not marked selected, skipping."
                            .format(stream_catalog.stream))
                continue

            for available_stream in self.available_streams:
                if available_stream.matches_catalog(stream_catalog):
                    if not available_stream.requirements_met(self.catalog):
                        raise RuntimeError(
                            "{} requires that that the following are "
                            "selected: {}"
                            .format(stream_catalog.stream,
                                    ','.join(available_stream.REQUIRES)))

                    if available_stream.TABLE in {'opportunity_applications',
                                                  'opportunity_offers',
                                                  'opportunity_referrals',
                                                  'opportunity_resumes'}:
                        LOGGER.info('Will sync %s during the Opportunity stream sync', available_stream.TABLE)
                        opportunity_child_catalogs[available_stream.TABLE] = stream_catalog
                    else:
                        to_add = available_stream(self.config, self.state, stream_catalog, self.client)
                        streams.append(to_add)

        return (streams, opportunity_child_catalogs)

    def do_sync(self):
        LOGGER.info("Starting sync.")

        streams, opportunity_child_catalogs = self.get_streams_to_replicate()

        if any(streams):
            LOGGER.info('Will sync: %s', ', '.join([stream.TABLE for stream in streams]))

        for stream in streams:
            stream.state = self.state

            if stream.TABLE == 'opportunities':
                stream.sync(opportunity_child_catalogs)
            else:
                stream.sync()
            self.state = stream.state
        save_state(self.state)


@singer.utils.handle_top_exception(LOGGER)
def main():
    args = singer.utils.parse_args(required_config_keys=['token'])
    client = LeverClient(args.config)
    runner = LeverRunner(
        args, client, AVAILABLE_STREAMS)

    if args.discover:
        runner.do_discover()
    else:
        runner.do_sync()


if __name__ == '__main__':
    main()

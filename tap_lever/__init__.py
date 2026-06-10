#!/usr/bin/env python3
"""Singer tap entry point and sync orchestration for the Lever API."""

import json
import sys

import singer

from tap_lever.client import LeverClient, LeverForbiddenError
from tap_lever.streams import AVAILABLE_STREAMS
from tap_lever.state import save_state
from tap_lever.streams.base import is_stream_selected

LOGGER = singer.get_logger()  # noqa


class LeverRunner:
    """Orchestrates discovery and sync for the Lever tap."""

    def __init__(self, args, client, available_streams):
        """Initialise the runner with parsed CLI args, an authenticated client and streams."""
        self.config = args.config
        self.state = args.state
        self.catalog = args.catalog
        self.client = client
        self.available_streams = available_streams

    def do_discover(self):
        """Probe each stream for read access and emit an accessible catalog to stdout."""
        LOGGER.info("Starting discovery.")

        parent_streams = [s for s in self.available_streams if s.PARENT is None]

        inaccessible_parents = set()
        for stream_cls in parent_streams:
            stream = stream_cls(self.config, {}, None, self.client)
            if not stream.check_access():
                inaccessible_parents.add(stream_cls.TABLE)

        if len(inaccessible_parents) == len(parent_streams):
            raise LeverForbiddenError(
                "HTTP-error-code: 403, Error: The account credentials supplied do not have "
                "'read' access to any of the streams supported by the tap. Data collection "
                "cannot be initiated due to lack of permissions."
            )

        if inaccessible_parents:
            LOGGER.warning(
                "The account credentials supplied do not have 'read' access to the "
                "following stream(s): %s. These streams have been excluded from the catalog.",
                ", ".join(sorted(inaccessible_parents)),
            )

        inaccessible = set(inaccessible_parents)
        for stream_cls in self.available_streams:
            if stream_cls.PARENT and stream_cls.PARENT in inaccessible:
                LOGGER.warning(
                    "Stream '%s' excluded from catalog because its parent stream "
                    "'%s' is not accessible.",
                    stream_cls.TABLE,
                    stream_cls.PARENT,
                )
                inaccessible.add(stream_cls.TABLE)

        catalog = []
        for available_stream in self.available_streams:
            if available_stream.TABLE in inaccessible:
                continue

            stream = available_stream(self.config, {}, None, self.client)

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
        """Return the list of selected streams and opportunity child catalogs to sync."""
        streams = []
        opportunity_child_catalogs = {}

        if not self.catalog:
            return streams, opportunity_child_catalogs
        for stream_catalog in self.catalog.streams:
            if not is_stream_selected(stream_catalog):
                LOGGER.info("'%s' is not marked selected, skipping.", stream_catalog.stream)
                continue

            for available_stream in self.available_streams:
                if available_stream.matches_catalog(stream_catalog):
                    if not available_stream.requirements_met(self.catalog):
                        raise RuntimeError(
                            f"{stream_catalog.stream} requires that that the following "
                            f"are selected: {','.join(available_stream.REQUIRES)}"
                        )

                    if available_stream.TABLE in {
                        'opportunity_applications',
                        'opportunity_offers',
                        'opportunity_referrals',
                        'opportunity_resumes',
                    }:
                        LOGGER.info(
                            'Will sync %s during the Opportunity stream sync',
                            available_stream.TABLE,
                        )
                        opportunity_child_catalogs[available_stream.TABLE] = stream_catalog
                    else:
                        to_add = available_stream(
                            self.config, self.state, stream_catalog, self.client,
                        )
                        streams.append(to_add)

        return (streams, opportunity_child_catalogs)

    def do_sync(self):
        """Execute an incremental or full-table sync for all selected streams."""
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
    """Parse CLI args, create an authenticated client and run discovery or sync."""
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

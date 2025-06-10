import inspect
import math
import os
import pytz
import singer
import singer.utils
import singer.metrics

from datetime import timedelta, datetime

from singer import metadata as meta
from tap_lever.streams import cache as stream_cache
from tap_lever.config import get_config_start_date
from tap_lever.state import incorporate, save_state, \
    get_last_record_value_for_table


LOGGER = singer.get_logger()


def is_stream_selected(stream):
    stream_metadata = meta.to_map(stream.metadata)

    selected = meta.get(stream_metadata, (), 'selected')
    inclusion = meta.get(stream_metadata, (), 'inclusion')
    if inclusion == 'unsupported':
        return False
    if selected is not None:
        return selected

    return inclusion == 'automatic'


class BaseStream:
    KEY_PROPERTIES = ['id']
    CACHE_RESULTS = False
    TABLE = None
    API_METHOD = 'GET'
    REQUIRES = []

    def __init__(self, config, state, catalog, client):
        self.config = config
        self.state = state
        self.catalog = catalog
        self.client = client
        self.substreams = []

    def get_class_path(self):
        return os.path.dirname(inspect.getfile(self.__class__))

    def load_schema_by_name(self, name):
        return singer.utils.load_json(
            os.path.normpath(
                os.path.join(
                    self.get_class_path(),
                    '../schemas/{}.json'.format(name))))

    def get_schema(self):
        return self.load_schema_by_name(self.TABLE)

    @classmethod
    def requirements_met(cls, catalog):
        selected_streams = [
            s.stream for s in catalog.streams if is_stream_selected(s)
        ]

        return set(cls.REQUIRES).issubset(selected_streams)

    @classmethod
    def matches_catalog(cls, stream_catalog):
        return stream_catalog.stream == cls.TABLE

    def generate_catalog(self):
        schema = self.get_schema()
        mdata = singer.metadata.new()

        mdata = singer.metadata.write(
            mdata,
            (),
            'inclusion',
            'available'
        )

        for field_name, field_schema in schema.get('properties').items():
            inclusion = 'available'

            if field_name in self.KEY_PROPERTIES:
                inclusion = 'automatic'

            mdata = singer.metadata.write(
                mdata,
                ('properties', field_name),
                'inclusion',
                inclusion
            )

        return [{
            'tap_stream_id': self.TABLE,
            'stream': self.TABLE,
            'key_properties': self.KEY_PROPERTIES,
            'schema': self.get_schema(),
            'metadata': singer.metadata.to_list(mdata)
        }]

    def transform_record(self, record):
        with singer.Transformer() as tx:
            metadata = {}

            if self.catalog.metadata is not None:
                metadata = singer.metadata.to_map(self.catalog.metadata)

            return tx.transform(
                record,
                self.catalog.schema.to_dict(),
                metadata)

    def write_schema(self):
        singer.write_schema(
            self.catalog.stream,
            self.catalog.schema.to_dict(),
            key_properties=self.catalog.key_properties)

    def sync(self):
        LOGGER.info('Syncing stream {} with {}'
                    .format(self.catalog.tap_stream_id,
                            self.__class__.__name__))

        self.write_schema()

        return self.sync_data()

    def get_url(self):
        return 'https://api.lever.co/v1{}'.format(self.path)

    def get_params(self, _next):
        params = {"limit": 100}
        if _next:
             params["offset"] = _next

        return params

    def sync_data(self):
        table = self.TABLE

        LOGGER.info('Syncing data for {}'.format(table))

        url = self.get_url()
        params = self.get_params(_next=None)
        resources = self.sync_paginated(url, params)

        if self.CACHE_RESULTS:
            stream_cache.add(table, resources)
            LOGGER.info('Added {} {}s to cache'.format(len(resources), table))

        LOGGER.info('Reached end of stream, moving on.')
        save_state(self.state)
        return self.state

    def sync_paginated(self, url, params=None):
        table = self.TABLE
        _next = True
        page = 1

        all_resources = []
        transformer = singer.Transformer(singer.UNIX_MILLISECONDS_INTEGER_DATETIME_PARSING)
        while _next is not None:
            result = self.client.make_request(url, self.API_METHOD, params=params)
            _next = result.get('next')
            data = self.get_stream_data(result['data'], transformer)

            with singer.metrics.record_counter(endpoint=table) as counter:
                singer.write_records(
                    table,
                    data)
                counter.increment(len(data))
                all_resources.extend(data)

            if _next:
                params['offset'] = _next

            LOGGER.info('Synced page {} for {}'.format(page, self.TABLE))
            page += 1
        transformer.log_warning()
        return all_resources

    def get_stream_data(self, result, transformer):
        metadata = {}

        if self.catalog.metadata is not None:
            metadata = singer.metadata.to_map(self.catalog.metadata)

        return [
            transformer.transform(record, self.catalog.schema.to_dict(), metadata)
            for record in result
        ]

class TimeRangeStream(BaseStream):
    RANGE_FIELD = 'updated_at'

    def get_params(self, start, end):
        return {
            self.RANGE_FIELD + '_start': int(start.timestamp() * 1000),
            self.RANGE_FIELD + '_end': int(end.timestamp() * 1000),
            "limit": 100
        }

    def sync_data(self):
        table = self.TABLE

        date = get_last_record_value_for_table(self.state, table)

        if date is None:
            date = get_config_start_date(self.config)

        interval = timedelta(days=7)

        all_resources = []
        while date < datetime.now(pytz.utc):
            res = self.sync_data_for_period(date, interval)
            all_resources.extend(res)
            date = date + interval

        if self.CACHE_RESULTS:
            stream_cache.add(table, all_resources)
            LOGGER.info('Added {} {}s to cache'.format(len(all_resources), table))

        return self.state

    def sync_data_for_period(self, date, interval):
        table = self.TABLE

        updated_after = date
        updated_before = updated_after + interval

        LOGGER.info(
            'Syncing data from {} to {}'.format(
                updated_after.isoformat(),
                updated_before.isoformat()))

        params = self.get_params(updated_after, updated_before)
        url = self.get_url()
        res = self.sync_paginated(url, params)

        self.state = incorporate(self.state,
                                 table,
                                 self.RANGE_FIELD,
                                 date.isoformat())

        save_state(self.state)
        return res

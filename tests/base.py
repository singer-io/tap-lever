import json
import os


class LeverBaseTest:
    """Base test case for tap-lever unit tests with mocked data (not a TestCase itself)."""

    PRIMARY_KEYS = "primary_keys"
    REPLICATION_METHOD = "replication_method"
    REPLICATION_KEYS = "replication_keys"
    OBEYS_START_DATE = "obeys_start_date"
    API_LIMIT = "api_limit"

    default_start_date = "2020-01-01T00:00:00Z"

    @classmethod
    def expected_metadata(cls):
        """The expected streams and metadata about the streams."""
        return {
            "candidates": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: True,
            },
            "opportunities": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: True,
            },
            "requisitions": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: True,
            },
            "archive_reasons": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
            },
            "postings": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
            },
            "sources": {
                cls.PRIMARY_KEYS: {"text"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
            },
            "stages": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
            },
            "users": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
            },
            "candidate_applications": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "candidates"
            },
            "candidate_offers": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "candidates"
            },
            "candidate_referrals": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "candidates"
            },
            "candidate_resumes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "candidates"
            },
            "opportunity_applications": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "opportunities"
            },
            "opportunity_offers": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "opportunities"
            },
            "opportunity_referrals": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "opportunities"
            },
            "opportunity_resumes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                "parent": "opportunities"
            }
        }

    def setUp(self):
            """Set up test fixtures - override in test classes if needed."""
            self.config = {
                "token": "mock_test_token",
                "start_date": self.default_start_date
            }
            self.state = {}

    def tearDown(self):
        """Clean up after tests."""
        pass

    @staticmethod
    def get_mock_config():
        """Return mock configuration."""
        return {
            "token": "mock_test_token",
            "start_date": "2020-01-01T00:00:00Z"
        }

    @staticmethod
    def get_mock_state():
        """Return initial mock state."""
        return {}

    @staticmethod
    def _schema_path(stream_name):
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(base_dir, "tap_lever", "schemas", f"{stream_name}.json")

    @classmethod
    def _load_schema(cls, stream_name):
        with open(cls._schema_path(stream_name), "r", encoding="utf-8") as schema_file:
            return json.load(schema_file)

    @staticmethod
    def _schema_type(schema):
        """Return concrete type when schema allows null union types."""
        schema_type = schema.get("type", "object")
        if isinstance(schema_type, list):
            non_null = [item for item in schema_type if item != "null"]
            return non_null[0] if non_null else "null"
        return schema_type

    @staticmethod
    def _generate_value(schema, date_value="2024-01-01T00:00:00Z"):
        """Generate one valid mock value for a JSON-schema fragment."""
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        schema_type = LeverBaseTest._schema_type(schema)
        if schema_type == "object":
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            return {
                key: LeverBaseTest._generate_value(value, date_value=date_value)
                for key, value in properties.items()
                if key in required or LeverBaseTest._schema_type(value) != "null"
            }
        if schema_type == "array":
            return [
                LeverBaseTest._generate_value(
                    schema.get("items", {"type": "string"}),
                    date_value=date_value,
                )
            ]
        if schema_type == "string":
            fmt = schema.get("format")
            return (
                date_value
                if fmt == "date-time"
                else "mock@example.com"
                if fmt == "email"
                else "mock"
            )
        return {"integer": 1, "number": 1.0, "boolean": True}.get(schema_type)

    @classmethod
    def _generate_stream_record(cls, stream_name, date_value="2024-01-01T00:00:00Z"):
        """Generate one schema-valid record for a stream."""
        return cls._generate_value(cls._load_schema(stream_name), date_value=date_value)

from unittest import mock

from taxii2client import Collection

from src.taxii import Taxii

"""
End to end test requiring docker services to be up
"""

TAXII_HOST = 'nginx_proxy'
TAXII_PORT = '8080'
TAXII_USER = 'admin'
TAXII_PASSWORD = 'Password!'


def check_object_in_collection(collection):
    collection = Collection(
        f'http://{TAXII_HOST}:{TAXII_PORT}/default-taxii-group/collections/{collection}/',
        user=TAXII_USER,
        password=TAXII_PASSWORD,
    )
    objects = collection.get_objects()
    return len(objects.get('objects', []))


def remove_objects(collection):
    collection = Collection(
        f'http://{TAXII_HOST}:{TAXII_PORT}/default-taxii-group/collections/{collection}/',
        user=TAXII_USER,
        password=TAXII_PASSWORD,
    )
    for obj in collection.get_objects().get('objects', []):
        collection.delete_object(obj['id'])
    assert len(collection.get_objects().get('objects', [])) == 0


class TestEndToEnd:
    test_collection = 'ip-collection'

    @classmethod
    def setup_class(cls):
        taxii = Taxii()
        assert taxii, "Taxii needs to be already initialized for tests to work"
        taxii.close()

    def setup_method(self, _m):
        remove_objects(self.test_collection)

    @mock.patch("main.datalake")
    @mock.patch("src.datalake.Datalake")  # Prevent the initialisation of the datalake module
    def test_add_no_threats(self, _unused_import, mocked_datalake):
        from main import push_data_from_query_hash
        mocked_datalake.retrieve_events_from_query_hash.return_value = []

        push_data_from_query_hash('some_query_hash', collection=self.test_collection)

        assert mocked_datalake.retrieve_events_from_query_hash.called
        assert check_object_in_collection(self.test_collection) == 0

    @mock.patch("main.datalake")
    @mock.patch("src.datalake.Datalake")  # Prevent the initialisation of the datalake module
    def test_add_2_bundles(self, _unused_import, mocked_datalake):
        from main import push_data_from_query_hash
        # <editor-fold defaultstate="collapsed" desc="Bundle definition">
        stix_bundle_1 = {
            "objects": [
                {
                    "created": "2021-06-02T08:51:04.000Z",
                    "modified": "2021-06-03T03:57:46.000Z",
                    "name": "0202020202",
                    "labels": [
                        "malware"
                    ],
                    "external_references": [
                        {
                            "url": "https://ti.extranet.mrti-center.com/api/v2/mrti/threats/"
                                   "1e873d51273e85e1ee50ed7259e4a062/",
                            "source_name": "https://ti.extranet.mrti-center.com",
                            "external_id": "1e873d51273e85e1ee50ed7259e4a062"
                        }
                    ],
                    "pattern": "[x-phone-number:national_phone_number = '0202020202']",
                    "pattern_type": "stix",
                    "pattern_version": "2.1",
                    "x_score": {
                        "malware": 25
                    },
                    "type": "indicator",
                    "spec_version": "2.1",
                    "id": "indicator--53796b61-7e92-437a-b3a3-dfa53a724745",
                    "valid_from": "2021-06-04T16:23:48.667451Z"
                },
                {
                    "first_seen": "2021-06-02T08:51:04Z",
                    "last_seen": "2021-06-03T03:57:46Z",
                    "count": 1,
                    "observed_data_refs": [
                        "observed-data--d1e6c2b0-caf4-4897-9e46-81e253577f53"
                    ],
                    "type": "sighting",
                    "spec_version": "2.1",
                    "id": "sighting--b9413054-41a0-4340-ae2b-ef08c80c4580",
                    "created": "2021-06-04T16:23:48.669869Z",
                    "modified": "2021-06-04T16:23:48.669869Z",
                    "sighting_of_ref": "indicator--53796b61-7e92-437a-b3a3-dfa53a724745"
                },
                {
                    "id": "observed-data--d1e6c2b0-caf4-4897-9e46-81e253577f53",
                    "first_observed": "2021-06-02T08:51:04Z",
                    "last_observed": "2021-06-03T03:57:46Z",
                    "number_observed": 4,
                    "objects": {
                        "0": {
                            "national_phone_number": "0202020202",
                            "type": "x-phone-number",
                            "spec_version": "2.1",
                            "id": "x-phone-number--07890545-d2e8-4c35-b3b3-63943952992e"
                        }
                    },
                    "type": "observed-data",
                    "spec_version": "2.1",
                    "created": "2021-06-04T16:23:48.669368Z",
                    "modified": "2021-06-04T16:23:48.669368Z"
                }
            ],
            "type": "bundle",
            "id": "bundle--2a971953-4b80-479e-9be4-2ce129f6f70a"
        }
        stix_bundle_2 = {
            "objects": [
                {
                    "created": "2021-05-30T00:57:53.000Z",
                    "modified": "2021-05-31T16:57:52.000Z",
                    "name": "0101010101",
                    "labels": [
                        "malware"
                    ],
                    "external_references": [
                        {
                            "url": "https://ti.extranet.mrti-center.com/api/v2/mrti/threats/"
                                   "32d0710b8b1ae11dd017dd3bab37ded4/",
                            "source_name": "https://ti.extranet.mrti-center.com",
                            "external_id": "32d0710b8b1ae11dd017dd3bab37ded4"
                        }
                    ],
                    "pattern": "[x-phone-number:national_phone_number = '0101010101']",
                    "pattern_type": "stix",
                    "pattern_version": "2.1",
                    "x_score": {
                        "malware": 2
                    },
                    "type": "indicator",
                    "spec_version": "2.1",
                    "id": "indicator--4a00e0a8-3687-4c12-925e-aee41771c4d4",
                    "valid_from": "2021-06-04T16:23:48.677902Z"
                },
                {
                    "first_seen": "2021-05-30T00:57:53Z",
                    "last_seen": "2021-05-31T16:57:52Z",
                    "count": 1,
                    "observed_data_refs": [
                        "observed-data--1e857dbe-035c-4094-933f-95ffbe94a195"
                    ],
                    "type": "sighting",
                    "spec_version": "2.1",
                    "id": "sighting--03afd35e-b624-4a66-991a-613b28731a88",
                    "created": "2021-06-04T16:23:48.679915Z",
                    "modified": "2021-06-04T16:23:48.679915Z",
                    "sighting_of_ref": "indicator--4a00e0a8-3687-4c12-925e-aee41771c4d4"
                },
                {
                    "id": "observed-data--1e857dbe-035c-4094-933f-95ffbe94a195",
                    "first_observed": "2021-05-30T00:57:53Z",
                    "last_observed": "2021-05-31T16:57:52Z",
                    "number_observed": 198,
                    "objects": {
                        "0": {
                            "national_phone_number": "0101010101",
                            "type": "x-phone-number",
                            "spec_version": "2.1",
                            "id": "x-phone-number--fa434650-df89-4450-8a43-73d5fc738ef7"
                        }
                    },
                    "type": "observed-data",
                    "spec_version": "2.1",
                    "created": "2021-06-04T16:23:48.679457Z",
                    "modified": "2021-06-04T16:23:48.679457Z"
                }
            ],
            "type": "bundle",
            "id": "bundle--a0319056-ce97-47f7-b170-5a4a2d4b9e7a"
        }
        # </editor-fold>
        mocked_datalake.retrieve_events_from_query_hash.return_value = [
            stix_bundle_1,
            stix_bundle_2,
        ]

        push_data_from_query_hash('some_query_hash', collection=self.test_collection)

        assert mocked_datalake.retrieve_events_from_query_hash.called
        assert check_object_in_collection(self.test_collection) == 6  # each bundle is 3 objects

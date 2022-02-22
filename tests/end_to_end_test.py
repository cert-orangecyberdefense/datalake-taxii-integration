from unittest import mock

from taxii2client import Collection

from src.taxii import Taxii

"""
End to end test requiring docker services to be up
"""

TAXII_HOST = 'nginx-proxy'
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
                "type": "bundle",
                "id": "bundle--00086382-23e1-428e-8680-03f24e588a06",
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--fa07e316-9572-4d61-aaf5-341d593037a7",
                        "created": "2022-02-14T16:39:51.163812Z",
                        "modified": "2022-02-14T16:39:51.163812Z",
                        "pattern": "[ipv4-addr:value = '72.34.54.123']",
                        "pattern_type": "stix",
                        "pattern_version": "2.1",
                        "valid_from": "2022-02-14T16:39:51.163812Z"
                    },
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--fa07e316-9572-4d61-aaf5-341d593037a1",
                        "created": "2022-02-14T16:39:51.163812Z",
                        "modified": "2022-02-14T16:39:51.163812Z",
                        "pattern": "[ipv4-addr:value = '72.34.54.123']",
                        "pattern_type": "stix",
                        "pattern_version": "2.1",
                        "valid_from": "2022-02-14T16:39:51.163812Z"
                    },
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--fa07e316-9572-4d61-aaf5-341d593037a6",
                        "created": "2022-02-14T16:39:51.163812Z",
                        "modified": "2022-02-14T16:39:51.163812Z",
                        "pattern": "[ipv4-addr:value = '72.34.54.123']",
                        "pattern_type": "stix",
                        "pattern_version": "2.1",
                        "valid_from": "2022-02-14T16:39:51.163812Z"
                    },
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--fa07e316-9572-4d61-aaf5-341d593037a2",
                        "created": "2022-02-14T16:39:51.163812Z",
                        "modified": "2022-02-14T16:39:51.163812Z",
                        "pattern": "[ipv4-addr:value = '72.34.54.123']",
                        "pattern_type": "stix",
                        "pattern_version": "2.1",
                        "valid_from": "2022-02-14T16:39:51.163812Z"
                    },
                ],
            }
        # </editor-fold>
        mocked_datalake.retrieve_events_from_query_hash.return_value = stix_bundle_1

        push_data_from_query_hash('some_query_hash', collection=self.test_collection)

        assert mocked_datalake.retrieve_events_from_query_hash.called
        assert check_object_in_collection(self.test_collection) == 6  # each bundle is 3 objects

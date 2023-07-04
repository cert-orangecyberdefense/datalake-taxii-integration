import timeit
from typing import Iterable, List

from requests import HTTPError
from taxii2client import Collection, Server
from pymongo import MongoClient

from src.config import OCD_DTL_TAXII_HOST, OCD_DTL_TAXII_GROUP, OCD_DTL_TAXII_USER, OCD_DTL_TAXII_PASSWORD, \
    OCD_DTL_TAXII_VERIFY_SSL, OCD_DTL_TAXII_MONGO_URL
from src.exceptions import NotInitializedTaxiiServer
from src.logger import logger
from src.types import DtlStixEvent


class Taxii:
    """Abstraction of the Taxii server"""

    def __init__(self):
        self.server = Server(
            f'{OCD_DTL_TAXII_HOST}/taxii2/',
            user=OCD_DTL_TAXII_USER,
            password=OCD_DTL_TAXII_PASSWORD,
            verify=OCD_DTL_TAXII_VERIFY_SSL
        )
        self.check_mongo_initialized()
        self.api_root = self.find_api_root(OCD_DTL_TAXII_GROUP)
        if not self.api_root:
            raise ValueError('Couldn\'t find the API root, please check the config')

        self.collection = {}  # collection indexed by id
        for existing_collection in self.api_root.collections:
            self.collection[existing_collection.id] = existing_collection
        self.is_shutting_down = False

    def check_mongo_initialized(self):
        try:
            _ = self.server.title
        except HTTPError as e:
            if e.response.status_code == 500:
                raise NotInitializedTaxiiServer(f'Taxii server (at {self.server.url}) not initialized, '
                                                f'use --init to automatically set it')
            else:
                raise

    def find_api_root(self, api_root_id: str):
        for api_root in self.server.api_roots:
            if api_root.url.strip('/').split('/')[-1] == api_root_id:
                return api_root

    def check_collection_exist(self, collection_id: str):
        return collection_id in self.collection

    @staticmethod
    def _add_bundle(bundle: Iterable, collection: Collection):
        return collection.add_objects(bundle)

    def add_stix_bundles_list(self, stix_bundles_list: List[DtlStixEvent], collection_id: str):
        inserted = 0
        self.delete_prev_objects(OCD_DTL_TAXII_MONGO_URL, collection_id)
        logger.info(f'adding bundles to collection {collection_id}.')
        for stix_bundle in stix_bundles_list:
            if self.is_shutting_down:
                logger.warning('Add objects called while taxii is already shutdown, not adding objects and exiting.')
                return inserted
            inserted += self.add_stix_bundles(stix_bundle, collection_id)
        return inserted

    def add_stix_bundles(self, stix_bundle: DtlStixEvent, collection_id: str) -> int:
        """Add bundles in batch by calling add_bundle"""

        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        start_time = timeit.default_timer()
        collection = self.collection[collection_id]
        bundle_inserted_successfully = 0
        bundle_inserted_failed = 0
        if 'objects' in stix_bundle:
            stix_chunks = chunks(stix_bundle['objects'], 500)
            for stixs in stix_chunks:
                fake_bundle = {
                    "type": "bundle",
                    "objects": stixs
                }
                results = self._add_bundle(fake_bundle, collection)
                bundle_inserted_failed += results.failure_count
                bundle_inserted_successfully += results.success_count
        objects_nb = len(stix_bundle['objects']) if 'objects' in stix_bundle else 0
        logger.debug(
            'TAXII: Done with the insertion of %s objects (%s failed), after %1.2fs',
            objects_nb,
            bundle_inserted_failed,
            timeit.default_timer() - start_time,
        )
        return bundle_inserted_successfully

    def close(self):
        """Close the taxii connection by finishing to push events marked for insertion"""
        logger.warning('Gracefully shutting down the taxii connector')
        self.is_shutting_down = True
        self.server.close()

    def delete_prev_objects(self, url, collection_id):
        if self.is_shutting_down:
            logger.warning('Taxii is already shutdown, not deleting previous objects')
            return
        client = MongoClient(url)
        collection = client[OCD_DTL_TAXII_GROUP]['objects']
        logger.info(f'removing previous objects for collection {collection_id}')
        collection.delete_many({"_collection_id": collection_id})

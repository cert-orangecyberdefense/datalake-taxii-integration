import timeit
from typing import Iterable, List

from requests import HTTPError
from taxii2client import Collection, Server

from src.cache import Cache
from src.config import OCD_DTL_TAXII_HOST, OCD_DTL_TAXII_GROUP, OCD_DTL_TAXII_USER, OCD_DTL_TAXII_PASSWORD
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
        )
        self.check_mongo_initialized()
        self.api_root = self.find_api_root(OCD_DTL_TAXII_GROUP)
        if not self.api_root:
            raise ValueError('Couldn\'t find the API root, please check the config')

        self.cache = Cache()
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

    def add_stix_bundles(self, stix_bundles: List[DtlStixEvent], collection_id: str):
        """Add bundles in batch by calling add_bundle"""
        start_time = timeit.default_timer()
        if self.is_shutting_down:
            logger.warning('Add objects called while taxii is already shutdown')
            return  # close() has already been called

        collection = self.collection[collection_id]
        bundle_inserted_successfully = 0
        bundle_inserted_failed = 0

        for bundle in stix_bundles:
            results = self._add_bundle(bundle, collection)
            bundle_inserted_failed += results.failure_count
            bundle_inserted_successfully += results.success_count
            if bundle_inserted_failed == 0:
                self.add_bundle_to_cache(bundle)  # Save it so we don't download it from Datalake again

        logger.debug(
            'TAXII: Done with the insertion of %s objects (%s failed), after %1.2fs',
            len(stix_bundles),
            bundle_inserted_failed,
            timeit.default_timer() - start_time,
        )
        return bundle_inserted_successfully

    def add_bundle_to_cache(self, bundle):
        references = bundle['objects'][0]['external_references']
        if len(references) != 1:
            logger.warning('Stix format returned by the API is not as expected')
        hashkey = references[0]['external_id']
        self.cache.set(hashkey)

    def close(self):
        """Close the taxii connection by finishing to push events marked for insertion"""
        logger.warning('Gracefully shutting down the taxii connector')
        self.is_shutting_down = True
        self.server.close()

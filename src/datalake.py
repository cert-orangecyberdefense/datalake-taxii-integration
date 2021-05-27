import logging
from dataclasses import dataclass
from typing import List

from datalake_scripts import BulkSearch, AdvancedSearch
from datalake_scripts.common.base_script import BaseScripts

from src.config import OCD_DTL_API_ENV, OCD_DTL_NB_THREAT_PER_BATCH, OCD_DTL_API_LOG_LVL
from src.logger import logger
from src.types import DtlStixEvent
from src.cache import Cache


@dataclass
class ConfigArg:
    loglevel: int
    env: str


class Datalake:
    """Abstraction of the Datalake server"""

    def __init__(self):
        args = ConfigArg(loglevel=OCD_DTL_API_LOG_LVL, env=OCD_DTL_API_ENV)
        endpoint_config, _, tokens = BaseScripts().load_config(args=args)
        self.bulk_threats_api = BulkSearch(endpoint_config, args.env, tokens)
        self.threats_api = AdvancedSearch(endpoint_config, args.env, tokens)
        self.cache = Cache()

    def retrieve_events_from_query_hash(self, query_hash: str) -> List[DtlStixEvent]:
        # Retrieve all hashkeys
        bulk_search_result = self.bulk_threats_api.get_threats(
            query_hash,
            query_fields=['threat_hashkey']
        )
        hashkeys_to_retrieve = []  # buffer
        all_threats = []
        if 'results' not in bulk_search_result:
            logger.warning(f'Something wrong happened with {query_hash}, is it a valid query hash ?')
            return []

        threat_in_cache = 0
        for hashkey, *_ in bulk_search_result['results']:
            # Filter hashkeys already ingested
            if self.cache.has(hashkey):
                threat_in_cache += 1
            else:
                hashkeys_to_retrieve.append(hashkey)
                if len(hashkeys_to_retrieve) >= OCD_DTL_NB_THREAT_PER_BATCH:
                    # Retrieve threats per batch
                    threats = self.retrieve_threats_from_hashkeys(hashkeys_to_retrieve)
                    all_threats.extend(threats)
                    hashkeys_to_retrieve.clear()
        if hashkeys_to_retrieve:
            threats = self.retrieve_threats_from_hashkeys(hashkeys_to_retrieve)
            all_threats.extend(threats)
        logger.debug(f'Hashkeys already in cache {threat_in_cache}/{len(bulk_search_result["results"])}')
        return all_threats

    def retrieve_threats_from_hashkeys(self, hashkeys: list):
        query_body = self.build_query_body(hashkeys)
        batch = self.threats_api.get_threats(
            query_body,
            limit=OCD_DTL_NB_THREAT_PER_BATCH,
            response_format='application/stix+json',
        )
        return batch

    @staticmethod
    def build_query_body(hashkeys: list):
        return {
            "AND": [
                {
                    "AND": [
                        {
                            "field": "hashkey",
                            "multi_values": hashkeys,
                            "type": "filter"
                        }
                    ]
                }
            ]
        }

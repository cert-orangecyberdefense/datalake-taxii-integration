import asyncio
from dataclasses import dataclass
from typing import List

from datalake import Datalake as dtl
from datalake.common.ouput import Output


from src.config import OCD_DTL_API_ENV, OCD_DTL_API_LOG_LVL
from src.types import DtlStixEvent


@dataclass
class ConfigArg:
    loglevel: int
    env: str


class Datalake:
    """Abstraction of the Datalake server"""

    def __init__(self):
        args = ConfigArg(loglevel=OCD_DTL_API_LOG_LVL, env=OCD_DTL_API_ENV)
        self.datalake = dtl(env=args.env, log_level=args.loglevel)

    def retrieve_events_from_query_hash(self, query_hash: str) -> DtlStixEvent:
        task = self.datalake.BulkSearch.create_task(
            query_hash=query_hash,
            for_stix_export=True
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stix_events = task.download_sync(output=Output.STIX)
        loop.close()
        return stix_events

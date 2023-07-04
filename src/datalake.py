import os
import json
from typing import List
import zipfile
import time
import shutil
from dataclasses import dataclass

from datalake import Datalake as dtl
from datalake.common.ouput import Output
from src.logger import logger


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

    def retrieve_events_from_query_hash(self, query_hash: str) -> List[DtlStixEvent]:
        timestamp = int(time.time())
        output_path = f'/code/output/{query_hash}-{timestamp}.zip'
        extract_path = f"/code/output/{query_hash}-{timestamp}/"

        task = self.datalake.BulkSearch.create_task(
            query_hash=query_hash,
            for_stix_export=True
        )

        task.download_sync_stream_to_file(output=Output.STIX_ZIP, output_path=output_path)
        json_stix = self.read_zip_file(filepath=output_path, extract_path=extract_path)
        return json_stix

    def cleanup(self, filepath=None, dirpath=None):
        logger.debug("Cleaning up STIX zip export...")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Removed file {filepath}")
        if dirpath and os.path.exists(dirpath):
            shutil.rmtree(dirpath)
            logger.debug(f"Removed directory {dirpath}")
        logger.debug("Cleanup done.")

    def read_zip_file(self, filepath, extract_path):
        if not os.path.exists(filepath):
            logger.warn(f"File path {filepath} does not exist. Exiting...")
            return []

        json_files_content = []

        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            logger.debug(f"Extracted zip file to {extract_path}")

        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), 'r') as json_file:
                        logger.debug(f"Reading file {file}")
                        data = json.load(json_file)
                        json_files_content.append(data)
                        json_file.close()
        self.cleanup(filepath, extract_path)
        logger.debug(f"Returning stix content from {len(json_files_content)} files")
        return json_files_content

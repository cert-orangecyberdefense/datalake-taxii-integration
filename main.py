import datetime
import json
import logging
import sys
import threading
import timeit
from time import sleep

import schedule

from src.cache import Cache
from src.config import OCD_DTL_QUERY_CONFIG_PATH, OCD_DTL_TAXII_MONGO_URL
from src.datalake import Datalake
from src.init_taxii_mongo import init_taxii
from src.logger import configure_logging, logger
from src.signal_manager import SignalManager
from src.taxii import Taxii

configure_logging(logging.DEBUG)

if len(sys.argv) == 2 and sys.argv[1] == '--init':
    INITIATING_MODE = True
    logger.warning('Initializing the taxii server and exiting')
    if not OCD_DTL_TAXII_MONGO_URL:
        logger.error('Env OCD_DTL_TAXII_MONGO_URL not defined, should be mongodb://<login>:<password>@<host>:27017/')
        exit(1)
    init_taxii(url=OCD_DTL_TAXII_MONGO_URL)
    logger.debug('Taxii server initialized')
    exit(0)


datalake = Datalake()
taxii = Taxii()
jobs_running = set()


def job(query_hash, collection_id):
    logger.debug('Starting to process %s' % query_hash)

    try:
        start_time = timeit.default_timer()
        events_pushed = push_data_from_query_hash(query_hash, collection=collection_id)
        logger.info(
            'Done with the process of %s : %s events, after %1.2fs',
            query_hash,
            events_pushed,
            timeit.default_timer() - start_time,
        )
    except:  # noqa: E722
        logger.exception(f'Threats for query hash {query_hash} '
                         f'failed to be retrieved and injected into taxii collection: {collection_id}')
        raise
    finally:
        jobs_running.remove((query_hash, collection_id))


def push_data_from_query_hash(query_hash, *, collection: str) -> int:
    """
    Retrieve stix bundles from Datalake and push them on the Taxii server to the given collection.

    :return the number of bundles successfully inserted.
    """
    events = datalake.retrieve_events_from_query_hash(query_hash)
    bundles_inserted = taxii.add_stix_bundles(events, collection)
    return bundles_inserted


def run_threaded(job_func, *args):
    if args not in jobs_running:  # Skip already running jobs
        jobs_running.add(args)
        job_thread = threading.Thread(target=job_func, args=args)
        job_thread.start()


def register_jobs(jobs_config_path):
    with open(jobs_config_path) as json_file:
        config = json.load(json_file)

    for query in config['queries']:
        frequency = query['frequency']
        query_hash = query['query_hash']
        collection_id = query['collection_id']

        if not taxii.check_collection_exist(collection_id):
            raise ValueError(f"Collection {collection_id} doesn't exist\n"
                             f"  hint: use --init")

        frequency_number = int(frequency[:-1])
        if frequency[-1] == 's':
            schedule.every(frequency_number).seconds.do(run_threaded, job, query_hash, collection_id)
        elif frequency[-1] == 'm':
            schedule.every(frequency_number).minutes.do(run_threaded, job, query_hash, collection_id)
        elif frequency[-1] == 'h':
            schedule.every(frequency_number).hours.do(run_threaded, job, query_hash, collection_id)
        else:
            raise ValueError(f'Config expect a frequency: <x>[s|m|h], got {frequency}')

    nb_queries = len(config['queries'])
    if nb_queries == 0:
        raise ValueError('No query found')
    next_run: datetime.timedelta = schedule.next_run() - datetime.datetime.now()
    logger.info('Loaded %s queries with success, next run in %1.0f s', nb_queries, next_run.total_seconds())


if __name__ == '__main__':
    cache = Cache()
    signal_manager = SignalManager()
    register_jobs(OCD_DTL_QUERY_CONFIG_PATH)
    while not signal_manager.is_stop_requested:
        schedule.run_pending()
        sleep(1)

    taxii.close()
    cache.close()

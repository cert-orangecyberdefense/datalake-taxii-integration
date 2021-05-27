import json

from pymongo import MongoClient, IndexModel, ASCENDING

from src.logger import logger
from src.config import OCD_DTL_QUERY_CONFIG_PATH, OCD_DTL_TAXII_HOST, OCD_DTL_TAXII_GROUP


def init_taxii(url):
    client = MongoClient(url)
    db = client['discovery_database']  # Retrieve or create db
    db['discovery_information'].replace_one(
        filter={'_id': 'OCD_ON_PREMISE_SERVER'},
        replacement={
            '_id': 'OCD_ON_PREMISE_SERVER',
            'title': 'OCD on premise Taxii server',
            'description': 'TAXII Server ingesting OCD\'s Datalake feed',
            'contact': 'cert-contact.ocd@orange.com',
            'default': f'{OCD_DTL_TAXII_HOST}/{OCD_DTL_TAXII_GROUP}/',
            'api_roots': [],
        },
        upsert=True,
    )

    api_root_db = medallion_add_api_root(
        client,
        url=f'{OCD_DTL_TAXII_HOST}/{OCD_DTL_TAXII_GROUP}/',
        title='Default Group',
    )

    # Add collections found in the config file
    with open(OCD_DTL_QUERY_CONFIG_PATH) as json_file:
        config = json.load(json_file)

    for query in config['queries']:
        collection_id = query['collection_id']

        if not api_root_db['collections'].find_one({'_id': collection_id}):
            logger.info(f'Create collection {collection_id}')
            api_root_db['collections'].insert_one({
                '_id': collection_id,
                'id': collection_id,
                'title': f'{collection_id} - OCD DTL generated collection',
                'can_read': True,
                'can_write': True,
                'media_types': [
                    'application/stix+json;version=2.1',
                ],
            })

    # Add indexes as by default in medallion
    add_default_indexes(api_root_db)


def add_default_indexes(api_root_db):
    id_index = IndexModel([("id", ASCENDING)])
    type_index = IndexModel([("type", ASCENDING)])
    collection_index = IndexModel([("_collection_id", ASCENDING)])
    date_index = IndexModel([("_manifest.date_added", ASCENDING)])
    version_index = IndexModel([("_manifest.version", ASCENDING)])
    date_and_spec_index = IndexModel([("_manifest.media_type", ASCENDING), ("_manifest.date_added", ASCENDING)])
    version_and_spec_index = IndexModel([("_manifest.media_type", ASCENDING), ("_manifest.version", ASCENDING)])
    collection_and_date_index = IndexModel([("_collection_id", ASCENDING), ("_manifest.date_added", ASCENDING)])
    api_root_db["objects"].create_indexes(
        [id_index, type_index, date_index, version_index, collection_index, date_and_spec_index,
         version_and_spec_index, collection_and_date_index]
    )


def medallion_add_api_root(client, url=None, title=None, description=None, versions=None, max_content_length=9765625):
    """
    Fill:
        Create a mongodb for a new api root, with collections: status, objects, manifest, (TAXII) collections.
        Update top-level mongodb for TAXII, discovery_database, with information about this api root.

    From https://github.com/oasis-open/cti-taxii-server/blob/master/medallion/test/generic_initialize_mongodb.py

    Args:
        client (pymongo.MongoClient): mongodb client connection
        url (str): url of this api root
        title (str):  title of this api root
        description (str): description of this api root
        versions (list of str):  versions of TAXII serviced by this api root
        max_content_length (int):  maximum size of requests to this api root
        default (bool):  is this the default api root for this TAXII server

    Returns:
        new api_root_db object

    """
    if not versions:
        versions = ['application/taxii+json;version=2.1']
    db = client['discovery_database']
    url_parts = url.split('/')
    name = url_parts[-2]
    discovery_info = db['discovery_information']
    info = discovery_info.find_one()
    info['api_roots'].append(name)
    discovery_info.update_one({'_id': info['_id']}, {'$set': {'api_roots': info['api_roots']}})
    api_root_info = db['api_root_info']
    api_root_info.replace_one(
        filter={'_id': name},
        replacement={
            '_id': name,
            '_url': url,
            '_name': name,
            'title': title,
            'description': description,
            'versions': versions,
            'max_content_length': max_content_length,
        },
        upsert=True,
    )
    api_root_db = client[name]
    return api_root_db

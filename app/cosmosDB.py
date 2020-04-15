
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import azure.cosmos.documents as documents

# collection link in cosmosDB
database_link = 'dbs/E2013'
collection_link='dbs/E2013/colls/'


def connect_to_db():
    # setup cosmosDB
    endpoint = 'https://e2013-db.documents.azure.com:443/'
    key = '2bpbyU4kJfh4vgvis2GbDDOpYJmUOfrMTSaXZz4tSas0zPhVvnoLRGSlX5nwFmveFN2iIb1FUudq8kZPpBYDhw=='
    return cosmos_client.CosmosClient(endpoint, {'masterKey': key})

def write_to_db(container_name, data):

    cosmos = connect_to_db()
    print("Connected to database")

    # create container if it doesn't exist
    try:
        container_definition = {'id': container_name, 'partitionKey': {'paths': ['/'+container_name], 'kind': documents.PartitionKind.Hash}}
        cosmos.CreateContainer(database_link, container_definition, options={'indexingMode': 'none'})
        print("Created container")    
    except errors.HTTPFailure as e:
        if e.status_code == http_constants.StatusCodes.CONFLICT:
            pass
        else:
            raise e

    cosmos.CreateItem(collection_link + container_name, data)
    print("Created new Item")

# skulle kanskje hette "query_from_db"
def read_from_db(container_name, query):
    try:
        cosmos = connect_to_db()
        items = cosmos.QueryItems(collection_link+container_name, query, {'enableCrossPartitionQuery':True})
        items = list(items) # save result as list
        return items
    except:
        print("Could not read fro database")
        return []
        
        

# new data må inneholde id
def replace_in_db(item_id, container_name, new_data):
    item_path = collection_link + container_name + '/docs/' + item_id
    cosmos = connect_to_db()
    cosmos.ReplaceItem(item_path, new_data)


# return containers from cosmos db
#def get_containers():
#    list_of_containers = []
#
#    for i in devices:
#        container = devices[i][0]
#        # add container to list if it isn't added alleready
#        if container in list_of_containers:
#            pass
#        else:
#            list_of_containers.append(container)
#
#    return list_of_containers
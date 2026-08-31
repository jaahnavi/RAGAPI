# Cosmos DB (NoSQL API) container setup
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.container import ContainerProxy

from app.config import settings

_container: ContainerProxy | None = None


def get_container() -> ContainerProxy:
    global _container
    if _container is None:
        client = CosmosClient.from_connection_string(settings.cosmos_connection_string)
        database = client.create_database_if_not_exists(id=settings.cosmos_database_name)
        _container = database.create_container_if_not_exists(
            id=settings.cosmos_container_name,
            partition_key=PartitionKey(path="/id"),
        )
    return _container


def get_db():
    yield get_container()

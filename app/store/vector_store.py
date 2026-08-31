# Azure AI Search client + index management (replaces the old ChromaDB store)

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.config import settings

_index_client: SearchIndexClient | None = None
_search_client: SearchClient | None = None

VECTOR_PROFILE_NAME = "default-vector-profile"
VECTOR_ALGORITHM_NAME = "hnsw-config"


def get_index_client() -> SearchIndexClient:
    global _index_client
    if _index_client is None:
        _index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )
    return _index_client


def get_search_client() -> SearchClient:
    """Data-plane client (upload/search/delete documents) for the index."""
    global _search_client
    if _search_client is None:
        _search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_api_key),
        )
    return _search_client


def build_index_schema() -> SearchIndex:
    """Schema mirrors what each chunk currently carries into Chroma:
    page_content -> content/content_vector, and metadata (doc_id, filename,
    source, source_type, page, chunk_index) -> filterable fields, so
    doc-scoped deletion and source citations keep working unchanged."""
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=settings.azure_search_vector_dimensions,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
        SimpleField(name="doc_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="filename", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="source_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="page", type=SearchFieldDataType.Int32, filterable=True),
        SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
            )
        ],
    )

    return SearchIndex(
        name=settings.azure_search_index_name,
        fields=fields,
        vector_search=vector_search,
    )


def create_index() -> None:
    """Creates the index if missing, or updates it in place to match the schema above."""
    get_index_client().create_or_update_index(build_index_schema())


def delete_index() -> None:
    """Deletes the whole index — used when wiping the store to re-embed everything
    with a new embedding model (old vectors would otherwise have the wrong dimensions)."""
    try:
        get_index_client().delete_index(settings.azure_search_index_name)
    except ResourceNotFoundError:
        pass


def delete_by_doc_id(doc_id: str) -> None:
    """Deletes every chunk belonging to one document (Azure AI Search has no
    delete-by-filter, so this looks up matching ids first, then deletes them)."""
    escaped_doc_id = doc_id.replace("'", "''")
    client = get_search_client()
    results = client.search(
        search_text="*",
        filter=f"doc_id eq '{escaped_doc_id}'",
        select=["id"],
    )
    ids = [hit["id"] for hit in results]
    if ids:
        client.delete_documents(documents=[{"id": chunk_id} for chunk_id in ids])

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cosmos_connection_string: str = ""
    cosmos_database_name: str = "ragapi"
    cosmos_container_name: str = "documents"

    azure_storage_connection_string: str = ""
    azure_storage_container: str = "documents"

    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4.1-mini"

    # Azure AI Foundry (Azure OpenAI v1 API) — base endpoint is the resource
    # host + "/openai/v1"; the OpenAI-compatible client appends "/responses",
    # "/embeddings", etc. itself.
    azure_openai_chat_endpoint: str = "https://jg-pharmacyfoundry.services.ai.azure.com/openai/v1"
    azure_openai_chat_api_key: str = ""
    azure_openai_embedding_endpoint: str = "https://jg-pharmacyfoundry.services.ai.azure.com/openai/v1"
    azure_openai_embedding_api_key: str = ""

    azure_search_endpoint: str = "https://aisearchrgjgpharmacyclaimdev7d69cf.search.windows.net"
    azure_search_api_key: str = ""
    azure_search_index_name: str = "jg-rag-docs-index"
    azure_search_vector_dimensions: int = 1536  # text-embedding-3-small output size

    # Azure AI Search's @search.score scale differs by mode: cosine-similarity-like
    # for vector-only (alpha=1.0), RRF-fused (small, ~0.01-0.03) for hybrid, and
    # BM25-like (unbounded) for keyword-only (alpha=0.0) — so these default to
    # "off" and should be tuned per alpha against real query scores if you want
    # low-confidence filtering.
    confidence_threshold: float = 0.0  # min top-hit score to attempt an answer
    score_threshold: float = 0.0  # min score for a chunk to count

    allowed_download_domains: set[str] = {"medicare.gov", "cms.gov", "healthcare.gov"}


settings = Settings()

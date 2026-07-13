from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "data/chroma"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vectorstore = Chroma(
    collection_name="health_insurance",
    embedding_function=embeddings,
    persist_directory=CHROMA_DIR
)

# Get first 5 records
results = vectorstore._collection.get(limit=5)

for i in range(len(results["ids"])):
    print("=" * 80)
    print("ID:", results["ids"][i])
    print("METADATA:", results["metadatas"][i])

    # Optional: print chunk text
    print("DOCUMENT:")
    print(results["documents"][i][:300])
    print()
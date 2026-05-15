import chromadb

chroma_client = chromadb.PersistentClient(path="./data/chroma")
collection = chroma_client.get_collection(name="destination_knowledge")

# 1. how many chunks are stored?
print(f"Total chunks stored: {collection.count()}")

# 2. peek at a few stored chunks
results = collection.peek(5)
print(results)
# for doc, meta in zip(results['documents'], results['metadatas']):
#     print(f"{meta['destination']} | {meta['section']}: {doc[:100]}")
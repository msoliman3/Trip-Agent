import os 
from xmlparser import parse_dump
from chunker import Chunk, chunk_article
from openai import OpenAI
import chromadb
from openai import AsyncOpenAI
import asyncio



client = OpenAI(api_key=os.getenv("RAG_EMBEDDING_KEY"))

#async_client allows making multiple api calls at once 
async_client = AsyncOpenAI(api_key=os.getenv("RAG_EMBEDDING_KEY"))



# Split the chunks into batches of 50
# For each batch, call the embeddings API with the list of chunk.text values
# Pair each chunk back up with its vector
# Return the full list of (chunk, vector) pairs

# had to limit the number of characters for each chunk since one chunk has more than 8192 tokens which exceeds the maximum limit for the api
MAX_CHUNK_CHARS = 6000
# Marks the function as asynchronous. This tells Python "this function can be paused and resumed while waiting for something".
# You can't use await inside a function unless it's marked async
#TODO Split into two functions a small one that handles a single batch, and the main one that fires them all concurrently, this will make the concurrency actually work
async def embed_chunks(chunks : list[Chunk]) -> list[tuple[Chunk, list[float]]]:
    embeddings = []
    for i in range(0, len(chunks), 50):
        batch = chunks[i:i+50]
        chunk_text = []
        for chunk in batch: 
            chunk_text.append(chunk.text[:MAX_CHUNK_CHARS])  
        # await Pauses the current function while the API call completes, but crucially — it doesn't block the whole program, 
        # just this function. Other async tasks can run during that pause. Without await, Python wouldn't know where the "waiting points" are.
        response = await async_client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk_text 
        )
        vectors = [item.embedding for item in response.data]
        batch_embeddings = zip(batch, vectors)
        embeddings.extend (list(batch_embeddings))


    return embeddings

def store_embeddings (embeddings:list[tuple[Chunk, list[float]]]) -> chromadb.Collection:
    chroma_client = chromadb.PersistentClient(path="./data/chroma")
    collection = chroma_client.get_or_create_collection(name="destination_knowledge")
    chunk_ids = []
    embedding_vectors = []
    docs = []
    metas = []
    for embedding in embeddings: 
        chunk = embedding[0]
        vector = embedding[1]
        embedding_vectors.append(vector)
        id = f"{chunk.metadata['destination']}_{chunk.metadata['section']}"
        chunk_ids.append(id)
        docs.append(chunk.text)
        metas.append(chunk.metadata)


    CHROMA_BATCH_SIZE = 500

    # ChromaDB has a limit on how many items you can add in one call (5461), so we need to store the items in batches 
    for i in range(0, len(chunk_ids), CHROMA_BATCH_SIZE):
        collection.add(
            ids=chunk_ids[i:i+CHROMA_BATCH_SIZE],
            documents=docs[i:i+CHROMA_BATCH_SIZE],
            embeddings=embedding_vectors[i:i+CHROMA_BATCH_SIZE],
            metadatas=metas[i:i+CHROMA_BATCH_SIZE]
        )

    return collection 


if __name__ == "__main__":
    articles = parse_dump("./data/enwikivoyage-20260501-pages-articles-multistream.xml")
    chunks = []
    for article in articles:
        chunks.extend(chunk_article(article))

    embeddings = asyncio.run(embed_chunks(chunks))
    store_embeddings(embeddings)

    
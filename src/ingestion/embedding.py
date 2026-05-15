import os 
from xmlparser import parse_dump
from chunker import Chunk, chunk_article
from openai import OpenAI
client = OpenAI(api_key=os.getenv("RAG_EMBEDDING_KEY"))

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Tokyo | Eat: Tsukiji Outer Market remains the go-to for..."
)
vector = response.data[0].embedding

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=["chunk text 1", "chunk text 2", "chunk text 3"]  # list, not a single string
)



vectors = [item.embedding for item in response.data]



# Split the chunks into batches of 50
# For each batch, call the embeddings API with the list of chunk.text values
# Pair each chunk back up with its vector
# Return the full list of (chunk, vector) pairs
MAX_CHUNK_CHARS = 6000
def embed_chunks(chunks : list[Chunk]) -> list[tuple[Chunk, list[float]]]:
    embeddings = []
    for i in range(0, len(chunks), 50):
        batch = chunks[i:i+50]
        chunk_text = []
        for chunk in batch: 
            chunk_text.append(chunk.text[:MAX_CHUNK_CHARS]) # had to limit the number of characters for each chunk since one chunk has more than 8192 tokens which exceeds the maximum limit for the api 
        response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk_text 
        )
        vectors = [item.embedding for item in response.data]
        batch_embeddings = zip(batch, vectors)
        embeddings.extend (list(batch_embeddings))


    return embeddings


if __name__ == "__main__":
    articles = parse_dump("./data/enwikivoyage-20260501-pages-articles-multistream.xml")
    chunks = []
    for article in articles:
        chunks.extend(chunk_article(article))

    embeddings = embed_chunks(chunks)
    print (embeddings[10])
    # print(f"Parsed {len(articles)} destination articles")

    # tokyo = next((a for a in articles if a.title == "Tokyo"), None)
    # if tokyo:
    #     print(f"\nTokyo sections: {list(tokyo.sections.keys())}")
    #     print(f"\nEat preview:\n{tokyo.sections.get('Eat', '')[:300]}")

    
    
   
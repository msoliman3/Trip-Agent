from langchain_classic.chains.query_constructor.base import AttributeInfo
from langchain_classic.retrievers import SelfQueryRetriever
from langchain_community.query_constructors.chroma import ChromaTranslator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
import os

# setting temperature to 0 since we want the llm to be deterministic and consistent when parsing queries into filters, not creative
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0,api_key=os.getenv("RAG_EMBEDDING_KEY"))

chroma_client = chromadb.PersistentClient(path="./data/chroma")

# LangChain wrapper around the raw chromadb client
vectorstore = Chroma(
    client=chroma_client,
    collection_name="destination_knowledge",
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small", api_key=os.getenv("RAG_EMBEDDING_KEY"))
)

metadata_field_info = [
    AttributeInfo(
        name="destination",
        description="The city or place the travel guide is about, e.g. Tokyo",
        type="string",
    ),
    AttributeInfo(
        name="section",
        description="The WikiVoyage section, one of: Eat, See, Do, Drink, Sleep, Buy",
        type="string",
    ),
    # AttributeInfo(
    #     name="country",
    #     description="The country the destination is in, e.g. Japan",
    #     type="string",
    # ),
    # AttributeInfo(
    #     name="region",
    #     description="The region or continent, e.g. Asia, Europe",
    #     type="string",
    # ),
]

retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="Travel guide sections for destinations around the world",
    metadata_field_info=metadata_field_info,
    structured_query_translator=ChromaTranslator(),
)

docs = retriever.invoke("best island in malaysia")
for doc in docs:
    print(doc.metadata)
    print(doc.page_content)
    print("---")
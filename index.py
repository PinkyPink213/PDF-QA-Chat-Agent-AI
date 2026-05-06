from dotenv import load_dotenv

from pathlib import Path

from qdrant_client import QdrantClient

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv()

COLLECTION_NAME = "learning_rag"

# Connect Qdrant
client = QdrantClient(
    url="http://vector-db:6333"
)

# Check if collection already exists
collections = client.get_collections().collections

exists = any(
    collection.name == COLLECTION_NAME
    for collection in collections
)

if exists:
    print("Collection already exists. Skipping indexing.")
    exit()

print("Starting document indexing...")

# Load PDF
pdf_path = Path(__file__).parent / "nodejs.pdf"

loader = PyPDFLoader(file_path=pdf_path)

docs = loader.load()

# Split documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

chunks = text_splitter.split_documents(docs)

# Embedding model
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

# Store in Qdrant
vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embedding_model,
    url="http://vector-db:6333",
    collection_name=COLLECTION_NAME
)

print("Indexing completed.")
from dotenv import load_dotenv
load_dotenv()

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from app.services.image_service import extract_text_from_image
import os
import uuid
import threading

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
VECTOR_SIZE    = 384          # ✅ all-MiniLM-L6-v2 outputs 384 dimensions
COLLECTION     = "documents"

_client: QdrantClient = None
_client_lock = threading.Lock()
_embeddings  = None
_embed_lock  = threading.Lock()


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                if not QDRANT_URL or not QDRANT_API_KEY:
                    raise ValueError("QDRANT_URL or QDRANT_API_KEY missing from .env")
                _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
                print("✅ Qdrant client connected")
    return _client


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        with _embed_lock:
            if _embeddings is None:
                print("⏳ Loading embeddings model...")
                _embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"  # ✅ ~90MB vs 420MB
                )
                print("✅ Embeddings model loaded")
    return _embeddings


def ensure_collection():
    client   = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"✅ Qdrant collection '{COLLECTION}' created")
    try:
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception:
        pass


def get_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        add_start_index=True
    )


def _upsert_chunks(chunks: list[Document], user_id: str):
    ensure_collection()
    client     = get_client()
    embeddings = get_embeddings()

    texts   = [c.page_content for c in chunks]
    vectors = embeddings.embed_documents(texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "text":    chunk.page_content,
                "source":  chunk.metadata.get("source", "unknown"),
                "type":    chunk.metadata.get("type",   "PDF"),
                "user_id": user_id,
            }
        )
        for chunk, vec in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)


def load_pdf(file_path: str, user_id: str, filename: str = None) -> int:
    loader    = PyPDFLoader(file_path)
    documents = loader.load()
    chunks    = get_splitter().split_documents(documents)

    label = filename or os.path.basename(file_path)
    for c in chunks:
        c.metadata["source"] = label
        c.metadata["type"]   = "PDF"

    _upsert_chunks(chunks, user_id)
    print(f"✅ PDF indexed: {label} ({len(chunks)} chunks) for user {user_id}")
    return len(chunks)


def load_image(file_path: str, user_id: str, filename: str = None) -> int:
    text = extract_text_from_image(file_path)
    if not text.strip():
        print("⚠️ OCR returned no text")
        return 0

    label  = filename or os.path.basename(file_path)
    doc    = Document(page_content=text, metadata={"source": label, "type": "Image"})
    chunks = get_splitter().split_documents([doc])

    _upsert_chunks(chunks, user_id)
    print(f"✅ Image indexed: {label} ({len(chunks)} chunks) for user {user_id}")
    return len(chunks)


def query_pdf(question: str, user_id: str, k: int = 8):
    ensure_collection()
    client     = get_client()
    embeddings = get_embeddings()

    query_vec = embeddings.embed_query(question)

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vec,
        limit=k,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
        )
    ).points

    if not results:
        print(f"⚠️ No RAG results for user {user_id}")
        return "", []

    context = ""
    sources = set()
    for r in results:
        context += r.payload["text"] + "\n\n"
        sources.add(r.payload.get("source", "Unknown"))

    print(f"✅ RAG retrieved {len(results)} chunks from: {sources}")
    return context[:3000], list(sources)
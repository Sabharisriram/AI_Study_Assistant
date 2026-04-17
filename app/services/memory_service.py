from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct, PayloadSchemaType
from fastembed import TextEmbedding
import os
import uuid
import threading

QDRANT_URL     = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
VECTOR_SIZE    = 384
COLLECTION     = "memory"

_client: QdrantClient = None
_client_lock = threading.Lock()
_embeddings: TextEmbedding = None
_embed_lock  = threading.Lock()


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                if not QDRANT_URL or not QDRANT_API_KEY:
                    raise ValueError("QDRANT_URL or QDRANT_API_KEY missing from .env")
                _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
                print("✅ Qdrant memory client connected")
    return _client


def get_embeddings() -> TextEmbedding:
    global _embeddings
    if _embeddings is None:
        with _embed_lock:
            if _embeddings is None:
                print("⏳ Loading fastembed memory model...")
                _embeddings = TextEmbedding(
                    model_name="BAAI/bge-small-en-v1.5"
                )
                print("✅ Fastembed memory model loaded")
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


def update_user_memory(user_id: str, role: str, content: str):
    ensure_collection()
    client     = get_client()
    embeddings = get_embeddings()

    text   = f"{role}: {content}"
    vector = list(embeddings.embed([text]))[0].tolist()

    client.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": text, "user_id": user_id, "role": role}
            )
        ]
    )


def get_user_memory(user_id: str, query: str, k: int = 5) -> list[str]:
    try:
        ensure_collection()
        client     = get_client()
        embeddings = get_embeddings()

        query_vec = list(embeddings.embed([query]))[0].tolist()

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

        return [r.payload["text"] for r in results]

    except Exception as e:
        print(f"⚠️ Memory retrieval failed: {e}")
        return []
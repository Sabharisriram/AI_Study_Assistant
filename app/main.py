from fastapi import FastAPI
from app.routes.chat   import router as chat_router
from app.routes.pdf    import router as pdf_router
from app.routes.upload import router as upload_router
from app.routes.auth   import router as auth_router
import os

app = FastAPI(title="AI Study Assistant")

app.include_router(auth_router, prefix="/auth",  tags=["Auth"])
app.include_router(chat_router, prefix="/chat",  tags=["Chat"])
app.include_router(pdf_router,  prefix="/pdf",   tags=["PDF"])
app.include_router(upload_router, prefix="/image", tags=["Image"])


@app.get("/status")
def status():
    from app.services.rag_service import get_client, COLLECTION
    try:
        client     = get_client()
        collection = client.get_collection(COLLECTION)
        return {"status": "ok", "vectors_count": collection.vectors_count}
    except Exception:
        return {"status": "ok", "vectors_count": 0}
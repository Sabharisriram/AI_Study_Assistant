from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from app.services.rag_service import load_image
from app.services.auth_service import get_user
import os

router = APIRouter()


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file.filename}"
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        chunk_count = load_image(file_path, user_id=user["user_id"], filename=file.filename)
        return {"message": "Image processed and indexed", "filename": file.filename, "chunks": chunk_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
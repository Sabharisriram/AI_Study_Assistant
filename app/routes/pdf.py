from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from app.services.rag_service import load_pdf
from app.services.auth_service import get_user
import shutil, os

router = APIRouter()


@router.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...), authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    file_path = f"temp_{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        chunk_count = load_pdf(file_path, user_id=user["user_id"], filename=file.filename)
        return {"message": "PDF uploaded and indexed", "filename": file.filename, "chunks": chunk_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
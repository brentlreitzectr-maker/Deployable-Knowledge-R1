import os
from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from fastapi.responses import JSONResponse
from pathlib import Path
from utility.parsing import parse_pdf
from utility.embedding_and_storing import db, chunk_text, embed_directory, embed_file

from config import (
    UPLOAD_DIR, PDF_DIR, DEFAULT_CHUNKING_METHOD, UPLOAD_CHUNKING_METHOD, ALLOWED_UPLOAD_EXTENSIONS
)
import re

router = APIRouter()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    """Strip any directory parts and unsafe characters from a client filename."""
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(name or "").name).strip()
    if cleaned in {"", ".", ".."}:
        raise ValueError("Invalid filename")
    return cleaned

@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Upload files and embed them into the database.
    This endpoint accepts multiple files, saves them to the upload directory,
    and processes each file to extract text and embed it into the database.

    - **files**: List of files to upload. Each file is processed to extract text and embed it.
    - Returns a JSON response with the status of each file upload.
    """
    results = []
    for file in files:
        try:
            name = safe_filename(file.filename)
            if Path(name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
                raise ValueError(f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}")
            destination = UPLOAD_DIR / name
            with open(destination, "wb") as f:
                f.write(await file.read())

            # Replace any earlier copy of this document instead of duplicating it
            db.delete_by_source(name)
            try:
                embed_file(
                    file_path=destination,
                    chunking_method=UPLOAD_CHUNKING_METHOD,
                    source_name=name,
                    tags=["uploaded"]
                )
            except Exception:
                destination.unlink(missing_ok=True)
                raise

            results.append({"filename": name, "status": "success"})
        except Exception as e:
            results.append({
                "filename": Path(file.filename or "").name,
                "status": "error",
                "message": str(e)
            })

    return JSONResponse({"uploads": results})

@router.post("/remove")
async def remove_document(source: str = Form(...)):
    """
    Remove a document from the database and delete its file.

    - **source**: The source name of the document to remove.
    - Returns a JSON response indicating the success or failure of the operation.
    """
    try:
        db.delete_by_source(source)
        file_path = UPLOAD_DIR / Path(source).name
        if file_path.exists():
            os.remove(file_path)
        return JSONResponse({"status": "success", "message": f"{source} removed."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    """
    Ingest all PDF files from the PDF_DIR, parse them, and embed the text into the database.
    This endpoint processes all PDF files in the PDF_DIR, converts them to text,
    and schedules the embedding of the text into the database.

    - **background_tasks**: FastAPI's background tasks to handle the embedding process asynchronously.
    - Returns a JSON response indicating the status of the ingestion process.
    """
    pdf_dir = PDF_DIR.resolve()
    txt_dir = UPLOAD_DIR.resolve()
    converted = []
    for pdf_file in pdf_dir.glob("*.pdf"):
        txt_file = txt_dir / f"{pdf_file.stem}.txt"
        try:
            pages = parse_pdf(pdf_file)  # list of {"page", "text"}
            txt_file.write_text("\n\n".join(p["text"] for p in pages), encoding="utf-8")
            converted.append(txt_file)
        except Exception as e:
            print(f"Failed to parse {pdf_file.name}: {e}")

    def embed_converted(files):
        # Only embed the files converted in this run, replacing older copies,
        # rather than re-embedding (and duplicating) everything in documents/.
        for txt_file in files:
            try:
                db.delete_by_source(txt_file.name)
                embed_file(file_path=txt_file, chunking_method=DEFAULT_CHUNKING_METHOD,
                           source_name=txt_file.name, tags=["auto_ingested"])
            except Exception as e:
                print(f"Failed to embed {txt_file.name}: {e}")

    background_tasks.add_task(embed_converted, converted)
    return {"status": "started", "message": f"Parsed {len(converted)} PDF(s) from pdfs/ and scheduled embedding."}


@router.post("/clear_db")
async def clear_db():
    """
    Clear the ChromaDB collection.
    This endpoint removes all documents from the ChromaDB collection.
    
    - Returns a JSON response indicating the success or failure of the operation.
    """
    try:
        db.clear_collection()
        return JSONResponse({"status": "success", "message": "ChromaDB collection cleared."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

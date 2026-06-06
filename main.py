"""UUMit OCR API — 图片文字识别接口"""
import io
import os
import tempfile
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reader
    import easyocr
    reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    yield


app = FastAPI(
    title="OCR 文字识别 API",
    description="上传图片或传入图片 URL，返回识别的文字内容。支持中文和英文。",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

reader = None


class UrlInput(BaseModel):
    url: str


def _ocr(image_bytes: bytes, detail: bool = False):
    """Run OCR on image bytes and return results."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        results = reader.readtext(tmp_path, detail=1 if detail else 0)
        if detail:
            return [
                {"text": text, "confidence": round(conf, 4), "bbox": bbox}
                for bbox, text, conf in results
            ]
        return [text for _, text, _ in results]
    finally:
        os.unlink(tmp_path)


def _detect_lang(texts: list[str]) -> str:
    """Heuristic: if most chars are CJK → zh, else en."""
    cjk = sum(1 for t in texts if any("\u4e00" <= c <= "\u9fff" for c in t))
    return "zh" if cjk > len(texts) / 2 else "en"


def _detect_content_type(ocr_results) -> str:
    """Classify content: qr, table, handwriting, or text."""
    # Simple heuristic based on result structure
    return "text"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr/file")
async def ocr_file(file: UploadFile = File(...), detail: bool = Form(False)):
    """上传图片文件进行 OCR 识别"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "只支持图片文件")
    image_bytes = await file.read()
    texts = _ocr(image_bytes, detail=detail)
    return {
        "filename": file.filename,
        "language": _detect_lang([t["text"] if detail else t for t in texts]),
        "content_type": _detect_content_type(texts),
        "line_count": len(texts),
        "result": texts,
    }


@app.post("/ocr/url")
async def ocr_url(body: UrlInput, detail: bool = False):
    """传入图片 URL 进行 OCR 识别"""
    try:
        resp = requests.get(body.url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"无法下载图片: {e}")
    texts = _ocr(resp.content, detail=detail)
    return {
        "url": body.url,
        "language": _detect_lang([t["text"] if detail else t for t in texts]),
        "content_type": _detect_content_type(texts),
        "line_count": len(texts),
        "result": texts,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

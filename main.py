"""UUMit OCR API — 图片文字识别 (Tesseract)"""
import os, tempfile
import requests
from typing import Any
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image

app = FastAPI(title="OCR 文字识别 API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LANG_MAP = {"zh": "chi_sim+chi_tra", "en": "eng", "auto": "chi_sim+eng"}


def _ocr(image_bytes: bytes, lang: str = "auto"):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes); p = tmp.name
    try:
        img = Image.open(p)
        text = pytesseract.image_to_string(img, lang=LANG_MAP.get(lang, LANG_MAP["auto"]))
        return [l.strip() for l in text.split("\n") if l.strip()]
    finally:
        os.unlink(p)


def _extract_url(data: dict) -> str:
    """Extract url from either flat or params-wrapped request."""
    if isinstance(data, dict):
        if "url" in data:
            return data["url"]
        if "params" in data and isinstance(data["params"], dict) and "url" in data["params"]:
            return data["params"]["url"]
    return ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr/url")
def ocr_url(data: dict = Body(...), lang: str = "auto"):
    url = _extract_url(data)
    if not url:
        return {"url": "", "line_count": 0, "result": [], "error": "missing url"}
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        texts = _ocr(resp.content, lang)
        return {"url": url, "line_count": len(texts), "result": texts}
    except Exception as e:
        return {"url": url, "line_count": 0, "result": [], "error": str(e)}


@app.post("/ocr/file")
def ocr_file(file: UploadFile = File(...), lang: str = "auto"):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "只支持图片文件")
    texts = _ocr(file.file.read(), lang)
    return {"filename": file.filename, "line_count": len(texts), "result": texts}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

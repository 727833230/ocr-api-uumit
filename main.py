"""UUMit OCR API — 图片文字识别 (Tesseract)"""
import os, tempfile
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pytesseract
from PIL import Image

app = FastAPI(title="OCR 文字识别 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class UrlInput(BaseModel):
    url: str

LANG_MAP = {
    "zh": "chi_sim+chi_tra",
    "en": "eng",
    "auto": "chi_sim+eng",
}

def _ocr(image_bytes: bytes, lang: str = "auto"):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        p = tmp.name
    try:
        img = Image.open(p)
        config = LANG_MAP.get(lang, LANG_MAP["auto"])
        text = pytesseract.image_to_string(img, lang=config)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return lines
    finally:
        os.unlink(p)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ocr/file")
async def ocr_file(file: UploadFile = File(...), lang: str = "auto"):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "只支持图片文件")
    texts = _ocr(await file.read(), lang)
    return {"filename": file.filename, "line_count": len(texts), "result": texts}

@app.post("/ocr/url")
async def ocr_url(body: UrlInput, lang: str = "auto"):
    resp = requests.get(body.url, timeout=30)
    resp.raise_for_status()
    texts = _ocr(resp.content, lang)
    return {"url": body.url, "line_count": len(texts), "result": texts}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

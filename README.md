# OCR API — 图片文字识别接口

基于 FastAPI + Tesseract OCR 的图片文字识别 API，支持中文、英文和俄文。

## 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/ocr/file` | POST | 上传图片文件识别 |
| `/ocr/url` | POST | 传入图片 URL 识别 |

## 部署到 Render（免费）

1. 将本目录推送到 GitHub 仓库
2. 在 [Render](https://render.com) → New Web Service → 连接你的 GitHub 仓库
3. Render 会自动识别 `render.yaml`，点击 Deploy
4. 部署完成后会得到一个 `https://ocr-api.onrender.com` 的地址

## 部署后用 curl 测试

```bash
# 图片 URL 识别
curl -X POST https://你的地址/ocr/url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/test.png"}'

# 图片文件上传识别
curl -X POST https://你的地址/ocr/file \
  -F "file=@test.png"
```

## 注册到 UUMit

部署后获得公网地址，然后在 UUMit 数据广场注册 API。

# 1. 使用輕量級的 Python 基礎鏡像
FROM python:3.10-slim

# 2. 設定容器內的工作目錄
WORKDIR /app

# 4. 複製 requirements.txt 並安裝 Python 依賴
# 這樣做的好處是：如果程式碼變了但 requirements 沒變，Docker 會使用緩存，構建速度超快
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製剩下的程式碼
COPY . .

# 6. 暴露 Port (FastAPI 預設通常用 8000)
EXPOSE 8000

# 7. 啟動命令 (對應你的 Procfile)
# 原本: web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
# Docker版: 直接指定 Port 8000
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
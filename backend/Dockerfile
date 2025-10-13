# # ---- Build Stage ----
# FROM python:3.11 as builder
# WORKDIR /app
# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# # 只有這一個 RUN 指令是安全的，因為它只安裝依賴
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # ---- Final Stage ----
# FROM python:3.11-slim
# WORKDIR /app
# COPY --from=builder /opt/venv /opt/venv

# # 把所有程式碼複製進來
# COPY . .

# ENV PATH="/opt/venv/bin:$PATH"

# # CMD 是在 Run Time 執行的，不是 Build Time，所以是安全的
# CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 使用 BuildKit 語法
# syntax = docker/dockerfile:1.4

FROM python:3.11-slim AS base
WORKDIR /app

# 預設先複製 requirements.txt
COPY requirements.txt .

# 使用 cache mount 來加速 pip install
RUN --mount=type=cache,id=s/railway-pip-cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# 再複製應用程式
COPY . .

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 若你的程式啟動是 uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

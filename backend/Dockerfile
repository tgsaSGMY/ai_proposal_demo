# ---- Build Stage ----
FROM python:3.11 as builder
WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 只有這一個 RUN 指令是安全的，因為它只安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

# 把所有程式碼複製進來
COPY . .

ENV PATH="/opt/venv/bin:$PATH"

# CMD 是在 Run Time 執行的，不是 Build Time，所以是安全的
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
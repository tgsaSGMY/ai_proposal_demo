from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://ai-proposal-platform-v1-0.pages.dev/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("正在加载服务器配置...")
    print("服务器配置加载完成。")

@app.get("/")
def read_root():
    return {"status": "FastAPI is running!"}

# 我们将要调用的测试 API 端点
@app.get("/api/greeting")
def get_greeting():
    # 获取当前时间
    now = datetime.datetime.now(datetime.timezone.utc)
    
    return {
        "message": "Hello from your FastAPI backend on Railway! 🚀",
        "timestamp": now.isoformat() # 返回 ISO 格式的时间字符串
    }
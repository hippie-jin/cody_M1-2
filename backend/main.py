from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import chat, conversations, data

app = FastAPI(
    title="나만의 AI 비서",
    description="시계열 데이터를 기반으로 맞춤형 답변을 제공하는 AI 챗봇 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/")
def health_check():
    return {"status": "ok"}

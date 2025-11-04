from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from routers.register_user import router as register_user_router
from routers.login import router as login_router
from config import MEDIA_ROOT
from config import SESSION_SECRET
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=60 * 60 * 24 * 7,
)

# /media を公開 (画像確認用)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT, check_dir=False), name="media")

# ルータ登録
app.include_router(register_user_router)
app.include_router(login_router)

@app.get("/health")
def health():
    return {"ok": True}

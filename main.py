from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from routers.register_user import router as register_user_router
from config import MEDIA_ROOT

app = FastAPI()

# /media を公開 (画像確認用)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT, check_dir=False), name="media")

# ルータ登録
app.include_router(register_user_router)

@app.get("/health")
def health():
    return {"ok": True}

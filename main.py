from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI()
app.mount("/media", StaticFiles(directory="/srv/app/media", check_dir=False), name="media")

@app.get("/health")
def health():
    return {"ok": True}

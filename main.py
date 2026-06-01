from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from routes import session, access
from db import init_db

app = FastAPI(title="Gatekeeper — AI Trust Gateway")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(session.router, prefix="/session")
app.include_router(access.router, prefix="/access")

@app.on_event("startup")
async def startup():
    init_db()
    print("Gatekeeper online.")

@app.get("/")
def serve_ui():
    return FileResponse("static/gatekeeper_ui.html")

@app.get("/health")
def health():
    return {"status": "online", "service": "Gatekeeper"}

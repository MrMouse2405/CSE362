import os
from fastapi import FastAPI
from starlette.responses import FileResponse

app = FastAPI()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "FastAPI is running"}

# 2. Catch-all for Svelte SPA and static files
static_dir = os.path.join(os.path.dirname(__file__), "static")

@app.get("/{catchall:path}")
def serve_spa(catchall: str):
    # Prevent directory traversal attacks
    safe_path = os.path.normpath(os.path.join(static_dir, catchall))
    if not safe_path.startswith(static_dir):
        return FileResponse(os.path.join(static_dir, "index.html"))

    if os.path.isfile(safe_path):
        return FileResponse(safe_path)
    
    # Fallback to Svelte's router
    return FileResponse(os.path.join(static_dir, "index.html"))
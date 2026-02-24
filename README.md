# CSE362 Project

## Running the Production Release

This release is a self-contained bundle containing the compiled frontend and the FastAPI backend. You do not need Node, Bun, or uv to run this release.

**Prerequisites:** Python 3.10+

1. Unzip `app-release.zip`
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Visit http://localhost:8000 in your browser.

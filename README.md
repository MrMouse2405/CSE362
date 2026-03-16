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

Set Environment Variables

```env
SUPER_USER_EMAIL="mrmouse2405@gmail.com"
SUPER_USER_PASSWORD="meowmeow"
JWT_SECRET="default_secret"
DATABASE_URL="sqlite+aiosqlite:///./app.db"
```

Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. Visit http://localhost:8000 in your browser.

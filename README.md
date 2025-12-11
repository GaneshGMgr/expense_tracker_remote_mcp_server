Setup
- uv init .
- .venv\Scripts\activate
- uv add fastmcp

Run (Windows)
- uv run python main.py
uv run fastmcp dev main.py
- If port 8000 is in use: set PORT and retry
	- $env:PORT=8001; uv run python main.py

Notes
- The `fastmcp dev` CLI may fail on Windows with "Failed to canonicalize script path". Use `uv run python main.py` instead.

### To Deploy fastmcp.cloud

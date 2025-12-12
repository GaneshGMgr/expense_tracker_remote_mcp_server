# Expense Tracker MCP Server

This README explains how to set up, run, and deploy Expense Tracker MCP server.

## Setup

# Initialize project
uv init .

# Activate virtual environment
.venv\Scripts\activate

# Add FastMCP to the project
uv add fastmcp

---

## Run (Windows)

# Run using Python directly
uv run python main.py

# Or run with FastMCP development mode
uv run fastmcp dev main.py

# If port 8000 is in use, set PORT and retry
$env:PORT=8001; uv run python main.py

---

## Notes

- On Windows, the `fastmcp dev` CLI may fail with "Failed to canonicalize script path". In this case, use `uv run python main.py` instead.
- Ensure your virtual environment `.venv` is activated before running any `uv` commands.

---

## Deploy to FastMCP Cloud

- Once your server is ready and tested locally, you can deploy it to [fastmcp.cloud](https://fastmcp.cloud) using:
uv run fastmcp deploy main.py

---

## Folder Structure

```text
proxy_server/
├── .git/                   # Git repository
├── .venv/                  # Python virtual environment
├── __pycache__/            # Python cache files
├── .gitignore              # Git ignore file
├── .python-version         # Python version file
├── categories.json         # Categories data
├── expenses.db             # SQLite database
├── main.py                 # Main proxy server script
├── pyproject.toml          # Project configuration
├── README.md               # This readme file
├── requirements.txt        # Python dependencies
└── uv.lock                 # uv.lock file
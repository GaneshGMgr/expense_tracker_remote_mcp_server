from fastmcp import FastMCP
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# Create a FastMCP server instance
mcp = FastMCP(name="Expense Tracker MCP Server")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT '',
                type TEXT NOT NULL DEFAULT 'expense',
                is_deleted INTEGER NOT NULL DEFAULT 0
            )
        """)


init_db()


def _validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except Exception:
        return False

def _validate_amount(amount: float) -> bool:
    try:
        return float(amount) >= 0
    except Exception:
        return False


# ADD EXPENSE
@mcp.tool()
def add_expense(amount: float, category: str, subcategory: str, note: str, date: str) -> Dict[str, Any]:
    """Add a new expense entry."""
    subcategory = subcategory or ""
    note = note or ""

    if not _validate_amount(amount):
        return {"status": "error", "message": "Invalid amount"}
    if not _validate_date(date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, category, subcategory, note, date, type) VALUES (?, ?, ?, ?, ?, 'expense')",
            (amount, category, subcategory, note, date)
        )
        return {
            "status": "success",
            "id": cursor.lastrowid,
            "message": "Expense added successfully"
        }


# ADD CREDIT (INCOME)
@mcp.tool()
def add_credit(amount: float, source: str, note: str, date: str) -> Dict[str, Any]:
    """Add an income/credit (e.g., salary)."""
    note = note or ""

    if not _validate_amount(amount):
        return {"status": "error", "message": "Invalid amount"}
    if not _validate_date(date):
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (amount, category, subcategory, note, date, type) VALUES (?, ?, '', ?, ?, 'income')",
            (amount, source, note, date)
        )
        return {
            "status": "success",
            "id": cursor.lastrowid,
            "message": "Credit added successfully"
        }


# LIST EXPENSES / INCOME
@mcp.tool()
def list_expenses(start_date: str, end_date: str) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """List all expense entries within an inclusive date range."""
    if not (_validate_date(start_date) and _validate_date(end_date)):
        return {"status": "error", "message": "Invalid date range format. Use YYYY-MM-DD"}

    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute("""
            SELECT id, date, amount, category, subcategory, note, type
            FROM expenses
            WHERE date BETWEEN ? AND ? AND is_deleted = 0
            ORDER BY date ASC, id ASC
        """, (start_date, end_date))
        return [dict(row) for row in cur.fetchall()]


# SUMMARIZE EXPENSES
@mcp.tool()
def summarize(start_date: str, end_date: str, category: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Summarize expenses by category within an inclusive date range (expense only)."""
    if not (_validate_date(start_date) and _validate_date(end_date)):
        return {"status": "error", "message": "Invalid date range format. Use YYYY-MM-DD"}

    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ? AND type = 'expense' AND is_deleted = 0
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]
        # ensure total_amount is float
        for r in results:
            if "total_amount" in r and r["total_amount"] is not None:
                r["total_amount"] = float(r["total_amount"])
        return results


# EDIT EXPENSE / INCOME
@mcp.tool()
def edit_expense(id: int, amount: Optional[float] = None, category: Optional[str] = None, subcategory: Optional[str] = None,
                 note: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
    """Edit an existing expense or income entry."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Build dynamic update query
        fields: List[str] = []
        params: List[Any] = []

        if amount is not None:
            if not _validate_amount(amount):
                return {"status": "error", "message": "Invalid amount"}
            fields.append("amount = ?")
            params.append(amount)

        if category is not None:
            fields.append("category = ?")
            params.append(category)

        if subcategory is not None:
            fields.append("subcategory = ?")
            params.append(subcategory)

        if note is not None:
            fields.append("note = ?")
            params.append(note)

        if date is not None:
            if not _validate_date(date):
                return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}
            fields.append("date = ?")
            params.append(date)

        if not fields:
            return {"status": "error", "message": "No fields provided to update"}

        params.append(id)

        query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"

        cursor.execute(query, params)

        if cursor.rowcount == 0:
            return {"status": "error", "message": "Expense not found"}

        return {"status": "success", "message": "Expense updated successfully"}


# SOFT DELETE — mark the entry as hidden
@mcp.tool()
def delete_expense(id: int) -> Dict[str, Any]:
    """Soft delete: hides an entry without removing it."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE expenses SET is_deleted = 1 WHERE id = ?",
            (id,)
        )

        if cursor.rowcount == 0:
            return {"status": "error", "message": "Entry not found"}

        return {"status": "success", "message": "Entry hidden (soft deleted)"}
    

@mcp.tool()
def restore_expense(id: int) -> Dict[str, Any]:
    """Restore a previously deleted entry."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE expenses SET is_deleted = 0 WHERE id = ?",
            (id,)
        )

        if cursor.rowcount == 0:
            return {"status": "error", "message": "Entry not found or already active"}

        return {"status": "success", "message": "Entry restored"}



# CATEGORIES RESOURCE
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Serve categories.json as a resource."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

# RUN SERVER
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000

    mcp.run(transport="http", host=host, port=port)  # streamable HTTP transport
    # mcp.run() # STDIO transport by default

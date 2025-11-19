"""
MCP Server for Customer + Ticket database.

Exposes 5 tools via MCP:
- get_customer(customer_id)
- list_customers(status, limit)
- update_customer(customer_id, data)
- create_ticket(customer_id, issue, priority)
- get_customer_history(customer_id)
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from flask import Flask, request, Response, jsonify
from flask_cors import CORS

# Path to the SQLite database created by database_setup.py
DB_PATH = "support.db"

# ---------------------------------------------------------------------
# Low-level DB helpers
# ---------------------------------------------------------------------


def get_db_connection():
    """Create a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a SQLite row to a plain Python dict."""
    return {key: row[key] for key in row.keys()}


# ---------------------------------------------------------------------
# Tool implementations (business logic)
# ---------------------------------------------------------------------


def get_customer(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific customer by ID.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            return {"success": True, "customer": row_to_dict(row)}
        else:
            return {"success": False, "error": f"Customer {customer_id} not found"}
    except Exception as e:
        return {"success": False, "error": f"Database error: {e}"}


def list_customers(status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    List customers, optionally filtered by status and limited in count.

    Args:
        status: 'active', 'disabled', or None for all customers.
        limit:  maximum number of rows to return.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if status:
            if status not in ["active", "disabled"]:
                return {
                    "success": False,
                    "error": 'Status must be "active" or "disabled"',
                }
            cur.execute(
                "SELECT * FROM customers WHERE status = ? "
                "ORDER BY id LIMIT ?",
                (status, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM customers ORDER BY id LIMIT ?",
                (limit,),
            )

        rows = cur.fetchall()
        conn.close()

        customers = [row_to_dict(r) for r in rows]
        return {"success": True, "count": len(customers), "customers": customers}
    except Exception as e:
        return {"success": False, "error": f"Database error: {e}"}


def update_customer(customer_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update customer fields using a generic data dict.

    Args:
        customer_id: id of the customer to update
        data: dict with any subset of: name, email, phone, status
    """
    try:
        allowed_fields = {"name", "email", "phone", "status"}
        updates: List[str] = []
        params: List[Any] = []

        for key, value in data.items():
            if key in allowed_fields and value is not None:
                updates.append(f"{key} = ?")
                params.append(value)

        if not updates:
            return {"success": False, "error": "No valid fields to update"}

        # Ensure customer exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return {"success": False, "error": f"Customer {customer_id} not found"}

        # Add updated_at timestamp
        updates.append("updated_at = CURRENT_TIMESTAMP")

        params.append(customer_id)
        query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
        cur.execute(query, params)
        conn.commit()

        # Return updated row
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        conn.close()

        return {
            "success": True,
            "message": f"Customer {customer_id} updated successfully",
            "customer": row_to_dict(row),
        }
    except Exception as e:
        return {"success": False, "error": f"Database error: {e}"}


def create_ticket(customer_id: int, issue: str, priority: str = "medium") -> Dict[str, Any]:
    """
    Create a new support ticket for a given customer.

    Args:
        customer_id: ID of the customer
        issue:       Description of the issue
        priority:    'low', 'medium', or 'high'
    """
    try:
        if priority not in ["low", "medium", "high"]:
            return {
                "success": False,
                "error": 'Priority must be one of: "low", "medium", "high"',
            }

        conn = get_db_connection()
        cur = conn.cursor()

        # Ensure customer exists
        cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return {"success": False, "error": f"Customer {customer_id} not found"}

        cur.execute(
            """
            INSERT INTO tickets (customer_id, issue, status, priority, created_at)
            VALUES (?, ?, 'open', ?, CURRENT_TIMESTAMP)
        """,
            (customer_id, issue, priority),
        )
        ticket_id = cur.lastrowid
        conn.commit()

        cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cur.fetchone()
        conn.close()

        return {"success": True, "ticket": row_to_dict(row)}
    except Exception as e:
        return {"success": False, "error": f"Database error: {e}"}


def get_customer_history(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve all tickets for a given customer.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        rows = cur.fetchall()
        conn.close()

        tickets = [row_to_dict(r) for r in rows]
        return {"success": True, "count": len(tickets), "tickets": tickets}
    except Exception as e:
        return {"success": False, "error": f"Database error: {e}"}


# ---------------------------------------------------------------------
# MCP tool metadata
# ---------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "get_customer",
        "description": "Retrieve a specific customer by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The unique ID of the customer",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "list_customers",
        "description": "List customers, optionally by status and with a limit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "disabled"],
                    "description": "Optional filter by status",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of customers to return",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "update_customer",
        "description": "Update an existing customer's fields using a data dict.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The ID of the customer to update",
                },
                "data": {
                    "type": "object",
                    "description": "Fields to update (name, email, phone, status).",
                },
            },
            "required": ["customer_id", "data"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Create a support ticket for a customer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Customer ID",
                },
                "issue": {
                    "type": "string",
                    "description": "Description of the issue",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Ticket priority",
                    "default": "medium",
                },
            },
            "required": ["customer_id", "issue"],
        },
    },
    {
        "name": "get_customer_history",
        "description": "Get all tickets for a customer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Customer ID",
                }
            },
            "required": ["customer_id"],
        },
    },
]

# Map tool names to Python functions
TOOL_FUNCTIONS = {
    "get_customer": get_customer,
    "list_customers": list_customers,
    "update_customer": update_customer,
    "create_ticket": create_ticket,
    "get_customer_history": get_customer_history,
}

# ---------------------------------------------------------------------
# MCP JSON-RPC handlers
# ---------------------------------------------------------------------


def handle_initialize(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP 'initialize' request."""
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "customer-support-mcp-server", "version": "1.0.0"},
        },
    }


def handle_tools_list(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP 'tools/list' request."""
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {"tools": MCP_TOOLS},
    }


def handle_tools_call(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP 'tools/call' request."""
    params = message.get("params", {})
    name = params.get("name")
    arguments = params.get("arguments", {})

    if name not in TOOL_FUNCTIONS:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {"code": -32601, "message": f"Tool not found: {name}"},
        }

    try:
        result = TOOL_FUNCTIONS[name](**arguments)
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2),
                    }
                ]
            },
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {"code": -32603, "message": f"Tool execution error: {e}"},
        }


def process_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Route MCP requests to the appropriate handler."""
    method = message.get("method")
    if method == "initialize":
        return handle_initialize(message)
    if method == "tools/list":
        return handle_tools_list(message)
    if method == "tools/call":
        return handle_tools_call(message)
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def create_sse_message(data: Dict[str, Any]) -> str:
    """Format a dict as an SSE event."""
    return f"data: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------

app = Flask(__name__)
CORS(app)


@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    """
    Single HTTP endpoint that receives MCP JSON-RPC messages
    and returns Server-Sent Events (SSE) with the response.
    """
    message = request.get_json()

    def generate():
        try:
            print(f"[MCP] Received: {message.get('method')}")
            response = process_mcp_message(message)
            print("[MCP] Sending response")
            yield create_sse_message(response)
        except Exception as e:
            error_resp = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32700, "message": f"Parse / server error: {e}"},
            }
            yield create_sse_message(error_resp)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/health", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify(
        {"status": "healthy", "server": "customer-support-mcp-server", "version": "1.0.0"}
    )


if __name__ == "__main__":
    print("Starting MCP server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)

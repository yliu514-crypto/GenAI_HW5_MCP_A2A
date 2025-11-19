"""
agents.py
---------

This module defines the three agents used in the Multi-Agent Customer Service System:

1. CustomerDataAgent (Specialist)
   - Communicates with the MCP server
   - Executes MCP tools: get_customer, list_customers, update_customer, create_ticket, get_customer_history

2. SupportAgent (Specialist)
   - Implements support-related reasoning logic
   - Uses CustomerDataAgent to access or update customer data
   - Handles upgrades, billing issues, escalation, multi-step flows

3. RouterAgent (Orchestrator)
   - Receives user queries
   - Detects intent using simple rules
   - Allocates tasks to specialist agents
   - Coordinates multi-step workflows
   - Produces detailed A2A logs to show agent-to-agent communication
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from termcolor import colored

# MCP endpoint (must match the port used by mcp_server.py)
MCP_URL = "http://127.0.0.1:5000/mcp"


# ---------------------------------------------------------
# MCP Client Helper
# ---------------------------------------------------------

def mcp_call_tool(name: str, arguments: Dict[str, Any], message_id: int = 1) -> Dict[str, Any]:
    """
    Generic helper for sending a JSON-RPC tools/call request to the MCP server.

    This performs:
    - Constructing the JSON-RPC payload
    - Sending it to the MCP server
    - Parsing the streamed SSE response
    - Extracting the tool result payload
    """
    payload = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }

    print(colored(f"\n[MCP] → Calling tool: {name}", "cyan"))
    print(colored(json.dumps(payload, indent=2), "cyan"))

    resp = requests.post(MCP_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()

    print(colored("[MCP] ← Response received", "green"))
    print(colored(json.dumps(data, indent=2), "green"))

    if "result" in data:
        text = data["result"]["content"][0]["text"]
        return json.loads(text)  # Convert back into Python dict
    return {"success": False, "error": data.get("error", {}).get("message", "Unknown error")}


# ---------------------------------------------------------
# CustomerDataAgent
# ---------------------------------------------------------

class CustomerDataAgent:
    """
    Specialist agent that interacts with the MCP server.

    This agent performs ONLY data-access tasks and no reasoning logic.
    """

    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        return mcp_call_tool("get_customer", {"customer_id": customer_id}, message_id=101)

    def list_customers(self, status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        args: Dict[str, Any] = {"limit": limit}
        if status is not None:
            args["status"] = status
        return mcp_call_tool("list_customers", args, message_id=102)

    def update_customer(self, customer_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        args = {"customer_id": customer_id, "data": data}
        return mcp_call_tool("update_customer", args, message_id=103)

    def create_ticket(self, customer_id: int, issue: str, priority: str = "medium") -> Dict[str, Any]:
        args = {"customer_id": customer_id, "issue": issue, "priority": priority}
        return mcp_call_tool("create_ticket", args, message_id=104)

    def get_customer_history(self, customer_id: int) -> Dict[str, Any]:
        return mcp_call_tool("get_customer_history", {"customer_id": customer_id}, message_id=105)

    def get_active_customers_with_open_tickets(self) -> Dict[str, Any]:
        """
        Helper for Scenario 3:
        - Get all active customers
        - For each, fetch ticket history
        - Return only those with at least 1 open ticket
        """
        base = self.list_customers(status="active", limit=100)
        if not base.get("success"):
            return base

        results: List[Dict[str, Any]] = []
        for cust in base["customers"]:
            hist = self.get_customer_history(cust["id"])
            if not hist.get("success"):
                continue

            open_tickets = [t for t in hist["tickets"] if t["status"] == "open"]
            if open_tickets:
                results.append({"customer": cust, "open_tickets": open_tickets})

        return {"success": True, "count": len(results), "items": results}


# ---------------------------------------------------------
# SupportAgent
# ---------------------------------------------------------

class SupportAgent:
    """
    Specialist agent responsible for:
    - Account assistance
    - Upgrade logic
    - Cancellation + billing negotiation
    - Escalation workflows (double charging)
    - Multi-intent flows (update email + show history)
    """

    def __init__(self, data_agent: CustomerDataAgent):
        self.data_agent = data_agent
        self.name = "SupportAgent"

    def handle_account_help(self, customer_id: int, logs: List[str]) -> str:
        logs.append(f"{self.name}: Requesting customer info via DataAgent.get_customer({customer_id})")
        result = self.data_agent.get_customer(customer_id)

        if not result.get("success"):
            return f"Unable to fetch account info for customer {customer_id}: {result['error']}"

        cust = result["customer"]
        return f"I found your account: {cust['name']} (ID {cust['id']}), status = {cust['status']}."

    def handle_upgrade_request(self, customer_id: int, logs: List[str]) -> str:
        logs.append(f"{self.name}: Fetching customer info before recommending upgrade")
        result = self.data_agent.get_customer(customer_id)

        if not result.get("success"):
            return f"Unable to fetch account info for customer {customer_id}: {result['error']}"

        cust = result["customer"]
        return (
            f"Hello {cust['name']}! Your current account status is {cust['status']}.\n"
            "Based on your typical usage, I can help you upgrade to a better plan if needed."
        )

    def handle_billing_and_cancel(self, logs: List[str]) -> str:
        logs.append(f"{self.name}: Handling combined billing + cancellation flow")
        return (
            "You mentioned both cancellation and billing issues.\n"
            "I will first investigate your recent billing records. If there were any incorrect charges, "
            "I will submit a refund request before completing your cancellation."
        )

    def handle_escalation_refund(self, customer_id: int, logs: List[str]) -> str:
        logs.append(f"{self.name}: Creating high-priority refund ticket due to double charge")

        ticket = self.data_agent.create_ticket(
            customer_id=customer_id,
            issue="Double charge / urgent refund",
            priority="high",
        )

        if not ticket.get("success"):
            return f"Failed to create escalation ticket: {ticket['error']}"

        t = ticket["ticket"]
        logs.append(f"{self.name}: High-priority ticket #{t['id']} created")

        return (
            "I’m sorry for the duplicate charge.\n"
            f"A high-priority refund ticket (ID {t['id']}) has been submitted. "
            "Our billing team will contact you shortly."
        )

    def handle_ticket_report(self, logs: List[str]) -> str:
        logs.append(f"{self.name}: Requesting active customers with open tickets")
        result = self.data_agent.get_active_customers_with_open_tickets()

        if not result.get("success"):
            return f"Unable to generate ticket report: {result['error']}"

        if result["count"] == 0:
            return "All active customers currently have no open tickets. System health looks good. ✓"

        lines = ["Here is the list of active customers with open tickets:"]
        for item in result["items"]:
            cust = item["customer"]
            lines.append(f"\n- {cust['name']} (ID {cust['id']})")
            for t in item["open_tickets"]:
                lines.append(f"    • Ticket #{t['id']}: {t['issue']} [priority={t['priority']}]")

        return "\n".join(lines)

    def handle_update_email_and_history(self, customer_id: int, new_email: str, logs: List[str]) -> str:
        logs.append(f"{self.name}: Updating email, then fetching ticket history")

        upd = self.data_agent.update_customer(customer_id, {"email": new_email})
        if not upd.get("success"):
            return f"Failed to update email: {upd['error']}"

        hist = self.data_agent.get_customer_history(customer_id)
        if not hist.get("success"):
            return f"Email updated to {new_email}, but failed to fetch ticket history."

        lines = [f"Email updated to {new_email}. Here’s your ticket history:"]
        for t in hist["tickets"]:
            lines.append(
                f"- Ticket #{t['id']}: {t['issue']} [status={t['status']}, priority={t['priority']}]"
            )
        return "\n".join(lines)


# ---------------------------------------------------------
# RouterAgent (Orchestrator)
# ---------------------------------------------------------

@dataclass
class RouterResult:
    """Return structure holding final answer and full A2A logs."""
    query: str
    final_answer: str
    logs: List[str] = field(default_factory=list)


class RouterAgent:
    """
    Orchestrator Agent.

    Responsibilities:
    - Receive user query
    - Detect intent
    - Allocate tasks to the correct specialist agent
    - Coordinate multi-step flows
    - Log all A2A communication for transparency
    """

    def __init__(self, data_agent: CustomerDataAgent, support_agent: SupportAgent):
        self.data_agent = data_agent
        self.support_agent = support_agent
        self.name = "RouterAgent"

    # ----- Helper regex extractors -----

    def _extract_customer_id(self, text: str) -> Optional[int]:
        match = re.search(r"(?:id|customer)\s*(\d+)", text.lower())
        return int(match.group(1)) if match else None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        return match.group(0) if match else None

    # ----- Primary routing logic -----

    def handle_query(self, query: str) -> RouterResult:
        logs: List[str] = []
        logs.append(f"{self.name}: Received user query → \"{query}\"")

        text = query.lower()
        cid = self._extract_customer_id(query)

        # --- Simple Query: direct MCP call ---
        if "get customer information" in text and cid is not None:
            logs.append(f"{self.name}: Detected simple query → DataAgent.get_customer")
            result = self.data_agent.get_customer(cid)

            if not result.get("success"):
                answer = f"Unable to retrieve customer {cid}: {result['error']}"
            else:
                c = result["customer"]
                answer = (
                    f"Customer {cid} information:\n"
                    f"- Name: {c['name']}\n"
                    f"- Email: {c['email']}\n"
                    f"- Phone: {c['phone']}\n"
                    f"- Status: {c['status']}"
                )

            return RouterResult(query, answer, logs)

        # --- Scenario 1: Task Allocation ---
        if "help with my account" in text and cid is not None:
            logs.append(f"{self.name}: Scenario 1 detected → delegating to SupportAgent")
            answer = self.support_agent.handle_account_help(cid, logs)
            return RouterResult(query, answer, logs)

        # --- Scenario 2: Negotiation / Billing + Cancel ---
        if "cancel" in text and "billing" in text:
            logs.append(f"{self.name}: Scenario 2 detected → SupportAgent handles negotiation flow")
            answer = self.support_agent.handle_billing_and_cancel(logs)
            return RouterResult(query, answer, logs)

        # --- Scenario 3: Multi-step coordination ---
        if "active customers" in text and "open tickets" in text:
            logs.append(f"{self.name}: Scenario 3 detected → multi-step flow")
            answer = self.support_agent.handle_ticket_report(logs)
            return RouterResult(query, answer, logs)

        # --- Coordinated Upgrade ---
        if "upgrading my account" in text and cid is not None:
            logs.append(f"{self.name}: Coordinated upgrade scenario")
            answer = self.support_agent.handle_upgrade_request(cid, logs)
            return RouterResult(query, answer, logs)

        # --- Escalation: duplicate charges ---
        if "charged twice" in text or "double charged" in text:
            logs.append(f"{self.name}: Escalation detected → high-priority refund")
            cid = cid or 1
            answer = self.support_agent.handle_escalation_refund(cid, logs)
            return RouterResult(query, answer, logs)

        # --- Multi-intent: update email + show history ---
        if "update my email" in text and "ticket history" in text:
            logs.append(f"{self.name}: Multi-intent flow detected")
            cid = cid or 1
            email = self._extract_email(query) or "new@example.com"
            answer = self.support_agent.handle_update_email_and_history(cid, email, logs)
            return RouterResult(query, answer, logs)

        # --- Fallback ---
        logs.append(f"{self.name}: No recognized pattern → fallback reply")
        return RouterResult(
            query,
            "I can assist with account questions, upgrades, billing issues, refunds, cancellations, "
            "or ticket history. Please try rephrasing your request.",
            logs,
        )

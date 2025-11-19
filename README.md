# GenAI_HW5_MCP_A2A
# Multi-Agent Customer Service System (Option A — Simple & Fully Compliant)

# Multi-Agent Customer Service System (Option A – A2A + MCP)

This repository contains a fully implemented **multi-agent customer service system** built using **Agent-to-Agent (A2A) communication** and a custom **Model Context Protocol (MCP) server**.

The project fulfills all requirements of the assignment:

- Three cooperating agents:
  - **RouterAgent** (orchestrator)
  - **CustomerDataAgent** (MCP specialist)
  - **SupportAgent** (support specialist)
- MCP server with the required 5 tools
- Full A2A message passing with detailed logs
- End-to-end demonstration script showing task allocation, negotiation, and multi-step coordination
- GitHub-ready code structure with virtual environment instructions and requirements.txt

---

## 📂 Project Structure

.
├── database_setup.py # Initializes SQLite database (provided by professor)
├── mcp_server.py # MCP server exposing customer/ticket tools
├── agents.py # RouterAgent, CustomerDataAgent, SupportAgent
├── run_demo.py # End-to-end A2A demonstration script
├── requirements.txt # Python dependencies
└── README.md

yaml
Copy code

---

## 🔧 Installation & Setup

### 1. Create Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
2. Initialize the SQLite Database
A helper script (database_setup.py) creates support.db with preloaded customer and ticket data.

Run:

bash
Copy code
python database_setup.py
After running, your repository will contain:

Copy code
support.db
Tables created:

Customers
Field	Type
id (PK)	INTEGER
name	TEXT
email	TEXT
phone	TEXT
status	active/disabled
created_at	TIMESTAMP
updated_at	TIMESTAMP

Tickets
Field	Type
id (PK)	INTEGER
customer_id	INTEGER FK
issue	TEXT
status	open / in_progress / resolved
priority	low / medium / high
created_at	DATETIME

🚀 Running the MCP Server
Start the MCP server locally:

bash
Copy code
python mcp_server.py
You should see output similar to:

arduino
Copy code
MCP Server running at http://127.0.0.1:5000
Check server health:

arduino
Copy code
http://127.0.0.1:5000/health
🤖 MCP Tools Exposed by the Server
The server implements 5 required tools:

✔ get_customer(customer_id)
Retrieve a customer's full details.

✔ list_customers(status, limit)
List customers with optional status filter.

✔ update_customer(customer_id, data)
Update name/email/phone/status.

✔ create_ticket(customer_id, issue, priority)
Create a support ticket.

✔ get_customer_history(customer_id)
Return all tickets for that customer.

All tools return structured JSON according to the MCP spec.

🧠 Multi-Agent Architecture
RouterAgent (Orchestrator)
Responsible for:

Understanding user intent

Delegating tasks to specialists

Managing multi-step workflows

Collecting logs for transparency

Producing the final natural-language response

CustomerDataAgent (Specialist for MCP Data Access)
Wraps all MCP calls:

Query customers

Fetch ticket histories

Create/modify records

Handles no reasoning—only structured data I/O.

SupportAgent (Specialist for Customer Support)
Handles:

Account help

Billing + cancellation negotiation

Refund escalation (double charge → high-priority ticket)

Multi-step workflows

Multi-intent (email update + ticket history)

Generates final explanations for the user

▶️ Running the End-to-End Demo
Use:

bash
Copy code
python run_demo.py
This script runs six test scenarios, all printed with:

User query

RouterAgent interpretation

Agent-to-agent communication logs

Final combined response

Included Scenarios
Scenario	Description
Simple Query	Get customer info
Task Allocation	“Help with my account, ID X”
Negotiation	Cancellation + billing issues
Multi-step	Active customers with open tickets
Escalation	Urgent refund for double charge
Multi-intent	Update email + ticket history

These cover all assignment requirements.

📝 Conclusion (Reflection)
During this project, I learned how to design clean multi-agent architectures that separate reasoning from data access. Building the MCP server helped me understand how tools can act as a stable API layer for agents. Implementing A2A coordination required careful thought about task allocation, negotiation, and multi-step reasoning.

The most challenging aspects included ensuring that information passed correctly between agents, handling multi-intent queries, and maintaining clear logs for transparency. This assignment strengthened my understanding of agent communication patterns and the importance of explicit state and message flow in real-world AI systems.


# GenAI_HW5_MCP_A2A
# Multi-Agent Customer Service System (Option A — Simple & Fully Compliant)

This repository contains a fully implemented Multi-Agent Customer Service System built using Agent-to-Agent (A2A) coordination and a custom Model Context Protocol (MCP) server. The project satisfies all assignment requirements:

• RouterAgent (Orchestrator)
• CustomerDataAgent (MCP Specialist)
• SupportAgent (Customer Support Specialist)
• MCP server with 5 required tools
• Three required A2A coordination scenarios
• End-to-end demonstration script with logs
• Proper Python project structure for submission

Project Structure

.
├── database_setup.py
├── mcp_server.py
├── agents.py
├── run_demo.py
├── requirements.txt
└── README.md

1. Installation

Create a virtual environment:

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

2. Initialize the Database

Run this once:

python database_setup.py

This generates support.db with two tables:

customers

id

name

email

phone

status

created_at

updated_at

tickets

id

customer_id

issue

status

priority

created_at

3. Run the MCP Server

python mcp_server.py

Server runs at:

http://127.0.0.1:5000

Health check:

http://127.0.0.1:5000/health

4. MCP Tools Provided

The server exposes all required tools:

get_customer(customer_id)

list_customers(status, limit)

update_customer(customer_id, data)

create_ticket(customer_id, issue, priority)

get_customer_history(customer_id)

All tools follow the MCP JSON-RPC format and return structured JSON.

5. Multi-Agent Architecture
RouterAgent (Orchestrator)

Interprets natural language queries

Detects intent

Delegates tasks to specialist agents

Handles multi-step reasoning

Logs agent-to-agent communication

CustomerDataAgent (MCP Specialist)

Executes all MCP tool calls

Retrieves and updates customer data

Retrieves ticket histories

Creates new tickets

No reasoning: pure structured I/O

SupportAgent (Support Specialist)

Provides customer support logic

Handles upgrades, account issues, billing, cancellation

Performs escalations (double charge → high-priority ticket)

Generates ticket status reports

Handles multi-intent queries

6. Run the End-to-End Demo

python run_demo.py

This script demonstrates all scenarios:

Simple Query

Task Allocation

Negotiation (billing + cancellation)

Multi-step reasoning (open tickets for active customers)

Escalation (double charge refund)

Multi-intent (update email + ticket history)

Output includes:

• User query
• Detailed agent-to-agent logs
• Final constructed answer

7. Conclusion (Reflection)

This project helped me understand how to design a clean multi-agent architecture where each agent has a specific role and communication between agents is explicit and traceable. Building the MCP server strengthened my understanding of separating data access from reasoning logic. Implementing multi-step workflows such as escalation and ticket-report generation required careful coordination and transparent logging, which was a core part of this assignment. Overall, this project improved my understanding of agent orchestration, tool integration, and system-level transparency in real-world AI applications.

8. Requirements

flask
flask-cors
requests
termcolor

9. Ready for Submission

This repository includes:

• MCP server
• Multi-agent system (Router, Data, Support)
• A2A coordination
• End-to-end demonstration
• README
• requirements.txt

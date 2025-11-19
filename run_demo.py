"""
run_demo.py
-----------

This script demonstrates the full end-to-end Agent-to-Agent (A2A) workflow:

1. Instantiate all agents:
   - CustomerDataAgent (specialist)
   - SupportAgent (specialist)
   - RouterAgent (orchestrator)

2. Execute the required test scenarios:
   - Simple Query
   - Coordinated Query
   - Multi-step Query
   - Escalation
   - Multi-intent Query

3. Print full logs showing:
   - How Router delegates tasks
   - How SupportAgent interacts with CustomerDataAgent
   - Full reasoning trace of the multi-agent system

Make sure the MCP server is already running:
    python mcp_server.py
"""

from agents import CustomerDataAgent, SupportAgent, RouterAgent


# ---------------------------------------------------------
# Helper to run a test and print results nicely
# ---------------------------------------------------------

def run_test(title: str, query: str, router: RouterAgent):
    print("\n" + "=" * 70)
    print(f"TEST: {title}")
    print("=" * 70)
    print(f"User Query: {query}\n")

    result = router.handle_query(query)

    print("\n--- Agent-to-Agent Logs ---")
    for log in result.logs:
        print("• " + log)

    print("\n--- Final Answer ---")
    print(result.final_answer)
    print("=" * 70 + "\n")


# ---------------------------------------------------------
# Main Demonstration
# ---------------------------------------------------------

def main():
    print("\n🚀 Starting A2A Demonstration...\n")

    # Create agents
    data_agent = CustomerDataAgent()
    support_agent = SupportAgent(data_agent)
    router = RouterAgent(data_agent, support_agent)

    # -------------------------------
    # Scenario 1: Simple Query
    # -------------------------------
    run_test(
        "Simple: Get customer info",
        "Get customer information for ID 1",
        router,
    )

    # -------------------------------
    # Scenario 2: Task Allocation
    # -------------------------------
    run_test(
        "Scenario 1 (Task Allocation): Help with account",
        "I need help with my account, customer ID 1",
        router,
    )

    # -------------------------------
    # Scenario 3: Negotiation / Escalation
    # -------------------------------
    run_test(
        "Scenario 2 (Negotiation): Cancel + Billing issue",
        "I want to cancel my subscription but I'm having billing issues",
        router,
    )

    # -------------------------------
    # Scenario 4: Multi-step Coordination
    # -------------------------------
    run_test(
        "Scenario 3 (Multi-step): Active customers with open tickets",
        "Show me all active customers who have open tickets",
        router,
    )

    # -------------------------------
    # Scenario 5: Escalation - double charge
    # -------------------------------
    run_test(
        "Escalation: Double charge refund",
        "I was charged twice, please refund immediately!",
        router,
    )

    # -------------------------------
    # Scenario 6: Multi-intent
    # -------------------------------
    run_test(
        "Multi-intent: Update email + ticket history",
        "Update my email to new@email.com and show my ticket history for customer 1",
        router,
    )

    print("\n🎉 All tests completed successfully!\n")


if __name__ == "__main__":
    main()

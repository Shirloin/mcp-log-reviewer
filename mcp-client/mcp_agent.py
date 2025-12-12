import asyncio
import json
import os
from datetime import datetime
from mcp_use import MCPClient, MCPAgent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Interval in minutes
RUN_INTERVAL_MINUTES = 5

# Get values from environment variables
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_PROJECT = os.getenv("GITHUB_PROJECT")

# Prompt for the agent
PROMPT = f"""You are a log analysis agent. Follow these steps in order:

        STEP 1: Query Logs
        - Use the logQuery tools to search for errors in the logs
        - Error logs from the last 5 minutes for the service are already provided
        - Review the provided log entries to identify errors
        - The logs are already filtered to show error entries

        STEP 2: If errors are found, analyze them
        - Extract the error messages, stack traces, and relevant context
        - Identify the key error information (error type, message, timestamp)

        STEP 3: Analyze the code from GitHub repository
        - Repository: {GITHUB_REPOSITORY}
        - Use GitHub tools to:
        a) Search for files that might be related to the error
        b) Read the relevant source code files
        c) Identify the exact file, line number, and code section causing the error
        d) Provide the specific code snippet that is causing the issue

        STEP 4: Create a GitHub backlog on Github Project
        - Use GitHub tools to search for the project named "{GITHUB_PROJECT}"
        - First, list all projects for user "{GITHUB_OWNER}" to find the correct project number
        - Once found, create a backlog item in that project
        - If the project doesn't exist, create it first, then add the backlog
        - Project should be under owner: {GITHUB_OWNER} (user, not org)
        - Title: Should describe the error briefly
        - If there are duplicate backlog with the same problem, update the existing backlog instead of creating new one


        IMPORTANT:
        - Only proceed to Step 2 if errors are found in Step 1
        - Only proceed to Step 3 if errors are found
        - Before creating the backlog, check all the backlogs in the {GITHUB_PROJECT} Project and if the error is already in the backlog, don't create a new backlog
        - Always create the backlog in Step 4 if errors are found
        - Be specific about file paths, line numbers, and code snippets
        - Format your response clearly with sections for each step


        Now execute this workflow for the service logs from the last 5 minutes."""

async def run_agent(agent):
    """Run the agent once."""
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting agent run...")
        result = await agent.run(PROMPT)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent run completed.")
        print(result)
        print("-" * 80)
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error running agent: {e}")
        print("-" * 80)

async def main():
    """Main function that runs the agent every 5 minutes."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Initializing agent...")

    # Initialize client, llm, and agent once
    with open("config.json", "r") as f:
        config = json.load(f)

    client = MCPClient.from_dict(config)
    llm = ChatOpenAI(model="gpt-5.2")
    agent = MCPAgent(client=client, llm=llm, max_steps=50)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent initialized. Starting scheduler. Running every {RUN_INTERVAL_MINUTES} minutes.")
    print("Press Ctrl+C to stop.")
    print("-" * 80)

    # Run immediately on startup
    await run_agent(agent)

    # Then run every 5 minutes
    while True:
        await asyncio.sleep(RUN_INTERVAL_MINUTES * 60)  # Convert minutes to seconds
        await run_agent(agent)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Agent scheduler stopped by user.")
# Log Watcher - Automated Error Detection and Backlog Creation

A comprehensive system that automatically monitors application logs, detects errors, analyzes code, and creates GitHub project backlog items using MCP (Model Context Protocol) and AI agents.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Flow](#system-flow)
- [Layer Breakdown](#layer-breakdown)
- [Getting Started](#getting-started)
- [Configuration Guide](#configuration-guide)
- [Usage](#usage)

---

## Architecture Overview

The Log Watcher system is built on a layered architecture that combines log aggregation, intelligent analysis, and automated task management. The system operates in a continuous loop, monitoring logs every 5 minutes and automatically creating backlog items when errors are detected.

The architecture follows the MCP (Model Context Protocol) pattern where:

- **MCP Servers** expose tools/capabilities
- **MCP Client** (Orchestration Layer) connects to multiple servers and coordinates tool usage
- **LLM Agent** uses the available MCP tools to perform intelligent analysis

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
│              (Generating logs with service labels)          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                         Loki                                │
│              (Log Aggregation & Storage)                    │
│  - External log storage service                             │
│  - Provides LogQL query API                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP API (LogQL)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP Servers (Tool Providers)                   │
│                                                             │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │ Loki Pooler          │      │ GitHub MCP Server    │     │
│  │ MCP Server           │      │ (Official)           │     │
│  │                      │      │                      │     │
│  │ Tool: log_query()    │      │ Tools:               │     │
│  │                      │      │ - search_code()      │     │
│  │ Queries Loki API     │      │ - get_file_contents()│     │
│  │ Returns log data     │      │ - list_projects()    │     │
│  │                      │      │ - create_issue()     │     │
│  └──────────────────────┘      └──────────────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ MCP Protocol (stdio)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Orchestration Layer (MCP Client + LLM Agent)        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              MCP Client                             │    │
│  │  - Connects to multiple MCP servers                 │    │
│  │  - Manages tool discovery and execution             │    │
│  │  - Handles communication protocol                   │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          │                                  │
│  ┌───────────────────────▼─────────────────────────────┐    │
│  │              LLM Agent (GPT-5.2)                    │    │
│  │                                                     │    │
│  │  Capabilities:                                      │    │
│  │  • LLM Review: Analyzes logs, investigates code     │    │
│  │  • Uses log_query() from Loki Pooler MCP Server     │    │
│  │  • Uses GitHub tools from GitHub MCP Server         │    │
│  │  • Creates/updates backlog items                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  - Schedules execution (every 5 minutes)                    │
│  - Coordinates workflow between tools                       │
│  - Makes intelligent decisions                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ GitHub API
                        ▼
              ┌─────────────────────┐
              │  GitHub Project     │
              │  Backlog Items      │
              │  (Created/Updated)  │
              └─────────────────────┘
```

### Why This Architecture?

The architecture follows the **MCP (Model Context Protocol)** pattern, which provides several key benefits:

1. **Separation of Concerns**:

   - Each MCP server is a specialized tool provider
   - Orchestration layer focuses on coordination, not implementation
   - Clear boundaries between log querying, code access, and project management

2. **Modularity and Extensibility**:

   - Easy to add new MCP servers (e.g., Jira, Slack, monitoring tools)
   - Each server can be developed, deployed, and updated independently
   - Tools are discoverable and self-documenting via MCP protocol

3. **Reusability**:

   - Loki Pooler MCP Server can be used by other applications
   - GitHub MCP Server is the official, maintained tool
   - No need to reimplement GitHub API integration

4. **Protocol Standardization**:

   - All tools communicate via MCP protocol (stdio)
   - Consistent interface regardless of tool implementation
   - Easy to swap implementations (e.g., different log query servers)

5. **AI Agent Flexibility**:
   - LLM Agent can discover and use any available tools
   - Agent decides which tools to use based on context
   - No hardcoded workflows - agent adapts to available capabilities

**Flow Explanation**:

- **Loki → Loki Pooler MCP Server**: Direct HTTP connection because Loki Pooler needs to query Loki's API
- **MCP Servers → Orchestration Layer**: MCP protocol (stdio) because this is the standard way MCP servers communicate
- **Orchestration Layer**: Contains both MCP Client (tool router) and LLM Agent (tool user) because they work together - the client manages connections while the agent uses the tools

---

## System Flow

### High-Level Workflow

1. **Log Collection**: Application logs are continuously sent to Loki
2. **Scheduled Polling**: Every 5 minutes, the system queries Loki for recent error logs
3. **Error Detection**: The system filters and identifies error entries
4. **Code Analysis**: AI agent analyzes the codebase to find the root cause
5. **Backlog Creation**: Automatically creates or updates GitHub project backlog items

### Detailed Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM EXECUTION CYCLE                       │
└─────────────────────────────────────────────────────────────────┘

1. SCHEDULER TRIGGER (Every 5 minutes)
   │
   ├─> Orchestration Layer starts agent execution
   │
2. LOG QUERY PHASE
   │
   ├─> LLM Agent requests log data
   │   ├─> MCP Client routes call to Loki Pooler MCP Server
   │   ├─> Loki Pooler MCP Server queries Loki API (HTTP)
   │   ├─> Filters logs by service name
   │   ├─> Retrieves logs from last 5 minutes
   │   └─> Returns formatted log data to LLM Agent
   │
3. ERROR ANALYSIS PHASE (If errors found)
   │
   ├─> LLM Review Agent receives log data
   │   ├─> Analyzes error messages
   │   ├─> Extracts stack traces
   │   ├─> Identifies error patterns
   │   └─> Determines error context
   │
4. CODE INVESTIGATION PHASE (If errors found)
   │
   ├─> LLM Agent requests code investigation
   │   ├─> MCP Client routes calls to GitHub MCP Server
   │   ├─> Agent uses search_code() tool → Finds relevant files
   │   ├─> Agent uses get_file_contents() tool → Reads source code
   │   ├─> Agent analyzes code to identify file and line numbers
   │   └─> Agent extracts code snippets causing errors
   │
5. BACKLOG MANAGEMENT PHASE (If errors found)
   │
   ├─> LLM Agent requests backlog management
   │   ├─> MCP Client routes calls to GitHub MCP Server
   │   ├─> Agent uses list_projects() tool → Finds target project
   │   ├─> Agent uses list_issues() tool → Checks for duplicates
   │   ├─> Agent uses create_issue() tool → Creates new backlog OR
   │   └─> Agent updates existing backlog item if duplicate found
   │
6. COMPLETION
   │
   └─> Wait 5 minutes, then repeat from step 1
```

---

## Layer Breakdown

### 1. Loki (Logs)

**Purpose**: Centralized log aggregation and storage system

**Description**:

- Loki is a horizontally-scalable, highly-available log aggregation system
- Collects logs from your application services
- Stores logs with labels (e.g., `service`, `environment`, `level`)
- Provides LogQL query interface for log retrieval

**Key Features**:

- Efficient log storage and indexing
- Label-based log filtering
- Time-range queries
- High availability and scalability

**Configuration**:

- Requires a running Loki instance
- Service logs must be labeled with `service` label
- Accessible via HTTP API endpoint

---

### 2. MCP Servers (Tool Providers)

**Purpose**: Expose specialized tools/capabilities via MCP protocol

**Architecture**: MCP Servers are independent processes that expose tools. The Orchestration Layer connects to multiple MCP servers to access their tools.

#### 2.1 Loki Pooler MCP Server

**Purpose**: Provides log querying capabilities as an MCP tool

**Location**: `mcp-server-log-query/`

**Components**:

- `log_query.py`: Core function that queries Loki API
- `main.py`: FastMCP server exposing `log_query` tool

**Functionality**:

- Queries Loki using LogQL syntax
- Filters logs by service name
- Retrieves logs from the last 5 minutes (configurable)
- Returns formatted JSON with log entries, timestamps, and metadata

**MCP Tool**: `log_query()`

- **Input**: None (uses environment variables)
- **Output**: JSON string with log results
- **Query Pattern**: `{service="<SERVICE_NAME>"}`
- **Connection**: Direct HTTP API calls to Loki

**Key Files**:

```
mcp-server-log-query/
├── log_query.py      # Loki query implementation
├── main.py           # MCP server with log_query tool
├── Dockerfile        # Container build configuration
└── docker-compose.yml # Docker deployment config
```

#### 2.2 GitHub MCP Server (Official)

**Purpose**: Provides GitHub repository and project management capabilities

**Description**:

- Official GitHub MCP server from GitHub
- Exposes comprehensive GitHub API tools
- Handles authentication and API communication

**Key MCP Tools Used**:

- `search_code()`: Search repository code
- `get_file_contents()`: Read source code files
- `list_projects()`: List GitHub projects
- `create_issue()`: Create backlog items
- `list_issues()`: Check for duplicates
- And many more GitHub operations

**Integration**:

- Connected via MCP protocol (stdio)
- Uses GitHub Personal Access Token for authentication
- Runs as Docker container

---

### 3. Orchestration Layer (MCP Client + LLM Agent)

**Purpose**: Coordinates all MCP tools and manages the intelligent agent workflow

**Location**: `mcp-client/`

**Components**:

- `mcp_agent.py`: Main orchestration script
- `config.json`: MCP server configuration

**Architecture**:
The Orchestration Layer consists of two main components working together:

1. **MCP Client**: Manages connections to MCP servers
2. **LLM Agent**: Uses the tools provided by MCP servers

**MCP Client Responsibilities**:

- Load MCP server configurations from `config.json`
- Establish connections to multiple MCP servers:
  - `log`: Loki Pooler MCP server
  - `github`: GitHub MCP server (official)
- Discover available tools from each server
- Execute tool calls on behalf of the agent
- Handle MCP protocol communication (stdio)

**LLM Agent Responsibilities**:

- Powered by OpenAI's GPT-5.2 model
- Receives workflow instructions via prompt
- Makes intelligent decisions about which tools to use
- Analyzes log data and code
- Coordinates multi-step workflows

**Workflow Execution**:

**Step 1: Query Logs**

- Agent calls `log_query()` tool from Loki Pooler MCP Server
- MCP Client routes the call to the appropriate server
- Loki Pooler queries Loki API and returns formatted logs
- Agent receives error logs from the last 5 minutes

**Step 2: Error Analysis** (If errors found)

- Agent analyzes log data using LLM capabilities
- Extracts error messages, stack traces, and context
- Identifies error types and patterns
- Determines error severity and impact

**Step 3: Code Investigation** (If errors found)

- Agent calls GitHub MCP tools (`search_code`, `get_file_contents`)
- MCP Client routes calls to GitHub MCP Server
- Agent receives source code files and identifies root causes
- Extracts file paths, line numbers, and code snippets

**Step 4: Backlog Management** (If errors found)

- Agent calls GitHub MCP tools (`list_projects`, `list_issues`)
- Checks for existing backlog items to prevent duplicates
- Creates new backlog item using `create_issue` tool
- Or updates existing item if error persists

**Scheduling**:

- Runs immediately on startup
- Executes every 5 minutes (configurable)
- Handles errors gracefully and continues running

**Key Features**:

- Multi-server tool coordination
- Intelligent workflow orchestration
- Error handling and logging
- Configurable execution intervals

---

### 4. LLM Review (Capability, not a separate layer)

**Note**: LLM Review is not a separate architectural layer. It's a **capability** of the LLM Agent in the Orchestration Layer.

**Purpose**: Intelligent log analysis and code investigation capability

**Description**:

- This is the intelligent analysis performed by the LLM Agent
- Uses GPT-5.2 model to understand and analyze data
- Makes decisions about which tools to use and when
- Synthesizes information from multiple sources

**Capabilities**:

- Error pattern recognition
- Code context understanding
- Root cause analysis
- Duplicate detection logic
- Natural language understanding

---

### 5. GitHub Project Backlog Creator (Capability, not a separate layer)

**Note**: GitHub Project Backlog Creator is not a separate architectural layer. It's a **capability** provided by the GitHub MCP Server tools, used by the LLM Agent.

**Purpose**: Automated backlog item creation and management capability

**Description**:

- This capability is achieved by the LLM Agent using GitHub MCP Server tools
- The agent intelligently decides when to create/update backlog items
- Uses multiple GitHub tools in coordination

**Tool Usage**:

- `list_projects()`: Find the target project
- `list_issues()`: Check for existing items
- `create_issue()`: Create new backlog items
- `get_file_contents()`: Include code references

**Backlog Item Structure**:

- **Title**: Brief error description (generated by agent)
- **Description**: Error details, code snippets, file paths (synthesized by agent)
- **Labels**: Automatic categorization
- **References**: Links to source code files and line numbers

---

## Getting Started

### Prerequisites

- **Docker**: For running MCP servers
- **Python 3.12+**: For MCP client
- **Loki Instance**: Running and accessible
- **GitHub Account**: With Personal Access Token
- **OpenAI API Key**: For LLM agent

### Required Environment Variables

#### For MCP Server (Loki Pooler)

- `LOKI_URL`: URL to your Loki instance (e.g., `http://localhost:3100`)
- `SERVICE_NAME`: Name of the service to monitor (e.g., `my-app`)

#### For MCP Client (Orchestration)

- `GITHUB_REPOSITORY`: Repository name (e.g., `my-org/my-repo`)
- `GITHUB_OWNER`: GitHub username or organization
- `GITHUB_PROJECT`: Project name for backlog items
- `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub PAT with repo and project permissions
- `OPENAI_API_KEY`: OpenAI API key for LLM

---

## Configuration Guide

### Step 1: Configure MCP Server (Loki Pooler)

#### 1.1 Build the Docker Image

Navigate to the MCP server directory:

```bash
cd mcp-server-log-query
```

Build the Docker image:

```bash
docker build -t mcp-log-query:latest .
```

Or use docker-compose:

```bash
docker-compose build
```

#### 1.2 Configure Environment Variables

Create a `.env` file in `mcp-server-log-query/`:

```env
LOKI_URL=http://your-loki-instance:3100
SERVICE_NAME=your-service-name
```

#### 1.3 Test the MCP Server

Run the server locally to test:

```bash
docker run -i --rm \
  -e LOKI_URL=http://your-loki-instance:3100 \
  -e SERVICE_NAME=your-service-name \
  mcp-log-query:latest
```

The server should start and wait for stdio input.

#### 1.4 Push to Container Registry (Optional)

If using remote Docker image:

```bash
docker tag mcp-log-query:latest your-registry/mcp-log-query:latest
docker push your-registry/mcp-log-query:latest
```

Update `docker-compose.yml` or `config.json` with your image name.

---

### Step 2: Configure MCP Client (Orchestration Layer)

#### 2.1 Install Dependencies

Navigate to the MCP client directory:

```bash
cd mcp-client
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install required packages:

```bash
pip install mcp-use langchain-openai python-dotenv
```

#### 2.2 Configure Environment Variables

Create a `.env` file in `mcp-client/`:

```env
# GitHub Configuration
GITHUB_REPOSITORY=your-org/your-repo
GITHUB_OWNER=your-org
GITHUB_PROJECT=Your Project Name
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key-here
```

#### 2.3 Configure MCP Servers

Copy the example configuration:

```bash
cp config.example.json config.json
```

Edit `config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_PERSONAL_ACCESS_TOKEN}",
        "-e",
        "GITHUB_TOOLSETS=all",
        "-e",
        "GITHUB_TOOLS=all",
        "ghcr.io/github/github-mcp-server"
      ]
    },
    "log": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--pull",
        "always",
        "-e",
        "LOKI_URL",
        "-e",
        "SERVICE_NAME",
        "your-registry/mcp-log-query:latest"
      ],
      "env": {
        "LOKI_URL": "${LOKI_URL}",
        "SERVICE_NAME": "${SERVICE_NAME}"
      }
    }
  }
}
```

**Important Configuration Notes**:

1. **Docker Image Name**: Replace `your-registry/mcp-log-query:latest` with your actual image name
2. **Environment Variables**: The `${VARIABLE}` syntax will be replaced from your `.env` file
3. **GitHub Token**: Ensure your token has these permissions:
   - `repo` (full control)
   - `read:org` (if using organization projects)
   - `project` (full control)

#### 2.4 Verify Configuration

Test the configuration by running a quick check:

```python
# test_config.py
import json
import os
from dotenv import load_dotenv

load_dotenv()

with open("config.json", "r") as f:
    config = json.load(f)

print("MCP Servers configured:")
for server_name in config["mcpServers"]:
    print(f"  - {server_name}")

print("\nEnvironment variables:")
print(f"  GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY')}")
print(f"  GITHUB_OWNER: {os.getenv('GITHUB_OWNER')}")
print(f"  GITHUB_PROJECT: {os.getenv('GITHUB_PROJECT')}")
print(f"  LOKI_URL: {os.getenv('LOKI_URL')}")
print(f"  SERVICE_NAME: {os.getenv('SERVICE_NAME')}")
```

---

## Usage

### Running the System

#### Start the MCP Client

From the `mcp-client/` directory:

```bash
python mcp_agent.py
```

The system will:

1. Initialize MCP connections to both servers
2. Start the AI agent
3. Run immediately on startup
4. Continue running every 5 minutes

#### Expected Output

```
[2024-01-15 10:00:00] Initializing agent...
[2024-01-15 10:00:01] Agent initialized. Starting scheduler. Running every 5 minutes.
Press Ctrl+C to stop.
--------------------------------------------------------------------------------
[2024-01-15 10:00:01] Starting agent run...
[2024-01-15 10:00:05] Agent run completed.
[Agent response with log analysis and backlog creation details]
--------------------------------------------------------------------------------
[2024-01-15 10:05:01] Starting agent run...
...
```

### Stopping the System

Press `Ctrl+C` to gracefully stop the agent scheduler.

---

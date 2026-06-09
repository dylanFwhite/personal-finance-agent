# Personal Finance Agent — Project Plan

## Overview

A locally hosted, LLM-powered personal finance management tool built incrementally as a personal development project for agentic AI systems. The tool is powered by a local database containing core personal finance datasets, with a locally hosted LLM interacting with the database to answer user questions, provide commentary, and make suggestions.

---

## Technology Stack

| Technology             | Role                                                  |
| ---------------------- | ----------------------------------------------------- |
| **LangGraph (Python)** | Core agentic orchestration logic                      |
| **Rust**               | Deterministic tools (parsing, financial calculations) |
| **DuckDB**             | Local embedded database / analytical compute engine   |
| **Ollama**             | Local LLM inference server, network-accessible        |
| **uv**                 | Python project management and distribution            |

### Technology Rationale

- **DuckDB** — Embedded (no server), fast on analytical queries, excellent CSV/Parquet ingestion, expressive SQL dialect. Ideal for a local-first finance tool.
- **LangGraph** — Explicit control over agent state machines via graph-based orchestration. Becomes especially valuable for multi-step workflows (ingestion pipelines, projection scenarios).
- **Rust** — Strong correctness guarantees for logic that must be deterministic (financial calculations, data parsing). Clean separation from the Python orchestration layer.
- **Ollama** — Already in use. Handles concurrent requests via queuing, exposes an OpenAI-compatible API. Bound to `0.0.0.0` to serve other machines on the local network.
- **uv** — Fast Python project management (from the ruff/Astral team). Enables simple distribution to non-technical users via a bootstrap script.

---

## Deployment Model

### Network Topology

The LLM runs on a single powerful machine and is accessed over the local network. Each user runs their own instance of the agent and database locally. Financial data never leaves the user's device — only LLM prompts and responses cross the network.

```
┌─────────────────────────────────────────────────┐
│              Host PC (LLM Server)               │
│  ┌───────────────────────────────────────────┐  │
│  │  Ollama (bound to 0.0.0.0:11434)          │  │
│  │  Serving model to local network           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
        ▲           ▲           ▲
        │           │           │
   Local Network  Local Network  Local Network
        │           │           │
┌───────┴──┐  ┌────┴─────┐  ┌─┴──────────┐
│  You     │  │  Friend  │  │  Family    │
│  Own PC  │  │  Laptop  │  │  Member    │
│          │  │          │  │            │
│ DuckDB   │  │ DuckDB   │  │ DuckDB    │
│ Agent    │  │ Agent    │  │ Agent     │
│ Data     │  │ Data     │  │ Data      │
└──────────┘  └──────────┘  └───────────┘
```

### Ollama Configuration

Ollama is already set up on the host PC. To serve the model to the local network, bind it to all interfaces rather than localhost only. Give the host PC a **static IP or DHCP reservation** on the router so that other users' configurations don't break after a router reboot.

### Distribution to Users

The tool is distributed as a project folder with a bootstrap script (`start.bat` for Windows, `start.sh` for macOS/Linux). Users double-click the script to launch the tool. The script handles:

1. Installing uv and setting up the Python environment (first run only)
2. Running first-run initialisation if needed (see below)
3. Launching the terminal agent

This is not a compiled binary — it's a **single-action launch** that abstracts away the technical details. uv's speed means first-run environment setup takes seconds, not minutes.

### First-Run Setup

On first launch, an initialisation module runs before the agent starts:

1. **Create the application data directory** (`~/.finance-agent/`)
2. **Create the DuckDB database** with the full schema
3. **Prompt for the Ollama server address** (with a sensible default pointing to the host PC's static IP)
4. **Save user preferences** to a config file
5. **Verify connectivity** to the Ollama server (fail gracefully with a clear message if unreachable)

```python
class FirstRunSetup:
    def __init__(self, app_dir: str):
        self.app_dir = app_dir
        self.db_path = os.path.join(app_dir, "finance.duckdb")

    def is_first_run(self) -> bool:
        return not os.path.exists(self.db_path)

    def run_setup(self):
        print("Welcome! Setting up your personal finance agent...")
        self._create_database()
        self._run_migrations()
        self._collect_user_preferences()
        print("Setup complete.")
```

### Application Data Directory

All user data lives under a single directory for simplicity and easy backups:

```
~/.finance-agent/
    finance.duckdb          # the database
    config.yaml             # user preferences (incl. Ollama server address)
    logs/                   # agent interaction logs
```

### Schema Migrations

Once users have data in their databases, schema changes must be handled via migrations rather than recreating the database. A simple numbered SQL migration approach:

```
migrations/
    001_initial_schema.sql
    002_add_categories_table.sql
    003_add_agent_history.sql
```

A `schema_version` table in DuckDB tracks which migrations have been applied. On startup, the tool checks the current version and applies any pending migrations automatically.

### Configuration

The LLM endpoint must be configurable since it is not on `localhost` for anyone except the host PC user:

```yaml
# ~/.finance-agent/config.yaml
llm:
  base_url: "http://192.168.1.100:11434"
  model: "llama3:70b"
```

**Key rule:** Don't hardcode paths or assume the development environment. Use the app data directory and configurable endpoints from day one so that distribution is a packaging concern, not a refactoring task.

---

## Architecture

### Core Principle

The agent is a **thin orchestration layer** that routes to specialised tools and sub-graphs — not a monolith.

```
┌─────────────────────────────────────────────────────────┐
│                    Terminal Interface                   │
│              (User input / output formatting)           │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Router / Supervisor                  │
│           (LangGraph entry point — classifies           │
│            intent, delegates to sub-graphs)             │
└────┬──────────┬──────────┬──────────┬───────────────────┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  Q&A   │ │Ingest  │ │Project-│ │ Future │
│Sub-graph│ │Sub-graph│ │ions    │ │Sub-graph│
│        │ │        │ │Sub-graph│ │        │
└───┬────┘ └───┬────┘ └───┬────┘ └────────┘
    │          │          │
    ▼          ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                     Tool Registry                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐             │
│  │ DuckDB    │ │ CSV/File  │ │ Financial │             │
│  │ Query     │ │ Parser    │ │ Calc      │             │
│  │ (Python)  │ │ (Rust)    │ │ (Rust)    │             │
│  └───────────┘ └───────────┘ └───────────┘             │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      DuckDB Instance                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │Transactions│ │ Categories │ │Agent History│          │
│  └────────────┘ └────────────┘ └────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

#### 1. Router / Supervisor Pattern

A top-level LangGraph graph that classifies user intent and delegates to the appropriate sub-graph. Even when only one sub-graph exists (Q&A), this structure should be in place so that adding new capabilities is a matter of registering a new sub-graph rather than modifying existing logic.

#### 2. Tool Definitions Separate from Agent Logic

Tools are standalone, independently testable units that know nothing about LangGraph. Thin wrappers expose them as LangGraph tools.

```python
# tools/duckdb_query.py — knows nothing about LangGraph
def execute_query(db_path: str, sql: str) -> QueryResult:
    ...

# agent/tools.py — thin LangGraph wrapper
@tool
def query_database(sql: str) -> str:
    result = execute_query(DB_PATH, sql)
    return format_result(result)
```

This allows isolated testing, reuse across sub-graphs, and a clean integration point for Rust tools.

#### 3. Shared State Schema

A typed LangGraph state object that flows through the graph, designed to be extensible.

```python
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    intent: str | None
    active_subgraph: str | None
    db_path: str
```

Sub-graphs should only read/write state keys they own, plus the shared `messages` list.

#### 4. DuckDB Access Layer

A thin abstraction over DuckDB that enforces read/write separation and provides schema context for LLM prompts.

```python
class FinanceDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_schema_description(self) -> str:
        """Returns human-readable schema for LLM context."""
        ...

    def execute_readonly(self, sql: str) -> QueryResult:
        """Execute a read-only query. Raises on write attempts."""
        ...

    def execute_write(self, sql: str) -> WriteResult:
        """Execute a write query. Only used by ingestion tools."""
        ...
```

#### 5. Prompt / Schema Registry

Structured prompt and schema management from the start.

```
prompts/
    system/
        router.txt
        qa.txt
        projections.txt
    schema/
        tables.sql            # DDL for reference
        descriptions.yaml     # human-readable table/column descriptions
    few_shot/
        qa_examples.yaml
```

The `descriptions.yaml` is critical — column names like `txn_amt` need descriptions such as "transaction amount in GBP, negative values are debits" for the LLM to generate correct SQL.

#### 6. Rust Tool Interface Contract

Rust tools communicate via JSON over stdin/stdout, starting as standalone CLI binaries.

```json
// Input (Python → Rust)
{
  "input_path": "/path/to/statement.csv",
  "bank_format": "monzo",
  "output_format": "json"
}

// Output (Rust → Python)
{
  "transactions": [...],
  "metadata": { "row_count": 142, "date_range": ["2026-01-01", "2026-01-31"] },
  "errors": []
}
```

Can later migrate to PyO3 if subprocess overhead becomes a concern — the JSON contract translates directly to PyO3 function signatures.

---

## Feature Roadmap (Incremental)

### Phase 1 — Foundation

**DuckDB schema + manual CSV loading**

- Design the core data model (transactions, categories, accounts).
- Load a few months of exported bank statements manually.
- Validate the schema works for the queries that matter.

**Design considerations:**

- Tables should be append-friendly — bank transactions are naturally immutable events.
- Think about categorisation early: transactions need categories for meaningful analysis.
- Build idempotent ingestion from the start to handle deduplication when multiple data sources overlap.

### Phase 2 — MVP: LLM Q&A

**LangGraph agent with a single tool: read-only SQL query against DuckDB.**

- Terminal-based interface.
- User asks natural language questions, agent generates SQL, executes, returns results with commentary.
- Router structure in place (even though it trivially routes to Q&A).
- Agent interaction logging to DuckDB for debugging and prompt improvement.

**LLM considerations:**

- Smaller local models (7–13B) can struggle with complex SQL. Consider starting with a cloud API during development, or use a larger local model (70B+ quantised) if hardware permits.
- Invest in the prompt layer: schema descriptions and few-shot examples matter more than model size.
- Validate generated SQL before execution — both for correctness and to prevent destructive operations.

### Phase 3 — File-Based Ingestion

**Automated parsing of bank statement CSVs/PDFs.**

- First Rust tool candidate: bank statement parser.
- Registered as a LangGraph tool the agent can invoke.
- Handles format detection and normalisation into the core schema.

### Phase 4 — Transaction Categorisation

**Rules-based categorisation, then LLM-assisted.**

- Start with deterministic rules (regex on merchant names, etc.).
- Layer in LLM-suggested categories for uncategorised transactions.
- Good opportunity to learn human-in-the-loop patterns in agentic systems.

### Phase 5 — Financial Projections

**Multi-step agent workflows for forward-looking analysis.**

- Gather historical data, apply assumptions, generate projections.
- Dedicated projections sub-graph in LangGraph.
- Rust-based financial calculation tools for deterministic computation.
- This is where LangGraph's graph-based orchestration shines.

### Phase 6 — Bank API Ingestion

**Live payment data via Open Banking / aggregator APIs.**

- Push this furthest down the roadmap — requires OAuth flows, token management, and ongoing API maintenance.
- File-based ingestion provides 90% of the value with 10% of the effort.

---

## Day One Checklist

Before writing the first sub-graph, have these in place:

| Component                                     | Purpose                                                | Complexity   |
| --------------------------------------------- | ------------------------------------------------------ | ------------ |
| `FinanceDB` class                             | DuckDB access layer with read/write separation         | Small        |
| `AgentState` schema                           | Shared typed state for LangGraph                       | Tiny         |
| Router graph structure                        | Top-level graph that delegates to sub-graphs           | Small        |
| Tool definitions separate from agent logic    | Independently testable tools                           | Pattern only |
| `prompts/` directory with schema descriptions | LLM context management                                 | Small        |
| Agent interaction logging table in DuckDB     | Debug and improvement over time                        | Tiny         |
| First-run setup module                        | DB creation, config prompts, Ollama connectivity check | Small        |
| Migration runner                              | Numbered SQL migrations with version tracking          | Small        |
| `config.yaml` loader                          | Configurable Ollama endpoint and model                 | Tiny         |
| Bootstrap script (`start.bat` / `start.sh`)   | Single-action launch for non-technical users           | Small        |

---

## What Not to Over-Engineer

- **No plugin system** — a simple Python package with sub-graph modules is enough for a single-developer project.
- **No LLM provider abstraction** — using Ollama; switching models is a `config.yaml` change, not an architecture change.
- **No configuration framework** — a simple `config.yaml` with a loader function is sufficient. No need for a library.
- **No compiled binary** — a bootstrap script with uv is enough. Only consider PyInstaller if the script approach proves insufficient.

---

## Adding New Capabilities (Repeatable Motion)

Once the foundation is in place, adding a new capability always follows the same pattern:

1. Write a tool (standalone, testable).
2. Write a sub-graph (LangGraph graph with its own prompt and logic).
3. Register it with the router.
4. Add a prompt to the prompts directory.

No existing code needs to change.

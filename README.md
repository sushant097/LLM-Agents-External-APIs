# 🤖 LLM Agents with External APIs & RAG

A modular **Agentic AI framework** that connects Large Language Models (LLMs) to **real-world tools and APIs** — from web search and Gmail to Google Sheets and RAG-based document memory.
It demonstrates how AI agents can *perceive*, *plan*, and *act* autonomously across multiple external systems using both **stdio** and **SSE** transports.

---

## 🚀 Overview

This project builds a complete **multi-tool LLM agent** capable of:

* Accessing **external APIs** (web, Gmail, Sheets, etc.)
* Performing **retrieval-augmented generation (RAG)** over local documents
* Parsing and understanding **webpages and PDFs**
* Running tool calls through the **Model Context Protocol (MCP)**
* Using **FAISS**-based long-term memory for contextual recall

Each agent follows a cognitive loop:

> **Perceive → Plan → Act → Remember**

This loop allows it to understand user intent, decide which tools to invoke, execute them safely, and learn from the results — similar to how autonomous AI systems operate.

---

## 🧩 Core Architecture

```
LLM (Gemini / Ollama)
      │
  ┌──────────────┐
  │  Agent Loop  │  ← Decision + Planning
  └──────────────┘
      │
  ┌──────────────┐
  │ MCP Transport│  ← stdio / SSE
  └──────────────┘
      │
  ┌──────────────┐
  │  MCP Servers │
  ├──────────────┤
  │  Web Search  │ 🌐
  │  Document RAG│ 📄
  │  Gmail       │ 📧
  │  Sheets/Drive│ 📊
  └──────────────┘
```

```
[ Telegram ]──►(Gateway)──►[ Agent Service ]
                                │
                                │ plan/decide
                                ▼
                    ┌───────────────────────────┐
                    │       Tools Layer          │
                    │                           │
   stdio MCP        │   [RAG Server]            │  SSE MCP (HTTP)
   (local)          │   - ingest/parse          │  [G Suite Server]
  ┌─────────┐       │   - semantic chunk + FAISS│  - create_sheet
  │ WebFetch│──────►│   - retrieve/query        │  - append_rows
  │ (search/│       │                           │  - send_email
  │ fetch)  │       └───────────────────────────┘
  └─────────┘                 ▲             ▲
                              │ memory      │ streams
                              └─────────────┘
```

---

## 🔧 Features

✅ **Tool-based reasoning** — Agents autonomously choose tools based on summarized descriptions.
✅ **RAG Memory System** — Uses FAISS + semantic chunking for fast document retrieval.
✅ **Stdio & SSE support** — Enables both local (stdio) and remote (HTTP + Server-Sent Events) tool execution.
✅ **Webpage & PDF extraction** — Powered by MarkItDown, Trafilatura, and PyMuPDF4LLM.
✅ **Google API integration** — Read/write from Sheets, send Gmail messages, manage Drive files.
✅ **Extensible design** — Easily add new tools or services as independent MCP servers.
✅ **Privacy-focused** — All processing can run locally with your own LLM endpoints.

---

## 🏗️ Tech Stack

| Component            | Technology                                      |
| -------------------- | ----------------------------------------------- |
| **LLM Backend**      | Gemini 2.0 / Ollama                             |
| **Framework**        | FastAPI, Python                                 |
| **Retrieval Engine** | FAISS, LlamaIndex                               |
| **Parsing**          | Trafilatura, MarkItDown, PyMuPDF4LLM            |
| **Communication**    | Model Context Protocol (stdio + SSE)            |
| **Vector Store**     | FAISS (incremental updates)                     |
| **Google APIs**      | Gmail, Sheets, Drive (OAuth2 / Service Account) |

---

## 🧠 Agent Flow

1. **Perception:** Understands user query and extracts intent.
2. **Planning:** Decides which external tool to use.
3. **Action:** Executes tool via MCP transport (stdio/SSE).
4. **Memory:** Stores outputs for contextual recall.

---

## ⚙️ Project Structure

*will change later*

```
LLM-Agents-External-APIs/
├── agent.py                # Main entrypoint (agent loop)
├── core/                   # Core logic (loop, context, strategy, etc.)
├── modules/                # LLM perception, decision, action, memory
├── config/                 # Model & agent profiles
├── mcp_server_1.py         # Example stdio server (math, utils)
├── mcp_server_2.py         # Document RAG server (FAISS + chunking)
├── mcp_server_3.py         # Web search / HTML extraction server
├── sse_server_gsuite.py    # SSE server for Gmail + Sheets (HTTP)
└── pyproject.toml          # Dependencies and project metadata
...
```

---

## 🧰 Getting Started

### 1️⃣ Setup Environment

```bash
git clone https://github.com/sushant097/LLM-Agents-External-APIs.git
cd LLM-Agents-External-APIs
uv venv && source .venv/bin/activate
uv pip install -e .
```

### 2️⃣ Configure Keys

Create a `.env` file:

```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_service_account.json
```

### 3️⃣ Start MCP Servers

```bash
# Local RAG server
python mcp_server_2.py
# Web search server
python mcp_server_3.py
# SSE Gmail/Sheets server
python sse_server_gsuite.py
```

### 4️⃣ Run the Agent

```bash
python agent.py
```

Then enter any query — the agent will autonomously decide which tool to use.

---

## 🧾 Example Use Cases

* 📄 “Summarize my recent research PDFs and email me the summary.”
* 📊 “Fetch the latest F1 standings and update a Google Sheet.”
* 🌐 “Search web pages about AI trends and build a mini RAG index.”
* 📧 “Send a Gmail reminder if a document hasn’t been updated in 7 days.”

---

## 🧩 Extending

Add new tools easily:

* Create a new `mcp_server_x.py`
* Define tool schema using Pydantic models
* Register it in the config and summary logic
* Run via stdio or SSE transport

---

## 🔒 Privacy & Local Mode

All components can run locally:

* Local FAISS database
* Ollama-based LLMs
* No data sent externally unless APIs are explicitly configured

---
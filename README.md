🚩 Problem Statement

Modern DevOps and SRE teams deal with overwhelming operational workloads: incident triage, GitHub issue scanning, log summarization, diagnostics, and long-running checks.
These tasks interrupt focused engineering work, require constant monitoring, and often span many steps where context is lost.

This leads to:

Slow incident resolution

Burnout from repetitive manual work

Fragmented tooling

No persistent record of decisions

Inefficient use of engineer time

Ops workflows require reasoning + tool usage + context + multi-step operations, which is why traditional automation falls short.

🤖 Why Agents?

Agents bring abilities that map perfectly onto real-world DevOps workflows:

✔ Maintain state

Multiple operations span minutes to hours — agents retain and recall context.

✔ Use tools autonomously

DevOps relies on GitHub APIs, shell commands, monitoring systems, and analytics tools.

✔ Run sequential & parallel tasks

Incident investigation may require ordered steps, but GitHub scanning can run in parallel.

✔ Handle long-running tasks

Diagnostics often take time — agents with pause/resume/cancel + persisted state are ideal.

✔ Provide observability

Prometheus metrics + logging + evaluation make behavior transparent and debuggable.

This is exactly why agents are the right solution for real-world enterprise Ops.

🧠 What I Created — Enterprise Ops Agent

A complete production-style AI Ops Agent System, built using ADK concepts:

🏗 Multi-Agent Architecture

Coordinator Agent — central router

Sequential Worker Agents — ordered reasoning

Parallel Worker Agents — concurrent tasks

🛠 Tools

GitHub Issue Search Tool (OpenAPI-based)

Command Execution Tool

Custom Incident Summary Tool

🧳 Persistent Memory

SQLite-backed session memory stores:

Request history

Tool results

Long-running operation metadata

🕒 Long-Running Ops Manager (MCP-style)

Supports:

Start

Pause

Resume

Cancel

Progress tracking

State persistence across restarts

📊 Observability

Prometheus /metrics endpoint exposes counters:

Requests processed

Worker task count

Operation state transitions

🧪 Evaluation

Pytest suite

Manual CLI evaluation

Metrics validation

🚀 Deployment

Fully deployable via:

GitHub Codespaces (devcontainer)

Python runtime

Containerization-ready

🎥 Demo Overview
▶️ Running the main agent
python main.py


This starts:

Flask API (health + metrics)

Demo agent sequence

Coordinator + workers

State persistence

▶️ Long-running ops
python -m agents.long_running_manager
m> start 8
m> pause <id>
m> resume <id>
m> list

▶️ Observability

Visit:

/metrics  


to see live Prometheus counters.

▶️ Memory

session_store.sqlite3 keeps all history.

🔨 The Build

Technologies used:

Python

Multi-agent design

Google ADK-inspired patterns

SQLite session memory

Prometheus client

Flask API

GitHub OpenAPI tool

Pytest evaluation suite

Long-running operation workflow

GitHub Codespaces Devcontainer

# 🚀 **Enterprise Ops Agent**
### **Autonomous Multi-Agent System for Incident & DevOps Automation**  
_Built for Google AI Agents Intensive Capstone_

---

## 🟥 **Problem Statement**
Modern DevOps and SRE teams face overwhelming operational workloads such as:

- Incident triage  
- Log and CPU diagnostics  
- GitHub issue scanning  
- Long-running backend checks  
- Manual summarization tasks  

These tasks interrupt engineering focus, lack automated context, and waste valuable time.

This results in:

- Slow incident resolution  
- Repetitive, manual tasks  
- Fragmented tooling  
- Lost historical context  
- High operational overhead  

Ops workflows require **reasoning + context + tool usage + long-running operations**, making them ideal for AI agents.

---

## 🧠 **Why Agents?**
Agents are a perfect match for DevOps automation because they:

### ✔ Maintain Context  
They remember previous steps, results, and state across long workflows.

### ✔ Use Tools Autonomously  
Agents can call GitHub APIs, execute commands, retrieve logs, and more.

### ✔ Support Sequential & Parallel Execution  
Some workflows require ordered logic; others can run concurrently.

### ✔ Manage Long-Running Operations  
Real diagnostics can take minutes or hours — agents handle pause/resume/cancel.

### ✔ Provide Observability  
Prometheus metrics, logs, and evaluation make behavior transparent.

---

## 🏗 **What I Created — Enterprise Ops Agent**
A complete, production-style AI system with:

### **🔹 1. Multi-Agent Architecture**
- **Coordinator Agent**  
- **Sequential Worker Agents**  
- **Parallel Worker Agents**

### **🔹 2. Tools**
- GitHub Issue Search Tool  
- Command Execution Tool  
- Custom Incident Summary Tool  

### **🔹 3. Persistent Memory**
SQLite-backed session memory storing:
- Request history  
- Tool outputs  
- Long-running operation metadata  

### **🔹 4. Long-Running Operation Manager (MCP-style)**
Supports:
- Start  
- Pause  
- Resume  
- Cancel  
- Progress tracking  
- Persistent state across runs  

### **🔹 5. Observability**
Prometheus `/metrics` endpoint exposing:
- Requests processed  
- Worker tasks  
- Operation lifecycle counters  

### **🔹 6. Evaluation**
- Pytest suite  
- Manual CLI verification  
- Metrics-based evaluation  

### **🔹 7. Deployment**
- Works directly in GitHub Codespaces  
- Devcontainer included  
- Flask API for health + metrics  

---

## 🎬 **Demo**

This section demonstrates how the Enterprise Ops Agent runs inside GitHub Codespaces, how it processes tasks, handles long-running operations, and exposes observability metrics.

---

### ▶️ **1. Run the Main Agent System**

Start the coordinator, workers, Flask API, and demo workflow:

```bash
python main.py


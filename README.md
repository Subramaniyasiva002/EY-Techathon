# 🔧 AutoHub — AI-Powered Predictive Vehicle Maintenance Platform

> **EY Techathon Submission** | An end-to-end multi-agent AI system for predictive vehicle diagnostics, automated service booking, and intelligent maintenance orchestration.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the System (6 Commands)](#running-the-system-6-commands)
- [Agent Roles](#-agent-roles)
- [Security — UEBA](#-security--ueba-user-and-entity-behavior-analytics)
- [Agent Failover System](#-intelligent-agent-failover-system)
- [Dataset](#-dataset)

---

## 🧠 Overview

**AutoHub** is a production-grade, multi-agent AI platform that predicts vehicle failures before they happen, automatically schedules maintenance, notifies customers, and continuously learns from real-world outcomes.

Built on top of **LangGraph** for agent orchestration and **LightGBM** for predictive ML, the system simulates an autonomous service centre — from telematics ingestion all the way to post-service RCA (Root Cause Analysis) and model refinement.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    TELEMATICS API  (FastAPI)                      │
│              Simulates real-time vehicle sensor data              │
└────────────────────────────┬─────────────────────────────────────┘
                             │ /telematics/{vehicle_id}
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│               DIAGNOSIS AGENT  (LightGBM + AI4I Model)           │
│     Classifies: No Failure / Heat / Power / Tool Wear / Strain   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ LangGraph StateGraph
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       MASTER AGENT  (LangGraph)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  ┌─────────┐  │
│  │  Scheduling │→ │   Customer   │→ │  Booking  │→ │Feedback │  │
│  │    Agent    │  │    Agent     │  │   Agent   │  │  Agent  │  │
│  └─────────────┘  └──────────────┘  └───────────┘  └────┬────┘  │
│                                                          │        │
│                                                    ┌─────▼─────┐ │
│                                                    │ RCA/CAPA  │ │
│                                                    │   Agent   │ │
│                                                    └───────────┘ │
└──────────────────────────────────────────────────────────────────┘
                             │
           ┌─────────────────┴──────────────────┐
           ▼                                    ▼
┌──────────────────┐                ┌───────────────────┐
│  Tech Dashboard  │                │ Customer Dashboard │
│  (Streamlit)     │                │  (Streamlit)       │
└──────────────────┘                └───────────────────┘
           │
    ┌──────▼──────┐       ┌─────────────────────┐
    │  UEBA Agent │       │  Agent Supervisor    │
    │ (Security)  │       │  (Failover + Backup) │
    └─────────────┘       └─────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent Orchestration** | LangGraph-powered pipeline with conditional routing |
| 🔬 **Predictive Diagnostics** | LightGBM model trained on AI4I 2020 dataset — 5-class failure classification |
| 📅 **Smart Scheduling** | RL Q-table + demand-aware heuristics for slot recommendation |
| 🔔 **Async Notifications** | Decoupled customer alert system with SQLite-backed booking queue |
| 🛡️ **UEBA Security** | Whitelist-based behavior analytics — blocks unauthorized agent actions |
| ♻️ **Agent Failover** | Auto-restart, backup agents, and quarantine for suspicious failures |
| 📊 **Dual Dashboards** | Technician command centre + customer self-service portal |
| 🔄 **Continuous Learning** | Outer loop triggers model refinement from real feedback data |
| 🏭 **RCA / CAPA** | Automated Root Cause Analysis and Corrective Action generation |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **ML Model** | LightGBM, Scikit-learn, TensorFlow |
| **Agent Orchestration** | LangGraph, LangChain Core |
| **Backend APIs** | FastAPI, Uvicorn |
| **Frontend Dashboards** | Streamlit |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Matplotlib, Seaborn |
| **Queue / Storage** | SQLite (booking_queue.db), JSON flat-files |
| **Security** | UEBA (custom whitelist + anomaly detection) |

---

## 📁 Project Structure

```
AutoHub/
├── 📊 Dashboards
│   ├── dashboard.py              # Technician / Admin dashboard (Streamlit)
│   └── customer_dashboard.py     # Customer self-service portal (Streamlit)
│
├── 🤖 Agents
│   ├── master_agent.py           # LangGraph pipeline steps (orchestrator)
│   ├── orchestration_graph.py    # StateGraph definition & conditional edges
│   ├── diagnosis_agent.py        # LightGBM failure prediction agent
│   ├── scheduling_agent.py       # Slot recommendation (RL + heuristic)
│   ├── customer_agent.py         # Customer message generation
│   ├── booking_agent.py          # Booking logic (via API)
│   ├── feedback_agent.py         # Post-service feedback & RL data collector
│   ├── rca_capa_agent.py         # Root Cause Analysis & CAPA generation
│   ├── data_analysis_agent.py    # Dataset insights agent
│   └── ueba_agent.py             # Security & behavior monitoring
│
├── 🛡️ Supervisor & Failover
│   ├── agent_supervisor.py       # Monitors agents, triggers failover
│   ├── supervisor_daemon.py      # Runs supervisor as a background service
│   └── backup_agents/            # Backup versions of all critical agents
│
├── 🔌 APIs & Services
│   ├── telematics_api.py         # Simulated vehicle sensor data (FastAPI)
│   ├── booking_api.py            # Booking REST API with async queue (FastAPI)
│   ├── booking_worker.py         # Queue consumer / booking processor
│   ├── booking_queue.py          # SQLite-backed message queue
│   └── slots_manager.py          # Slot availability & booking state manager
│
├── 🧪 Training & Data
│   ├── preprocess.py             # Data cleaning & feature engineering
│   ├── refinement_train_new_model.py  # Outer loop model retraining
│   ├── rl_train.py               # Reinforcement learning (Q-table training)
│   ├── real_time.py              # Real-time simulation runner
│   ├── ai4i2020.csv              # Raw AI4I 2020 dataset
│   └── ai4i_processed.csv        # Preprocessed dataset
│
├── 💾 Models
│   ├── models/ai4i_lgbm_refined.joblib   # Active production model
│   ├── models/ai4i_lgbm_model.joblib     # Base trained model
│   └── models/q_table.npy                # RL Q-table for scheduling
│
├── 📦 Utilities
│   ├── notifications_manager.py  # Async notification system
│   ├── state_model.py            # LangGraph state schema (TypedDict)
│   └── sample_store.py           # Sample vehicle data store
│
├── assets/                       # CSS and UI assets
├── requirements.txt              # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.9+**
- pip package manager
- (Recommended) A virtual environment

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/EY-Techathon.git
cd EY-Techathon

# 2. Create and activate a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

---

## ▶️ Running the System (6 Commands)

Each service runs in a **separate terminal**. Open 6 terminals and run one command per terminal in the order shown below.

---

### Terminal 1 — 🛰️ Telematics API
> Starts the simulated vehicle sensor data server. All other services depend on this.

```bash
python -m uvicorn telematics_api:app --host 0.0.0.0 --port 8000 --reload
```
📍 Accessible at: `http://localhost:8000/telematics/VH001`

---

### Terminal 2 — 📦 Booking API
> Starts the async booking REST API backed by the SQLite queue.

```bash
python -m uvicorn booking_api:app --host 0.0.0.0 --port 9000 --reload
```
📍 Accessible at: `http://localhost:9000/slots`

---

### Terminal 3 — 👷 Booking Worker
> Starts the background consumer that processes queued bookings from the message queue.

```bash
python booking_worker.py
```

---

### Terminal 4 — 🛡️ Agent Supervisor
> Launches all AI agents under supervision — monitors health, auto-restarts on failure, and quarantines on security violations.

```bash
python supervisor_daemon.py
```

---

### Terminal 5 — 📊 Technician Dashboard
> Launches the main Streamlit dashboard for technicians and admins (diagnostics, scheduling, UEBA logs, security).

```bash
streamlit run dashboard.py
```
📍 Accessible at: `http://localhost:8501`

---

### Terminal 6 — 🚗 Customer Dashboard
> Launches the customer-facing portal to view service notifications, approve bookings, and provide feedback.

```bash
streamlit run customer_dashboard.py
```
📍 Accessible at: `http://localhost:8502`

---

### ✅ Quick Reference — All 6 Commands

```bash
# Terminal 1
python -m uvicorn telematics_api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
python -m uvicorn booking_api:app --host 0.0.0.0 --port 9000 --reload

# Terminal 3
python booking_worker.py

# Terminal 4
python supervisor_daemon.py

# Terminal 5
streamlit run dashboard.py

# Terminal 6
streamlit run customer_dashboard.py
```

---

## 🤖 Agent Roles

| Agent | Role |
|---|---|
| **DiagnosisAgent** | Loads LightGBM model, predicts failure class & risk score from sensor features |
| **SchedulingAgent** | Recommends maintenance slots using RL Q-table and heuristic demand logic |
| **CustomerInteractionAgent** | Generates personalised maintenance alerts and push notifications |
| **BookingAgent** | Posts booking requests to the Booking API (async queue) |
| **FeedbackAgent** | Records service outcomes, rejections, and customer feedback for RL training |
| **RCACAPAAgent** | Analyses failure patterns, generates Root Cause Analysis and corrective actions |
| **UEBAAgent** | Enforces action whitelists per agent, logs and alerts on anomalous behavior |
| **MasterAgent** | Coordinates the full LangGraph pipeline — conditionally routes state between agents |

---

## 🛡️ Security — UEBA (User and Entity Behavior Analytics)

Every agent action is validated against a **strict whitelist** before execution.

```
Agent performs action
        │
        ▼
UEBAAgent.log_event(agent, action)
        │
   ┌────┴────┐
   │Allowed? │
   └────┬────┘
   Yes  │  No
        │   └──► Action BLOCKED + Incident logged to ueba_log.json
        ▼
  Action proceeds
```

**Threat Levels:**
- 🟡 `WARNING` — Unusual frequency or timing anomaly detected
- 🔴 `BLOCKED` — Action not in whitelist → workflow halted immediately

All incidents are logged to `ueba_log.json` and surfaced in the **Admin & Security** tab of the Technician Dashboard.

---

## ♻️ Intelligent Agent Failover System

| Failure Type | Classification | Action |
|---|---|---|
| Crash / OOM / Network | `ACCIDENTAL` | Auto-restart (up to 3 attempts) |
| 3 failed restarts | `PERSISTENT` | Failover to backup agent |
| UEBA security violation | `SUSPICIOUS` | Quarantine + start backup in **SAFE MODE** (read-only) |
| User shutdown | `MANUAL` | No action |

Security incidents are logged to `security_incidents.json` and monitored in real-time by the `AgentSupervisor`.

---

## 📂 Dataset

**AI4I 2020 Predictive Maintenance Dataset**
- **Source:** UCI Machine Learning Repository
- **Records:** 10,000 machine readings
- **Features:** Air temperature, Process temperature, Rotational speed, Torque, Tool wear + engineered features (Power_W, Strain_Index, Temp_Diff)
- **Target Classes:**
  - `0` — No Failure
  - `1` — Heat Dissipation Failure
  - `2` — Power / Battery Failure
  - `3` — Tool Wear / Vibration Failure
  - `4` — Overstrain Failure

The model continuously improves via an **outer feedback loop** — real service outcomes are fed back to retrain the LightGBM model via `refinement_train_new_model.py`.

---

## 📄 License

This project was built for the **EY Techathon** competition. All rights reserved.

---

<div align="center">
  <b>Built with ❤️ for EY Techathon</b><br/>
  <i>Predictive Intelligence · Autonomous Agents · Secure by Design</i>
</div>

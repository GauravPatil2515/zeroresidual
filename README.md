# 🏛️ ZeroResidual: The Open-Source UPI Settlement & Discrepancy Engine

> **Curated for Hacktoberfest Hack Day Mumbai 2026 @ Paytm Office · Hackerspace Mumbai**  
> *Best Use of Google Gemma (2B) · Financial Infrastructure · Air-Gapped Precision*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Google Gemma](https://img.shields.io/badge/Powered_by-Google_Gemma_2_(2B)-4285F4.svg)](https://ai.google.dev/gemma)
[![Precision](https://img.shields.io/badge/Precision-0.01_Paisa_Strict-success.svg)](#)
[![Air Gapped](https://img.shields.io/badge/Privacy-100%25_Offline-green.svg)](#)
[![Tests](https://img.shields.io/badge/Tests-9_Passing-brightgreen.svg)](#)

---

## ⚡ Overview

ZeroResidual is an open-source, air-gapped reconciliation engine for Indian merchant settlements. It reconciles **Merchant POS orders**, **Payment Gateway S2S Webhooks**, and **Bank Settlement UTR reports** down to the exact paisa:

* 🎯 **Strict Decimal Precision:** Zero float arithmetic. Every balance, fee, refund, and GST split is tracked down to 0.01 INR using Python `Decimal`.
* ⚡ **Dual-Mode Engine:** Runs deterministically via regex rules and pluggable bank adapters in `< 5ms` with `--no-llm`, or unlocks local **Google Gemma 2 2B** for fuzzy narration classification.
* 🛡️ **The Honest Residual:** Refuses to guess or hallucinate explanations when an unexplained shortfall exists. Halts with **exit code 1** for CI pipelines and flags the exact difference for escalation.
* 🔒 **Anti-Hallucination Number Guard:** Every monetary value emitted by the local LLM is intercepted and validated against an immutable arithmetic fact sheet.
* 🏦 **Pluggable Bank Adapters:** Out-of-the-box support for HDFC, State Bank of India (SBI), and Paytm Payments Bank statements.

---

## 📊 Live Demonstration Scenarios

| Scenario | Gross POS | Expected Net | Bank Credit | Residual | Status | Exit Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario 1 (Tie-Out)** | ₹50,000.00 | ₹43,000.00 | ₹43,000.00 | **₹0.00** | `RECONCILED` | `0` |
| **Scenario 2 (Residual)** | ₹50,000.00 | ₹43,000.00 | ₹42,788.00 | **₹212.00** | `UNEXPLAINED_DISCREPANCY` | `1` |

### Scenario 1 Waterfall Breakdown
* **Gross POS Sales:** ₹50,000.00 (50 transactions)
* **Customer Refunds:** - ₹2,400.00 (2 refunds)
* **Dispute / Escrow Hold:** - ₹3,100.00 (Order #ORD-8812)
* **T+1 Cutoff Delayed:** - ₹1,000.00 (3 orders after 23:00 IST)
* **Soundbox 4G IoT Rental:** - ₹423.73
* **Statutory GST (18%):** - ₹76.27
* **Bank Received Payout:** ₹43,000.00 (UTR: PAYTM88912001928)
* **Residual:** **₹0.00** *(Clean Tie-Out)*

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/GauravPatil2515/zeroresidual.git
cd zeroresidual

# Install in editable mode
pip install -e .
```

### 2. Run Automated Tests
```bash
pytest tests/ -v
```

### 3. Run Live CLI Demos
```bash
# Scenario 1 (Tie-Out): Returns exit code 0
zeroresidual demo-tieout --no-llm

# Scenario 2 (The Honest Residual): Returns exit code 1
zeroresidual demo-unexplained --no-llm

# Machine-readable JSON output for automated CI pipelines
zeroresidual demo-tieout --no-llm --json
```

---

## 🖥️ Web Dashboard & Interactive Studio

ZeroResidual includes a Poster Doctrine editorial dashboard built with React, Vite, and Tailwind CSS.

### Starting the Servers
```bash
# Start FastAPI backend (port 8000)
python3 -m uvicorn zeroresidual.server.app:app --host 0.0.0.0 --port 8000

# Start Vite frontend (port 5173)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to explore:
* **Interactive Settlement Waterfall:** Real-time visual accounting ledger.
* **Dispute Defense Workbench:** One-click evidence submission and escrow claim defense.
* **Gemma 2 Narration Tester:** Test arbitrary bank strings against local Google Gemma 2 (2B).

---

## 🏛️ System Architecture & Invariants

```
Merchant POS Orders (CSV) ──┐
Payment Gateway Webhooks  ──┼──> Pluggable Bank Adapters ──> Decimal Recon Engine ──> Number Guard ──> Exit 0 (Tie-Out) / Exit 1 (Residual)
Bank UTR Statements (CSV) ──┘
```

For in-depth mathematical guarantees and security controls, see:
* [Architecture & Math Proof](docs/ARCHITECTURE.md)
* [Hacktoberfest Presentation Script](docs/HACKATHON_DEMO.md)
* [Bank Adapters Guide](docs/BANK_ADAPTERS.md)
* [Agent Memory & System Instructions](AGENTS.md)

---

## 📜 License & Compliance

Distributed under the **Apache-2.0 License**.  
Compliant with Reserve Bank of India (RBI) Data Localization directives (100% offline, air-gapped processing with zero external telemetry).

# 🏛️ ZeroResidual: The Open-Source UPI Settlement & Discrepancy Engine
> **Curated for Hacktoberfest Hack Day Mumbai 2026 @ Paytm Office · Hackerspace Mumbai**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Google Gemma](https://img.shields.io/badge/Powered_by-Google_Gemma_2_(2B)-4285F4.svg)](https://ai.google.dev/gemma)
[![Precision](https://img.shields.io/badge/Precision-0.01_Paisa_Strict-success.svg)](#)
[![Air Gapped](https://img.shields.io/badge/Privacy-100%25_Offline-green.svg)](#)

---

## ⚡ Overview

ZeroResidual is an open-source, air-gapped reconciliation engine for Indian merchant settlements. It reconciles Merchant POS orders, Payment Gateway S2S Webhooks, and Bank Settlement UTR reports down to the exact paisa:

- **Strict Decimal Precision:** Zero float arithmetic. Every balance and fee is tracked down to 0.01 INR.
- **Dual-Mode Engine:** Runs deterministically via regex rules and pluggable bank adapters in `< 5ms` with `--no-llm`, or unlocks local **Google Gemma 2 2B** for fuzzy narration classification.
- **The Honest Residual:** Refuses to guess or hallucinate explanations when an unexplained difference exists (exits with code 1).
- **Anti-Hallucination Number Guard:** Every number emitted in explanations is strictly verified against an immutable fact sheet.
- **Pluggable Bank Adapters:** Add support for any Indian bank in 20 lines of code.

---

## 🛠️ Project Structure

```
zeroresidual/
├── pyproject.toml
├── LICENSE
├── README.md
├── src/
│   └── zeroresidual/
│       ├── __init__.py
│       ├── cli.py
│       ├── engine/
│       │   ├── types.py
│       │   ├── recon.py
│       │   └── number_guard.py
│       ├── adapters/
│       │   ├── base.py
│       │   ├── hdfc.py
│       │   ├── sbi.py
│       │   └── paytm.py
│       ├── llm/
│       │   └── gemma.py
│       └── server/
│           └── app.py
├── data/
└── tests/
```

---

## 🚀 Quickstart

```bash
# Clone and install in editable mode
git clone https://github.com/GauravPatil2515/zeroresidual.git
cd zeroresidual
pip install -e .

# Run automated tests
pytest tests/ -v
```

Licensed under **Apache-2.0**.

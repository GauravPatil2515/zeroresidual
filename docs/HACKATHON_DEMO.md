# 🎪 Hacktoberfest Hack Day Mumbai 2026 — Live Demo Playbook

> **Event:** Hacktoberfest Hack Day Mumbai 2026  
> **Host Venue:** Paytm Office · Hackerspace Mumbai  
> **Target Tracks:** Best Use of Google Gemma (2B) · Financial Infrastructure · Air-Gapped Precision  
> **Presenters:** Gaurav Patil (@GauravPati69760)

---

## ⏱️ 3-Minute Judge Presentation Pitch

### 1. The Hook (0:00 - 0:45)
> "Good afternoon! If you run a high-volume merchant store in India processing ₹1,00,000 every day across UPI QR codes and POS machines, let me ask you: **How do you verify your morning bank settlement credit down to the exact paisa?**
>
> In reality, you see ₹50,000 on your POS, but only ₹43,000 lands in your bank account. Where did the missing ₹7,000 go? Was it customer refunds? Was it a chargeback dispute? Was it late night cutoff? Or did the gateway deduct a device fee?
>
> Today, merchants either guess or manually reconcile messy Excel files with broken float math.
>
> Introducing **ZeroResidual** — the open-source, air-gapped UPI settlement and discrepancy reconciliation engine with embedded local Google Gemma 2."

---

### 2. Live Demo Part 1: Scenario 1 Tie-Out (0:45 - 1:30)
Run in terminal:
```bash
python3 -m zeroresidual.cli demo-tieout --no-llm
```
* **Judge Attention:** Point to the Rich waterfall breakdown table.
* **Explanation:**
  - Gross POS Sales: ₹50,000.00
  - Customer Refunds: - ₹2,400.00
  - Dispute / Chargeback Hold: - ₹3,100.00 (Order #ORD-8812)
  - T+1 Cutoff Delayed: - ₹1,000.00 (3 transactions after 23:00 IST)
  - Soundbox Rental Fee: - ₹423.73
  - GST on Soundbox (18%): - ₹76.27
  - Expected Net Payout: ₹43,000.00
  - Actual Bank UTR: ₹43,000.00
  - **Residual: ₹0.00 (Exact Tie-Out, Exit Code 0)**

---

### 3. Live Demo Part 2: Scenario 2 "The Honest Residual" (1:30 - 2:15)
Run in terminal:
```bash
python3 -m zeroresidual.cli demo-unexplained --no-llm
```
* **Judge Attention:** Notice the red audit failure alert and terminal exit code 1.
* **Key Innovation:**
  - "The bank only credited ₹42,788.00 instead of ₹43,000.00. That leaves an unexplained shortfall of **₹212.00**."
  - "Most AI tools hallucinate a reason: 'Oh, it might be an extra fee.'
  - **ZeroResidual refuses to hallucinate.** Our Anti-Hallucination Number Guard verifies all numbers against an immutable fact sheet. It halts, exits with code 1, and generates an automated bank dispute letter with the exact UTR."

---

### 4. Live Demo Part 3: Web Dashboard & Local Google Gemma (2:15 - 3:00)
* Open the Poster Doctrine dashboard at `http://localhost:5173`.
* Toggle between Scenario 1 and Scenario 2.
* Show the interactive dispute defense form where the merchant can click "Defend Dispute" with evidence notes.
* Highlight that Google Gemma 2 (2B) runs **100% locally and offline** via Ollama/Llama.cpp, ensuring full RBI data privacy compliance with zero external API calls.

---

## 🏆 Key Differentiators to Emphasize to Judges

| Feature | Typical Hackathon Project | ZeroResidual |
| :--- | :--- | :--- |
| **Monetary Math** | Float (`0.1 + 0.2 = 0.30000000000000004`) | **Strict Decimal (Paise)** |
| **Missing Money** | Hallucinates an explanation | **The Honest Residual (Exit Code 1)** |
| **LLM Output** | Unverified text | **Anti-Hallucination Number Guard** |
| **Data Privacy** | Cloud API (sends bank data to OpenAI) | **100% Air-Gapped Local Google Gemma 2** |
| **Bank Statements** | Hardcoded format | **Pluggable Adapters (HDFC, SBI, Paytm)** |
| **CI/CD Ready** | Interactive only | **Clean JSON stdout + Exit Codes 0/1** |

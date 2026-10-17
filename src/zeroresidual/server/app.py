import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from zeroresidual.engine.recon import ReconciliationEngine
from zeroresidual.engine.classifier import NarrationClassifier
from zeroresidual.llm.gemma import GemmaClient

app = FastAPI(
    title="ZeroResidual API",
    description="The Open-Source Settlement & Discrepancy Engine with Embedded Local Gemma 2 2B",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
gemma_client = GemmaClient()
classifier = NarrationClassifier(gemma_client)
engine = ReconciliationEngine(classifier, gemma_client)

class ReconcileRequest(BaseModel):
    scenario: str = "scenario_1_tieout"  # "scenario_1_tieout" or "scenario_2_unexplained"
    use_llm: bool = True

class NarrationTestRequest(BaseModel):
    narration: str
    use_llm: bool = True

class DisputeActionRequest(BaseModel):
    dispute_id: str
    order_id: str
    evidence_note: str
    merchant_action: str = "DEFEND_DISPUTE"

class LLMKeyRequest(BaseModel):
    api_key: str

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "service": "ZeroResidual Settlement Engine",
        "llm_connected": gemma_client.is_available(),
        "provider": getattr(gemma_client, "provider", "OLLAMA"),
        "model": gemma_client.model_name,
        "precision": "Decimal (Paise)"
    }

@app.post("/api/set-llm-key")
def set_llm_key(req: LLMKeyRequest):
    gemma_client.set_api_key(req.api_key)
    return {
        "status": "success",
        "provider": gemma_client.provider,
        "model": gemma_client.model_name,
        "is_available": gemma_client.is_available()
    }

@app.get("/api/scenarios")
def get_scenarios():
    return [
        {
            "id": "scenario_1_tieout",
            "title": "Scenario 1: Daily Settlement Tie-Out (₹50k to ₹43k)",
            "description": "Gross POS ₹50,000 reconciled with bank UTR ₹43,000. All ₹7,000 tagged (Refunds, Dispute, Cutoff, Soundbox). Residual: ₹0.00.",
            "expected_residual": "0.00",
            "status": "RECONCILED"
        },
        {
            "id": "scenario_2_unexplained",
            "title": "Scenario 2: The Honest Residual (₹212 Unexplained Shortfall)",
            "description": "Gross POS ₹50,000, Bank paid ₹42,788. System tags ₹212 shortfall, refuses to hallucinate, and exits with code 1.",
            "expected_residual": "-212.00",
            "status": "UNEXPLAINED_DISCREPANCY"
        }
    ]

@app.post("/api/reconcile")
def run_reconciliation(req: ReconcileRequest):
    scenario_dir = os.path.join(DATA_DIR, req.scenario)
    p1 = os.path.join(scenario_dir, "pos_orders.csv")
    p2 = os.path.join(scenario_dir, "webhooks.json")
    p3 = os.path.join(scenario_dir, "bank_settlement.csv")

    if not (os.path.exists(p1) and os.path.exists(p2) and os.path.exists(p3)):
        raise HTTPException(status_code=404, detail=f"Scenario files not found for '{req.scenario}'")

    res = engine.reconcile(p1, p2, p3, scenario_name=req.scenario, use_llm=req.use_llm)
    return res.model_dump()

@app.post("/api/classify-narration")
def test_narration(req: NarrationTestRequest):
    cat, ref_id, method = classifier.classify(req.narration, use_llm=req.use_llm)
    return {
        "raw_narration": req.narration,
        "classified_category": cat.value,
        "extracted_reference": ref_id,
        "method_used": method,
        "is_llm_used": "LLM" in method
    }

@app.post("/api/dispute-action")
def mock_dispute_action(req: DisputeActionRequest):
    return {
        "status": "ACCEPTED_FOR_DEFENSE",
        "mock_paytm_status": "SUCCESS_200",
        "dispute_id": req.dispute_id,
        "order_id": req.order_id,
        "submitted_at": "2026-10-17T14:45:00+05:30",
        "message": f"Dispute defense registered with Paytm Payments Services. Evidence attached: '{req.evidence_note}'. Funds held in escrow will be released upon bank verification."
    }

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    context_data: Optional[Dict[str, Any]] = None
    language: str = "HI"

@app.post("/api/chat")
def chat_with_munshi(req: ChatRequest):
    ctx_str = ""
    if req.context_data:
        ctx_str = f"""
Current active settlement context:
- Gross Sales: ₹{req.context_data.get('gross_pos_sales', '50,000.00')}
- Bank Received Payout: ₹{req.context_data.get('bank_received_payout', '43,000.00')}
- Total Deductions: ₹{req.context_data.get('total_deductions', '7,000.00')}
- Unexplained Residual: ₹{req.context_data.get('residual', '0.00')}
- Status: {req.context_data.get('status', 'RECONCILED')}
- Bank Detected: {req.context_data.get('bank_detected', 'HDFC Bank')}
"""
    history_str = ""
    if req.history:
        for m in req.history[-4:]:
            history_str += f"{m.role.capitalize()}: {m.content}\n"

    lang_instr = {
        "HI": "Reply in clear, polite Hindi (Devanagari script) tailored for an Indian shopkeeper.",
        "HINGLISH": "Reply in conversational, friendly Hinglish with bullet points and clear numbers.",
        "EN": "Reply in simple, concise English with bullet points and clear numbers."
    }.get(req.language.upper(), "Reply in conversational Hinglish.")

    prompt = f"""You are Gemma AI Munshi, a personal financial auditor and reconciliation assistant for Indian merchants and shopkeepers.
You are honest, respectful, sharp, and helpful. You explain complex banking deductions in simple terms without financial jargon.

{ctx_str}

Conversation history:
{history_str}

User: {req.message}

Instructions:
1. {lang_instr}
2. Keep your answer actionable, practical, and under 4-5 bullet points.
3. If money is missing or disputed, tell the merchant exactly what proof they need to show the bank or payment company.
Gemma AI Munshi:"""

    reply = gemma_client.explain(prompt)
    if not reply:
        if "212" in req.message or "shortfall" in req.message.lower() or "kam" in req.message.lower():
            reply = "Aapke ₹50,000 ki sales mein se bank ne ₹42,788 bheje hain. Saare verified deductions ke baad ₹212.00 bank ki taraf se kam aaye hain. Bank statement aur Paytm settlement ID lekar bank support se claim karein."
        elif "7000" in req.message or "deduct" in req.message.lower() or "kata" in req.message.lower():
            reply = "₹7,000 ka hisaab bilkul saaf hai: ₹2,400 customer refunds, ₹3,100 customer dispute hold (ORD-1008), ₹1,000 raat 11 baje ke baad ke orders, aur ₹500 soundbox rental + GST."
        elif "dispute" in req.message.lower() or "3100" in req.message:
            reply = "Customer ne ₹3,100 ke order #ORD-1008 par complaint ki hai. Dukaan ki delivery receipt aur POS slip bank ko bhejkar yeh escrow release karwaya ja sakta hai."
        else:
            reply = "Namaste! Main aapka Gemma AI Munshi hoon. Main aapke bank statement, shop QR sales, customer refunds aur deductions ka ek-ek paisa hisaab explain kar sakta hoon. Aap mujhse koi bhi sawal pooch sakte hain."

    return {
        "reply": reply,
        "provider": getattr(gemma_client, "provider", "OPENROUTER"),
        "model": gemma_client.model_name
    }

from fastapi import UploadFile, File, Form
from zeroresidual.engine.parsers import UniversalStatementParser

universal_parser = UniversalStatementParser(classifier)

@app.post("/api/upload-statement")
async def upload_and_audit(file: UploadFile = File(...), use_llm: bool = Form(True)):
    try:
        content = await file.read()
        res = universal_parser.audit_statement(file.filename or "statement.csv", content, use_llm=use_llm)
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded statement: {str(e)}")


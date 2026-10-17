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
    ctx = req.context_data or {}
    gross_val = str(ctx.get('gross_pos_sales', '50,000.00'))
    payout_val = str(ctx.get('bank_received_payout', '43,000.00'))
    deductions_val = str(ctx.get('total_deductions', '7,000.00'))
    residual_val = str(ctx.get('residual', '0.00'))
    status_val = str(ctx.get('status', 'RECONCILED'))
    bank_val = str(ctx.get('bank_detected', 'HDFC Bank'))
    file_name = str(ctx.get('file_name', 'Current Statement'))
    total_rows = str(ctx.get('total_rows', '24'))
    
    top_deductions = ctx.get('top_deductions', [])
    deductions_list_str = "\n".join([f"  • {d}" for d in top_deductions]) if top_deductions else "  • Refunds, Dispute Escrows, Hardware Rentals, GST"

    ctx_str = f"""
Active Statement Audit Context:
- Statement / File: {file_name} ({total_rows} entries processed)
- Bank / Source: {bank_val}
- Gross Sales / Credits: ₹{gross_val}
- Bank Net Payout: ₹{payout_val}
- Total Deductions & Adjustments: ₹{deductions_val}
- Itemized Deductions:
{deductions_list_str}
- Discrepancy / Unexplained Residual: ₹{residual_val}
- Audit Status: {status_val}
- Calculation Precision: 100% exact to the paisa (0.01 INR)
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

User Question: {req.message}

Instructions:
1. {lang_instr}
2. Ground your response STRICTLY on the numbers in the Active Statement Audit Context above.
3. Keep your answer actionable, practical, and structured with 3-4 clear bullet points.
4. If money is missing or held in dispute, tell the merchant exactly what proof they need to show the bank or payment company.
Gemma AI Munshi:"""

    reply = gemma_client.explain(prompt)
    if not reply:
        # Dynamic Heuristic Munshi Engine (Offline/Fallback)
        msg_lower = req.message.lower()
        is_hi = req.language.upper() == "HI"

        if any(w in msg_lower for w in ["212", "shortfall", "kam", "missing", "difference", "फर्क"]):
            if "212" in residual_val or "212" in req.message:
                reply = (
                    f"आपके ₹{gross_val} की बिक्री में से बैंक ने ₹{payout_val} भेजे हैं। "
                    f"सभी सत्यापित कटौतियों (₹{deductions_val}) के बाद भी ₹212.00 बैंक की तरफ से कम आए हैं। "
                    f"यह बैंक का अस्पष्ट शॉर्टफॉल है—बैंक स्टेटमेंट और सेटलमेंट आईडी लेकर बैंक सपोर्ट से क्लेम करें।"
                    if is_hi else
                    f"Out of ₹{gross_val} gross sales, the bank credited ₹{payout_val}. "
                    f"After all verified deductions (₹{deductions_val}), exactly ₹212.00 is missing. "
                    f"This is an unexplained bank shortfall—contact your acquiring bank with the settlement UTR."
                )
            else:
                reply = (
                    f"इस एक्टिव स्टेटमेंट में कोई अनसुलझा फर्क नहीं है! कुल ग्रॉस क्रेडिट ₹{gross_val} में से "
                    f"₹{deductions_val} की कटौती के बाद शुद्ध ₹{payout_val} का हिसाब 100% सही मिलान हुआ है।"
                    if is_hi else
                    f"There is no unexplained shortfall in this statement! Gross ₹{gross_val} minus "
                    f"deductions ₹{deductions_val} matches net payout ₹{payout_val} to the exact paisa."
                )
        elif any(w in msg_lower for w in ["deduct", "kata", "cut", "कटौती", "चार्ज", "चार्जेस", "breakdown", "विस्तार"]):
            if is_hi:
                ded_lines = "\n".join([f"• {d}" for d in top_deductions]) if top_deductions else f"• कुल कटौतियां: ₹{deductions_val}"
                reply = (
                    f"आपके स्टेटमेंट में कुल ₹{deductions_val} की कटौती हुई है। इसका पूरा विवरण निम्नलिखित है:\n"
                    f"{ded_lines}\n"
                    f"• कटौतियों के बाद बैंक में शुद्ध ₹{payout_val} जमा हुआ है।"
                )
            else:
                ded_lines = "\n".join([f"• {d}" for d in top_deductions]) if top_deductions else f"• Total deductions: ₹{deductions_val}"
                reply = (
                    f"Total deductions for this statement amount to ₹{deductions_val}. Itemized breakdown:\n"
                    f"{ded_lines}\n"
                    f"• Net payout credited to your bank: ₹{payout_val}."
                )
        elif any(w in msg_lower for w in ["dispute", "chargeback", "डिस्प्यूट", "होल्ड", "claim", "escrow"]):
            reply = (
                f"कस्टमर डिस्प्यूट / चार्जबैक होल्ड के लिए बैंक या गेटवे आपके पैसे एस्क्रो में रोक लेता है। "
                f"इसे वापस पाने के लिए:\n"
                f"1. ग्राहक का बिल या डिलीवरी चालान कॉपी तैयार रखें।\n"
                f"2. POS मशीन या साउंडबॉक्स की सफल पेमेंट रसीद लगाएं।\n"
                f"3. हमारे 'Defend Dispute' बटन से बैंक नोडल अधिकारी को रिप्लाई भेजें।"
                if is_hi else
                f"Customer dispute holds are held in escrow pending verification. To claim back your funds:\n"
                f"1. Attach customer order invoice or delivery proof.\n"
                f"2. Attach POS terminal transaction receipt with timestamp.\n"
                f"3. Submit evidence directly via our Defend Dispute action."
            )
        elif any(w in msg_lower for w in ["soundbox", "rent", "साउंडबॉक्स", "किराया", "mdr", "fee"]):
            reply = (
                f"साउंडबॉक्स और हार्डवेयर डिवाइस का किराया:\n"
                f"• 4G IoT साउंडबॉक्स मासिक किराया लगभग ₹423.73 कटता है।\n"
                f"• इस पर सरकारी नियमानुसार 18% GST (₹76.27) चार्ज होता है।\n"
                f"• कार्ड स्वाइप पर MDR इंटरचेंज फीस (जैसे ₹540 + GST) कटती है। यह नियमानुसार वैध है।"
                if is_hi else
                f"Soundbox rental and processing fees breakdown:\n"
                f"• Monthly 4G IoT Soundbox hardware rental: ₹423.73.\n"
                f"• Applicable 18% GST on device rental: ₹76.27 (HSN 9983).\n"
                f"• Card swipe MDR interchange fees apply per RBI merchant guidelines."
            )
        elif any(w in msg_lower for w in ["payout", "net", "balance", "पेआउट", "शुद्ध", "बैलेंस", "कुल", "sales", "hisaab", "हिसाब"]):
            reply = (
                f"आपके स्टेटमेंट ({file_name}) का पूरा हिसाब:\n"
                f"• कुल ग्रॉस बिक्री / क्रेडिट: ₹{gross_val}\n"
                f"• कुल कटौतियां व चार्जेस: -₹{deductions_val}\n"
                f"• बैंक में प्राप्त शुद्ध पेआउट: ₹{payout_val}\n"
                f"• अनसुलझा अंतर (Residual): ₹{residual_val} (पैसे-पैसे का हिसाब)"
                if is_hi else
                f"Audit summary for {file_name}:\n"
                f"• Gross merchant sales/credits: ₹{gross_val}\n"
                f"• Total deductions & clawbacks: -₹{deductions_val}\n"
                f"• Net payout credited to bank: ₹{payout_val}\n"
                f"• Unexplained residual: ₹{residual_val} (Audited to 0.01 INR)"
            )
        else:
            reply = (
                f"नमस्ते! मैं आपका जेम्मा AI मुंशी हूँ। मैंने '{file_name}' ({total_rows} प्रविष्टियां) का हिसाब लोड किया है। "
                f"कुल ग्रॉस बिक्री ₹{gross_val} और बैंक पेआउट ₹{payout_val} है। आप मुझसे किसी भी कटौती या रिफंड के बारे में पूछ सकते हैं।"
                if is_hi else
                f"Namaste! I am your Gemma AI Munshi. I have loaded '{file_name}' ({total_rows} entries). "
                f"Gross credits: ₹{gross_val}, Bank payout: ₹{payout_val}, Deductions: ₹{deductions_val}. Ask me any questions!"
            )

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


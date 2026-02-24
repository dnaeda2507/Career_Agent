from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
from pydantic import BaseModel


from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # daha güvenli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


LOG_FILE = "career_agent_logs.txt"

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


name = "Eda Dana"


# ==============================
# Load CV (PDF)
# ==============================
reader = PdfReader("EDA_DANA_CV.pdf")
cv_text = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        cv_text += text

# ==============================
# Load Summary
# ==============================
with open("summary.txt", "r", encoding="utf-8") as f:
    summary_text = f.read()

# ==============================
# Request Model
# ==============================
class EmployerMessage(BaseModel):
    user_id: str
    message: str

# ==============================
# 2. MODELLER (Pydantic)
# ==============================
class Evaluation(BaseModel):
    professional_tone: int # 1-10
    clarity: int
    completeness: int
    safety: int
    relevance: int
    overall_score: float
    is_acceptable: bool
    feedback: str

def build_system_prompt():
    system_prompt = f"""
You are acting as {name}. You are answering questions on {name}'s website,
particularly questions related to {name}'s career, background, skills and experience.
Your responsibility is to represent {name} for interactions on the website as faithfully as possible.
You are given a summary of {name}'s background and CV profile which you can use to answer questions.
You are communicating with potential employers on behalf of {name}.
Be professional and engaging, as if talking to a potential client or future employer who came across the website.
If you don't know the answer, say so.

You are given the following information about {name}:
"""
    system_prompt += f"\n\n## Summary:\n{summary_text}\n\n## CV:\n{cv_text}\n\n"
    system_prompt += """
Rules:
- Maintain professional, concise, polite tone
- Do not hallucinate
- Do not invent experience
- If unsure, ask for clarification
- Answer interview invitations appropriately
- Respond to technical questions accurately but not too technical
- Always use the 'record_unknown_question' tool for salaries, legal issues or anything not in your CV.
- Always use the 'record_user_details' tool if the employer wants to connect or leaves an email.
- Politely decline offers when needed
"""
    system_prompt += f"With this context, please chat with the user, always staying in character as {name}. Your name is {name}."
    return system_prompt



def build_evaluator_system_prompt():
    return f"""You are a Response Evaluator Agent. Your job is to score the AI's response to an employer.
Criteria (1-10):
- Professional Tone, Clarity, Completeness, Safety (no false claims), Relevance.
Threshold: A score below 7.0 or any safety issue means 'is_acceptable' must be False.
Context for Verification:
{summary_text}
{cv_text}"""


# ==============================
# 4. AGENT FONKSİYONLARI
# ==============================
def evaluate(reply, message, history) -> Evaluation:
    evaluator_user_prompt = f"History: {history}\nEmployer Message: {message}\nGenerated Reply: {reply}"
    
    response = client.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": build_evaluator_system_prompt()},
            {"role": "user", "content": evaluator_user_prompt}
        ],
        response_format=Evaluation
    )
    return response.choices[0].message.parsed

def rerun(original_reply, message, history, feedback):
    updated_system_prompt = build_system_prompt() + f"""
    \n\n## REVISION REQUIRED
    Your previous answer was rejected by the Evaluator.
    Reason: {feedback}
    Original Attempt: {original_reply}
    Please correct the mistakes and provide a better response.
    """
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content


# ==============================
# Simple Memory Store
# ==============================
conversation_memory = {}

def log_to_file(entry: dict):
    """Append a structured log entry to the file"""
    timestamp = datetime.utcnow().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": timestamp, **entry}, ensure_ascii=False) + "\n")

    # =========================
# Telegram Notification
# =========================
def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram notification failed:", e)


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "user_name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

def record_user_details(email, user_name="Unknown", notes="No notes"):
    send_telegram_notification(f"🌟 NEW CONTACT REQUEST\nName: {user_name}\nEmail: {email}\nNotes: {notes}")
    log_to_file({"type": "user_details", "user_name": user_name, "email": email, "notes": notes})
    return {"status": "ok", "message": "Your contact details have been forwarded to Eda."}

def record_unknown_question(question, user_id, confidence=None):
    send_telegram_notification(f"⚠️ UNKNOWN QUESTION (Action Required)\nUser ID: {user_id[:8]}\nQuestion: {question}\nConfidence: {confidence}")
    log_to_file({"type": "unknown_question", "user_id": user_id, "question": question, "confidence": confidence})
    return {"status": "ok", "message": "I have forwarded this specific question to Eda; she will get back to you."}

def handle_tool_calls(tool_calls, user_id):
    results = []
    for tool_call in tool_calls:
        func_name= tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        if func_name == "record_user_details":
            res = record_user_details(**args)
        elif func_name == "record_unknown_question":
            res = record_unknown_question(args.get("question"), user_id)
        results.append({"role": "tool", "content": json.dumps(res), "tool_call_id": tool_call.id})
    return results

@app.post("/career-agent")
def career_agent1(request: EmployerMessage):

    user_id = request.user_id
    user_msg = request.message


    send_telegram_notification(f"📩 New Message ({user_id[:8]}):\n{user_msg}")

    
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    history = conversation_memory[user_id]

    messages = (
        [{"role": "system", "content": build_system_prompt()}]
        + history
        + [{"role": "user", "content": request.message}]
    )

#--------------------------------
    # --- AGENT LOOP ---
    done = False
    reply = ""
    intent = "normal"
    confidence_score = 1.0
    while not done:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages, 
            tools=tools)
        msg = response.choices[0].message
        
        if msg.tool_calls:
            tool_results = handle_tool_calls(msg.tool_calls, user_id)
            messages.append(msg)
            messages.extend(tool_results)
        else:
             # --- Confidence Check for unknown question ---
            confidence_prompt = f"Rate confidence of this answer (0-1) as a single float number only (no extra text): {msg.content}"
            conf_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"You are a confidence evaluator."},
                          {"role":"user","content":confidence_prompt}]
            )

            confidence_score = float(conf_response.choices[0].message.content.strip())

            if confidence_score < 0.7:
                record_unknown_question(user_msg, user_id, confidence=confidence_score)
                intent = "unknown"
            else:
                intent = "normal"

            reply = msg.content
            done = True


    is_revised = False

    # --- Step 2: Evaluate (Hybrid Approach) ---
    evaluation = evaluate(reply, user_msg, history)

    # --- Step 3: Threshold Check & Rerun ---
    if not evaluation.is_acceptable or evaluation.overall_score < 7.0:
        print(f"Low Score ({evaluation.overall_score}): Revising...")
        is_revised = True
        reply = rerun(reply, user_msg, history, evaluation.feedback)


    send_telegram_notification(f"✅ Approved Response:\n{reply}")

   # --- Step 4: Update Memory ---
    conversation_memory[user_id].append({"role": "user", "content": user_msg})
    conversation_memory[user_id].append({
    "role": "assistant",
    "content": reply,
    "confidence": confidence_score,
    "intent": intent
})
    conversation_memory[user_id] = conversation_memory[user_id][-10:] # Keep last 10

    return {
    "response": reply,
    "is_revised": is_revised,
    "evaluation_log": evaluation.model_dump(),
    "intent": intent,
    "confidence": confidence_score
}

@app.get("/conversation/{user_id}")
def get_conversation(user_id: str):
    return conversation_memory.get(user_id, [])
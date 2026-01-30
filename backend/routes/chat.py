from __future__ import annotations

from typing import List

from flask import current_app, jsonify, request

from ..extensions import db
from ..models import Chat
from ..services.ollama_client import OllamaError, check_ollama_health, generate_response
from ..utils import login_required
from . import chat_bp

SYSTEM_CONTEXT = (
    "You are Mama Akinyi, a wise, supportive Kenyan woman from the lakeside village of Matoso. "
    "Respond with warmth, cultural awareness, and practical guidance. "
    "Use Kenyan idioms sparingly, offer encouragement, and keep responses concise yet meaningful. "
    "If you offer advice, root it in local context, community values, and respectful tone."
)


def build_prompt(history: List[Chat], latest_message: str, user_name: str) -> str:
    """Create a contextual prompt for the Ollama model."""
    transcript_lines = []
    for chat in history:
        speaker = "Mama Akinyi" if chat.sender == "assistant" else user_name or "Mwanafunzi"
        transcript_lines.append(f"{speaker}: {chat.message}")

    transcript = "\n".join(transcript_lines).strip()

    return (
        f"{SYSTEM_CONTEXT}\n\n"
        "Conversation so far:\n"
        f"{transcript}\n\n"
        f"{user_name or 'Mwanafunzi'} just said: \"{latest_message}\"\n"
        "Respond as Mama Akinyi:"
    )


@chat_bp.post("/chat")
@login_required
def chat(user):
    """Handle chat messages and forward them to the local Ollama instance."""
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Persist the user's message first.
    user_entry = Chat(user_id=user.id, message=message, sender="user")
    db.session.add(user_entry)
    db.session.flush()  # ensures new entry has an ID if needed later

    # Include the fresh message plus recent history for context.
    recent_history = (
        Chat.query.filter_by(user_id=user.id)
        .order_by(Chat.timestamp.desc())
        .limit(10)
        .all()
    )
    ordered_history = list(reversed(recent_history))

    prompt = build_prompt(ordered_history, latest_message=message, user_name=user.username)
    model_name = (payload.get("model") or "").strip() or "llama2"

    try:
        response_text = generate_response(prompt, model=model_name)
    except OllamaError as exc:
        db.session.rollback()
        current_app.logger.exception("Ollama generation failed for user %s: %s", user.id, exc)
        suggestion = (
            f"Open a terminal and run `ollama run {model_name}` to restart the local model, "
            "then refresh this page."
        )
        return (
            jsonify(
                {
                    "error": "Mama Akinyi is offline.",
                    "details": {
                        "reason": getattr(exc, "reason", str(exc)),
                        "suggestion": suggestion,
                        "model": model_name,
                    },
                }
            ),
            503,
        )

    assistant_entry = Chat(user_id=user.id, message=response_text, sender="assistant")
    db.session.add(assistant_entry)
    db.session.commit()

    return jsonify(
        {
            "reply": response_text,
            "chat": {
                "user_message": user_entry.to_dict(),
                "assistant_message": assistant_entry.to_dict(),
            },
        }
    )


@chat_bp.get("/ollama/health")
def ollama_health():
    """Expose Ollama readiness for quick troubleshooting from the UI."""
    try:
        info = check_ollama_health()
        return jsonify({"status": "online", "ollama": info})
    except OllamaError as exc:
        current_app.logger.warning("Ollama health check failed: %s", exc, exc_info=True)
        return (
            jsonify(
                {
                    "status": "offline",
                    "error": str(exc),
                    "details": {
                        "reason": getattr(exc, "reason", None),
                        "suggestion": "Ensure the Ollama daemon is running (e.g. run `ollama run llama2`).",
                    },
                }
            ),
            503,
        )


@chat_bp.get("/chat")
@login_required
def history(user):
    """Return recent chat history for the authenticated user."""
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))

    chat_entries = (
        Chat.query.filter_by(user_id=user.id)
        .order_by(Chat.timestamp.desc())
        .limit(limit)
        .all()
    )
    ordered = list(reversed(chat_entries))
    return jsonify({"history": [item.to_dict() for item in ordered]})

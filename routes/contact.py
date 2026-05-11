# =============================================================
# routes/contact.py — Studyverse Café | Contact Form API
# =============================================================
# Handles messages submitted via the website contact form.
#
# Endpoints:
#   POST  /api/contact/         → Submit a contact message
#   GET   /api/contact/         → List messages (admin)
#   PATCH /api/contact/<id>/read → Mark message as read (admin)
#   DELETE /api/contact/<id>    → Delete message (admin)
# =============================================================

from flask import Blueprint, request, jsonify, current_app
from utils.db         import query
from utils.validators import validate_contact
from utils.email_helper import send_email, contact_auto_reply_email

contact_bp = Blueprint("contact", __name__)


# ── POST /api/contact/ ────────────────────────────────────────
# Receives a contact form submission.
# Body: { name, email, subject?, message }
@contact_bp.route("/", methods=["POST"])
def submit_contact():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body received"}), 400

    # 1. Validate
    ok, err = validate_contact(data)
    if not ok:
        return jsonify({"error": err}), 422

    # 2. Save to DB
    new_id = query(
        """
        INSERT INTO contact_messages (name, email, subject, message)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data["name"].strip(),
            data["email"].strip().lower(),
            data.get("subject", "").strip() or None,
            data["message"].strip(),
        ),
        commit=True
    )

    # 3. Auto-reply to customer
    send_email(
        to        = data["email"],
        subject   = "We got your message — Studyverse Café ☕",
        html_body = contact_auto_reply_email(data["name"])
    )

    # 4. Notify the café owner
    owner_body = f"""
    <div style="font-family:sans-serif;padding:20px;background:#f5f5f5;">
      <h3>New Contact Message #{new_id}</h3>
      <p><strong>From:</strong> {data['name']} ({data['email']})</p>
      <p><strong>Subject:</strong> {data.get('subject', '—')}</p>
      <hr>
      <p>{data['message']}</p>
    </div>
    """
    send_email(
        to        = current_app.config["CAFE_EMAIL"],
        subject   = f"📬 New Message from {data['name']} — Studyverse",
        html_body = owner_body
    )

    return jsonify({
        "message"   : "Your message has been sent! We'll reply within 24 hours.",
        "message_id": new_id
    }), 201


# ── GET /api/contact/ ─────────────────────────────────────────
# Admin: list all contact messages.
# Optional filter: ?unread=true
@contact_bp.route("/", methods=["GET"])
def list_messages():
    unread_only = request.args.get("unread", "").lower() == "true"

    if unread_only:
        rows = query(
            "SELECT * FROM contact_messages WHERE is_read = 0 ORDER BY created_at DESC"
        )
    else:
        rows = query(
            "SELECT * FROM contact_messages ORDER BY created_at DESC"
        )

    for r in rows:
        r["created_at"] = str(r["created_at"])

    return jsonify({"messages": rows, "count": len(rows)}), 200


# ── PATCH /api/contact/<id>/read ─────────────────────────────
# Admin: mark a message as read.
@contact_bp.route("/<int:msg_id>/read", methods=["PATCH"])
def mark_as_read(msg_id):
    row = query("SELECT id FROM contact_messages WHERE id = %s", (msg_id,), one=True)
    if not row:
        return jsonify({"error": "Message not found"}), 404

    query(
        "UPDATE contact_messages SET is_read = 1 WHERE id = %s",
        (msg_id,), commit=True
    )
    return jsonify({"message": f"Message #{msg_id} marked as read"}), 200


# ── DELETE /api/contact/<id> ──────────────────────────────────
@contact_bp.route("/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    row = query("SELECT id FROM contact_messages WHERE id = %s", (msg_id,), one=True)
    if not row:
        return jsonify({"error": "Message not found"}), 404

    query("DELETE FROM contact_messages WHERE id = %s", (msg_id,), commit=True)
    return jsonify({"message": f"Message #{msg_id} deleted"}), 200

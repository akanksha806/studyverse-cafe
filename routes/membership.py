# =============================================================
# routes/membership.py — Studyverse Café | Membership API
# =============================================================
# Handles membership plan purchases and lookups.
#
# Endpoints:
#   POST  /api/membership/          → Purchase a plan
#   GET   /api/membership/          → List all members (admin)
#   GET   /api/membership/<id>      → Single member record
#   GET   /api/membership/lookup    → Customer checks own status by email
#   PATCH /api/membership/<id>      → Cancel/update (admin)
# =============================================================

from flask import Blueprint, request, jsonify
from utils.db         import query
from utils.validators import validate_membership
from utils.email_helper import send_email, membership_confirmation_email
from datetime import date, timedelta

membership_bp = Blueprint("membership", __name__)


# ── Plan pricing & duration map ───────────────────────────────
PLAN_CONFIG = {
    "Daily Pass"     : {"price": 199.00,  "days": 1},
    "Weekly Pass"    : {"price": 999.00,  "days": 7},
    "Monthly Member" : {"price": 2499.00, "days": 30},
}


def calculate_end_date(start_date_str: str, days: int) -> str:
    """
    Given a start date string (YYYY-MM-DD) and duration in days,
    returns the end date string.
    """
    start = date.fromisoformat(start_date_str)
    end   = start + timedelta(days=days - 1)
    return end.isoformat()


# ── POST /api/membership/ ─────────────────────────────────────
# Customer buys a membership plan.
# Body: { full_name, phone, email, plan, start_date, payment_ref? }
@membership_bp.route("/", methods=["POST"])
def purchase_membership():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body received"}), 400

    # 1. Validate
    ok, err = validate_membership(data)
    if not ok:
        return jsonify({"error": err}), 422

    plan   = data["plan"]
    config = PLAN_CONFIG.get(plan)
    if not config:
        return jsonify({"error": "Unknown plan"}), 422

    # 2. Calculate dates & price
    start_date = data["start_date"]
    end_date   = calculate_end_date(start_date, config["days"])
    price      = config["price"]

    # 3. Insert into DB
    new_id = query(
        """
        INSERT INTO memberships
            (full_name, phone, email, plan, amount_paid, start_date, end_date, payment_ref)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data["full_name"].strip(),
            data["phone"].strip(),
            data["email"].strip().lower(),
            plan,
            price,
            start_date,
            end_date,
            data.get("payment_ref", "").strip() or None,
        ),
        commit=True
    )

    # 4. Send confirmation email
    html = membership_confirmation_email({
        "full_name"  : data["full_name"],
        "plan"       : plan,
        "start_date" : start_date,
        "end_date"   : end_date,
        "amount_paid": f"{price:.2f}",
    })
    send_email(
        to        = data["email"],
        subject   = f"✦ Welcome to Studyverse — Your {plan} is Active!",
        html_body = html
    )

    return jsonify({
        "message"      : f"{plan} activated successfully!",
        "membership_id": new_id,
        "start_date"   : start_date,
        "end_date"     : end_date,
        "amount"       : price,
    }), 201


# ── GET /api/membership/ ──────────────────────────────────────
# Admin: list all members. Filter by ?status=active or ?plan=...
@membership_bp.route("/", methods=["GET"])
def list_members():
    status = request.args.get("status")
    plan   = request.args.get("plan")

    sql    = "SELECT * FROM memberships WHERE 1=1"
    params = []

    if status:
        sql += " AND status = %s"
        params.append(status)
    if plan:
        sql += " AND plan = %s"
        params.append(plan)

    sql += " ORDER BY created_at DESC"
    rows = query(sql, tuple(params))

    for r in rows:
        r["start_date"]  = str(r["start_date"])
        r["end_date"]    = str(r["end_date"])
        r["amount_paid"] = float(r["amount_paid"])
        r["created_at"]  = str(r["created_at"])
        r["updated_at"]  = str(r["updated_at"])

    return jsonify({"members": rows, "count": len(rows)}), 200


# ── GET /api/membership/<id> ──────────────────────────────────
@membership_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id):
    row = query("SELECT * FROM memberships WHERE id = %s", (member_id,), one=True)
    if not row:
        return jsonify({"error": "Membership not found"}), 404

    row["start_date"]  = str(row["start_date"])
    row["end_date"]    = str(row["end_date"])
    row["amount_paid"] = float(row["amount_paid"])
    row["created_at"]  = str(row["created_at"])
    return jsonify(row), 200


# ── GET /api/membership/lookup?email=... ──────────────────────
# Customer self-service: check active membership by email.
@membership_bp.route("/lookup", methods=["GET"])
def lookup_membership():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "email query param is required"}), 400

    row = query(
        """
        SELECT * FROM memberships
        WHERE email = %s AND status = 'active'
        ORDER BY end_date DESC
        LIMIT 1
        """,
        (email,),
        one=True
    )
    if not row:
        return jsonify({"active": False, "message": "No active membership found for this email"}), 200

    # Check if it's actually still valid by today's date
    today    = date.today()
    end_date = row["end_date"]   # already a date object from MySQL

    if end_date < today:
        # Auto-expire it
        query(
            "UPDATE memberships SET status = 'expired' WHERE id = %s",
            (row["id"],), commit=True
        )
        return jsonify({"active": False, "message": "Your membership has expired"}), 200

    row["start_date"]  = str(row["start_date"])
    row["end_date"]    = str(row["end_date"])
    row["amount_paid"] = float(row["amount_paid"])
    row["created_at"]  = str(row["created_at"])
    row["updated_at"]  = str(row["updated_at"])
    return jsonify({"active": True, "membership": row}), 200


# ── PATCH /api/membership/<id> ────────────────────────────────
# Admin: cancel or change plan status.
# Body: { "status": "cancelled" }
@membership_bp.route("/<int:member_id>", methods=["PATCH"])
def update_membership(member_id):
    row = query("SELECT id FROM memberships WHERE id = %s", (member_id,), one=True)
    if not row:
        return jsonify({"error": "Membership not found"}), 404

    data       = request.get_json()
    new_status = data.get("status")
    if new_status not in ["active", "expired", "cancelled"]:
        return jsonify({"error": "status must be active, expired, or cancelled"}), 422

    query(
        "UPDATE memberships SET status = %s WHERE id = %s",
        (new_status, member_id), commit=True
    )
    return jsonify({"message": f"Membership #{member_id} status → '{new_status}'"}), 200

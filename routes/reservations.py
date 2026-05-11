# =============================================================
# routes/reservations.py — Studyverse Café | Reservation API
# =============================================================
# Handles all seat booking logic.
#
# Endpoints:
#   POST   /api/reservations/         → Create new reservation
#   GET    /api/reservations/         → List all reservations (admin)
#   GET    /api/reservations/<id>     → Get one reservation
#   PATCH  /api/reservations/<id>     → Update status (confirm/cancel)
#   DELETE /api/reservations/<id>     → Delete a reservation
# =============================================================

from flask import Blueprint, request, jsonify, current_app
from utils.db         import query
from utils.validators import validate_reservation
from utils.email_helper import (
    send_email,
    reservation_confirmation_email
)
import mysql.connector

reservations_bp = Blueprint("reservations", __name__)


# ── POST /api/reservations/ ───────────────────────────────────
# Creates a new reservation.
# Frontend sends JSON body with booking details.
@reservations_bp.route("/", methods=["POST"])
def create_reservation():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body received"}), 400

    # 1. Validate all inputs before touching the DB
    ok, err = validate_reservation(data)
    if not ok:
        return jsonify({"error": err}), 422   # 422 = Unprocessable Entity

    # 2. Insert into DB
    try:
        new_id = query(
            """
            INSERT INTO reservations
                (full_name, phone, email, visit_date, arrival_time, zone, plan, special_note)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["full_name"].strip(),
                data["phone"].strip(),
                data.get("email", "").strip() or None,
                data["visit_date"],
                data["arrival_time"],
                data["zone"],
                data["plan"],
                data.get("special_note", "").strip() or None,
            ),
            commit=True
        )
    except mysql.connector.IntegrityError:
        # Triggered by the UNIQUE KEY (date + time + zone)
        return jsonify({
            "error": f"Sorry, {data['zone']} is already booked at that time. "
                      "Please choose a different time or zone."
        }), 409   # 409 = Conflict

    # 3. Send confirmation email if customer provided email
    if data.get("email"):
        html = reservation_confirmation_email({
            "full_name"   : data["full_name"],
            "zone"        : data["zone"],
            "visit_date"  : data["visit_date"],
            "arrival_time": data["arrival_time"],
            "plan"        : data["plan"],
        })
        send_email(
            to      = data["email"],
            subject = f"✦ Reservation Confirmed — Studyverse Café",
            html_body = html
        )
        # Also notify café owner
        send_email(
            to        = current_app.config["CAFE_EMAIL"],
            subject   = f"New Reservation #{new_id} — {data['full_name']}",
            html_body = html
        )

    return jsonify({
        "message"       : "Reservation created successfully!",
        "reservation_id": new_id
    }), 201   # 201 = Created


# ── GET /api/reservations/ ────────────────────────────────────
# Returns all reservations. Add auth middleware before making
# this live — right now it's open for development.
@reservations_bp.route("/", methods=["GET"])
def list_reservations():
    # Optional filters via query params: ?date=2025-01-01&status=pending
    date_filter   = request.args.get("date")
    status_filter = request.args.get("status")

    sql    = "SELECT * FROM reservations WHERE 1=1"
    params = []

    if date_filter:
        sql += " AND visit_date = %s"
        params.append(date_filter)

    if status_filter:
        sql += " AND status = %s"
        params.append(status_filter)

    sql += " ORDER BY visit_date ASC, arrival_time ASC"

    rows = query(sql, tuple(params))
    # Convert date/time objects to strings for JSON serialization
    for r in rows:
        r["visit_date"]   = str(r["visit_date"])
        r["arrival_time"] = str(r["arrival_time"])
        r["created_at"]   = str(r["created_at"])
        r["updated_at"]   = str(r["updated_at"])

    return jsonify({"reservations": rows, "count": len(rows)}), 200


# ── GET /api/reservations/<id> ────────────────────────────────
# Returns a single reservation by its ID.
@reservations_bp.route("/<int:reservation_id>", methods=["GET"])
def get_reservation(reservation_id):
    row = query(
        "SELECT * FROM reservations WHERE id = %s",
        (reservation_id,),
        one=True
    )
    if not row:
        return jsonify({"error": "Reservation not found"}), 404

    row["visit_date"]   = str(row["visit_date"])
    row["arrival_time"] = str(row["arrival_time"])
    row["created_at"]   = str(row["created_at"])
    return jsonify(row), 200


# ── PATCH /api/reservations/<id> ─────────────────────────────
# Update the status of a reservation.
# Body: { "status": "confirmed" }
@reservations_bp.route("/<int:reservation_id>", methods=["PATCH"])
def update_reservation_status(reservation_id):
    data = request.get_json()
    new_status = data.get("status")

    valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 422

    # Check it exists first
    row = query("SELECT id FROM reservations WHERE id = %s", (reservation_id,), one=True)
    if not row:
        return jsonify({"error": "Reservation not found"}), 404

    query(
        "UPDATE reservations SET status = %s WHERE id = %s",
        (new_status, reservation_id),
        commit=True
    )
    return jsonify({"message": f"Reservation #{reservation_id} marked as '{new_status}'"}), 200


# ── DELETE /api/reservations/<id> ────────────────────────────
# Permanently removes a reservation.
@reservations_bp.route("/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
    row = query("SELECT id FROM reservations WHERE id = %s", (reservation_id,), one=True)
    if not row:
        return jsonify({"error": "Reservation not found"}), 404

    query("DELETE FROM reservations WHERE id = %s", (reservation_id,), commit=True)
    return jsonify({"message": f"Reservation #{reservation_id} deleted"}), 200

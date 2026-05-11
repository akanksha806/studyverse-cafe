# =============================================================
# routes/menu.py — Studyverse Café | Menu API
# =============================================================
# Manages café menu items.
#
# Endpoints:
#   GET    /api/menu/              → All available menu items
#   GET    /api/menu/signature     → Only homepage-featured items
#   GET    /api/menu/<id>          → Single item
#   POST   /api/menu/              → Add new item (admin)
#   PATCH  /api/menu/<id>          → Update item (price/availability)
#   DELETE /api/menu/<id>          → Remove item (admin)
# =============================================================

from flask import Blueprint, request, jsonify
from utils.db import query
import mysql.connector

menu_bp = Blueprint("menu", __name__)


# ── GET /api/menu/ ────────────────────────────────────────────
# Returns all items that are currently available (is_available=1).
# Optional filter: ?category=hot_drinks
@menu_bp.route("/", methods=["GET"])
def get_menu():
    category = request.args.get("category")

    if category:
        items = query(
            "SELECT * FROM menu_items WHERE is_available = 1 AND category = %s ORDER BY name",
            (category,)
        )
    else:
        items = query(
            "SELECT * FROM menu_items WHERE is_available = 1 ORDER BY category, name"
        )

    # Convert Decimal price to float for JSON
    for item in items:
        item["price"] = float(item["price"])
        item["created_at"] = str(item["created_at"])
        item["updated_at"] = str(item["updated_at"])

    return jsonify({"menu": items, "count": len(items)}), 200


# ── GET /api/menu/signature ───────────────────────────────────
# Returns only the 5 signature drinks shown on the homepage.
@menu_bp.route("/signature", methods=["GET"])
def get_signature_items():
    items = query(
        "SELECT * FROM menu_items WHERE is_signature = 1 AND is_available = 1 ORDER BY id"
    )
    for item in items:
        item["price"] = float(item["price"])
        item["created_at"] = str(item["created_at"])
        item["updated_at"] = str(item["updated_at"])

    return jsonify({"signature_items": items}), 200


# ── GET /api/menu/<id> ────────────────────────────────────────
@menu_bp.route("/<int:item_id>", methods=["GET"])
def get_menu_item(item_id):
    item = query("SELECT * FROM menu_items WHERE id = %s", (item_id,), one=True)
    if not item:
        return jsonify({"error": "Menu item not found"}), 404

    item["price"] = float(item["price"])
    item["created_at"] = str(item["created_at"])
    return jsonify(item), 200


# ── POST /api/menu/ ───────────────────────────────────────────
# Add a new menu item (admin use).
# Body: { name, description, price, category, emoji, is_signature }
@menu_bp.route("/", methods=["POST"])
def add_menu_item():
    data = request.get_json()

    required = ["name", "price", "category"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 422

    valid_categories = ["hot_drinks", "cold_drinks", "shakes", "food", "specials"]
    if data["category"] not in valid_categories:
        return jsonify({"error": f"category must be one of: {valid_categories}"}), 422

    try:
        price = float(data["price"])
    except (ValueError, TypeError):
        return jsonify({"error": "price must be a number"}), 422

    new_id = query(
        """
        INSERT INTO menu_items (name, description, price, category, emoji, is_signature)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            data["name"].strip(),
            data.get("description", "").strip() or None,
            price,
            data["category"],
            data.get("emoji", "☕"),
            1 if data.get("is_signature") else 0,
        ),
        commit=True
    )
    return jsonify({"message": "Menu item added", "item_id": new_id}), 201


# ── PATCH /api/menu/<id> ──────────────────────────────────────
# Update any field of a menu item.
# Common uses: toggle availability, update price.
@menu_bp.route("/<int:item_id>", methods=["PATCH"])
def update_menu_item(item_id):
    item = query("SELECT id FROM menu_items WHERE id = %s", (item_id,), one=True)
    if not item:
        return jsonify({"error": "Menu item not found"}), 404

    data = request.get_json()

    # Build dynamic SET clause — only update fields that were sent
    allowed = ["name", "description", "price", "category", "emoji", "is_available", "is_signature"]
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 422

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values     = list(updates.values()) + [item_id]

    query(f"UPDATE menu_items SET {set_clause} WHERE id = %s", tuple(values), commit=True)
    return jsonify({"message": f"Item #{item_id} updated"}), 200


# ── DELETE /api/menu/<id> ─────────────────────────────────────
@menu_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_menu_item(item_id):
    item = query("SELECT id FROM menu_items WHERE id = %s", (item_id,), one=True)
    if not item:
        return jsonify({"error": "Menu item not found"}), 404

    query("DELETE FROM menu_items WHERE id = %s", (item_id,), commit=True)
    return jsonify({"message": f"Item #{item_id} deleted"}), 200

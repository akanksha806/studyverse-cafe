# =============================================================
# utils/db.py — Studyverse Café | MySQL Connection Helper
# =============================================================
# Every route file imports get_db() from here to get a
# database connection. Using a helper means you only write
# the connection logic once — change it here, it changes
# everywhere.
#
# Pattern used: open → use → close per request.
# This is simple and safe for a small-traffic café app.
# For high traffic, switch to a connection pool (see bottom).
# =============================================================

import mysql.connector
from flask import current_app, g


def get_db():
    """
    Returns a MySQL connection for the current request.
    
    Flask's `g` object lives for one request only.
    Storing the connection in `g` means we reuse the same
    connection if get_db() is called multiple times in one
    request, instead of opening a new one each time.
    """
    if "db" not in g:
        g.db = mysql.connector.connect(
            host     = current_app.config["MYSQL_HOST"],
            port     = current_app.config["MYSQL_PORT"],
            user     = current_app.config["MYSQL_USER"],
            password = current_app.config["MYSQL_PASSWORD"],
            database = current_app.config["MYSQL_DB"],
            # Return rows as dicts {"col": val} instead of plain tuples
            # so you can do row["full_name"] instead of row[1]
        )
    return g.db


def close_db(e=None):
    """
    Closes the DB connection at end of each request.
    Registered in app factory via app.teardown_appcontext.
    """
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def query(sql, params=(), one=False, commit=False):
    """
    Convenience wrapper for running SQL queries.

    Args:
        sql     : SQL string, use %s for placeholders (never f-strings!)
        params  : tuple of values to safely substitute
        one     : True → return one dict, False → return list of dicts
        commit  : True → commit after query (INSERT/UPDATE/DELETE)

    Returns:
        dict | list[dict] | lastrowid (for INSERT with commit=True)

    Example:
        # SELECT
        rows = query("SELECT * FROM menu_items WHERE is_available = %s", (1,))

        # INSERT
        new_id = query(
            "INSERT INTO reservations (full_name, phone) VALUES (%s, %s)",
            ("Aanya", "9876543210"),
            commit=True
        )
    """
    conn   = get_db()
    # dictionary=True makes rows come back as dicts
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(sql, params)

        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id          # return the new row's ID

        result = cursor.fetchone() if one else cursor.fetchall()
        cursor.close()
        return result

    except mysql.connector.Error as err:
        conn.rollback()
        cursor.close()
        raise err                   # let the route handle the error

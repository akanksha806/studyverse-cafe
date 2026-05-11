# =============================================================
# utils/email_helper.py — Studyverse Café | Email Utility
# =============================================================
# Sends HTML confirmation emails using Flask-Mail + Gmail SMTP.
# Called by routes after a successful DB insert.
#
# Two emails are sent on reservation:
#   1. To the customer — booking confirmation
#   2. To the café    — new booking notification
# =============================================================

from flask_mail import Mail, Message
from flask import current_app

# Single Mail instance, initialized in send_email()
# (avoids needing app context at import time)
mail = Mail()


def init_mail(app):
    """
    Call this once inside create_app() to bind Flask-Mail to the app.
    Add:  from utils.email_helper import init_mail
          init_mail(app)
    in your app.py after app is created.
    """
    mail.init_app(app)


def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Sends a single HTML email.

    Args:
        to        : recipient email address
        subject   : email subject line
        html_body : HTML string for the email body

    Returns:
        True if sent, False if it failed (logged, not raised)
    """
    try:
        msg = Message(
            subject    = subject,
            sender     = current_app.config["MAIL_SENDER"],
            recipients = [to],
            html       = html_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        # Don't crash the request if email fails
        current_app.logger.error(f"Email send failed to {to}: {e}")
        return False


# ── Email Templates ──────────────────────────────────────────

def reservation_confirmation_email(reservation: dict) -> str:
    """
    HTML email sent to the customer after booking.
    `reservation` dict has keys: full_name, zone, visit_date,
    arrival_time, plan.
    """
    cfg = current_app.config
    return f"""
    <div style="background:#080705;padding:40px;font-family:Georgia,serif;color:#d4c4a0;max-width:600px;margin:auto;border:1px solid #2a2215;border-radius:12px;">
      <h1 style="color:#c9a84c;font-size:28px;margin-bottom:4px;">Studyverse Café</h1>
      <p style="color:#8a7a5a;font-size:13px;margin-bottom:32px;letter-spacing:2px;">JAIPUR · YOUR SECOND STUDY HOME</p>

      <h2 style="color:#f5f0e8;font-size:20px;">Your spot is reserved ✦</h2>
      <p style="line-height:1.8;">Hi <strong style="color:#e8c97a;">{reservation['full_name']}</strong>, your reservation at Studyverse Café is confirmed. We can't wait to have you.</p>

      <div style="background:#1c1710;border:1px solid #2a2215;border-radius:8px;padding:24px;margin:24px 0;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="color:#8a7a5a;padding:6px 0;">Date</td>       <td style="color:#f5f0e8;text-align:right;">{reservation['visit_date']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Arrival</td>    <td style="color:#f5f0e8;text-align:right;">{reservation['arrival_time']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Zone</td>       <td style="color:#c9a84c;text-align:right;">{reservation['zone']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Plan</td>       <td style="color:#f5f0e8;text-align:right;">{reservation['plan']}</td></tr>
        </table>
      </div>

      <p style="line-height:1.8;font-size:13px;color:#8a7a5a;">
        📍 {cfg['CAFE_ADDRESS']}<br>
        📞 {cfg['CAFE_PHONE']}<br>
        Please arrive 5 minutes early. Show this email at the counter.
      </p>

      <p style="margin-top:32px;font-size:12px;color:#5a4a2a;border-top:1px solid #2a2215;padding-top:16px;">
        © 2025 {cfg['CAFE_NAME']} · Jaipur, Rajasthan
      </p>
    </div>
    """


def membership_confirmation_email(member: dict) -> str:
    """HTML email sent to a new member after plan purchase."""
    cfg = current_app.config
    return f"""
    <div style="background:#080705;padding:40px;font-family:Georgia,serif;color:#d4c4a0;max-width:600px;margin:auto;border:1px solid #2a2215;border-radius:12px;">
      <h1 style="color:#c9a84c;font-size:28px;margin-bottom:4px;">Studyverse Café</h1>
      <p style="color:#8a7a5a;font-size:13px;margin-bottom:32px;letter-spacing:2px;">MEMBERSHIP CONFIRMED ✦</p>

      <h2 style="color:#f5f0e8;">Welcome to the inner circle, {member['full_name']} 🎉</h2>
      <p style="line-height:1.8;">Your <strong style="color:#e8c97a;">{member['plan']}</strong> is now active. Every seat, every late night, every cup — it's yours.</p>

      <div style="background:#1c1710;border:1px solid #2a2215;border-radius:8px;padding:24px;margin:24px 0;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr><td style="color:#8a7a5a;padding:6px 0;">Plan</td>       <td style="color:#c9a84c;text-align:right;">{member['plan']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Valid From</td> <td style="color:#f5f0e8;text-align:right;">{member['start_date']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Valid Until</td><td style="color:#f5f0e8;text-align:right;">{member['end_date']}</td></tr>
          <tr><td style="color:#8a7a5a;padding:6px 0;">Amount</td>     <td style="color:#f5f0e8;text-align:right;">₹{member['amount_paid']}</td></tr>
        </table>
      </div>

      <p style="font-size:13px;color:#8a7a5a;">📍 {cfg['CAFE_ADDRESS']} · 📞 {cfg['CAFE_PHONE']}</p>
      <p style="margin-top:32px;font-size:12px;color:#5a4a2a;border-top:1px solid #2a2215;padding-top:16px;">
        © 2025 {cfg['CAFE_NAME']}
      </p>
    </div>
    """


def contact_auto_reply_email(name: str) -> str:
    """Auto-reply sent to customer after they submit the contact form."""
    cfg = current_app.config
    return f"""
    <div style="background:#080705;padding:40px;font-family:Georgia,serif;color:#d4c4a0;max-width:600px;margin:auto;border:1px solid #2a2215;border-radius:12px;">
      <h1 style="color:#c9a84c;font-size:28px;margin-bottom:32px;">Studyverse Café</h1>
      <p>Hi <strong style="color:#e8c97a;">{name}</strong>,</p>
      <p style="line-height:1.8;">Thanks for reaching out! We've received your message and will get back to you within 24 hours.</p>
      <p style="line-height:1.8;font-size:13px;color:#8a7a5a;margin-top:24px;">
        In the meantime, feel free to drop by — we're open till 3AM.<br><br>
        📍 {cfg['CAFE_ADDRESS']}<br>
        📞 {cfg['CAFE_PHONE']}
      </p>
      <p style="margin-top:32px;font-size:12px;color:#5a4a2a;border-top:1px solid #2a2215;padding-top:16px;">
        © 2025 {cfg['CAFE_NAME']}
      </p>
    </div>
    """

import os
import sys
import base64
import re
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from math import ceil
import uuid
import hashlib
import hmac
import secrets
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pymysql
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import Config
from vetai_service import vetai_service
from AI_Assistent import LivestockGeminiAssistant
from animal_domain_validator import validate_question_with_context
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import urljoin, urlparse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_cors import CORS
from api_routes import api_v1

app = Flask(__name__)
# app.run(host='0.0.0.0',port=5000)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config.from_object(Config)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config.setdefault("MAX_CONTENT_LENGTH", 20 * 1024 * 1024)
app.config.setdefault("UPLOAD_FOLDER", os.path.join(app.root_path, "static", "uploads"))
app.secret_key = app.config["SECRET_KEY"]
app.permanent_session_lifetime = timedelta(days=14)

app.register_blueprint(api_v1)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
CSRF_EXEMPT_ENDPOINTS = {"static", "razorpay_webhook"}
MONEY_QUANTUM = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def money_paise(value):
    return int((money(value) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def distance_label(value):
    distance = float(value or 0)
    return "<0.1 km" if distance < 0.1 else f"{distance:.1f} km"


def calculate_commissions(base_amount, buyer_percent=None, seller_percent=None):
    """Calculate and snapshot all marketplace amounts using Decimal arithmetic."""
    base = money(base_amount)
    buyer_rate = money(buyer_percent if buyer_percent is not None else app.config["BUYER_COMMISSION_PERCENT"])
    seller_rate = money(seller_percent if seller_percent is not None else app.config["SELLER_COMMISSION_PERCENT"])
    buyer_commission = money(base * buyer_rate / Decimal("100"))
    seller_commission = money(base * seller_rate / Decimal("100"))
    return {
        "base_amount": base,
        "buyer_commission_percent": buyer_rate,
        "buyer_commission_amount": buyer_commission,
        "seller_commission_percent": seller_rate,
        "seller_commission_amount": seller_commission,
        "buyer_payable_amount": money(base + buyer_commission),
        "seller_payout_amount": money(base - seller_commission),
        "admin_gross_commission": money(buyer_commission + seller_commission),
    }


def serialize_money_fields(values):
    return {key: str(value) if isinstance(value, Decimal) else value for key, value in values.items()}


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    if request.path.startswith("/api/"):
        return
    if request.endpoint in CSRF_EXEMPT_ENDPOINTS:
        return
    submitted = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("csrf_token", "")
    if not expected or not submitted or not hmac.compare_digest(submitted, expected):
        session["csrf_token"] = secrets.token_urlsafe(32)
        flash("Your session token expired. Please submit the form again.", "warning")
        return redirect(request.path)


def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.get("user") is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if normalize_role(g.user.get("role")) != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped_view


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=app.config["MYSQL_HOST"],
            port=app.config["MYSQL_PORT"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DB"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return g.db


def normalize_role(role):
    return (role or "").strip().lower()


def get_current_seller_id():
    if not g.get("user"):
        return None

    user_id = g.user.get("user_id")
    if not user_id:
        return None

    with get_db().cursor() as cursor:
        cursor.execute("SELECT seller_id FROM seller_profile WHERE user_id = %s LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            return row["seller_id"]

        full_name = (g.user.get("full_name") or "").strip() or (g.user.get("email") or "").split("@", 1)[0]
        cursor.execute(
            "INSERT INTO seller_profile (user_id, shop_name, address, city, state, country, verified, rating, total_animals) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, full_name, "", "", "", "India", 1, 4.8, 0),
        )
        return cursor.lastrowid


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.errorhandler(pymysql.err.OperationalError)
def handle_mysql_error(error):
    app.logger.exception("MySQL operational error")
    return render_template(
        "error.html",
        title="Database connection failed",
        message="LivestockAI could not connect to your MySQL database.",
        details=str(error),
        suggestion="Verify your .env settings or environment variables for MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, and MYSQL_DB.",
    ), 500


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        try:
            with get_db().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s LIMIT 1", (user_id,))
                g.user = cursor.fetchone()
        except Exception:
            g.user = None


@app.before_request
def enforce_csrf():
    return validate_csrf()


@app.context_processor
def inject_globals():
    nav_categories = []
    try:
        with get_db().cursor() as cursor:
            nav_categories = fetch_category_choices(cursor)
    except Exception:
        nav_categories = []
    current_user = g.get("user")
    return {
        "nav_categories": nav_categories,
        "current_user": current_user,
        "current_user_role": normalize_role(current_user.get("role")) if current_user else None,
        "csrf_token": get_csrf_token(),
        "animal_image_url": animal_image_url,
    }


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def animal_image_url(animal):
    """Return the first usable image URL for an animal record or ID."""
    animal_id = animal.get("animal_id") if isinstance(animal, dict) else animal
    stored_url = (animal.get("image_url") or animal.get("image")) if isinstance(animal, dict) else None

    image_dir = os.path.join(app.root_path, "static", "uploads", "animals")
    stored_filenames = []
    if stored_url:
        stored_filename = os.path.basename(urlparse(str(stored_url).split("?", 1)[0]).path)
        if stored_filename:
            stored_filenames.append(stored_filename)
            if stored_filename.lower().endswith(".jpg"):
                stored_filenames.append(f"{stored_filename}.png")
            if stored_filename.lower().endswith(".jpeg"):
                stored_filenames.append(f"{stored_filename}.png")

    for filename in stored_filenames:
        if os.path.isfile(os.path.join(image_dir, filename)):
            return url_for("static", filename=f"uploads/animals/{filename}")

    try:
        numeric_id = int(animal_id)
    except (TypeError, ValueError):
        return url_for("static", filename="images/hero-farm.svg")

    candidates = [
        f"animal_{numeric_id}.jpg",
        f"animal_{numeric_id:03d}.jpg.png",
        f"animal_{numeric_id:03d}.png",
        f"animal_{numeric_id}.jpg.png",
        f"animal_{numeric_id}.png",
        f"animal_{numeric_id}.jpeg",
        f"animal_{numeric_id}.webp",
    ]
    for filename in candidates:
        if os.path.isfile(os.path.join(image_dir, filename)):
            return url_for("static", filename=f"uploads/animals/{filename}")

    return url_for("static", filename="images/hero-farm.svg")


app.add_template_global(animal_image_url, name="animal_image_url")
app.add_template_global(distance_label, name="distance_label")


def fetch_category_choices(cursor):
    cursor.execute("SELECT animal_type AS category_name FROM animals WHERE animal_type IN ('Cow', 'Dog', 'Cat', 'Horse') GROUP BY animal_type ORDER BY animal_type")
    rows = cursor.fetchall()
    icons = {
        "cow": "fa-cow",
        "dog": "fa-dog",
        "cat": "fa-cat",
        "horse": "fa-horse",
    }
    categories = []
    for index, row in enumerate(rows, start=1):
        category_name = row["category_name"]
        categories.append({
            "category_id": index,
            "category_name": category_name,
            "icon": icons.get(category_name.lower(), "fa-paw"),
        })
    return categories


def get_testimonials():
    return [
        {
            "testimonial_id": 1,
            "full_name": "Priya",
            "role_name": "Buyer",
            "avatar": "https://ui-avatars.com/api/?name=Priya&background=0f766e&color=fff",
            "rating": 5,
            "quote": "The marketplace made it easy to list and discover animals.",
        },
        {
            "testimonial_id": 2,
            "full_name": "Rahul",
            "role_name": "Seller",
            "avatar": "https://ui-avatars.com/api/?name=Rahul&background=1d4ed8&color=fff",
            "rating": 5,
            "quote": "The AI assistant helped me compare breeds and pricing quickly.",
        },
    ]


def fetch_breed_options(cursor, categories):
    cursor.execute(
        """
        SELECT DISTINCT a.animal_type AS animal_type, a.breed AS breed
        FROM animals a
        ORDER BY a.animal_type, a.breed
        """
    )
    rows = cursor.fetchall()
    category_map = {row["category_name"].lower(): row["category_id"] for row in categories}
    breed_options = []
    for row in rows:
        category_id = category_map.get(row["animal_type"].lower())
        if category_id is None:
            continue
        breed_options.append({"animal_type": row["animal_type"], "breed": row["breed"], "category_id": category_id})
    return breed_options


def mock_disease_inference(filename):
    predictions = [
        ("No major symptoms detected", "Maintain regular vaccination and a clean shelter environment."),
        ("Possible skin fungal infection", "Isolate the animal and consult a veterinarian for antifungal treatment."),
        ("Likely eye irritation", "Wash with sterile saline and schedule a veterinary check if symptoms persist."),
        ("Possible digestive stress", "Hydrate properly and review feed quality for 48 hours."),
    ]
    idx = int(hashlib.md5(filename.encode("utf-8")).hexdigest(), 16) % len(predictions)
    disease, recommendation = predictions[idx]
    confidence = 78.0 + ((idx + 1) * 4.9)
    return disease, min(confidence, 97.9), recommendation


# --- Password reset token helpers ---
def _get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def generate_password_reset_token(email: str) -> str:
    s = _get_serializer()
    return s.dumps(email, salt="password-reset-salt")


def confirm_password_reset_token(token: str, expiration: int = 3600):
    s = _get_serializer()
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=expiration)
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"
    return email, None


def get_json_payload():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def get_gemini_client():
    """Create Gemini lazily so a missing optional key never stops Flask starting."""
    api_key = app.config.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        app.logger.exception("Gemini client could not be initialised")
        return None


def get_ai_assistant():
    db_config = {
        "host": app.config.get("AI_MYSQL_HOST") or app.config.get("MYSQL_HOST", "localhost"),
        "port": int(app.config.get("AI_MYSQL_PORT") or app.config.get("MYSQL_PORT", "3306")),
        "user": app.config.get("AI_MYSQL_USER") or app.config.get("MYSQL_USER", "root"),
        "password": app.config.get("AI_MYSQL_PASSWORD") or app.config.get("MYSQL_PASSWORD", ""),
        "database": app.config.get("AI_MYSQL_DB") or app.config.get("MYSQL_DB", "livestockai"),
    }
    return LivestockGeminiAssistant(
        api_key=app.config.get("GEMINI_API_KEY"),
        model=app.config.get("GEMINI_MODEL", "gemini-2.5-flash"),
        db_config=db_config,
    )


def get_ai_history(user_id, limit=8):
    """Use the existing table while keeping its legacy schema untouched."""
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT question, response, created_at FROM (SELECT question, response, created_at FROM ai_chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s) history ORDER BY created_at ASC",
            (user_id, limit),
        )
        rows = cursor.fetchall()
    for row in rows:
        row["intent"] = "DATABASE_QUERY" if any(word in row["question"].lower() for word in ("show", "find", "available", "price", "cow", "animal")) else "GENERAL_QUERY"
    return rows


def process_ai_chat(question, user_id):
    """Use the Gemini notebook assistant for both database-backed marketplace answers and general advice.
    
    Applies strict animal domain validation:
    - Allows questions about: Cow, Cat, Dog, Horse
    - Rejects questions about unsupported animals
    - Rejects completely unrelated questions
    - Handles ambiguous questions by asking for clarification
    """
    assistant = get_ai_assistant()
    answer = "I couldn't process your question right now. Please try again."
    marketplace_items = []
    intent = "GENERAL_QUERY"
    
    try:
        # Get conversation history for context
        chat_history = get_ai_history(user_id, limit=10)
        
        # LAYER 1: Application-level domain validation
        validation_status, restriction_message = validate_question_with_context(question, chat_history)
        
        # If validation failed, return restriction message immediately
        if validation_status != "allowed":
            answer = restriction_message or "I couldn't process your question right now. Please try again."
            intent = "RESTRICTED_QUERY"
        else:
            # Validation passed, proceed with existing logic
            route = assistant.decide_route(question)
            intent = route.upper() + "_QUERY"
            
            if route == "marketplace":
                answer, rows = assistant.database_answer_with_rows(question)
                marketplace_items = [
                    {
                        "animal_id": row.get("animal_id"),
                        "animal_type": row.get("animal_type"),
                        "breed": row.get("breed"),
                        "animal_name": row.get("animal_name"),
                        "health_status": row.get("health_status"),
                        "city": row.get("city"),
                        "state": row.get("state"),
                        "price": row.get("price"),
                        "image_url": row.get("image_url"),
                        "availability": row.get("availability"),
                        "detail_url": url_for("animal_detail", animal_id=row.get("animal_id")),
                    }
                    for row in rows
                    if row.get("animal_id") is not None
                ]
            else:
                answer = assistant.general_advice(question)
    except Exception:
        app.logger.exception("Gemini notebook assistant failed for user %s", user_id)
        answer = "I couldn't access the AI assistant right now. Please try again in a moment."

    with get_db().cursor() as cursor:
        cursor.execute("INSERT INTO ai_chat_history (user_id, question, response) VALUES (%s, %s, %s)", (user_id, question, answer))
    return {
        "success": True,
        "intent": intent,
        "message": answer,
        "answer": answer,
        "data": {"type": "animal_results", "items": marketplace_items} if marketplace_items else None,
    }


@app.route("/admin/api/users", methods=["GET"])
@admin_required
def admin_users_api():
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT user_id, full_name, email, phone, role, status, created_at FROM users ORDER BY created_at DESC"
        )
        return jsonify(cursor.fetchall())


@app.route("/admin/api/users/<int:user_id>", methods=["PATCH", "DELETE"])
@admin_required
def admin_user_mutation(user_id):
    payload = get_json_payload()
    with get_db().cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s LIMIT 1", (user_id,))
        if not cursor.fetchone():
            abort(404)
        if request.method == "DELETE":
            if user_id == g.user["user_id"]:
                return jsonify({"error": "You cannot delete your own admin account."}), 400
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            return jsonify({"deleted": True})
        status = payload.get("status")
        role = payload.get("role")
        if status not in {"Active", "Suspended", "Inactive"} and role not in {"Admin", "Seller", "Buyer"}:
            return jsonify({"error": "Provide a valid status or role."}), 400
        fields, values = [], []
        if status in {"Active", "Suspended", "Inactive"}:
            fields.append("status = %s")
            values.append(status)
        if role in {"Admin", "Seller", "Buyer"}:
            fields.append("role = %s")
            values.append(role)
        values.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = %s", values)
    return jsonify({"updated": True})


@app.route("/admin/api/sellers", methods=["GET"])
@admin_required
def admin_sellers_api():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT s.seller_id, s.shop_name, s.verified, s.rating, s.city, s.state,
                   u.user_id, u.full_name, u.email, u.status
            FROM seller_profile s JOIN users u ON u.user_id = s.user_id
            ORDER BY s.created_at DESC
            """
        )
        return jsonify(cursor.fetchall())


@app.route("/admin/api/sellers/<int:seller_id>", methods=["PATCH", "DELETE"])
@admin_required
def admin_seller_mutation(seller_id):
    payload = get_json_payload()
    with get_db().cursor() as cursor:
        cursor.execute("SELECT user_id FROM seller_profile WHERE seller_id = %s LIMIT 1", (seller_id,))
        seller = cursor.fetchone()
        if not seller:
            abort(404)
        if request.method == "DELETE":
            cursor.execute("UPDATE users SET status = 'Inactive' WHERE user_id = %s", (seller["user_id"],))
            return jsonify({"deleted": True})
        if "verified" not in payload or payload["verified"] not in {0, 1, True, False}:
            return jsonify({"error": "verified must be boolean."}), 400
        cursor.execute("UPDATE seller_profile SET verified = %s WHERE seller_id = %s", (int(payload["verified"]), seller_id))
        if payload.get("status") in {"Active", "Suspended", "Inactive"}:
            cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (payload["status"], seller["user_id"]))
    return jsonify({"updated": True})


@app.route("/admin/api/animals", methods=["GET"])
@admin_required
def admin_animals_api():
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT animal_id, seller_id, animal_type, breed, price, availability, health_status, created_at FROM animals ORDER BY created_at DESC"
        )
        return jsonify(cursor.fetchall())


@app.route("/admin/api/animals/<int:animal_id>", methods=["PATCH", "DELETE"])
@admin_required
def admin_animal_mutation(animal_id):
    payload = get_json_payload()
    with get_db().cursor() as cursor:
        cursor.execute("SELECT animal_id FROM animals WHERE animal_id = %s LIMIT 1", (animal_id,))
        if not cursor.fetchone():
            abort(404)
        if request.method == "DELETE":
            cursor.execute("DELETE FROM animals WHERE animal_id = %s", (animal_id,))
            return jsonify({"deleted": True})
        availability = payload.get("availability")
        health_status = payload.get("health_status")
        if availability not in {"Available", "Sold", "Reserved"} and health_status not in {"Healthy", "Recovered", "Under Treatment", "Critical"}:
            return jsonify({"error": "Provide a valid availability or health_status."}), 400
        fields, values = [], []
        if availability in {"Available", "Sold", "Reserved"}:
            fields.append("availability = %s")
            values.append(availability)
        if health_status in {"Healthy", "Recovered", "Under Treatment", "Critical"}:
            fields.append("health_status = %s")
            values.append(health_status)
        values.append(animal_id)
        cursor.execute(f"UPDATE animals SET {', '.join(fields)} WHERE animal_id = %s", values)
    return jsonify({"updated": True})


@app.route("/admin/api/reports", methods=["GET"])
@admin_required
def admin_reports_api():
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT report_id, reported_by, seller_id, animal_id, reason, description, status, admin_action, created_at FROM reports ORDER BY created_at DESC"
        )
        return jsonify(cursor.fetchall())


@app.route("/admin/api/reports/<int:report_id>", methods=["PATCH"])
@admin_required
def admin_report_mutation(report_id):
    payload = get_json_payload()
    status = payload.get("status")
    if status not in {"Pending", "Under Review", "Resolved", "Dismissed"}:
        return jsonify({"error": "Invalid report status."}), 400
    with get_db().cursor() as cursor:
        cursor.execute("UPDATE reports SET status = %s, admin_id = %s, admin_action = %s WHERE report_id = %s", (status, g.user["user_id"], payload.get("admin_action", ""), report_id))
        if cursor.rowcount == 0:
            abort(404)
    return jsonify({"updated": True})


@app.route("/api/location", methods=["POST"])
@login_required
def save_browser_location():
    payload = get_json_payload()
    try:
        latitude = float(payload.get("latitude"))
        longitude = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid latitude and longitude are required."}), 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return jsonify({"error": "Coordinates are out of range."}), 400

    with get_db().cursor() as cursor:
        role = normalize_role(g.user.get("role"))
        if role == "buyer":
            cursor.execute("UPDATE buyer_profile SET latitude = %s, longitude = %s WHERE user_id = %s", (latitude, longitude, g.user["user_id"]))
        elif role == "seller":
            cursor.execute("SELECT seller_id FROM seller_profile WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
            seller = cursor.fetchone()
            if not seller:
                return jsonify({"error": "Seller profile not found."}), 404
            cursor.execute("UPDATE seller_profile SET latitude = %s, longitude = %s WHERE seller_id = %s", (latitude, longitude, seller["seller_id"]))
            cursor.execute("UPDATE animals SET latitude = %s, longitude = %s WHERE seller_id = %s", (latitude, longitude, seller["seller_id"]))
        else:
            return jsonify({"error": "Only buyers and sellers can save locations."}), 403
    return jsonify({"saved": True, "latitude": latitude, "longitude": longitude})


@app.route("/payment/create/<int:order_id>", methods=["POST"])
@login_required
def create_payment(order_id):
    if normalize_role(g.user.get("role")) != "buyer":
        return jsonify({"error": "Only buyers can create payments."}), 403
    if not app.config.get("RAZORPAY_KEY_ID") or not app.config.get("RAZORPAY_KEY_SECRET"):
        return jsonify({"error": "Payment gateway is not configured."}), 503
    try:
        import razorpay
    except ImportError:
        return jsonify({"error": "Razorpay dependency is not installed."}), 503

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT o.*, sp.razorpay_linked_account_id
                   FROM orders o JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id
                   LEFT JOIN seller_profile sp ON sp.seller_id = o.seller_id
                   WHERE o.order_id = %s AND bp.user_id = %s
                     AND o.order_status IN ('Pending', 'Confirmed') LIMIT 1 FOR UPDATE""",
                (order_id, g.user["user_id"]),
            )
            order = cursor.fetchone()
            if not order:
                abort(404)
            if order["payment_status"] == "Paid":
                return jsonify({"error": "This order has already been paid."}), 409
            try:
                amounts = calculate_commissions(order["price"])
            except (InvalidOperation, ValueError):
                return jsonify({"error": "The order price is invalid."}), 500
            cursor.execute(
                """UPDATE orders SET base_amount = %s, buyer_commission_percent = %s,
                   buyer_commission_amount = %s, seller_commission_percent = %s,
                   seller_commission_amount = %s, buyer_payable_amount = %s,
                   seller_payout_amount = %s, admin_gross_commission = %s
                   WHERE order_id = %s""",
                (*amounts.values(), order_id),
            )
            cursor.execute("SELECT * FROM payments WHERE order_id = %s ORDER BY payment_id DESC LIMIT 1 FOR UPDATE", (order_id,))
            payment = cursor.fetchone()
            if not payment:
                cursor.execute(
                    "INSERT INTO payments (order_id, amount, payment_method, transfer_status, refund_status) VALUES (%s, %s, %s, 'NOT_READY', 'NOT_REQUIRED')",
                    (order_id, amounts["buyer_payable_amount"], "Razorpay"),
                )
                payment = {"payment_id": cursor.lastrowid, "razorpay_order_id": None, "payment_status": "Pending"}
            elif payment["payment_status"] == "Paid":
                return jsonify({"error": "This order has already been paid."}), 409
            gateway_order = None
            if payment.get("razorpay_order_id") and payment["payment_status"] == "Pending" and money(payment["amount"]) == amounts["buyer_payable_amount"]:
                gateway_order = {"id": payment["razorpay_order_id"], "amount": money_paise(amounts["buyer_payable_amount"]), "currency": "INR"}
            else:
                client = razorpay.Client(auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"]))
                gateway_order = client.order.create({"amount": money_paise(amounts["buyer_payable_amount"]), "currency": "INR", "receipt": f"livestock-order-{order_id}"})
                cursor.execute("UPDATE payments SET razorpay_order_id = %s, amount = %s, payment_status = 'Pending', failure_reason = NULL WHERE payment_id = %s", (gateway_order["id"], amounts["buyer_payable_amount"], payment["payment_id"]))
            db.commit()
    except Exception:
        db.rollback()
        raise
    checkout = {"key_id": app.config["RAZORPAY_KEY_ID"], "gateway_order_id": gateway_order["id"], "amount": gateway_order["amount"], "currency": gateway_order["currency"]}
    checkout.update(serialize_money_fields({"base_amount": amounts["base_amount"], "buyer_commission": amounts["buyer_commission_amount"], "buyer_payable": amounts["buyer_payable_amount"]}))
    return jsonify(checkout)


@app.route("/payment/verify", methods=["POST"])
@login_required
def verify_payment():
    payload = get_json_payload()
    required = {"razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "order_id"}
    if not required.issubset(payload):
        return jsonify({"error": "Incomplete payment response."}), 400
    if not app.config.get("RAZORPAY_KEY_SECRET"):
        return jsonify({"error": "Payment gateway is not configured."}), 503
    try:
        internal_order_id = int(payload["order_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid order ID."}), 400
    try:
        import razorpay
        client = razorpay.Client(auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"]))
        signature_data = {"razorpay_order_id": payload["razorpay_order_id"], "razorpay_payment_id": payload["razorpay_payment_id"], "razorpay_signature": payload["razorpay_signature"]}
        client.utility.verify_payment_signature(signature_data)
        gateway_payment = client.payment.fetch(payload["razorpay_payment_id"])
    except Exception:
        app.logger.exception("Razorpay payment verification failed")
        return jsonify({"error": "Payment verification failed."}), 400

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """SELECT p.*, o.order_id, o.buyer_id, o.buyer_payable_amount
                   FROM payments p JOIN orders o ON o.order_id = p.order_id
                   JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id
                   WHERE o.order_id = %s AND bp.user_id = %s LIMIT 1 FOR UPDATE""",
                (internal_order_id, g.user["user_id"]),
            )
            payment = cursor.fetchone()
            if not payment:
                abort(404)
            if payment["razorpay_order_id"] != payload["razorpay_order_id"]:
                return jsonify({"error": "Razorpay order does not match."}), 400
            if payment["payment_status"] == "Paid":
                if payment["razorpay_payment_id"] == payload["razorpay_payment_id"]:
                    return jsonify({"verified": True, "duplicate": True})
                return jsonify({"error": "This order has already been paid."}), 409
            cursor.execute("SELECT payment_id FROM payments WHERE razorpay_payment_id = %s LIMIT 1 FOR UPDATE", (payload["razorpay_payment_id"],))
            if cursor.fetchone():
                return jsonify({"error": "This payment has already been processed."}), 409
            expected_paise = money_paise(payment["buyer_payable_amount"])
            if int(gateway_payment.get("amount", -1)) != expected_paise or gateway_payment.get("status") != "captured":
                return jsonify({"error": "Payment amount or capture status is invalid."}), 400
            cursor.execute(
                "UPDATE payments SET payment_status = 'Paid', razorpay_payment_id = %s, captured_at = CURRENT_TIMESTAMP, failure_reason = NULL WHERE payment_id = %s",
                (payload["razorpay_payment_id"], payment["payment_id"]),
            )
            cursor.execute("UPDATE orders SET payment_status = 'Paid', order_status = 'Confirmed' WHERE order_id = %s", (internal_order_id,))
            db.commit()
    except Exception:
        db.rollback()
        raise
    transfer_status = create_seller_transfer(internal_order_id)
    return jsonify({"verified": True, "transfer_status": transfer_status})


def create_seller_transfer(order_id):
    """Create at most one Route transfer, or leave it explicitly not ready."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """SELECT p.payment_id, p.transfer_status, p.razorpay_transfer_id,
                      p.seller_payout_amount, o.seller_id, sp.razorpay_linked_account_id
               FROM payments p JOIN orders o ON o.order_id = p.order_id
               LEFT JOIN seller_profile sp ON sp.seller_id = o.seller_id
               WHERE p.order_id = %s AND p.payment_status = 'Paid'
               ORDER BY p.payment_id DESC LIMIT 1 FOR UPDATE""",
            (order_id,),
        )
        payment = cursor.fetchone()
        if not payment:
            return "NOT_READY"
        if payment["transfer_status"] == "SUCCESS" or payment["razorpay_transfer_id"]:
            return "SUCCESS"
        if payment["transfer_status"] == "PENDING":
            return "PENDING"
        if not app.config.get("RAZORPAY_ROUTE_ENABLED") or not payment["razorpay_linked_account_id"]:
            cursor.execute("UPDATE payments SET transfer_status = 'NOT_READY' WHERE payment_id = %s", (payment["payment_id"],))
            db.commit()
            return "NOT_READY"
        cursor.execute("UPDATE payments SET transfer_status = 'PENDING' WHERE payment_id = %s", (payment["payment_id"],))
        db.commit()
    try:
        import razorpay
        client = razorpay.Client(auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"]))
        transfer = client.transfer.create({
            "account": payment["razorpay_linked_account_id"],
            "amount": money_paise(payment["seller_payout_amount"]),
            "currency": "INR",
            "notes": {"order_id": str(order_id)},
        })
    except Exception as error:
        with db.cursor() as cursor:
            cursor.execute("UPDATE payments SET transfer_status = 'FAILED', failure_reason = %s WHERE payment_id = %s AND transfer_status = 'PENDING'", (str(error)[:500], payment["payment_id"]))
            db.commit()
        app.logger.exception("Razorpay seller transfer failed")
        return "FAILED"
    with db.cursor() as cursor:
        cursor.execute("UPDATE payments SET transfer_status = 'SUCCESS', razorpay_transfer_id = %s, failure_reason = NULL WHERE payment_id = %s AND transfer_status = 'PENDING'", (transfer["id"], payment["payment_id"]))
        db.commit()
    return "SUCCESS"


def _webhook_entity(payload, entity_type):
    return payload.get("payload", {}).get(entity_type, {}).get("entity", {})


@app.route("/webhooks/razorpay", methods=["POST"])
def razorpay_webhook():
    secret = app.config.get("RAZORPAY_WEBHOOK_SECRET")
    signature = request.headers.get("X-Razorpay-Signature", "")
    raw_body = request.get_data()
    if not secret or not signature:
        return jsonify({"error": "Webhook is not configured."}), 503
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({"error": "Invalid webhook signature."}), 400
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid webhook payload."}), 400
    event_id = request.headers.get("X-Razorpay-Event-Id") or payload.get("event_id") or hashlib.sha256(raw_body).hexdigest()
    event_type = payload.get("event", "")
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO razorpay_webhook_events (event_id, event_type, payload_hash) VALUES (%s, %s, %s)", (event_id, event_type, hashlib.sha256(raw_body).hexdigest()))
            payment_entity = _webhook_entity(payload, "payment")
            transfer_entity = _webhook_entity(payload, "transfer")
            refund_entity = _webhook_entity(payload, "refund")
            gateway_payment_id = payment_entity.get("id")
            gateway_transfer_id = transfer_entity.get("id")
            gateway_refund_payment_id = refund_entity.get("payment_id")
            if event_type in {"payment.captured", "payment.failed"} and gateway_payment_id:
                status = "Paid" if event_type == "payment.captured" else "Failed"
                cursor.execute("SELECT payment_id, order_id, amount FROM payments WHERE razorpay_payment_id = %s OR razorpay_order_id = %s LIMIT 1 FOR UPDATE", (gateway_payment_id, payment_entity.get("order_id", "")))
                payment = cursor.fetchone()
                if payment and status == "Paid" and int(payment_entity.get("amount", -1)) == money_paise(payment["amount"]):
                    cursor.execute("UPDATE payments SET payment_status = 'Paid', razorpay_payment_id = %s, captured_at = CURRENT_TIMESTAMP, webhook_last_event_id = %s WHERE payment_id = %s AND payment_status <> 'Paid'", (gateway_payment_id, event_id, payment["payment_id"]))
                    cursor.execute("UPDATE orders SET payment_status = 'Paid', order_status = 'Confirmed' WHERE order_id = %s", (payment["order_id"],))
                elif payment and status == "Failed":
                    cursor.execute("UPDATE payments SET payment_status = 'Failed', failure_reason = %s, webhook_last_event_id = %s WHERE payment_id = %s AND payment_status = 'Pending'", (payment_entity.get("error_description", "Payment failed")[:500], event_id, payment["payment_id"]))
            elif event_type in {"transfer.processed", "transfer.failed"} and gateway_transfer_id:
                status = "SUCCESS" if event_type == "transfer.processed" else "FAILED"
                cursor.execute("UPDATE payments SET transfer_status = %s, razorpay_transfer_id = %s, webhook_last_event_id = %s WHERE razorpay_transfer_id = %s OR (razorpay_transfer_id IS NULL AND transfer_status = 'PENDING' AND order_id = %s)", (status, gateway_transfer_id, event_id, gateway_transfer_id, transfer_entity.get("notes", {}).get("order_id", -1)))
            elif event_type in {"refund.processed", "refund.failed"} and gateway_refund_payment_id:
                refund_status = "SUCCESS" if event_type == "refund.processed" else "FAILED"
                cursor.execute("UPDATE payments SET refund_status = %s, payment_status = %s, webhook_last_event_id = %s WHERE razorpay_payment_id = %s", (refund_status, "Refunded" if refund_status == "SUCCESS" else "Paid", event_id, gateway_refund_payment_id))
            db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()
        return jsonify({"received": True, "duplicate": True})
    except Exception:
        db.rollback()
        app.logger.exception("Razorpay webhook processing failed")
        return jsonify({"error": "Webhook processing failed."}), 500
    if event_type == "payment.captured" and gateway_payment_id:
        with db.cursor() as cursor:
            cursor.execute("SELECT order_id FROM payments WHERE razorpay_payment_id = %s LIMIT 1", (gateway_payment_id,))
            captured = cursor.fetchone()
        if captured:
            create_seller_transfer(captured["order_id"])
    return jsonify({"received": True})


@app.route("/payment/refund/<int:order_id>", methods=["POST"])
@admin_required
def refund_payment(order_id):
    if not app.config.get("RAZORPAY_KEY_SECRET"):
        return jsonify({"error": "Payment gateway is not configured."}), 503
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT p.*, o.animal_id FROM payments p JOIN orders o ON o.order_id = p.order_id WHERE p.order_id = %s AND p.payment_status = 'Paid' ORDER BY p.payment_id DESC LIMIT 1 FOR UPDATE", (order_id,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({"error": "A captured payment was not found."}), 404
        if payment["transfer_status"] == "SUCCESS":
            cursor.execute("UPDATE payments SET refund_status = 'PENDING' WHERE payment_id = %s", (payment["payment_id"],))
            db.commit()
            return jsonify({"error": "Seller transfer reversal requires manual Razorpay review.", "refund_status": "PENDING"}), 409
        if payment["refund_status"] == "SUCCESS" or payment["payment_status"] == "Refunded":
            return jsonify({"refunded": True, "duplicate": True}), 200
        if payment["refund_status"] == "PENDING":
            return jsonify({"refund_status": "PENDING"}), 202
        cursor.execute("UPDATE payments SET refund_status = 'PENDING', refund_amount = %s WHERE payment_id = %s", (payment["amount"], payment["payment_id"]))
        db.commit()
    try:
        import razorpay
        client = razorpay.Client(auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"]))
        client.payment.refund(payment["razorpay_payment_id"], {"amount": money_paise(payment["amount"])})
    except Exception as error:
        with db.cursor() as cursor:
            cursor.execute("UPDATE payments SET refund_status = 'FAILED', failure_reason = %s WHERE payment_id = %s AND refund_status = 'PENDING'", (str(error)[:500], payment["payment_id"]))
            db.commit()
        return jsonify({"error": "Refund request failed."}), 502
    with db.cursor() as cursor:
        cursor.execute("UPDATE payments SET refund_status = 'SUCCESS', payment_status = 'Refunded' WHERE payment_id = %s AND refund_status = 'PENDING'", (payment["payment_id"],))
        cursor.execute("UPDATE orders SET payment_status = 'Refunded', order_status = 'Cancelled' WHERE order_id = %s", (order_id,))
        cursor.execute("UPDATE animals SET availability = 'Available' WHERE animal_id = %s AND availability = 'Reserved'", (payment["animal_id"],))
        db.commit()
    return jsonify({"refunded": True, "amount": str(payment["amount"])})


def send_password_reset_email(email, reset_link):
    """Send reset mail through SMTP; development falls back to application logs."""
    host = app.config.get("MAIL_SERVER")
    if not host:
        app.logger.warning("SMTP is not configured; reset link for %s: %s", email, reset_link)
        return

    message = EmailMessage()
    message["Subject"] = "Reset your LivestockAI password"
    message["From"] = app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = email
    message.set_content(
        f"Use this link to reset your LivestockAI password. It expires in one hour:\n\n{reset_link}"
    )
    with smtplib.SMTP(host, app.config["MAIL_PORT"], timeout=15) as smtp:
        if app.config.get("MAIL_USE_TLS"):
            smtp.starttls()
        if app.config.get("MAIL_USERNAME"):
            smtp.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
        smtp.send_message(message)


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")
PASSWORD_RESET_OTP_SESSION_KEY = "password_reset_otp"
PASSWORD_RESET_OTP_TTL_SECONDS = 300
PASSWORD_RESET_OTP_RESEND_SECONDS = 60
PASSWORD_RESET_OTP_MAX_ATTEMPTS = 5


def normalize_phone_number(value):
    phone = re.sub(r"[\s().-]", "", (value or "").strip())
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    elif not phone.startswith("+"):
        default_country_code = app.config.get("PHONE_DEFAULT_COUNTRY_CODE", "91").lstrip("+")
        if len(phone) == 10:
            phone = f"+{default_country_code}{phone}"
        elif len(phone) == 11 and phone.startswith("0"):
            phone = f"+{default_country_code}{phone[1:]}"
        else:
            phone = "+" + phone
    return phone if PHONE_PATTERN.fullmatch(phone) else None


def password_validation_error(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    if not any(character.isalpha() for character in password) or not any(character.isdigit() for character in password):
        return "Password must include at least one letter and one number."
    return None


def is_valid_email(email):
    return len(email) <= 254 and EMAIL_PATTERN.fullmatch(email) is not None


def password_reset_otp_hash(user_id, phone, nonce, otp):
    payload = f"{nonce}:{user_id or ''}:{phone}:{otp}".encode()
    return hmac.new(app.secret_key.encode(), payload, hashlib.sha256).hexdigest()


def twilio_sms_configured():
    return bool(
        app.config.get("TWILIO_ACCOUNT_SID")
        and app.config.get("TWILIO_AUTH_TOKEN")
        and (app.config.get("TWILIO_FROM_NUMBER") or app.config.get("TWILIO_MESSAGING_SERVICE_SID"))
    )


def local_password_reset_debug_enabled():
    return app.config.get("PASSWORD_RESET_DEBUG_OTP", False) and request.remote_addr in {"127.0.0.1", "::1"}


def send_password_reset_otp(phone, otp):
    account_sid = app.config["TWILIO_ACCOUNT_SID"]
    auth_token = app.config["TWILIO_AUTH_TOKEN"]
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    message = {
        "To": phone,
        "Body": f"Your LivestockAI password reset code is {otp}. It expires in 5 minutes.",
    }
    messaging_service_sid = app.config.get("TWILIO_MESSAGING_SERVICE_SID")
    if messaging_service_sid:
        message["MessagingServiceSid"] = messaging_service_sid
    else:
        message["From"] = app.config["TWILIO_FROM_NUMBER"]
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    request = Request(
        endpoint,
        data=urlencode(message).encode(),
        headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError("SMS provider rejected the reset code.")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_page = request.args.get("next") or request.form.get("next") or url_for("profile")
        error = None

        remember = request.form.get("remember") == "on"
        if not email or not password:
            error = "Please enter both email and password."
        elif not is_valid_email(email):
            error = "Enter a valid email address."
        else:
            with get_db().cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (email,))
                user = cursor.fetchone()
                password_hash = user.get("password_hash") if user else None
                if user is None or not password_hash or not check_password_hash(password_hash, password):
                    error = "Invalid email or password."
                else:
                    session.clear()
                    session["user_id"] = user["user_id"]
                    session.permanent = remember
                    with get_db().cursor() as history_cursor:
                        history_cursor.execute(
                            "INSERT INTO login_history (user_id, ip_address, device, browser) VALUES (%s, %s, %s, %s)",
                            (user["user_id"], request.remote_addr, request.user_agent.platform, request.user_agent.browser),
                        )
                        session["login_id"] = history_cursor.lastrowid
                    flash("Logged in successfully.", "success")
                    if is_safe_url(next_page):
                        return redirect(next_page)
                    return redirect(url_for("profile"))

        flash(error or "Login failed.", "danger")
        return redirect(url_for("login", next=next_page))

    return render_template("login.html", next=request.args.get("next", ""), active_page="login")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    otp_pending = bool(session.get(PASSWORD_RESET_OTP_SESSION_KEY))
    otp_phone = ""
    phone_value = request.form.get("phone", "").strip()
    if request.method == "POST":
        action = request.form.get("action", "send_otp")
        if action == "send_otp":
            phone = normalize_phone_number(request.form.get("phone", ""))
            if not phone:
                flash("Enter a valid phone number with country code, such as +919876543210.", "danger")
            elif not twilio_sms_configured() and not local_password_reset_debug_enabled():
                flash("Mobile password reset is not configured. Please contact the site administrator.", "danger")
            else:
                phone_value = phone
                now = time.time()
                previous = session.get(PASSWORD_RESET_OTP_SESSION_KEY, {})
                if previous.get("phone") == phone and now - previous.get("sent_at", 0) < PASSWORD_RESET_OTP_RESEND_SECONDS:
                    otp_pending = True
                    otp_phone = f"ending in {phone[-4:]}"
                    flash("Please wait before requesting another code.", "warning")
                else:
                    compact_phone = "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(phone, ' ', ''), '-', ''), '(', ''), ')', ''), '.', '')"
                    phone_candidates = [phone]
                    country_code = app.config.get("PHONE_DEFAULT_COUNTRY_CODE", "91").lstrip("+")
                    legacy_local_phone = phone[1 + len(country_code):]
                    if phone.startswith(f"+{country_code}") and len(legacy_local_phone) == 10:
                        phone_candidates.append(legacy_local_phone)
                    phone_predicate = " OR ".join(f"{compact_phone} = %s" for _ in phone_candidates)
                    with get_db().cursor() as cursor:
                        cursor.execute(f"SELECT user_id FROM users WHERE ({phone_predicate}) LIMIT 1", phone_candidates)
                        user = cursor.fetchone()
                    user_id = user.get("user_id") if user else None
                    otp = f"{secrets.randbelow(1_000_000):06d}"
                    nonce = secrets.token_urlsafe(18)
                    session[PASSWORD_RESET_OTP_SESSION_KEY] = {
                        "user_id": user_id,
                        "phone": phone,
                        "nonce": nonce,
                        "otp_hash": password_reset_otp_hash(user_id, phone, nonce, otp),
                        "expires_at": now + PASSWORD_RESET_OTP_TTL_SECONDS,
                        "sent_at": now,
                        "attempts": 0,
                    }
                    if user_id is not None:
                        try:
                            if twilio_sms_configured():
                                send_password_reset_otp(phone, otp)
                            else:
                                app.logger.warning(
                                    "Development password reset code for phone ending in %s: %s",
                                    phone[-4:],
                                    otp,
                                )
                        except Exception:
                            session.pop(PASSWORD_RESET_OTP_SESSION_KEY, None)
                            app.logger.exception("Unable to send password reset OTP")
                            flash("Could not send a reset code right now. Please try again later.", "danger")
                        else:
                            otp_pending = True
                            otp_phone = f"ending in {phone[-4:]}"
                            if twilio_sms_configured():
                                flash("If an account is linked to that number, a reset code has been sent.", "success")
                            else:
                                flash("Development reset code logged to the server console.", "success")
                    else:
                        otp_pending = True
                        otp_phone = f"ending in {phone[-4:]}"
                        flash("If an account is linked to that number, a reset code has been sent.", "success")
        elif action == "reset_password":
            state = session.get(PASSWORD_RESET_OTP_SESSION_KEY)
            otp_pending = bool(state)
            if not state or state.get("expires_at", 0) < time.time():
                session.pop(PASSWORD_RESET_OTP_SESSION_KEY, None)
                otp_pending = False
                flash("That reset code has expired. Request a new code.", "danger")
            elif state.get("attempts", 0) >= PASSWORD_RESET_OTP_MAX_ATTEMPTS:
                session.pop(PASSWORD_RESET_OTP_SESSION_KEY, None)
                otp_pending = False
                flash("Too many incorrect attempts. Request a new code.", "danger")
            else:
                otp_phone = f"ending in {state['phone'][-4:]}"
                phone_value = state["phone"]
                state["attempts"] += 1
                session[PASSWORD_RESET_OTP_SESSION_KEY] = state
                otp = request.form.get("otp", "").strip()
                expected = password_reset_otp_hash(state.get("user_id"), state["phone"], state["nonce"], otp)
                if state.get("user_id") is None or not re.fullmatch(r"\d{6}", otp) or not hmac.compare_digest(state["otp_hash"], expected):
                    if state["attempts"] >= PASSWORD_RESET_OTP_MAX_ATTEMPTS:
                        session.pop(PASSWORD_RESET_OTP_SESSION_KEY, None)
                        otp_pending = False
                        flash("Too many incorrect attempts. Request a new code.", "danger")
                    else:
                        flash("The reset code is invalid. Please check it and try again.", "danger")
                else:
                    password = request.form.get("password", "")
                    confirm_password = request.form.get("confirm_password", "")
                    error = password_validation_error(password)
                    if error:
                        flash(error, "danger")
                    elif password != confirm_password:
                        flash("Passwords do not match.", "danger")
                    else:
                        with get_db().cursor() as cursor:
                            cursor.execute(
                                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                                (generate_password_hash(password), state["user_id"]),
                            )
                        session.pop(PASSWORD_RESET_OTP_SESSION_KEY, None)
                        flash("Your password has been reset. You can now log in.", "success")
                        return redirect(url_for("login"))
        else:
            flash("Choose a valid password-reset action.", "danger")

    state = session.get(PASSWORD_RESET_OTP_SESSION_KEY, {})
    otp_pending = otp_pending and state.get("expires_at", 0) >= time.time()
    if otp_pending and not otp_phone:
        otp_phone = f"ending in {state.get('phone', '')[-4:]}"
        phone_value = state.get("phone", phone_value)
    return render_template("forgot_password.html", active_page="login", otp_pending=otp_pending, otp_phone=otp_phone, phone_value=phone_value)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email, err = confirm_password_reset_token(token)
    if err == "expired":
        flash("The reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("forgot_password"))
    if err == "invalid" or email is None:
        flash("Invalid password reset link.", "danger")
        return redirect(url_for("forgot_password"))

    role = "buyer"

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        error = password_validation_error(password)
        if error:
            flash(error, "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        else:
            try:
                with get_db().cursor() as cursor:
                    cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (generate_password_hash(password), email))
                flash("Your password has been reset. You can now log in.", "success")
                return redirect(url_for("login"))
            except Exception as e:
                app.logger.exception("Failed to reset password: %s", e)
                flash("An error occurred while resetting your password.", "danger")

    return render_template("reset_password.html", email=email, token=token, active_page="login")


@app.route("/register", methods=["GET", "POST"])
def register():
    role = "buyer"

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone_input = request.form.get("phone", "").strip()
        phone = normalize_phone_number(phone_input)
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = (request.form.get("role", "buyer") or "buyer").strip().lower()
        next_page = request.args.get("next") or request.form.get("next") or url_for("profile")
        error = None

        if not all([full_name, email, phone_input, password, confirm_password]):
            error = "Please fill in all required fields."
        elif len(full_name) > 100:
            error = "Name must be 100 characters or fewer."
        elif not is_valid_email(email):
            error = "Enter a valid email address."
        elif not phone:
            error = "Enter a valid phone number with 8 to 15 digits."
        elif role not in {"buyer", "seller", "user", "admin"}:
            error = "Choose a valid account type."
        elif password_validation_error(password):
            error = password_validation_error(password)
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            with get_db().cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE email = %s LIMIT 1", (email,))
                if cursor.fetchone():
                    error = "An account already exists with that email."
                else:
                    allowed_roles = {"buyer": "Buyer", "seller": "Seller", "user": "Buyer", "admin": "Admin"}
                    role_name = allowed_roles.get(role, "Buyer")
                    if role == "admin":
                        admin_code = request.form.get("admin_code", "").strip()
                        expected = app.config.get("ADMIN_SIGNUP_CODE", "")
                        if not expected:
                            error = "Admin signups are disabled. Contact the site administrator."
                        elif admin_code != expected:
                            error = "Invalid admin code provided."
                        if error:
                            flash(error, "danger")
                            return redirect(url_for("register", next=next_page))
                    cursor.execute(
                        "INSERT INTO users (full_name, email, phone, profile_image, role, password_hash) VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            full_name,
                            email,
                            phone,
                            "/static/images/avatar-1.svg",
                            role_name,
                            generate_password_hash(password),
                        ),
                    )
                    user_id = cursor.lastrowid
                    if role_name == "Seller":
                        cursor.execute(
                            "INSERT INTO seller_profile (user_id, shop_name, address, city, state, country, verified, rating, total_animals) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (user_id, full_name, "", "Ahmedabad", "Gujarat", "India", 1, 4.8, 0),
                        )
                    elif role_name == "Buyer":
                        cursor.execute(
                            "INSERT INTO buyer_profile (user_id, city, state, country) VALUES (%s, %s, %s, %s)",
                            (user_id, "Ahmedabad", "Gujarat", "India"),
                        )
                    session.clear()
                    session["user_id"] = user_id
                    flash("Account created successfully.", "success")
                    if is_safe_url(next_page):
                        return redirect(next_page)
                    return redirect(url_for("profile"))

        flash(error or "Registration failed.", "danger")
        return redirect(url_for("register", next=next_page))

    return render_template("register.html", next=request.args.get("next", ""), active_page="register")


@app.route("/logout")
def logout():
    if session.get("login_id"):
        with get_db().cursor() as cursor:
            cursor.execute("UPDATE login_history SET logout_time = CURRENT_TIMESTAMP WHERE login_id = %s", (session["login_id"],))
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/")
def index():
    db = get_db()
    with db.cursor() as cursor:
        categories = fetch_category_choices(cursor)
        breed_options = fetch_breed_options(cursor, categories)

        cursor.execute(
            "SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image FROM animals a ORDER BY a.animal_id DESC LIMIT 6"
        )
        featured_animals = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM animals WHERE availability = 'Available'")
        active_listings = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM seller_profile WHERE verified = 1")
        verified_sellers = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM orders WHERE order_status IN ('Confirmed', 'Completed')")
        successful_deals = cursor.fetchone()["total"]
        statistics = [
            {"statistic_id": 1, "stat_label": "Animals Listed", "stat_value": active_listings, "stat_suffix": "+", "icon": "fa-cow"},
            {"statistic_id": 2, "stat_label": "Verified Sellers", "stat_value": verified_sellers, "stat_suffix": "+", "icon": "fa-users"},
            {"statistic_id": 3, "stat_label": "Successful Deals", "stat_value": successful_deals, "stat_suffix": "+", "icon": "fa-handshake"},
            {"statistic_id": 4, "stat_label": "AI Support", "stat_value": "24", "stat_suffix": "/7", "icon": "fa-shield-heart"},
        ]
        testimonials = get_testimonials()

    return render_template(
        "index.html",
        categories=categories,
        breed_options=breed_options,
        featured_animals=featured_animals,
        statistics=statistics,
        testimonials=testimonials,
        active_page="home",
    )


@app.route("/animals")
def animals():
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 12
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", "").strip()
    breed = request.args.get("breed", "").strip()
    gender = request.args.get("gender", "")
    vaccinated = request.args.get("vaccinated", "")
    sort = request.args.get("sort", "latest")

    where_clauses = ["a.animal_type IN ('Cow', 'Dog', 'Cat', 'Horse')"]
    params = []

    if search:
        where_clauses.append("(a.animal_type LIKE %s OR a.breed LIKE %s OR a.city LIKE %s OR a.state LIKE %s OR a.description LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like, like, like])

    if breed:
        where_clauses.append("a.breed LIKE %s")
        params.append(f"%{breed}%")

    if gender in {"Male", "Female", "Other"}:
        where_clauses.append("a.gender = %s")
        params.append(gender)

    if vaccinated in {"Yes", "No"}:
        where_clauses.append("a.vaccinated = %s")
        params.append(vaccinated)

    db = get_db()
    with db.cursor() as cursor:
        categories = fetch_category_choices(cursor)
        breed_options = fetch_breed_options(cursor, categories)

        # Handle category filter BEFORE building where_sql
        if category_id.isdigit():
            category_id_value = int(category_id)
            category_choices = fetch_category_choices(cursor)
            selected_category = next((row for row in category_choices if row["category_id"] == category_id_value), None)
            if selected_category:
                where_clauses.append("a.animal_type = %s")
                params.append(selected_category["category_name"])

        # Build where_sql AFTER all filters are added
        where_sql = " AND ".join(where_clauses)

        order_sql = "a.animal_id DESC"
        if sort == "price_low":
            order_sql = "a.price ASC"
        elif sort == "price_high":
            order_sql = "a.price DESC"
        elif sort == "oldest":
            order_sql = "a.animal_id ASC"

        cursor.execute(f"SELECT COUNT(*) AS total FROM animals a WHERE {where_sql}", params)
        total = cursor.fetchone()["total"]

        total_pages = max(ceil(total / per_page), 1)
        page = min(page, total_pages)
        offset = (page - 1) * per_page

        cursor.execute(
            f"""
            SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image
            FROM animals a
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset],
        )
        items = cursor.fetchall()

    return render_template(
        "animals.html",
        animals=items,
        categories=categories,
        breed_options=breed_options,
        active_page="animals",
        search=search,
        category_id=category_id,
        breed=breed,
        gender=gender,
        vaccinated=vaccinated,
        sort=sort,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page,
    )


@app.route("/api/animals")
def api_animals():
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT animal_id, CONCAT(animal_type, ' ', breed) AS animal_name, breed, price, city, state, image_url AS image FROM animals ORDER BY animal_id DESC LIMIT 6"
        )
        return jsonify(cursor.fetchall())


@app.route("/animal/<int:animal_id>")
def animal_detail(animal_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image, u.full_name AS seller_name, u.phone AS seller_phone FROM animals a LEFT JOIN seller_profile sp ON sp.seller_id = a.seller_id LEFT JOIN users u ON u.user_id = sp.user_id WHERE a.animal_id = %s LIMIT 1",
            (animal_id,),
        )
        animal = cursor.fetchone()
        if not animal:
            abort(404)

        cursor.execute(
            "SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image FROM animals a WHERE a.animal_type = %s AND a.animal_id <> %s ORDER BY a.animal_id DESC LIMIT 3",
            (animal["animal_type"], animal_id),
        )
        related_animals = cursor.fetchall()

    return render_template(
        "animal_details.html",
        animal=animal,
        related_animals=related_animals,
        active_page="animals",
    )


@app.route("/animal/<int:animal_id>/buy", methods=["POST"])
@login_required
def buy_animal(animal_id):
    if normalize_role(g.user.get("role")) != "buyer":
        flash("Only buyer accounts can place purchase requests.", "danger")
        return redirect(url_for("animal_detail", animal_id=animal_id))

    with get_db().cursor() as cursor:
        cursor.execute("SELECT buyer_id FROM buyer_profile WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
        buyer = cursor.fetchone()
        cursor.execute(
            "SELECT animal_id, seller_id, price, availability FROM animals WHERE animal_id = %s LIMIT 1",
            (animal_id,),
        )
        animal = cursor.fetchone()
        if not buyer or not animal:
            abort(404)
        if animal["availability"] != "Available":
            flash("This animal is no longer available.", "warning")
            return redirect(url_for("animal_detail", animal_id=animal_id))

        amounts = calculate_commissions(animal["price"])
        cursor.execute(
            """INSERT INTO orders (
                buyer_id, seller_id, animal_id, price, base_amount,
                buyer_commission_percent, buyer_commission_amount,
                seller_commission_percent, seller_commission_amount,
                buyer_payable_amount, seller_payout_amount, admin_gross_commission
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                buyer["buyer_id"], animal["seller_id"], animal_id, animal["price"],
                amounts["base_amount"], amounts["buyer_commission_percent"],
                amounts["buyer_commission_amount"], amounts["seller_commission_percent"],
                amounts["seller_commission_amount"], amounts["buyer_payable_amount"],
                amounts["seller_payout_amount"], amounts["admin_gross_commission"],
            ),
        )
        cursor.execute("UPDATE animals SET availability = 'Reserved' WHERE animal_id = %s", (animal_id,))
    flash("Purchase request sent to the seller.", "success")
    return redirect(url_for("buyer_dashboard"))


@app.route("/animal/<int:animal_id>/inquire", methods=["POST"])
@login_required
def inquire_about_animal(animal_id):
    if normalize_role(g.user.get("role")) != "buyer":
        flash("Only buyer accounts can contact sellers.", "danger")
        return redirect(url_for("animal_detail", animal_id=animal_id))
    message = request.form.get("message", "").strip()
    if not message:
        flash("Please write a message before contacting the seller.", "warning")
        return redirect(url_for("animal_detail", animal_id=animal_id))

    with get_db().cursor() as cursor:
        cursor.execute("SELECT buyer_id FROM buyer_profile WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
        buyer = cursor.fetchone()
        cursor.execute("SELECT seller_id FROM animals WHERE animal_id = %s LIMIT 1", (animal_id,))
        animal = cursor.fetchone()
        if not buyer or not animal:
            abort(404)
        cursor.execute(
            "INSERT INTO inquiries (buyer_id, seller_id, animal_id, message) VALUES (%s, %s, %s, %s)",
            (buyer["buyer_id"], animal["seller_id"], animal_id, message),
        )
    flash("Your inquiry has been sent to the seller.", "success")
    return redirect(url_for("animal_detail", animal_id=animal_id))


@app.route("/sell-animal", methods=["GET", "POST"])
@login_required
def sell_animal():
    if normalize_role(g.user.get("role")) != "seller":
        flash("Only seller accounts can create animal listings.", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    with db.cursor() as cursor:
        categories = fetch_category_choices(cursor)

    if request.method == "POST":
        form = request.form
        animal_type = form.get("animal_type", "").strip()
        breed = form.get("breed", "").strip()
        age = form.get("age", "").strip()
        weight = form.get("weight", "").strip()
        gender = form.get("gender", "").strip()
        price = form.get("price", "").strip()
        city = form.get("city", "").strip()
        state = form.get("state", "").strip()
        color = form.get("color", "").strip()
        milk_yield = form.get("milk_yield", "").strip()
        description = form.get("description", "").strip()
        price_value = "".join(ch for ch in price if ch.isdigit() or ch == ".")

        if not all([animal_type, breed, age, weight, gender, price_value, city, state, description]):
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("sell_animal"))

        images = []
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        for file_storage in request.files.getlist("images"):
            if not file_storage or not file_storage.filename:
                continue
            if not allowed_image(file_storage.filename):
                flash("Only JPG, JPEG, PNG, WEBP or GIF images are allowed.", "danger")
                return redirect(url_for("sell_animal"))
            filename = f"{uuid.uuid4().hex}_{secure_filename(file_storage.filename)}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file_storage.save(file_path)
            images.append(f"/static/uploads/{filename}")

        if not images:
            flash("Please upload at least one animal image.", "danger")
            return redirect(url_for("sell_animal"))

        seller_id = get_current_seller_id()
        if seller_id is None:
            flash("Unable to associate your account with a seller profile.", "danger")
            return redirect(url_for("sell_animal"))

        with db.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO animals (
                    seller_id, animal_type, breed, age, weight, gender, price,
                    city, state, color, milk_yield, vaccinated, health_status, image_url, description
                    , latitude, longitude
                ) SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, latitude, longitude
                FROM seller_profile WHERE seller_id = %s
                """,
                (
                    seller_id,
                    animal_type,
                    breed,
                    age,
                    weight,
                    gender,
                    float(price_value or 0),
                    city,
                    state,
                    color,
                    milk_yield,
                    1,
                    "Healthy",
                    images[0],
                    description,
                    seller_id,
                ),
            )
            animal_id = cursor.lastrowid

            flash("Your animal listing has been submitted successfully.", "success")
            return redirect(url_for("animal_detail", animal_id=animal_id))

    return render_template("sell_animal.html", categories=categories, active_page="sell")


@app.route("/about-us")
def about_us():
    db = get_db()
    with db.cursor() as cursor:
        statistics = [
            {"statistic_id": 1, "label": "Active Listings", "value": "4+"},
            {"statistic_id": 2, "label": "Verified Sellers", "value": "1"},
            {"statistic_id": 3, "label": "AI Queries", "value": "Live"},
        ]
        testimonials = get_testimonials()
    return render_template("about_us.html", statistics=statistics, testimonials=testimonials, active_page="about")


@app.route("/contact-us", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        if not all([name, email, subject, message]):
            flash("Please complete all required fields.", "danger")
            return redirect(url_for("contact_us"))
        with get_db().cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
                (1, subject, f"Contact message from {name}: {message}"),
            )
        flash("Your message has been sent successfully.", "success")
        return redirect(url_for("contact_us"))
    return render_template("contact_us.html", active_page="contact")


@app.route("/wishlist")
@login_required
def wishlist():
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image
            FROM favorites f
            JOIN animals a ON a.animal_id = f.animal_id
            JOIN buyer_profile bp ON bp.buyer_id = f.buyer_id
            WHERE bp.user_id = %s
            ORDER BY f.created_at DESC
            """,
            (g.user["user_id"],),
        )
        wishlist_items = cursor.fetchall()
    return render_template("wishlist.html", wishlist_items=wishlist_items, active_page="wishlist")


@app.route("/profile")
@login_required
def profile():
    with get_db().cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM favorites f JOIN buyer_profile bp ON bp.buyer_id = f.buyer_id WHERE bp.user_id = %s", (g.user["user_id"],))
        wishlist_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM animals")
        animal_count = cursor.fetchone()["total"]
        profile_table = "buyer_profile" if normalize_role(g.user.get("role")) == "buyer" else "seller_profile"
        cursor.execute(f"SELECT city, state FROM {profile_table} WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
        location = cursor.fetchone() or {}
        g.user["location"] = ", ".join(value for value in (location.get("city"), location.get("state")) if value) or "Not set"
    return render_template("profile.html", user=g.user, wishlist_count=wishlist_count, animal_count=animal_count, active_page="profile")


@app.route("/wishlist/add/<int:animal_id>", methods=["POST"])
@login_required
def add_to_wishlist(animal_id):
    with get_db().cursor() as cursor:
        cursor.execute("SELECT buyer_id FROM buyer_profile WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
        buyer_row = cursor.fetchone()
        if buyer_row is None:
            flash("A buyer profile is required to save favorites.", "warning")
            return redirect(request.referrer or url_for("animals"))
        cursor.execute("SELECT favorite_id FROM favorites WHERE buyer_id = %s AND animal_id = %s LIMIT 1", (buyer_row["buyer_id"], animal_id))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO favorites (buyer_id, animal_id) VALUES (%s, %s)", (buyer_row["buyer_id"], animal_id))
            flash("Added to your wishlist.", "success")
        else:
            flash("This animal is already in your wishlist.", "info")
    return redirect(request.referrer or url_for("animals"))


@app.route("/wishlist/remove/<int:animal_id>", methods=["POST"])
@login_required
def remove_from_wishlist(animal_id):
    with get_db().cursor() as cursor:
        cursor.execute("SELECT buyer_id FROM buyer_profile WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
        buyer_row = cursor.fetchone()
        if buyer_row is not None:
            cursor.execute("DELETE FROM favorites WHERE buyer_id = %s AND animal_id = %s", (buyer_row["buyer_id"], animal_id))
    flash("Removed from your wishlist.", "success")
    return redirect(request.referrer or url_for("wishlist"))


def process_image_chat(question, image_bytes, mime_type, user_id):
    """Process image queries with animal domain validation.
    
    For image-based disease detection or animal identification:
    1. If a question is provided, validate it first
    2. Process the image if validation passes
    3. The image analysis restricts to supported animals (Cow, Dog, Cat, Horse)
    """
    assistant = get_ai_assistant()
    
    # If question is provided, validate it first
    if question and question.strip():
        chat_history = get_ai_history(user_id, limit=10)
        validation_status, restriction_message = validate_question_with_context(question, chat_history)
        
        # If validation failed, return restriction message
        if validation_status != "allowed":
            answer = restriction_message or "I couldn't process your question right now. Please try again."
            with get_db().cursor() as cursor:
                cursor.execute("INSERT INTO ai_chat_history (user_id, question, response) VALUES (%s, %s, %s)", (user_id, question, answer))
            return {
                "success": True,
                "intent": "RESTRICTED_IMAGE_QUERY",
                "message": answer,
                "answer": answer,
                "data": None,
            }
    
    # Validation passed or no question provided, process image
    result = assistant.process_image_query(question, image_bytes or b"", mime_type or "image/jpeg")
    answer = result.get("message", "I could not analyze that image right now.")
    
    with get_db().cursor() as cursor:
        cursor.execute("INSERT INTO ai_chat_history (user_id, question, response) VALUES (%s, %s, %s)", (user_id, question, answer))
    return {
        "success": True,
        "intent": "IMAGE_QUERY", 
        "message": answer,
        "answer": answer,
        "data": {
            "type": "animal_results",
            "items": result.get("results", []),
            "mode": result.get("mode"),
            "disease": result.get("disease"),
            "solution": result.get("solution"),
            "warning": result.get("warning"),
        } if result.get("results") or result.get("mode") in {"disease", "similar_animal"} else None,
    }


@app.route("/api/ai/chat", methods=["POST"])
@login_required
def ai_chat_api():
    if request.content_type and "multipart/form-data" in request.content_type:
        question = (request.form.get("message") or request.form.get("question") or "").strip()
        image_file = request.files.get("image")
        if not question and not image_file:
            return jsonify({"success": False, "error": "Please enter a question or upload an image."}), 400
        image_bytes = image_file.read() if image_file and image_file.filename else b""
        mime_type = image_file.mimetype or "image/jpeg"
        if not image_bytes and not question:
            return jsonify({"success": False, "error": "Please add a question or upload an image."}), 400
        return jsonify(process_image_chat(question, image_bytes, mime_type, g.user["user_id"]) if image_bytes else process_ai_chat(question, g.user["user_id"]))

    question = str(get_json_payload().get("message", "")).strip()
    if not question or len(question) > 1500:
        return jsonify({"success": False, "error": "Enter a question up to 1,500 characters."}), 400
    return jsonify(process_ai_chat(question, g.user["user_id"]))


@app.route("/api/ai/speak", methods=["POST"])
@login_required
def ai_speak_api():
    payload = get_json_payload()
    text = str(payload.get("text", "")).strip()
    language = str(payload.get("language", "")).strip().lower()
    if not text or language != "mr":
        return jsonify({"success": False, "error": "Marathi speech requires Marathi text."}), 400
    try:
        from io import BytesIO
        from gtts import gTTS

        audio = BytesIO()
        gTTS(text=text, lang="mr", slow=False).write_to_fp(audio)
        audio.seek(0)
        return send_file(audio, mimetype="audio/mpeg", download_name="marathi-response.mp3")
    except Exception:
        app.logger.exception("Marathi speech generation failed")
        return jsonify({"success": False, "error": "Marathi voice service is temporarily unavailable."}), 503


@app.route("/ai-assistant", methods=["GET", "POST"])
@login_required
def ai_assistant():
    # Preserve the former form endpoint for bookmarked/custom clients.
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if not question:
            return jsonify({"error": "Please enter a question first."}), 400
        return jsonify(process_ai_chat(question, g.user["user_id"]))

    chat_history = get_ai_history(g.user["user_id"], limit=20)
    suggestions = [
        "🐄 Find cows under ₹50,000",
        "📍 Find animals in Pune",
        "💉 Show vaccinated animals",
        "💰 Find affordable livestock",
        "❓ What can you do?",
    ]
    return render_template("ai_assistant.html", chat_history=chat_history, suggestions=suggestions, active_page="assistant")


@app.route("/dashboard")
@login_required
def dashboard():
    if normalize_role(g.user.get("role")) == "seller":
        return redirect(url_for("seller_dashboard"))
    if normalize_role(g.user.get("role")) == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("buyer_dashboard"))


@app.route("/buyer-dashboard")
@login_required
def buyer_dashboard():
    with get_db().cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM favorites f JOIN buyer_profile bp ON bp.buyer_id = f.buyer_id WHERE bp.user_id = %s", (g.user["user_id"],))
        wishlist_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM orders o JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id WHERE bp.user_id = %s AND o.order_status IN ('Pending', 'Confirmed')", (g.user["user_id"],))
        order_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COALESCE(SUM(COALESCE(o.buyer_payable_amount, o.price)), 0) AS total FROM orders o JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id WHERE bp.user_id = %s AND o.order_status IN ('Confirmed', 'Completed') AND o.payment_status = 'Paid'", (g.user["user_id"],))
        total_spending = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM seller_profile WHERE verified = 1")
        verified_sellers = cursor.fetchone()["total"]
        cursor.execute(
            """
                 SELECT o.order_id, o.animal_id, CONCAT(a.animal_type, ' ', a.breed) AS animal_name,
                     a.image_url AS image, o.price, o.base_amount, o.buyer_commission_amount, o.buyer_payable_amount,
                     o.order_status, o.payment_status, u.full_name AS seller_name
            FROM orders o
            JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id
            JOIN animals a ON a.animal_id = o.animal_id
            JOIN seller_profile sp ON sp.seller_id = o.seller_id
            JOIN users u ON u.user_id = sp.user_id
            WHERE bp.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT 5
            """,
            (g.user["user_id"],),
        )
        latest_orders = cursor.fetchall()
        cursor.execute(
            """
            SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location, a.image_url AS image
            FROM animals a
            ORDER BY a.animal_id DESC
            LIMIT 6
            """
        )
        recommended_animals = cursor.fetchall()
        categories = fetch_category_choices(cursor)
    return render_template(
        "buyer_dashboard.html",
        user=g.user,
        wishlist_count=wishlist_count,
        order_count=order_count,
        total_spending=total_spending,
        verified_sellers=verified_sellers,
        latest_orders=latest_orders,
        recommended_animals=recommended_animals,
        categories=categories,
        active_page="buyer-dashboard",
    )


@app.route("/seller-dashboard")
@login_required
def seller_dashboard():
    if normalize_role(g.user.get("role")) != "seller":
        flash("You do not have access to the seller dashboard.", "danger")
        return redirect(url_for("dashboard"))

    seller_id = get_current_seller_id()
    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT seller_id, user_id, shop_name AS seller_name, address, city, state, country, latitude, longitude, verified, rating, total_animals, verified_at, created_at, updated_at
            FROM seller_profile
            WHERE seller_id = %s
            LIMIT 1
            """,
            (seller_id,),
        )
        seller = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS total FROM animals WHERE seller_id = %s", (seller_id,))
        total_animals = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM animals WHERE seller_id = %s", (seller_id,))
        active_listings = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM orders WHERE seller_id = %s", (seller_id,))
        total_orders = cursor.fetchone()["total"]
        cursor.execute("SELECT COALESCE(SUM(COALESCE(seller_payout_amount, price)), 0) AS total FROM orders WHERE seller_id = %s AND order_status = 'Completed' AND payment_status = 'Paid'", (seller_id,))
        total_earnings = cursor.fetchone()["total"]
        cursor.execute("SELECT COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' THEN COALESCE(o.base_amount, o.price) ELSE 0 END), 0) AS gross_sales, COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' THEN o.seller_commission_amount ELSE 0 END), 0) AS seller_commissions, COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' THEN o.seller_payout_amount ELSE 0 END), 0) AS net_earnings, COALESCE(SUM(CASE WHEN o.payment_status = 'Paid' AND p.transfer_status IN ('PENDING', 'NOT_READY') THEN o.seller_payout_amount ELSE 0 END), 0) AS pending_payouts, COALESCE(SUM(CASE WHEN p.transfer_status = 'SUCCESS' THEN o.seller_payout_amount ELSE 0 END), 0) AS completed_payouts, COALESCE(SUM(CASE WHEN p.transfer_status = 'FAILED' THEN o.seller_payout_amount ELSE 0 END), 0) AS failed_payouts FROM orders o JOIN payments p ON p.order_id = o.order_id WHERE o.seller_id = %s", (seller_id,))
        seller_financials = cursor.fetchone()
        cursor.execute(
            """
            SELECT o.order_id, o.animal_id, CONCAT(a.animal_type, ' ', a.breed) AS animal_name,
                     a.image_url AS image, o.price, o.base_amount, o.seller_commission_amount, o.seller_payout_amount,
                     o.order_status, o.payment_status, p.transfer_status, p.razorpay_transfer_id, u.full_name AS buyer_name
            FROM orders o
                 LEFT JOIN payments p ON p.order_id = o.order_id
            JOIN animals a ON a.animal_id = o.animal_id
            JOIN buyer_profile bp ON bp.buyer_id = o.buyer_id
            LEFT JOIN users u ON u.user_id = bp.user_id
            WHERE o.seller_id = %s
            ORDER BY o.created_at DESC
            LIMIT 5
            """,
            (seller_id,),
        )
        recent_orders = cursor.fetchall()
        cursor.execute(
            """
            SELECT a.animal_id, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.image_url AS image, a.price, a.health_status
            FROM animals a
            WHERE a.seller_id = %s
            ORDER BY a.animal_id DESC
            LIMIT 6
            """,
            (seller_id,),
        )
        top_animals = cursor.fetchall()
        cursor.execute("SELECT availability AS status, COUNT(*) AS total FROM animals WHERE seller_id = %s GROUP BY availability", (seller_id,))
        seller_status_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT DATE_FORMAT(created_at, '%%b') AS month_name, COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE seller_id = %s AND order_status = 'Completed'
              AND created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
            GROUP BY YEAR(created_at), MONTH(created_at), DATE_FORMAT(created_at, '%%b')
            ORDER BY YEAR(created_at), MONTH(created_at)
            """,
            (seller_id,),
        )
        seller_sales_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT i.inquiry_id, CONCAT(a.animal_type, ' ', a.breed) AS animal_name,
                   i.status, i.created_at, u.full_name AS buyer_name
            FROM inquiries i
            JOIN animals a ON a.animal_id = i.animal_id
            JOIN buyer_profile bp ON bp.buyer_id = i.buyer_id
            JOIN users u ON u.user_id = bp.user_id
            WHERE i.seller_id = %s
            ORDER BY i.created_at DESC
            LIMIT 5
            """,
            (seller_id,),
        )
        recent_inquiries = cursor.fetchall()
    return render_template(
        "seller_dashboard.html",
        seller=seller,
        total_animals=total_animals,
        active_listings=active_listings,
        total_orders=total_orders,
        total_earnings=total_earnings,
        seller_financials=seller_financials,
        recent_orders=recent_orders,
        top_animals=top_animals,
        recent_inquiries=recent_inquiries,
        seller_status_data={"labels": [row["status"] for row in seller_status_rows], "values": [row["total"] for row in seller_status_rows]},
        seller_sales_data={"labels": [row["month_name"] for row in seller_sales_rows], "values": [float(row["total"]) for row in seller_sales_rows]},
        active_page="seller-dashboard",
    )


@app.route("/seller/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    if normalize_role(g.user.get("role")) != "seller":
        abort(403)
    status = request.form.get("order_status", "")
    if status not in {"Confirmed", "Completed", "Cancelled"}:
        flash("Invalid order status.", "danger")
        return redirect(url_for("seller_dashboard"))

    seller_id = get_current_seller_id()
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT animal_id, order_status, payment_status FROM orders WHERE order_id = %s AND seller_id = %s LIMIT 1",
            (order_id, seller_id),
        )
        order = cursor.fetchone()
        if not order:
            abort(404)
        if status == "Completed" and order["payment_status"] != "Paid":
            flash("An order must be paid before it can be completed.", "warning")
            return redirect(url_for("seller_dashboard"))
        if status == "Cancelled" and order["payment_status"] == "Paid":
            flash("Paid orders require an admin refund before cancellation.", "warning")
            return redirect(url_for("seller_dashboard"))
        cursor.execute("UPDATE orders SET order_status = %s WHERE order_id = %s AND seller_id = %s", (status, order_id, seller_id))
        if status == "Completed":
            cursor.execute("UPDATE animals SET availability = 'Sold' WHERE animal_id = %s", (order["animal_id"],))
        elif status == "Cancelled":
            cursor.execute("UPDATE animals SET availability = 'Available' WHERE animal_id = %s AND availability = 'Reserved'", (order["animal_id"],))
    flash(f"Order #{order_id} marked {status.lower()}.", "success")
    return redirect(url_for("seller_dashboard"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if normalize_role(g.user.get("role")) != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))

    with get_db().cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM seller_profile WHERE verified = 1")
        active_sellers = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM animals")
        animal_listings = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM reports")
        reports = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM ai_chat_history")
        ai_usage = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM favorites")
        wishlist_total = cursor.fetchone()["total"]
        cursor.execute("""SELECT
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN COALESCE(o.base_amount, o.price) ELSE 0 END), 0) AS total_gmv,
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN o.buyer_commission_amount ELSE 0 END), 0) AS buyer_commissions,
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN o.seller_commission_amount ELSE 0 END), 0) AS seller_commissions,
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN o.admin_gross_commission ELSE 0 END), 0) AS gross_commission,
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN o.seller_payout_amount ELSE 0 END), 0) AS seller_payouts,
            COALESCE(SUM(CASE WHEN p.payment_status = 'Paid' THEN p.amount ELSE 0 END), 0) AS buyer_payments,
            SUM(p.payment_status = 'Paid') AS successful_payments, SUM(p.payment_status = 'Pending') AS pending_payments,
            SUM(p.payment_status = 'Failed') AS failed_payments, SUM(p.transfer_status = 'PENDING' OR p.transfer_status = 'NOT_READY') AS pending_transfers,
            SUM(p.transfer_status = 'SUCCESS') AS successful_transfers, SUM(p.transfer_status = 'FAILED') AS failed_transfers,
            COALESCE(SUM(CASE WHEN p.refund_status = 'SUCCESS' THEN p.refund_amount ELSE 0 END), 0) AS refunds
            FROM orders o JOIN payments p ON p.order_id = o.order_id""")
        financial_metrics = cursor.fetchone()
        cursor.execute("SELECT status AS label, COUNT(*) AS total FROM users WHERE role = 'Seller' GROUP BY status ORDER BY status")
        seller_status_rows = cursor.fetchall()
        cursor.execute(
            """
            SELECT DATE_FORMAT(created_at, '%%b') AS month_name, COUNT(*) AS total
            FROM users
            WHERE created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
            GROUP BY YEAR(created_at), MONTH(created_at), DATE_FORMAT(created_at, '%%b')
            ORDER BY YEAR(created_at), MONTH(created_at)
            """
        )
        user_growth_rows = cursor.fetchall()

        cursor.execute("SELECT animal_type AS category_name, COUNT(*) AS total FROM animals GROUP BY animal_type ORDER BY animal_type")
        category_counts = cursor.fetchall()

        cursor.execute(
            """
            SELECT CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.image_url AS image, a.price, a.animal_id, a.animal_type AS category_name, a.created_at
            FROM animals a
            ORDER BY a.animal_id DESC
            LIMIT 6
            """
        )
        recent_listings = cursor.fetchall()

        cursor.execute(
            """
            SELECT title AS subject, message AS name, created_at
            FROM notifications
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        recent_messages = cursor.fetchall()

        cursor.execute(
            """
            SELECT shop_name AS seller_name, rating, verified
            FROM seller_profile
            ORDER BY rating DESC
            LIMIT 5
            """
        )
        top_sellers = cursor.fetchall()

        cursor.execute(
            """
            SELECT shop_name AS seller_name, latitude, longitude, verified, rating
            FROM seller_profile
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY seller_id ASC
            LIMIT 10
            """
        )
        seller_locations = cursor.fetchall()

    status_data = {"labels": [row["label"] for row in seller_status_rows], "values": [row["total"] for row in seller_status_rows]}

    category_chart = {
        "labels": [row["category_name"] for row in category_counts],
        "values": [row["total"] for row in category_counts],
    }

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        active_sellers=active_sellers,
        animal_listings=animal_listings,
        reports=reports,
        ai_usage=ai_usage,
        wishlist_total=wishlist_total,
        financial_metrics=financial_metrics,
        recent_listings=recent_listings,
        recent_messages=recent_messages,
        top_sellers=top_sellers,
        seller_locations=seller_locations,
        status_data=status_data,
        category_chart=category_chart,
        user_growth_data={"labels": [row["month_name"] for row in user_growth_rows], "values": [row["total"] for row in user_growth_rows]},
        active_page="admin-dashboard",
    )


@app.route("/disease-detection", methods=["GET", "POST"])
@login_required
def disease_detection():
    current_result = None

    if request.method == "POST":
        image = request.files.get("disease_image")
        if not image or not image.filename:
            flash("Please upload an image for disease detection.", "danger")
            return redirect(url_for("disease_detection"))

        if not allowed_image(image.filename):
            flash("Unsupported image format. Use JPG, JPEG, PNG, WEBP, or GIF.", "danger")
            return redirect(url_for("disease_detection"))

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        filename = f"disease_{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(save_path)
        image_path = f"/static/uploads/{filename}"

        selected_animal = request.form.get("animal_type", "").strip()
        symptoms = request.form.get("symptoms", "").strip()
        
        # Validate that the selected animal is supported (Cow, Cat, Dog, Horse)
        supported_animals = {"Cow", "Cat", "Dog", "Horse"}
        if selected_animal and selected_animal not in supported_animals:
            os.remove(save_path)
            flash(f"I currently support disease detection for cows, cats, dogs, and horses. '{selected_animal}' is not yet supported.", "danger")
            return redirect(url_for("disease_detection"))
        
        try:
            prediction = vetai_service.predict(save_path, selected_animal, symptoms)
        except ValueError as error:
            os.remove(save_path)
            flash(str(error), "danger")
            return redirect(url_for("disease_detection"))
        if prediction.get("available"):
            disease = prediction["predicted_disease"]
            confidence = prediction["confidence"]
            recommendation = prediction["recommendation"]
            flash("VetAI image and symptom analysis completed.", "success")
        else:
            disease, confidence, recommendation = mock_disease_inference(filename)
            flash("VetAI model artifacts are not installed; showing the existing fallback signal.", "warning")
        with get_db().cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO disease_detection_logs (user_id, uploaded_image, predicted_disease, confidence_score, treatment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (g.user["user_id"] if g.get("user") else None, image_path, disease, confidence, recommendation),
            )
            prediction_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT prediction_id, uploaded_image AS image_path, predicted_disease, confidence_score AS confidence, treatment AS recommendation, created_at
                FROM disease_detection_logs
                WHERE prediction_id = %s
                LIMIT 1
                """,
                (prediction_id,),
            )
            current_result = cursor.fetchone()

        flash("Image analyzed successfully.", "success")

    with get_db().cursor() as cursor:
        cursor.execute(
            """
            SELECT prediction_id, uploaded_image AS image_path, predicted_disease, confidence_score AS confidence, treatment AS recommendation, created_at
            FROM disease_detection_logs
            ORDER BY created_at DESC
            LIMIT 6
            """
        )
        prediction_history = cursor.fetchall()

    return render_template(
        "disease_detection.html",
        current_result=current_result,
        prediction_history=prediction_history,
        active_page="disease",
    )


def haversine_sql(lat1, lon1, lat2_col="latitude", lon2_col="longitude"):
    return f"(6371 * ACOS(LEAST(1, COS(RADIANS(%s)) * COS(RADIANS({lat2_col})) * COS(RADIANS({lon2_col}) - RADIANS(%s)) + SIN(RADIANS(%s)) * SIN(RADIANS({lat2_col})))) )"


@app.route("/nearby-animals")
def nearby_animals():
    try:
        radius = int(request.args.get("radius", 25))
    except (TypeError, ValueError):
        radius = 25
    radius = min(max(radius, 1), 100)
    animal_type = request.args.get("animal_type", "")
    gender = request.args.get("gender", "")
    vaccinated = request.args.get("vaccinated", "")
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)
    per_page = 8

    user_lat, user_lon = 18.5204, 73.8567
    if g.get("user"):
        profile_table = "buyer_profile" if normalize_role(g.user.get("role")) == "buyer" else "seller_profile"
        with get_db().cursor() as cursor:
            cursor.execute(f"SELECT latitude, longitude FROM {profile_table} WHERE user_id = %s LIMIT 1", (g.user["user_id"],))
            saved_location = cursor.fetchone()
        if saved_location and saved_location["latitude"] is not None and saved_location["longitude"] is not None:
            user_lat = float(saved_location["latitude"])
            user_lon = float(saved_location["longitude"])
    distance_expr = haversine_sql(user_lat, user_lon, "a.latitude", "a.longitude")

    where_clauses = ["a.latitude IS NOT NULL", "a.longitude IS NOT NULL"]
    params = [user_lat, user_lon, user_lat]

    if animal_type:
        where_clauses.append("a.animal_type = %s")
        params.append(animal_type)
    if gender in {"Male", "Female", "Other"}:
        where_clauses.append("a.gender = %s")
        params.append(gender)
    if vaccinated in {"Yes", "No"}:
        where_clauses.append("a.vaccinated = %s")
        params.append(vaccinated)

    where_sql = " AND ".join(where_clauses)

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT a.*, CONCAT(a.animal_type, ' ', a.breed) AS animal_name, a.animal_type AS category_name, CONCAT(a.city, ', ', a.state) AS location,
                     a.image_url AS image, a.latitude, a.longitude, {distance_expr} AS distance_km
            FROM animals a
                 JOIN seller_profile s ON s.seller_id = a.seller_id
            WHERE {where_sql}
            HAVING distance_km <= %s
            ORDER BY distance_km ASC
            """,
            params + [radius],
        )
        all_items = cursor.fetchall()

        total = len(all_items)
        total_pages = max(ceil(total / per_page), 1)
        page = min(page, total_pages)
        start = (page - 1) * per_page
        items = all_items[start:start + per_page]

        user_id = g.user["user_id"] if g.get("user") else None
        if user_id is not None:
            cursor.execute("SELECT city, state FROM buyer_profile WHERE user_id = %s LIMIT 1", (user_id,))
            current_location = cursor.fetchone() or {"city": "Pune", "state": "Maharashtra"}
        else:
            current_location = {"city": "Pune", "state": "Maharashtra"}

    map_points = [
        {
            "name": row.get("animal_name") or f"{row.get('animal_type', '')} {row.get('breed', '')}".strip(),
            "lat": float(row["latitude"] or 0),
            "lng": float(row["longitude"] or 0),
            "image": row["image"],
            "price": float(row["price"]),
            "distance_km": round(float(row["distance_km"]), 1),
            "distance_label": distance_label(row["distance_km"]),
        }
        for row in all_items
    ]

    return render_template(
        "nearby_animals.html",
        animals=items,
        map_points=map_points,
        current_location=current_location,
        user_lat=user_lat,
        user_lon=user_lon,
        active_page="nearby",
        radius=radius,
        animal_type=animal_type,
        gender=gender,
        vaccinated=vaccinated,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False), use_reloader=False)

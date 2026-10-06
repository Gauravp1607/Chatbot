import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(DOTENV_PATH)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root").strip() or "root"
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "livestockai")
    MYSQL_CURSORCLASS = "DictCursor"
    # Optional secret code required to allow creation of admin accounts via the registration form.
    # Set ADMIN_SIGNUP_CODE in your .env to enable admin self-signup with that code.
    ADMIN_SIGNUP_CODE = os.getenv("ADMIN_SIGNUP_CODE", "Gaurav1234")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@livestockai.local")
    PHONE_DEFAULT_COUNTRY_CODE = os.getenv("PHONE_DEFAULT_COUNTRY_CODE", "91")
    PASSWORD_RESET_DEBUG_OTP = os.getenv("PASSWORD_RESET_DEBUG_OTP", "false").lower() == "true"
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    RAZORPAY_ROUTE_ENABLED = os.getenv("RAZORPAY_ROUTE_ENABLED", "false").lower() == "true"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    # This account must be granted SELECT only on the marketplace database.
    # Deliberately do not fall back to the application's write-capable account.
    AI_MYSQL_HOST = os.getenv("AI_MYSQL_HOST", "")
    AI_MYSQL_PORT = int(os.getenv("AI_MYSQL_PORT", "3306"))
    AI_MYSQL_USER = os.getenv("AI_MYSQL_USER", "")
    AI_MYSQL_PASSWORD = os.getenv("AI_MYSQL_PASSWORD", "")
    AI_MYSQL_DB = os.getenv("AI_MYSQL_DB", "")
    VETAI_ARTIFACT_DIR = os.getenv("VETAI_ARTIFACT_DIR", os.path.join(BASE_DIR, "ai_artifacts"))
    BUYER_COMMISSION_PERCENT = os.getenv("BUYER_COMMISSION_PERCENT", "5")
    SELLER_COMMISSION_PERCENT = os.getenv("SELLER_COMMISSION_PERCENT", "5")

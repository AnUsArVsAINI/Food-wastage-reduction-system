"""
test_mail.py  –  Run this once to verify your Gmail SMTP credentials.
Usage:  python test_mail.py
"""
import smtplib, os, sys

# ── Read .env manually ────────────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

SENDER  = "anusarv2016@gmail.com"
APP_PW  = os.environ.get("GMAIL_APP_PASSWORD", "")
DEST    = input("Enter your email to receive the test message: ").strip()

# ── Pre-flight checks ─────────────────────────────────────────
if not APP_PW or APP_PW == "your_16_char_app_password_here":
    print("\n❌  GMAIL_APP_PASSWORD is not set in .env")
    print("    Open .env and replace the placeholder with your real 16-char App Password.")
    print("    See: https://myaccount.google.com/apppasswords\n")
    sys.exit(1)

if len(APP_PW.replace(" ", "")) != 16:
    print(f"\n⚠️  App password looks wrong – should be 16 chars, got {len(APP_PW.replace(' ',''))}")

print(f"\n🔄  Connecting to smtp.gmail.com:587 …")

try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
        s.ehlo()
        s.starttls()
        print("🔐  TLS OK – logging in …")
        s.login(SENDER, APP_PW.replace(" ", ""))
        print("✅  Login OK – sending test email …")

        msg  = f"Subject: FoodBridge SMTP Test\r\nFrom: {SENDER}\r\nTo: {DEST}\r\n\r\nIf you see this, Gmail SMTP is working!"
        s.sendmail(SENDER, DEST, msg)
        print(f"🎉  Done! Check {DEST} for the test email.\n")

except smtplib.SMTPAuthenticationError:
    print("\n❌  SMTPAuthenticationError – wrong App Password or 2FA not enabled.")
    print("    Fix: go to https://myaccount.google.com/apppasswords and generate a new one.\n")
except smtplib.SMTPConnectError:
    print("\n❌  Cannot connect to smtp.gmail.com:587 – check your internet / firewall.\n")
except Exception as e:
    print(f"\n❌  Unexpected error: {e}\n")

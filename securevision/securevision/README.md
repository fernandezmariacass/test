# 🛡️ SecureVision

A **production-ready, GEDSI-aligned** security monitoring web application built with Python/Flask.

> **GEDSI** = Gender Equality, Disability, and Social Inclusion  
> The UI meets WCAG 2.1 AA, uses inclusive language, and supports keyboard + screen-reader navigation.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔒 IP Allow-list | Only registered IPs/CIDRs can access the site |
| 📷 Live Camera | MJPEG stream from webcam or RTSP/CCTV |
| 📋 Audit Logs | Every login stored with timestamp, username, IP |
| 🚨 Alerts | Email (Resend/SMTP) + Telegram Bot notifications |
| 🛑 Rate Limiting | Brute-force protection (configurable threshold) |
| ♿ Accessibility | ARIA labels, skip-link, high contrast, reduced-motion |
| 🔑 RBAC | admin / operator / viewer roles |

---

## 🗂️ Project Structure

```
securevision/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # ⚠️ Config classes (no secrets here)
│   ├── models/
│   │   ├── user.py          # ⚠️ SECURITY: User + LoginLog models
│   │   └── allowed_ip.py    # ⚠️ SECURITY: IP allow-list model
│   ├── routes/
│   │   ├── auth.py          # ⚠️ SECURITY: Login + IP check logic
│   │   ├── dashboard.py     # Main dashboard
│   │   ├── camera.py        # MJPEG streaming
│   │   ├── admin.py         # ⚠️ SECURITY: Admin-only routes
│   │   └── errors.py        # Error handlers
│   ├── services/
│   │   ├── security.py      # ⚠️ SECURITY: Allow-list & rate limiter
│   │   ├── notifications.py # ⚠️ SECURITY: Email/Telegram alerts
│   │   └── camera.py        # OpenCV camera manager
│   └── utils/
│       └── forms.py         # WTForms
├── templates/
│   ├── base.html            # GEDSI base layout
│   ├── auth/login.html      # Accessible login page
│   ├── dashboard/           # Dashboard templates
│   └── errors/              # Error pages
├── instance/
│   └── config.py.example    # ⚠️ Copy → config.py (git-ignored)
├── .env.example             # Copy → .env (git-ignored)
├── .gitignore               # Excludes all secrets
├── requirements.txt
└── run.py
```

---

## 🚀 Quick Start

### 1. Clone & set up environment
```bash
git clone https://github.com/yourorg/securevision.git
cd securevision
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure secrets
```bash
cp .env.example .env
# Edit .env with your real values
cp instance/config.py.example instance/config.py
# Edit instance/config.py with IPs, API keys, etc.
```

### 3. Run
```bash
python run.py
# → http://localhost:5000
# Default credentials: admin / ChangeMe123!  ← CHANGE IMMEDIATELY
```

### 4. Production (Gunicorn)
```bash
FLASK_ENV=production gunicorn "run:app" -w 4 -b 0.0.0.0:8000
```

---

## ⚠️ Security-Critical Files

These files contain security logic and **must never be publicly committed with real values**:

| File | What it protects |
|---|---|
| `instance/config.py` | Real IP list, API keys, DB URL |
| `.env` | All secrets as env vars |
| `app/services/security.py` | Allow-list enforcement logic |
| `app/services/notifications.py` | Notification credential handling |
| `app/routes/auth.py` | Login flow, rate-limit, audit log |
| `app/models/user.py` | Password hashing, role model |

---

## 🌐 Camera Configuration

| Source type | CAMERA_SOURCE value |
|---|---|
| First webcam | `0` |
| RTSP stream | `rtsp://user:pass@192.168.1.100:554/stream` |
| HTTP MJPEG | `http://192.168.1.100:8080/video` |

Set `CAMERA_SOURCE` in `.env` — never hardcode credentials.

---

## ♿ GEDSI Compliance Notes

- **Color contrast**: All text meets WCAG AA (≥4.5:1 ratio)  
- **Focus indicators**: Visible 3px orange ring on all interactive elements  
- **Screen readers**: Full ARIA labels, roles, and live regions  
- **Skip link**: "Skip to main content" visible on focus  
- **Inclusive language**: Error messages are non-blaming and supportive  
- **Reduced motion**: Animations disabled when `prefers-reduced-motion` is set  
- **Keyboard navigation**: All actions reachable without a mouse  

---

## 📬 Notification Setup

### Email via Resend
1. Sign up at https://resend.com and get an API key
2. Set `RESEND_API_KEY` and `NOTIFY_EMAIL_ENABLED=true`

### Email via SMTP (Gmail)
1. Enable 2FA and create an App Password
2. Set `SMTP_USER`, `SMTP_PASSWORD`, `NOTIFY_EMAIL_ENABLED=true`

### Telegram Bot
1. Create a bot via @BotFather → get token
2. Get your chat ID via `@userinfobot`
3. Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `NOTIFY_TELEGRAM_ENABLED=true`

---

## 🧪 Tests
```bash
pytest tests/ -v
```

---

## 📄 License
MIT — see LICENSE for details.

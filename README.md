# CampusNest - Quick Start Guide

## Prerequisites
- Python 3.13
- `uv` package manager
- Git

## Initial Setup
### 1. Clone the Repository
```bash
git clone <repository-url>
cd campusnest_pure_django
```

### 2. Create Virtual Environment with uv
```bash
uv venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Note:** For email functionality, you need a Gmail App Password (not your regular password).
### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## Project Structure
```
CampusNest/
├── accounts/           # User authentication (register, login, password reset)
├── profiles/           # User profiles
├── templates/          # Shared templates
├── media/             # User uploaded files
├── manage.py
└── .env               # Environment variables (DO NOT COMMIT)
```

---

## Available URLs

### Authentication
- `/accounts/register/` - Create new account
- `/accounts/login/` - Login
- `/accounts/logout/` - Logout
- `/accounts/password-reset/` - Reset password
- `/accounts/resend-verification/` - Resend verification email

### Profiles
- `/` - Home (redirects based on auth status)
- `/profiles/view/` - View your profile
- `/profiles/create/` - Create profile
- `/profiles/edit/` - Edit profile
- `/profiles/admin-dashboard/` - Admin dashboard (staff only)

### Admin
- `/admin/` - Django admin panel


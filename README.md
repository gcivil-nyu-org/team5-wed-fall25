# CampusNest

[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/team5-wed-fall25.svg?token=WHHjuyD4b8zGdFuFp8yp)](https://app.travis-ci.com/gcivil-nyu-org/team5-wed-fall25)
[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/team5-wed-fall25/badge.svg?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/team5-wed-fall25?branch=develop)

## Video Demonstration
- https://drive.google.com/file/d/1ScsrWaBaZHOPLpYz85jaMxOKqKPg2015/view?usp=sharing

## CampusNest - Quick Start Guide

### Prerequisites
- Python 3.13
- `uv` package manager
- Git

### Initial Setup
#### 1. Clone the Repository
```bash
git clone <repository-url>
cd campusnest_pure_django
```

#### 2. Create Virtual Environment with uv
```bash
uv venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
uv pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Note:** For email functionality, you need a Gmail App Password (not your regular password).

#### 5. Run Database Migrations
```bash
python manage.py migrate
```

#### 6. Create a Superuser (Optional)
```bash
python manage.py createsuperuser
```

#### 7. Run the Development Server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## Running Tests

### Run all tests:
```bash
python manage.py test
```

### Run tests with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

### Check code quality:
```bash
flake8 .
black . --check
```

---

## Project Structure
```
CampusNest/
├── accounts/           # User authentication (register, login, password reset)
├── profiles/           # User profiles
├── listings/           # Housing listings
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

### Listings
- `/listings/my-listings/` - View your listings
- `/listings/create/` - Create new listing
- `/listings/<id>/` - View listing details
- `/listings/<id>/edit/` - Edit listing
- `/listings/<id>/delete/` - Delete listing

### Admin
- `/admin/` - Django admin panel

---

## CI/CD

This project uses Travis CI for continuous integration and Coveralls for coverage reporting.

### Travis CI Setup:
1. Go to [travis-ci.com](https://travis-ci.com)
2. Sign in with your GitHub account
3. Enable Travis CI for your repository
4. Push changes to trigger builds

### Coveralls Setup:
1. Go to [coveralls.io](https://coveralls.io)
2. Sign in with your GitHub account
3. Add your repository
4. Get your repo token from settings
5. Add `COVERALLS_REPO_TOKEN` as environment variable in Travis CI settings

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is developed for educational purposes.

# Payroll Management System

A full-stack web application for managing employee payrolls, departments, and payslips with role-based authentication. Built with Flask and SQLite.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Architecture](#-architecture)
- [Database Schema](#-database-schema)
- [API Endpoints](#-api-endpoints)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Contributing](#-contributing)

---

## 🚀 Features

### Employee Management
- CRUD operations for employee records
- Track employee details: name, position, department, salary, contact info
- Configurable tax rates and allowances per employee

### Payroll Processing
- Automated salary calculations with tax deductions
- Customizable allowances and tax rates
- Bulk payroll export to CSV

### Payslip Generation
- Professional PDF payslip generation using ReportLab
- Automated email delivery via SMTP (Gmail)
- Payslip history tracking per employee

### Department Management
- Create and manage departments
- Department-wise salary analytics
- Visual charts for salary distribution

### User Management & Authentication
- Role-based access control (Admin/Employee)
- Secure password hashing with Werkzeug
- Session management via Flask-Login
- Employee self-service dashboard

### Data Management
- Automated database backups (last 5 retained)
- CSV export functionality
- SQLite database with migration support

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.8+, Flask 2.3.3 |
| **Database** | SQLite3 |
| **Authentication** | Flask-Login 0.6.3, Werkzeug 2.3.7 |
| **PDF Generation** | ReportLab 4.0.4 |
| **Email** | smtplib (SMTP/TLS) |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Image Processing** | Pillow 10.0.1 |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Browser)                       │
│                   HTML5 / Bootstrap 5 / JS                  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│                     Flask Application                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Routes    │  │  Templates  │  │   Static Assets     │  │
│  │  (app.py)   │  │  (Jinja2)   │  │   (CSS/JS/PDF)      │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
│         │                                                    │
│  ┌──────▼──────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │Flask-Login  │  │  ReportLab  │  │     smtplib         │  │
│  │(Auth/RBAC)  │  │(PDF Gen)    │  │   (Email SMTP)      │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────┐
│                    SQLite Database                          │
│     employees │ users │ payslips │ departments              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄 Database Schema

### `employees`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary Key (Auto-increment) |
| `name` | TEXT | Employee full name |
| `position` | TEXT | Job title |
| `department` | TEXT | Department name |
| `salary` | REAL | Base salary |
| `tax_rate` | REAL | Tax rate (default: 0.15) |
| `allowances` | REAL | Additional allowances |
| `email` | TEXT | Contact email |
| `phone` | TEXT | Contact phone |
| `created_at` | TIMESTAMP | Record creation time |

### `users`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary Key (Auto-increment) |
| `username` | TEXT | Unique username |
| `email` | TEXT | Unique email |
| `password_hash` | TEXT | Hashed password (Werkzeug) |
| `role` | TEXT | `admin` or `employee` |
| `employee_id` | INTEGER | FK → employees.id |
| `created_at` | TIMESTAMP | Account creation time |

### `payslips`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary Key (Auto-increment) |
| `employee_id` | INTEGER | FK → employees.id |
| `month` | TEXT | Payslip month |
| `year` | INTEGER | Payslip year |
| `gross_pay` | REAL | Total before deductions |
| `tax_amount` | REAL | Tax deducted |
| `allowances` | REAL | Allowances added |
| `net_pay` | REAL | Final pay amount |
| `generated_by` | INTEGER | FK → users.id |
| `pdf_path` | TEXT | Path to PDF file |
| `created_at` | TIMESTAMP | Generation time |

### `departments`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary Key (Auto-increment) |
| `name` | TEXT | Unique department name |
| `created_at` | TIMESTAMP | Creation time |

---

## 🔗 API Endpoints

### Authentication
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET/POST | `/login` | Public | User login |
| GET | `/logout` | Authenticated | User logout |
| GET/POST | `/register` | Admin | Register new user |
| GET/POST | `/change_password` | Authenticated | Change password |

### Employee Management
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/` | Admin | Dashboard with stats |
| GET/POST | `/add` | Admin | Add new employee |
| GET | `/view` | Admin | List all employees |
| GET/POST | `/edit/<id>` | Admin | Edit employee |
| GET | `/delete/<id>` | Admin | Delete employee |

### Payroll & Payslips
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/payroll` | Admin | Calculate payroll |
| GET | `/export_payroll` | Admin | Export to CSV |
| GET | `/generate_payslip/<id>` | Admin | Generate PDF payslip |
| GET | `/download_payslip/<id>` | Authenticated | Download payslip PDF |
| GET | `/send_payslip/<id>` | Admin | Email payslip |

### Departments & Reports
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET/POST | `/departments` | Admin | Manage departments |
| GET | `/delete_department/<id>` | Admin | Delete department |
| GET | `/department_report` | Admin | Salary analytics |

### User Management
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/users` | Admin | List all users |
| GET/POST | `/edit_user/<id>` | Admin | Edit user |
| POST | `/delete_user/<id>` | Admin | Delete user |
| GET | `/employee_dashboard` | Employee | Employee self-service |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/payroll-management-system.git
   cd payroll-management-system
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   ```
   http://127.0.0.1:5000
   ```

### Default Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |

> ⚠️ **Important**: Change the default admin password after first login!

---

## ⚙️ Configuration

### Email Configuration (Gmail SMTP)

Edit the `EMAIL_CONFIG` dictionary in `app.py`:

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'your.email@gmail.com',      # Your Gmail address
    'password': 'your-app-password',       # Gmail App Password (NOT regular password)
    'use_tls': True,
    'enabled': True                        # Set to True to enable
}
```

#### Generating Gmail App Password:
1. Enable 2-Factor Authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use the 16-character password in the config

See [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md) for detailed instructions.

### Application Settings

| Setting | Location | Default |
|---------|----------|---------|
| Secret Key | `app.py` | `payrollsystem123` |
| Database Path | `app.py` | `payroll_system/database.db` |
| Backup Directory | `app.py` | `payroll_system/backups/` |
| Payslips Directory | `app.py` | `static/payslips/` |
| Max Backups | `app.py` | 5 |

---

## 🎯 Usage

### Admin Workflow
1. **Login** with admin credentials
2. **Add Departments** via Department Management
3. **Add Employees** with salary, tax rate, and allowances
4. **Calculate Payroll** to view all salary computations
5. **Generate Payslips** as PDF for individual employees
6. **Email Payslips** directly to employee email addresses
7. **Export Reports** to CSV for external processing

### Employee Workflow
1. **Login** with employee credentials
2. **View Dashboard** with personal information
3. **Download Payslips** for personal records
4. **Change Password** for account security

---

## 📁 Project Structure

```
payroll_system/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── EMAIL_SETUP_GUIDE.md      # Email configuration guide
│
├── payroll_system/
│   ├── database.db           # SQLite database
│   └── backups/              # Automated database backups
│
├── static/
│   ├── style.css             # Custom styles
│   ├── payroll_export.csv    # Exported payroll data
│   └── payslips/             # Generated PDF payslips
│
└── templates/
    ├── index.html            # Admin dashboard
    ├── login.html            # Login page
    ├── register.html         # User registration
    ├── add_employee.html     # Add employee form
    ├── edit_employee.html    # Edit employee form
    ├── view_employees.html   # Employee list
    ├── calculate_payroll.html# Payroll calculations
    ├── departments.html      # Department management
    ├── department_report.html# Analytics dashboard
    ├── manage_users.html     # User management
    ├── edit_user.html        # Edit user form
    ├── change_password.html  # Password change
    └── employee_dashboard.html# Employee portal
```

---

## 🔒 Security

### Implemented Security Measures
- **Password Hashing**: Werkzeug's `generate_password_hash` with PBKDF2-SHA256
- **Session Management**: Flask-Login with secure session cookies
- **RBAC**: Role-based decorators (`@admin_required`, `@employee_required`)
- **SQL Injection Prevention**: Parameterized queries throughout
- **CSRF Protection**: Flask's built-in session management

### Recommendations for Production
- [ ] Change default `secret_key` to a strong random value
- [ ] Enable HTTPS with SSL/TLS certificates
- [ ] Use environment variables for sensitive configs
- [ ] Implement rate limiting on login endpoint
- [ ] Add CSRF tokens to all forms
- [ ] Regular database backups to external storage
- [ ] Use a production WSGI server (Gunicorn/uWSGI)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Gokila-S**

---

## 🙏 Acknowledgments

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5](https://getbootstrap.com/)
- [ReportLab](https://www.reportlab.com/)
- [Flask-Login](https://flask-login.readthedocs.io/)

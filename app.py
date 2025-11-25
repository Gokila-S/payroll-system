from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import csv
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from io import StringIO, BytesIO
import shutil
from functools import wraps
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
app.secret_key = "payrollsystem123"  # For flash messages

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Ensure database directory exists
os.makedirs('payroll_system', exist_ok=True)
os.makedirs('static/payslips', exist_ok=True)

# Email Configuration 
# IMPORTANT: To enable email functionality, you need to:
# 1. Set your Gmail address in 'email' field
# 2. Generate an App Password from Google Account settings (not your regular password)
# 3. Set 'enabled' to True
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'gokixyz404@gmail.com',  # YOUR EMAIL HERE (e.g., 'your.email@gmail.com')
    'password': 'axeg`lphobwadvedu',  # YOUR APP PASSWORD HERE (not regular password)
    'use_tls': True,
    'enabled': True  # Set to True after configuring email and password above
}

def send_email_with_attachment(to_email, subject, body, attachment_path=None):
    """Send email with optional attachment"""
    
    # Check if email is configured and enabled
    if not EMAIL_CONFIG.get('enabled', False):
        return False, "Email is not configured. Please update EMAIL_CONFIG in app.py and set enabled=True"
    
    if not EMAIL_CONFIG.get('email') or not EMAIL_CONFIG.get('password'):
        return False, "Email credentials not configured. Please set email and password in EMAIL_CONFIG"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(attachment_path)}'
            )
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        if EMAIL_CONFIG['use_tls']:
            server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.sendmail(EMAIL_CONFIG['email'], to_email, msg.as_string())
        server.quit()
        
        return True, "Email sent successfully"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, role, employee_id=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.employee_id = employee_id

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[4], user_data[5])
    return None

# Role-based access decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def backup_database():
    """Create a backup of the database"""
    try:
        backup_dir = 'payroll_system/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'{backup_dir}/database_backup_{timestamp}.db'
        
        shutil.copy2('payroll_system/database.db', backup_path)
        print(f"Database backed up to: {backup_path}")
        
        # Keep only the last 5 backups
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.startswith('database_backup_')])
        if len(backup_files) > 5:
            for old_backup in backup_files[:-5]:
                os.remove(os.path.join(backup_dir, old_backup))
                
    except Exception as e:
        print(f"Backup failed: {str(e)}")

def init_db():
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Employee table with additional fields
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                department TEXT,
                salary REAL NOT NULL,
                tax_rate REAL DEFAULT 0.15,
                allowances REAL DEFAULT 0,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
    
    # Check if email and phone columns exist, if not add them
    c.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'email' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN email TEXT")
        print("Added email column to employees table")
    
    if 'phone' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN phone TEXT")
        print("Added phone column to employees table")
    
    # Users table for authentication
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                employee_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )''')
    
    # Payslips table
    c.execute('''CREATE TABLE IF NOT EXISTS payslips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                gross_pay REAL NOT NULL,
                tax_amount REAL NOT NULL,
                allowances REAL NOT NULL,
                net_pay REAL NOT NULL,
                generated_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pdf_path TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (id),
                FOREIGN KEY (generated_by) REFERENCES users (id)
            )''')
    
    # Departments table
    c.execute('''CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
    
    # Add some default departments if none exist
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        departments = ['Engineering', 'Marketing', 'HR', 'Sales', 'Finance']
        for dept in departments:
            c.execute("INSERT INTO departments (name) VALUES (?)", (dept,))
    
    # Create default admin user if no users exist
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_password = generate_password_hash('admin123')
        c.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                 ('admin', 'admin@payroll.com', admin_password, 'admin'))
        print("Default admin user created - Username: admin, Password: admin123")
    
    # Log current state
    c.execute("SELECT COUNT(*) FROM employees")
    emp_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM departments")
    dept_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    print(f"Database initialized - Employees: {emp_count}, Departments: {dept_count}, Users: {user_count}")
    
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('payroll_system/database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[4], user_data[5])
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        employee_id = request.form.get('employee_id') if request.form.get('employee_id') else None
        
        # Check if username or email already exists
        conn = sqlite3.connect('payroll_system/database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if c.fetchone():
            flash('Username or email already exists.', 'danger')
            conn.close()
            return redirect(url_for('register'))
        
        # Hash password and create user
        password_hash = generate_password_hash(password)
        c.execute("INSERT INTO users (username, email, password_hash, role, employee_id) VALUES (?, ?, ?, ?, ?)",
                 (username, email, password_hash, role, employee_id))
        conn.commit()
        conn.close()
        
        flash('User registered successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    # Get employees for dropdown (for employee role)
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM employees")
    employees = c.fetchall()
    conn.close()
    
    return render_template('register.html', employees=employees)

@app.route('/users')
@admin_required
def manage_users():
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.email, u.role, e.name as employee_name, u.created_at 
                 FROM users u 
                 LEFT JOIN employees e ON u.employee_id = e.id 
                 ORDER BY u.created_at DESC""")
    users = c.fetchall()
    conn.close()
    
    return render_template('manage_users.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        employee_id = request.form.get('employee_id')
        
        # Convert empty employee_id to None
        if employee_id == '':
            employee_id = None
        
        # Check if username already exists (excluding current user)
        c.execute("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
        if c.fetchone():
            flash('Username already exists!', 'danger')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))
        
        # Check if email already exists (excluding current user)
        c.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
        if c.fetchone():
            flash('Email already exists!', 'danger')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))
        
        # Update user
        c.execute("""UPDATE users 
                     SET username = ?, email = ?, role = ?, employee_id = ? 
                     WHERE id = ?""",
                 (username, email, role, employee_id, user_id))
        conn.commit()
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    # GET request - show edit form
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if not user:
        flash('User not found!', 'danger')
        conn.close()
        return redirect(url_for('manage_users'))
    
    # Get all employees for dropdown
    c.execute("SELECT id, name FROM employees ORDER BY name")
    employees = c.fetchall()
    
    conn.close()
    
    return render_template('edit_user.html', user=user, employees=employees)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get user info before deletion
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    if not user:
        flash('User not found!', 'danger')
        conn.close()
        return redirect(url_for('manage_users'))
    
    username = user[0]
    
    # Prevent deletion of admin user
    if username == 'admin':
        flash('Cannot delete the main admin user!', 'danger')
        conn.close()
        return redirect(url_for('manage_users'))
    
    # Check if user is currently logged in
    if current_user.id == user_id:
        flash('Cannot delete yourself while logged in!', 'danger')
        conn.close()
        return redirect(url_for('manage_users'))
    
    try:
        # Delete the user
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        
        flash(f'User "{username}" has been deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    conn.close()
    return redirect(url_for('manage_users'))

@app.route('/employee_dashboard')
@employee_required
def employee_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get employee info
    c.execute("SELECT * FROM employees WHERE id = ?", (current_user.employee_id,))
    employee = c.fetchone()
    
    # Get payslips
    c.execute("""SELECT id, month, year, gross_pay, net_pay, created_at, pdf_path 
                 FROM payslips WHERE employee_id = ? ORDER BY year DESC, month DESC""", 
                 (current_user.employee_id,))
    payslips = c.fetchall()
    
    conn.close()
    
    return render_template('employee_dashboard.html', employee=employee, payslips=payslips)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required!', 'danger')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long!', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            return render_template('change_password.html')
        
        # Get current user from database
        conn = sqlite3.connect('payroll_system/database.db')
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (current_user.id,))
        user_data = c.fetchone()
        
        if not user_data or not check_password_hash(user_data[0], current_password):
            flash('Current password is incorrect!', 'danger')
            conn.close()
            return render_template('change_password.html')
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                 (new_password_hash, current_user.id))
        conn.commit()
        conn.close()
        
        flash('Password changed successfully!', 'success')
        
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('employee_dashboard'))
    
    return render_template('change_password.html')

@app.route('/')
@login_required
def index():
    # Admin dashboard
    if current_user.role != 'admin':
        return redirect(url_for('employee_dashboard'))
        
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get quick stats
    c.execute("SELECT COUNT(*) FROM employees")
    emp_count = c.fetchone()[0]
    
    c.execute("SELECT SUM(salary) FROM employees")
    total_salary = c.fetchone()[0] or 0
    
    c.execute("SELECT AVG(salary) FROM employees")
    avg_salary = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'employee'")
    user_count = c.fetchone()[0]
    
    conn.close()
    
    return render_template('index.html', 
                          emp_count=emp_count,
                          total_salary=round(total_salary, 2),
                          avg_salary=round(avg_salary, 2),
                          user_count=user_count)

@app.route('/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if request.method == 'POST':
        try:
            name = request.form['name']
            position = request.form['position']
            department = request.form['department']
            salary = float(request.form['salary'])
            tax_rate = float(request.form['tax_rate'])
            allowances = float(request.form['allowances'])
            email = request.form.get('email', '')
            phone = request.form.get('phone', '')
            
            conn = sqlite3.connect('payroll_system/database.db')
            c = conn.cursor()
            c.execute("INSERT INTO employees (name, position, department, salary, tax_rate, allowances, email, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                     (name, position, department, salary, tax_rate, allowances, email, phone))
            conn.commit()
            
            # Verify the insert
            c.execute("SELECT COUNT(*) FROM employees")
            count = c.fetchone()[0]
            print(f"Employee added successfully. Total employees now: {count}")
            
            conn.close()
            
            flash('Employee added successfully!', 'success')
            return redirect('/view')
            
        except Exception as e:
            print(f"Error adding employee: {str(e)}")
            flash(f'Error adding employee: {str(e)}', 'danger')
            return redirect('/add')
    
    # Get departments for dropdown
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("SELECT name FROM departments")
    departments = [dept[0] for dept in c.fetchall()]
    conn.close()
    
    return render_template('add_employee.html', departments=departments)

@app.context_processor
def inject_email_config():
    """Make email configuration status available to all templates"""
    email_configured = (EMAIL_CONFIG.get('enabled', False) and 
                        EMAIL_CONFIG.get('email') and 
                        EMAIL_CONFIG.get('password'))
    return {'email_configured': email_configured}

@app.route('/view')
@admin_required
def view_employees():
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    employees = c.fetchall()
    conn.close()
    return render_template('view_employees.html', employees=employees, email_configured=EMAIL_CONFIG['enabled'])

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_employee(id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        department = request.form['department']
        salary = float(request.form['salary'])
        tax_rate = float(request.form['tax_rate']) / 100  # Convert percentage to decimal
        allowances = float(request.form['allowances'])
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        
        # Get the department name from the department ID
        if department:
            c.execute("SELECT name FROM departments WHERE id=?", (department,))
            dept_result = c.fetchone()
            if dept_result:
                department = dept_result[0]
        
        c.execute("UPDATE employees SET name=?, position=?, department=?, salary=?, tax_rate=?, allowances=?, email=?, phone=? WHERE id=?", 
                 (name, position, department, salary, tax_rate, allowances, email, phone, id))
        conn.commit()
        
        flash('Employee updated successfully!', 'success')
        return redirect('/view')
    
    # Get employee data
    c.execute("SELECT * FROM employees WHERE id=?", (id,))
    employee = c.fetchone()
    
    # Get departments for dropdown
    c.execute("SELECT id, name FROM departments")
    departments = c.fetchall()
    
    # Find the department ID for the current employee's department
    selected_dept_id = None
    if employee[3]:  # If employee has a department
        c.execute("SELECT id FROM departments WHERE name=?", (employee[3],))
        dept_result = c.fetchone()
        if dept_result:
            selected_dept_id = dept_result[0]
    
    conn.close()
    
    return render_template('edit_employee.html', 
                          employee=employee, 
                          departments=departments,
                          selected_dept_id=selected_dept_id)


@app.route('/delete/<int:id>')
@admin_required
def delete_employee(id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("DELETE FROM employees WHERE id=?", (id,))
    conn.commit()
    conn.close()
    
    flash('Employee deleted successfully!', 'warning')
    return redirect('/view')

@app.route('/payroll')
@admin_required
def calculate_payroll():
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, department, salary, tax_rate, allowances FROM employees")
    employees = c.fetchall()
    conn.close()
    
    payroll_data = []
    total_gross = 0
    total_tax = 0
    total_net = 0
    
    for emp in employees:
        emp_id, name, department, salary, tax_rate, allowances = emp
        gross_pay = salary
        tax_amount = gross_pay * tax_rate
        net_pay = gross_pay - tax_amount + allowances
        
        payroll_data.append({
            'id': emp_id,
            'name': name,
            'department': department,
            'gross_pay': gross_pay,
            'tax_amount': tax_amount,
            'allowances': allowances,
            'net_pay': net_pay
        })
        
        total_gross += gross_pay
        total_tax += tax_amount
        total_net += net_pay
    
    summary = {
        'total_gross': total_gross,
        'total_tax': total_tax,
        'total_net': total_net
    }
    
    return render_template('calculate_payroll.html', 
                          payroll=payroll_data, 
                          summary=summary)

@app.route('/departments', methods=['GET', 'POST'])
@admin_required
def manage_departments():
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        department_name = request.form['department_name']
        c.execute("INSERT INTO departments (name) VALUES (?)", (department_name,))
        conn.commit()
        flash('Department added successfully!', 'success')
    
    c.execute("SELECT * FROM departments")
    departments = c.fetchall()
    
    # Get count of employees by department
    dept_counts = {}
    for dept in departments:
        c.execute("SELECT COUNT(*) FROM employees WHERE department=?", (dept[1],))
        dept_counts[dept[0]] = c.fetchone()[0]
    
    conn.close()
    
    return render_template('departments.html', 
                          departments=departments, 
                          dept_counts=dept_counts)

@app.route('/delete_department/<int:id>')
@admin_required
def delete_department(id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get department name
    c.execute("SELECT name FROM departments WHERE id=?", (id,))
    dept_name = c.fetchone()[0]
    
    # Check if department is in use
    c.execute("SELECT COUNT(*) FROM employees WHERE department=?", (dept_name,))
    if c.fetchone()[0] > 0:
        flash('Cannot delete department that has employees!', 'danger')
    else:
        c.execute("DELETE FROM departments WHERE id=?", (id,))
        conn.commit()
        flash('Department deleted successfully!', 'warning')
    
    conn.close()
    return redirect('/departments')

@app.route('/export_payroll')
@admin_required
def export_payroll():
    try:
        # Ensure static directory exists
        os.makedirs('static', exist_ok=True)
        
        conn = sqlite3.connect('payroll_system/database.db')
        c = conn.cursor()
        c.execute("SELECT id, name, department, salary, tax_rate, allowances FROM employees")
        employees = c.fetchall()
        conn.close()
        
        # Full path to the export file - use absolute path to avoid any directory issues
        export_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'payroll_export.csv')
        
        # Open the file directly and write to it
        with open(export_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['ID', 'Name', 'Department', 'Gross Pay', 'Tax Amount', 'Allowances', 'Net Pay'])
            
            # Write data rows
            for emp in employees:
                emp_id, name, department, salary, tax_rate, allowances = emp
                gross_pay = salary
                tax_amount = gross_pay * tax_rate
                net_pay = gross_pay - tax_amount + allowances
                
                writer.writerow([
                    emp_id, name, department, 
                    f"{gross_pay:.2f}", f"{tax_amount:.2f}", 
                    f"{allowances:.2f}", f"{net_pay:.2f}"
                ])
        
        # Verify file exists and has content
        if os.path.exists(export_path) and os.path.getsize(export_path) > 0:
            flash('Payroll data exported successfully! <a href="/static/payroll_export.csv" download>Download CSV</a>', 'success')
        else:
            flash('Error creating export file. Please try again.', 'danger')
            
        return redirect('/payroll')
        
    except Exception as e:
        flash(f'Export error: {str(e)}', 'danger')
        return redirect('/payroll')
    

@app.route('/department_report')
@admin_required
def department_report():
    try:
        conn = sqlite3.connect('payroll_system/database.db')
        c = conn.cursor()
        
        # Get all departments
        c.execute("SELECT name FROM departments")
        departments = [dept[0] for dept in c.fetchall()]
        
        dept_data = {}
        for dept in departments:
            # Get employee count
            c.execute("SELECT COUNT(*) FROM employees WHERE department=?", (dept,))
            emp_count = c.fetchone()[0]
            
            # Get salary stats only if there are employees in this department
            if emp_count > 0:
                c.execute("SELECT SUM(salary), AVG(salary), MIN(salary), MAX(salary) FROM employees WHERE department=?", (dept,))
                salary_data = c.fetchone()
                
                dept_data[dept] = {
                    'count': emp_count,
                    'total_salary': round(salary_data[0], 2) if salary_data[0] else 0,
                    'avg_salary': round(salary_data[1], 2) if salary_data[1] else 0,
                    'min_salary': round(salary_data[2], 2) if salary_data[2] else 0,
                    'max_salary': round(salary_data[3], 2) if salary_data[3] else 0
                }
            else:
                # Include departments with 0 employees for completeness
                dept_data[dept] = {
                    'count': 0,
                    'total_salary': 0,
                    'avg_salary': 0,
                    'min_salary': 0,
                    'max_salary': 0
                }
        
        conn.close()
        
        return render_template('department_report.html', dept_data=dept_data)
        
    except Exception as e:
        flash(f'Error generating department report: {str(e)}', 'danger')
        return redirect('/')

def generate_payslip_pdf(employee_data, payroll_data, month, year):
    """Generate a professional PDF payslip"""
    
    # Create filename
    filename = f"payslip_{employee_data[1].replace(' ', '_')}_{month}_{year}.pdf"
    filepath = os.path.join('static', 'payslips', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("PAYSLIP", title_style))
    
    # Company header
    header_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Normal'],
        fontSize=14,
        spaceAfter=20,
        alignment=1
    )
    story.append(Paragraph("Payroll Management System", header_style))
    story.append(Spacer(1, 20))
    
    # Employee and pay period info
    emp_info_data = [
        ['Employee Information', '', 'Pay Period', ''],
        ['Name:', employee_data[1], 'Month:', month],
        ['Position:', employee_data[2], 'Year:', str(year)],
        ['Department:', employee_data[3], 'Generated:', datetime.now().strftime('%Y-%m-%d')],
        ['Employee ID:', str(employee_data[0]), '', '']
    ]
    
    emp_info_table = Table(emp_info_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
    emp_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(emp_info_table)
    story.append(Spacer(1, 30))
    
    # Salary breakdown
    salary_data = [
        ['Description', 'Amount (₹)'],
        ['Gross Salary', f"{payroll_data['gross_pay']:.2f}"],
        ['Tax Deduction', f"-{payroll_data['tax_amount']:.2f}"],
        ['Allowances', f"+{payroll_data['allowances']:.2f}"],
        ['', ''],
        ['Net Salary', f"{payroll_data['net_pay']:.2f}"]
    ]
    
    salary_table = Table(salary_data, colWidths=[4*inch, 2*inch])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
    ]))
    
    story.append(salary_table)
    story.append(Spacer(1, 50))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=1
    )
    story.append(Paragraph("This is a computer-generated payslip and does not require a signature.", footer_style))
    
    # Build PDF
    doc.build(story)
    
    return filepath

@app.route('/generate_payslip/<int:employee_id>')
@admin_required
def generate_payslip(employee_id):
    month = request.args.get('month', datetime.now().strftime('%B'))
    year = request.args.get('year', datetime.now().year, type=int)
    
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get employee data
    c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee = c.fetchone()
    
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('view_employees'))
    
    # Calculate payroll
    gross_pay = employee[4]  # salary
    tax_amount = gross_pay * employee[5]  # tax_rate
    allowances = employee[6]  # allowances
    net_pay = gross_pay - tax_amount + allowances
    
    payroll_data = {
        'gross_pay': gross_pay,
        'tax_amount': tax_amount,
        'allowances': allowances,
        'net_pay': net_pay
    }
    
    try:
        # Generate PDF
        pdf_path = generate_payslip_pdf(employee, payroll_data, month, year)
        
        # Save payslip record
        c.execute("""INSERT INTO payslips (employee_id, month, year, gross_pay, tax_amount, allowances, net_pay, generated_by, pdf_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (employee_id, month, year, gross_pay, tax_amount, allowances, net_pay, current_user.id, pdf_path))
        conn.commit()
        
        flash(f'Payslip generated successfully for {employee[1]}!', 'success')
        
        # Return PDF file
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
        
    except Exception as e:
        flash(f'Error generating payslip: {str(e)}', 'danger')
        return redirect(url_for('view_employees'))
    finally:
        conn.close()

@app.route('/download_payslip/<int:payslip_id>')
@employee_required
def download_payslip(payslip_id):
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Check if user can access this payslip
    if current_user.role == 'admin':
        c.execute("SELECT pdf_path, employee_id FROM payslips WHERE id = ?", (payslip_id,))
    else:
        c.execute("SELECT pdf_path, employee_id FROM payslips WHERE id = ? AND employee_id = ?", 
                 (payslip_id, current_user.employee_id))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        flash('Payslip not found or access denied.', 'danger')
        return redirect(url_for('employee_dashboard'))
    
    pdf_path, employee_id = result
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    else:
        flash('PDF file not found.', 'danger')
        return redirect(url_for('employee_dashboard'))

@app.route('/send_payslip/<int:employee_id>')
@admin_required
def send_payslip(employee_id):
    # Check if email is configured before proceeding
    if not EMAIL_CONFIG.get('enabled', False) or not EMAIL_CONFIG.get('email') or not EMAIL_CONFIG.get('password'):
        flash('Email is not configured. Please update EMAIL_CONFIG in app.py to enable email functionality.', 'warning')
        return redirect(url_for('view_employees'))
    
    month = request.args.get('month', datetime.now().strftime('%B'))
    year = request.args.get('year', datetime.now().year, type=int)
    
    conn = sqlite3.connect('payroll_system/database.db')
    c = conn.cursor()
    
    # Get employee data
    c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    employee = c.fetchone()
    
    if not employee or not employee[7]:  # employee[7] is email
        flash('Employee not found or email not provided.', 'danger')
        conn.close()
        return redirect(url_for('view_employees'))
    
    # Calculate payroll
    gross_pay = employee[4]
    tax_amount = gross_pay * employee[5]
    allowances = employee[6]
    net_pay = gross_pay - tax_amount + allowances
    
    payroll_data = {
        'gross_pay': gross_pay,
        'tax_amount': tax_amount,
        'allowances': allowances,
        'net_pay': net_pay
    }
    
    try:
        # Generate PDF
        pdf_path = generate_payslip_pdf(employee, payroll_data, month, year)
        
        # Save payslip record
        c.execute("""INSERT INTO payslips (employee_id, month, year, gross_pay, tax_amount, allowances, net_pay, generated_by, pdf_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (employee_id, month, year, gross_pay, tax_amount, allowances, net_pay, current_user.id, pdf_path))
        conn.commit()
        
        # Send email
        subject = f"Payslip for {month} {year}"
        body = f"""Dear {employee[1]},

Please find attached your payslip for {month} {year}.

Payslip Summary:
- Gross Pay: ₹{gross_pay:.2f}
- Tax Deduction: ₹{tax_amount:.2f}
- Allowances: ₹{allowances:.2f}
- Net Pay: ₹{net_pay:.2f}

Best regards,
HR Department
Payroll Management System"""

        success, message = send_email_with_attachment(employee[7], subject, body, pdf_path)
        
        if success:
            flash(f'Payslip generated and sent successfully to {employee[1]} at {employee[7]}!', 'success')
        else:
            flash(f'Payslip generated but email failed: {message}. Please check email configuration.', 'warning')
        
        return redirect(url_for('view_employees'))
        
    except Exception as e:
        flash(f'Error processing payslip: {str(e)}', 'danger')
        return redirect(url_for('view_employees'))
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starting Payroll Management System...")
    # Create a backup before starting
    if os.path.exists('payroll_system/database.db'):
        backup_database()
    
    init_db()
    # Remove debug=True for production to prevent data loss on restarts
    app.run(debug=False, host='127.0.0.1', port=5000)
# 📧 Email Setup Guide for Payroll Management System

## Quick Setup Steps

### Step 1: Enable Gmail App Passwords

1. **Go to Google Account Settings**
   - Visit: https://myaccount.google.com/
   - Sign in with your Gmail account

2. **Enable 2-Step Verification** (Required first)
   - Go to "Security" → "2-Step Verification"
   - Follow the setup process (you'll need your phone)

3. **Generate App Password**
   - Go to "Security" → "App passwords"
   - Click "Select app" → Choose "Mail"
   - Click "Select device" → Choose "Other (custom name)"
   - Type: "Payroll System"
   - Click "Generate"
   - **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

### Step 2: Configure Your Payroll System

1. **Open `app.py` file**

2. **Find the EMAIL_CONFIG section** (around line 30):

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': '',  # YOUR EMAIL HERE
    'password': '',  # YOUR APP PASSWORD HERE
    'use_tls': True,
    'enabled': False  # Change to True
}
```

3. **Update the configuration**:
   - `'email': 'your.email@gmail.com'` ← Your actual Gmail address
   - `'password': 'abcd efgh ijkl mnop'` ← The 16-character app password
   - `'enabled': True` ← Change from False to True

### Step 3: Example Configuration

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'gokila.example@gmail.com',  # ← Your email
    'password': 'abcd efgh ijkl mnop',     # ← Your app password
    'use_tls': True,
    'enabled': True  # ← Set to True
}
```

### Step 4: Test Email Functionality

1. **Restart your Flask application**
2. **Add an employee with an email address**
3. **Go to View Employees page**
4. **Click the green envelope button** next to an employee
5. **Check if the email was sent successfully**

## 🚨 Important Security Notes

- **NEVER use your regular Gmail password** - only use App Passwords
- **Keep your app password secure** - don't share it
- **Don't commit credentials to Git** - add `app.py` to `.gitignore` if sharing code

## 🔧 Troubleshooting

### "Email is not configured" message
- Make sure `'enabled': True` in EMAIL_CONFIG
- Check that email and password fields are not empty

### "Authentication failed" error
- Verify you're using an App Password, not regular password
- Ensure 2-Step Verification is enabled on your Google account
- Double-check the email address is correct

### "SMTP connection failed"
- Check your internet connection
- Gmail SMTP might be blocked on some networks
- Try using a different network

### Email button not showing
- Employee must have an email address in the system
- Email must be configured and enabled
- Only admins can send emails

## 📱 Alternative Email Providers

If you don't want to use Gmail, update EMAIL_CONFIG:

### Outlook/Hotmail:
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp-mail.outlook.com',
    'smtp_port': 587,
    'email': 'your.email@outlook.com',
    'password': 'your_app_password',
    'use_tls': True,
    'enabled': True
}
```

### Yahoo Mail:
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.mail.yahoo.com',
    'smtp_port': 587,
    'email': 'your.email@yahoo.com',
    'password': 'your_app_password',
    'use_tls': True,
    'enabled': True
}
```

## ✅ Once Configured Successfully

Your payroll system will be able to:
- ✉️ Send payslips via email to employees
- 📄 Include PDF attachments automatically
- 📧 Show email buttons in the interface
- 🔔 Provide success/error notifications

---

**Need Help?** The email functionality is optional - your system works perfectly without it for PDF downloads!
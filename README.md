# College Exam Portal — Beginner Setup Guide

This is a **starter project** (Login System + Role-based Dashboards).
Get this running first, then we'll add features step by step.

---

## Folder Structure Explanation

```
college-exam-portal/
│
├── app/
│   ├── __init__.py          → Flask app is created here
│   ├── models/
│   │   └── user.py          → Code for reading/writing user data in the database
│   ├── routes/
│   │   ├── auth.py          → Login, Register, Logout
│   │   └── dashboard.py     → Admin/Teacher/Student dashboard routes
│   ├── templates/           → All HTML pages (Jinja2)
│   │   ├── auth/             → login.html, register.html
│   │   ├── admin/             → admin dashboard
│   │   ├── teacher/           → teacher dashboard
│   │   └── student/           → student dashboard
│   └── static/
│       ├── css/style.css    → Styling
│       ├── js/               → JavaScript files (added later)
│       └── uploads/          → User photos, question images get saved here
│
├── config/
│   └── config.py            → App settings (DB connection, secret key)
│
├── database/
│   └── schema.sql           → SQL script that creates all MySQL tables
│
├── .env                     → Passwords/secrets (never commit this to GitHub)
├── requirements.txt         → List of required Python packages
├── run.py                   → Starts the app
├── create_admin.py          → Creates the first Admin account
└── test_db_connection.py    → Debug tool to test the MySQL connection
```

---

## Step-by-Step Setup (From Scratch)

### Step 1: Move the project folder to your computer
Copy the whole `college-exam-portal` folder anywhere on your computer (e.g. `Desktop/college-exam-portal`).

### Step 2: Create a Virtual Environment (in Terminal/CMD)
```bash
cd college-exam-portal
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

Once activated, you'll see `(venv)` at the start of your terminal line.

### Step 3: Install Packages
```bash
pip install -r requirements.txt
```

> If `mysqlclient` fails to install (common on Windows), try:
> ```bash
> pip install --only-binary :all: mysqlclient
> ```

### Step 4: Create the Database in MySQL
1. Open MySQL Workbench (or run `mysql -u root -p` in a terminal)
2. Open and run the `database/schema.sql` file — this creates the
   `college_exam_portal` database along with all the required tables

> **Already have the database from before?** If you set up this project earlier,
> just run the extra migration files once on your existing database:
> ```bash
> mysql -u root -p college_exam_portal < database/migration_2_student_features.sql
> mysql -u root -p college_exam_portal < database/migration_3_forgot_password.sql
> mysql -u root -p college_exam_portal < database/migration_4_notifications.sql
> mysql -u root -p college_exam_portal < database/migration_5_settings_and_photos.sql
> mysql -u root -p college_exam_portal < database/migration_6_student_registration.sql
> mysql -u root -p college_exam_portal < database/migration_7_images_in_db.sql

> ⚠️ **Important behavior changes after migration_6:**
> - Students now log in with their **Registration Number** (not email) — the login page field is labeled "Email or Registration Number" and accepts both.
> - Students who self-register now **also need admin approval** before they can log in (previously they were active immediately).
> - If you already have student accounts from before this update, they won't have a Registration Number yet — as admin, edit each one (Manage Students → Edit) to add one, or ask them to contact you.
> ```
> Brand new installs don't need this — `schema.sql` already includes everything.

### Step 5: Update the `.env` File
Open `.env` and set your actual MySQL password:
```
MYSQL_PASSWORD=your_actual_mysql_password
```

For the "Forgot Password" feature to send real emails, also fill in `MAIL_USERNAME`
and `MAIL_PASSWORD` (see the comments inside `.env` for how to get a Gmail App
Password). **This is optional** — if you skip it, the app will just show the OTP
directly on screen instead of emailing it, so you can still test the feature.

### Step 6: Test Your Database Connection (recommended)
```bash
python test_db_connection.py
```
You should see `SUCCESS! Connected to MySQL.`

### Step 7: Create the First Admin Account
```bash
python create_admin.py
```
Expected output:
```
Admin account created successfully!
   Email: admin@college.com
   Password: Admin@123
```

### Step 8: Start the App!
```bash
python run.py
```

Go to: **http://localhost:5000**

Log in with:
- **Email:** admin@college.com
- **Password:** Admin@123

---

## What's Working Right Now

- Secure login (with password hashing)
- Registration page (Student/Teacher)
- Role-based dashboards (Admin/Teacher/Student, each different)
- Session management + Logout
- Login attempt limiting (blocks after 5 failed attempts)
- Modern responsive UI (Bootstrap 5 + glassmorphism)

## What We'll Build Next (Step by Step)

1. Admin: Teacher/Student CRUD (Add/Edit/Delete)
2. Teacher: "Create Test" form + Question Bank
3. Student: "Attempt Test" page with a timer
4. Auto-evaluation + Result system
5. Reports & Charts (Chart.js)
6. Advanced features (AI proctoring, etc.) — built last

---

## Common Errors & Solutions

| Error | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Virtual env isn't activated — repeat Step 2 |
| `Access denied for user 'root'` | Wrong password in `.env` — double check it |
| `Unknown database 'college_exam_portal'` | You haven't run `database/schema.sql` yet — repeat Step 4 |
| `mysqlclient` install fails | Try the alternate command in Step 3 |
| `'mysql' is not recognized...` | MySQL isn't in your Windows PATH — use the full path to `mysql.exe`, or add MySQL's `bin` folder to PATH |
| Page not found (404) | Check that `python run.py` is actually running |

---

## Deploying Online (Render)

Want your project live on the internet so anyone can access it? See
**[DEPLOYMENT.md](DEPLOYMENT.md)** for a full step-by-step guide covering
GitHub, a free cloud MySQL database, and Render.

---

**In your next message, tell me which feature to build next — e.g. "Build the Teacher Create Test feature" — and I'll build it step by step.**

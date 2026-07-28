# Deploying to Render — Step-by-Step Guide

Render doesn't offer a free MySQL database (only PostgreSQL), so we'll use
**Aiven** for a genuinely free MySQL database (no credit card, supports
foreign keys — unlike PlanetScale, which dropped its free tier and doesn't
support foreign keys at all).

**Overview of what we're doing:**
1. Push your code to GitHub
2. Create a free MySQL database on Aiven
3. Import your schema into it
4. Create a Web Service on Render, pointed at your GitHub repo
5. Set environment variables on Render (instead of using `.env`)

---

## Step 1: Push Your Code to GitHub

If you don't have Git installed, download it from https://git-scm.com/downloads

In your project folder:
```bash
git init
git add .
git commit -m "Initial commit"
```

Create a new repository at https://github.com/new (don't add a README —
you already have one), then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/college-exam-portal.git
git branch -M main
git push -u origin main
```

> ✅ Your `.env` file will NOT be pushed (it's in `.gitignore`) — this is
> intentional, since it contains passwords. You'll set those directly in
> Render's dashboard instead (Step 4).

---

## Step 2: Create a Free MySQL Database on Aiven

1. Go to https://aiven.io/free-mysql-database and sign up (no card needed)
2. Create a new service → select **MySQL** → choose the **Free** plan
3. Pick a cloud region close to you, and wait ~2 minutes for it to start
4. Once it's running, open the service and go to the **Overview** tab —
   you'll see connection details:
   - **Host**
   - **Port** (NOT 3306 — Aiven uses a custom port, e.g. 14322)
   - **User** (usually `avnadmin`)
   - **Password**
   - **Database name** (usually `defaultdb`)
5. Download the **CA Certificate** shown on that same page (a `.pem` file) —
   you'll need it for SSL, since Aiven requires encrypted connections.

## Step 3: Import Your Schema into Aiven

Copy the downloaded CA certificate into your project, e.g.:
```
college-exam-portal/database/aiven-ca.pem
```

Then run your schema against the Aiven database from your computer:
```bash
mysql --host=YOUR_AIVEN_HOST --port=YOUR_AIVEN_PORT --user=avnadmin -p \
      --ssl-ca=database/aiven-ca.pem defaultdb < database/schema.sql
```
(Enter the Aiven password when prompted.)

> This creates all your tables directly on the cloud database — schema.sql
> already includes everything (users, tests, questions, notifications, etc.)
> for a fresh install, so you don't need to run the other migration files
> separately.

Create your first Admin account against this same database:
```bash
mysql --host=YOUR_AIVEN_HOST --port=YOUR_AIVEN_PORT --user=avnadmin -p \
      --ssl-ca=database/aiven-ca.pem defaultdb
```
Then inside the MySQL prompt, paste (replace the password hash — see note below):
```sql
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Super Admin', 'admin@college.com',
        'pbkdf2:sha256:600000$...your-generated-hash...', 'admin', 1);
```
> Getting a real password hash: run this on your computer first —
> `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourPassword123'))"`
> — then paste the output into the SQL above.

---

## Step 4: Create the Web Service on Render

1. Go to https://render.com and sign up / log in
2. Click **New +** → **Web Service**
3. Connect your GitHub account and select your `college-exam-portal` repo
4. Fill in:
   - **Name:** `college-exam-portal` (or anything you like)
   - **Region:** closest to you
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
   - **Instance Type:** Free

5. Before clicking "Create", scroll to **Environment Variables** and add:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | any long random string |
   | `MYSQL_HOST` | your Aiven host |
   | `MYSQL_PORT` | your Aiven port |
   | `MYSQL_USER` | `avnadmin` |
   | `MYSQL_PASSWORD` | your Aiven password |
   | `MYSQL_DB` | `defaultdb` |
   | `MYSQL_SSL_CA` | `database/aiven-ca.pem` |
   | `MAIL_USERNAME` | your Gmail address (optional) |
   | `MAIL_PASSWORD` | your Gmail App Password (optional) |
   | `PYTHON_VERSION` | `3.11.9` |

6. Click **Create Web Service**. Render will install dependencies and start
   your app — first build takes 2–5 minutes. Watch the **Logs** tab for
   progress or errors.

7. Once live, Render gives you a URL like:
   `https://college-exam-portal.onrender.com`

---

## ⚠️ Important Limitations (Free Tier)

- **App sleeps after 15 minutes of inactivity.** The first request after
  that takes ~30–60 seconds to "wake up" — this is normal on Render's free
  tier, not a bug.
- **Uploaded files don't persist.** Profile photos and the college logo are
  saved to the app's local disk, which Render **wipes on every redeploy or
  restart** on the free tier. For a college project demo this is usually
  fine — just re-upload if they disappear. (A permanent fix would mean
  storing uploads on something like Cloudinary or AWS S3 — a bigger change,
  ask if you'd like this built.)
- **Email OTP:** if you don't set `MAIL_USERNAME`/`MAIL_PASSWORD`, the
  Forgot Password OTP will show directly on the page instead of emailing it
  (same as local — see `app/routes/auth.py`).

---

## Updating Your Live Site Later

Every time you `git push` to the `main` branch, Render automatically
rebuilds and redeploys — no extra steps needed.

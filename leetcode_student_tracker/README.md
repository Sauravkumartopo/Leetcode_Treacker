# LeetCode Student Tracker — v1 Prototype

Faculty dashboard for tracking public LeetCode problem-solving activity.

## Features
- Overview dashboard
- Student search and detail view
- Easy / Medium / Hard solved counts
- Total submissions and acceptance rate when exposed by the public profile
- Latest recorded submission time
- Configurable Active / Needs Attention / Inactive status
- Leaderboards: total solved, difficulty score, weekly solved, consistency/activity
- Analytics charts
- CSV student import
- CSV leaderboard export
- Optional public-profile live sync
- SQLite local database

## Run
Python 3.10+ recommended.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
Community Cloud deploys from GitHub. In this repository, the app and its `requirements.txt` are inside the `leetcode_student_tracker` subdirectory. Do not upload `leetcode_tracker.db`, `.env`, or passwords into GitHub; `.gitignore` excludes them.

1. From the repository root (the folder containing `README.md` and `leetcode_student_tracker`), publish the signup changes to the existing GitHub repository:

```powershell
git add leetcode_student_tracker/app.py leetcode_student_tracker/password_auth.py leetcode_student_tracker/email_verification.py leetcode_student_tracker/README.md leetcode_student_tracker/compose.yaml leetcode_student_tracker/.env.example leetcode_student_tracker/.gitignore
git commit -m "Require email verification for admin signup"
git push
```

2. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and choose **Create app**. Select your repository, branch `main`, and main file path `leetcode_student_tracker/app.py`. The `requirements.txt` beside the entrypoint will be installed automatically.
3. Create a Resend account using `sktopo26@gmail.com`, create an API key, then add it in **App settings → Secrets**:

```toml
RESEND_API_KEY = "re_..."
```

The app uses Resend's `onboarding@resend.dev` sender by default. Resend test sending is limited to the email address on your Resend account, so use `sktopo26@gmail.com` for that account. For a different account or production sender, verify a sending domain in Resend and optionally add `RESEND_FROM_EMAIL = "LeetCode Student Tracker <codes@your-verified-domain.com>"` to Secrets. Delivery uses HTTPS, not SMTP. Before initial signup, set app sharing to private if available. Open **Data Management → Sign Up**, create the administrator username and a password of at least 12 characters, request the email code, and enter it before creating the account. The code expires in 10 minutes, allows five attempts, and is rate-limited to one request per minute and five per hour. Signup closes after the first administrator account is created.

**Protect student data:** the admin password only protects roster changes. The Overview, Students, Leaderboard, and Analytics pages are otherwise visible to anyone who can open the app. Set app sharing to private and verify access while signed out before using real student names or USNs. If private sharing is unavailable for your account, do not deploy identifiable student data publicly without adding viewer authentication.

**Persistence limitation:** the SQLite file is excluded from Git and Community Cloud's local filesystem is not durable storage. Data may be lost when the app restarts or redeploys. This deployment path is suitable for a demo; use an external persistent database before relying on it for a live student roster. Export/import the roster with CSV when testing.

## VPS Deployment
The Compose deployment runs one Streamlit instance with SQLite on a persistent volume and Caddy as an HTTPS reverse proxy. You need an Ubuntu VPS with a public IP, a DNS name pointed at that IP, and Docker Engine with the Compose plugin. Do not run multiple app replicas with SQLite.

1. Create a DNS `A` record for your domain pointing to the VPS. Allow inbound TCP ports 80 and 443 (and UDP 443 for HTTP/3) in the provider firewall. Keep SSH access enabled.
2. Install Docker Engine and the Compose plugin using the [official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
3. Push this project to a Git repository, then clone it on the VPS and enter the `leetcode_student_tracker` directory.
4. Create the protected environment file and replace the domain with your real DNS name:

```bash
read -r -p "Public domain: " DOMAIN
read -r -s -p "Resend API key: " RESEND_API_KEY
printf '\n'
umask 077
printf 'DOMAIN=%s\nRESEND_API_KEY=%s\n' "$DOMAIN" "$RESEND_API_KEY" > .env
unset RESEND_API_KEY
```

5. Start the deployment and check service health:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f proxy
```

Caddy obtains and renews the TLS certificate automatically after DNS resolves and ports 80/443 are reachable. Open `https://your-domain`. Streamlit is not published directly on a host port. The `.env` file is excluded from Git. SQLite and Caddy certificates persist in named Docker volumes; back them up. `docker compose down -v` deletes those volumes and the database. For updates, run `git pull` followed by `docker compose up --build -d`.

The one-time administrator signup is a basic profile-management gate, not individual faculty identity or role-based access. For multiple accounts or replicas, use PostgreSQL, individual authentication, and managed backups.

## Student Profile Authorization
Adding, deleting, and importing student profiles requires the verified administrator account. Signup sends a six-digit code to `sktopo26@gmail.com`; the account is created only after the code is entered correctly. Codes expire after 10 minutes. The app stores only salted PBKDF2-SHA256 password hashes in SQLite. Use **Log Out of Profile Management** to end the authorized session. Keep the Resend API key in Streamlit Cloud Secrets or the VPS `.env`; never commit it.

## Student CSV
`student_id,usn,name,section,leetcode_username`

## Data notes
The dashboard calls the latest recorded submission **Last submission**, not page-visit activity. A complete lifetime distinct "attempted problems" count is not inferred from the public profile alone; the app stores observable recent submissions so a stronger collector can be added later.

The public profile and recent-submission interfaces can change. Before institutional deployment, add individual faculty accounts with role-based authorization, rate limiting, scheduled snapshots, PostgreSQL, audit logging and an approved/permissioned data source where required. The shared administrator password is a basic profile-management gate, not a substitute for individual accounts.

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
Community Cloud deploys from GitHub. The simplest repository layout is to make the contents of this `leetcode_student_tracker` folder the repository root, so `app.py` and `requirements.txt` are both at the root. Do not upload `leetcode_tracker.db`, `.env`, or any password/hash into GitHub; `.gitignore` excludes them.

1. Create an empty GitHub repository. From PowerShell, in this folder, initialize and push the project (replace the URL with your repository URL):

```powershell
git init
git add .
git commit -m "Prepare LeetCode tracker for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

2. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub and choose **Create app**. Select your repository, branch `main`, and main file path `app.py`. The existing `requirements.txt` is beside the entrypoint and will be installed automatically.
3. Generate the admin hash locally with `py .\password_auth.py`; enter and confirm the password in the terminal. In the app's **Advanced settings** before deployment, or **App settings → Secrets** after deployment, add this TOML setting, replacing the value with the generated hash:

```toml
STUDENT_ADMIN_PASSWORD_HASH = "pbkdf2_sha256$600000$YOUR_SALT$YOUR_HASH"
```

4. Deploy or save the settings, then open the app and sign in on **Data Management** using the original password, not the hash.

**Protect student data:** the admin password only protects roster changes. The Overview, Students, Leaderboard, and Analytics pages are otherwise visible to anyone who can open the app. Set app sharing to private and verify access while signed out before using real student names or USNs. If private sharing is unavailable for your account, do not deploy identifiable student data publicly without adding viewer authentication.

**Persistence limitation:** the SQLite file is excluded from Git and Community Cloud's local filesystem is not durable storage. Data may be lost when the app restarts or redeploys. This deployment path is suitable for a demo; use an external persistent database before relying on it for a live student roster. Export/import the roster with CSV when testing.

## VPS Deployment
The Compose deployment runs one Streamlit instance with SQLite on a persistent volume and Caddy as an HTTPS reverse proxy. You need an Ubuntu VPS with a public IP, a DNS name pointed at that IP, and Docker Engine with the Compose plugin. Do not run multiple app replicas with SQLite.

1. Create a DNS `A` record for your domain pointing to the VPS. Allow inbound TCP ports 80 and 443 (and UDP 443 for HTTP/3) in the provider firewall. Keep SSH access enabled.
2. Install Docker Engine and the Compose plugin using the [official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
3. Push this project to a Git repository, then clone it on the VPS and enter the `leetcode_student_tracker` directory.
4. Create the protected environment file. Replace the domain with your real DNS name; the password prompts are hidden and the hash is captured directly into `.env`:

```bash
read -r -p "Public domain: " DOMAIN
STUDENT_ADMIN_PASSWORD_HASH="$(python3 password_auth.py)" || exit 1
umask 077
printf 'DOMAIN=%s\nSTUDENT_ADMIN_PASSWORD_HASH=%s\n' "$DOMAIN" "$STUDENT_ADMIN_PASSWORD_HASH" > .env
unset STUDENT_ADMIN_PASSWORD_HASH
```

5. Start the deployment and check service health:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f proxy
```

Caddy obtains and renews the TLS certificate automatically after DNS resolves and ports 80/443 are reachable. Open `https://your-domain`. Streamlit is not published directly on a host port. The `.env` file is excluded from Git. SQLite and Caddy certificates persist in named Docker volumes; back them up. `docker compose down -v` deletes those volumes and the database. For updates, run `git pull` followed by `docker compose up --build -d`.

The shared admin password is a basic profile-management gate, not individual faculty identity or role-based access. For multiple users or replicas, use PostgreSQL, individual authentication, and managed backups.

## Student Profile Authorization
Adding, deleting, and importing student profiles requires an administrator password. The app stores only a salted PBKDF2-SHA256 password hash in the `STUDENT_ADMIN_PASSWORD_HASH` environment variable. Generate a hash in PowerShell from this folder; the password is entered without being echoed:

```powershell
$hash = py .\password_auth.py
$env:STUDENT_ADMIN_PASSWORD_HASH = $hash.Trim()
streamlit run app.py
```

The generator prompts twice to confirm the password and prints only its salted hash. Keep the hash in a protected environment variable; do not put the original password or hash in source control. The previous plaintext `STUDENT_ADMIN_PASSWORD` setting is no longer used. Without `STUDENT_ADMIN_PASSWORD_HASH`, profile-management actions stay disabled. After login, use **Log Out of Profile Management** to end the authorized session.

## Student CSV
`student_id,usn,name,section,leetcode_username`

## Data notes
The dashboard calls the latest recorded submission **Last submission**, not page-visit activity. A complete lifetime distinct "attempted problems" count is not inferred from the public profile alone; the app stores observable recent submissions so a stronger collector can be added later.

The public profile and recent-submission interfaces can change. Before institutional deployment, add individual faculty accounts with role-based authorization, rate limiting, scheduled snapshots, PostgreSQL, audit logging and an approved/permissioned data source where required. The shared administrator password is a basic profile-management gate, not a substitute for individual accounts.

# Architecture

Browser → Streamlit UI → SQLite

Optional sync:
Streamlit → LeetCode public GraphQL → profile stats + recent submissions → SQLite

Tables:
- students
- stats
- submissions
- daily_activity

Deployment baseline:
- Docker image runs as a non-root user
- SQLite path configurable with STUDENT_TRACKER_DB_PATH
- Docker volume persists the database between container replacements
- Health check monitors the Streamlit endpoint
- Admin password verified against a salted PBKDF2-SHA256 hash

Production roadmap for multi-user or horizontally scaled deployments:
- FastAPI backend
- PostgreSQL
- Scheduled worker
- Individual faculty accounts and role-based authorization
- Student self-service view
- Historical snapshots
- Robust attempted-problem calculation from a permitted complete submission source

# Corvus Restore Protocol

Step-by-step guide to restore Corvus from scratch on a fresh Linux environment (tested on ChromeOS/Crostini Debian).

---

## Prerequisites

| Component | Version Used | Install |
|-----------|-------------|---------|
| Python | 3.11+ | `sudo apt install python3 python3-venv python3-pip` |
| Node.js | 20.x or 22.x | Via [nvm](https://github.com/nvm-sh/nvm) |
| PostgreSQL | 15.x | `sudo apt install postgresql postgresql-client` |
| Git | any | `sudo apt install git` |

---

## 1. Clone the Repository

```bash
mkdir -p ~/Projects && cd ~/Projects
git clone https://github.com/tylerbvogel-max/corvus.git
cd corvus
```

---

## 2. Set Up PostgreSQL

Start the service and create the database user and database:

```bash
sudo service postgresql start
sudo -u postgres psql <<SQL
CREATE USER corvus WITH PASSWORD 'corvus';
CREATE DATABASE corvus OWNER corvus;
GRANT ALL PRIVILEGES ON DATABASE corvus TO corvus;
SQL
```

Verify connectivity:

```bash
psql -U corvus -h localhost -c "SELECT 1;" corvus
```

> If prompted for a password, it's `corvus`. You can add `localhost:5432:corvus:corvus:corvus` to `~/.pgpass` and `chmod 600 ~/.pgpass` to skip prompts.

---

## 3. Restore the Database Backup

Backups are gzipped SQL dumps stored in the project root.

```bash
cd ~/Projects/corvus

# Find the latest backup
ls -lt corvus_backup_*.sql.gz | head -1

# Restore it (replace filename with latest)
gunzip -c corvus_backup_2026-03-11.sql.gz | psql -U corvus -h localhost corvus
```

> If restoring into a database that already has data, drop and recreate first:
> ```bash
> sudo -u postgres psql -c "DROP DATABASE corvus;"
> sudo -u postgres psql -c "CREATE DATABASE corvus OWNER corvus;"
> gunzip -c corvus_backup_2026-03-11.sql.gz | psql -U corvus -h localhost corvus
> ```

Verify the restore:

```bash
psql -U corvus -h localhost corvus -c "SELECT COUNT(*) FROM neurons;"
# Expected: ~2100 neurons
psql -U corvus -h localhost corvus -c "SELECT COUNT(*) FROM neuron_edges;"
# Expected: ~390K+ edges
```

---

## 4. Set Up the Backend

```bash
cd ~/Projects/corvus/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

The backend reads config from environment or a `.env` file. The defaults work for local dev, but you need your Anthropic API key:

```bash
cat > ~/Projects/corvus/backend/.env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=postgresql+asyncpg://corvus:corvus@localhost:5432/corvus
EOF
```

### Start the Backend

```bash
cd ~/Projects/corvus/backend
source venv/bin/activate
uvicorn app.main:app --port 8002 --reload
```

Verify:

```bash
curl -s http://localhost:8002/health | python3 -m json.tool
# Should show status: ok, neuron_count: ~2100
```

---

## 5. Set Up the Frontend

```bash
cd ~/Projects/corvus/frontend
npm install
```

### For development:

```bash
npm run dev
# Runs on port 5173, proxies API calls to localhost:8002
```

### For production build (served by FastAPI):

```bash
npm run build
# Outputs to frontend/dist/, automatically served by the backend
```

---

## 6. Running as a Background Service (Optional)

To run the backend in the background without a terminal:

```bash
cd ~/Projects/corvus/backend
source venv/bin/activate
nohup uvicorn app.main:app --port 8002 --reload > /dev/null 2>&1 &
```

To stop it:

```bash
fuser -k 8002/tcp
```

---

## 7. Creating New Backups

Run this periodically or before any risky changes:

```bash
pg_dump -U corvus -h localhost corvus | gzip > ~/Projects/corvus/corvus_backup_$(date +%Y-%m-%d).sql.gz
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start PostgreSQL | `sudo service postgresql start` |
| Start backend | `cd backend && source venv/bin/activate && uvicorn app.main:app --port 8002 --reload` |
| Start frontend (dev) | `cd frontend && npm run dev` |
| Build frontend | `cd frontend && npm run build` |
| Health check | `curl localhost:8002/health` |
| Backup DB | `pg_dump -U corvus -h localhost corvus \| gzip > corvus_backup_$(date +%Y-%m-%d).sql.gz` |
| Restore DB | `gunzip -c backup.sql.gz \| psql -U corvus -h localhost corvus` |
| Kill backend | `fuser -k 8002/tcp` |

# PatchOps — Wazuh Patch Management Dashboard

Production-ready full-stack application for Wazuh security monitoring, vulnerability management, and incident response.

## Architecture

```
┌─────────────────────────┐     ┌──────────────────────────────┐
│   Vue 3 Frontend        │────▶│   FastAPI Backend (Python)    │
│   (Vite, Pinia)         │     │                              │
│   Port: 3000            │     │   • JWT Authentication       │
│                         │     │   • Wazuh API Proxy          │
│   Browser ── /api/* ──▶ │     │   • Indexer Proxy            │
│                         │     │   • Ticket CRUD              │
│   No credentials stored │     │   • Playbook CRUD            │
│   in browser            │     │   • NVD CVE Proxy            │
└─────────────────────────┘     │   Port: 8000                 │
                                │                              │
                                │   ┌─── Wazuh API (:55000)    │
                                │   ├─── Indexer (:9200)       │
                                │   ├─── NVD API (internet)    │
                                │   └─── data/ (JSON storage)  │
                                └──────────────────────────────┘
```

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Wazuh API URL and settings

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# From the project root
npm install
npm run dev
```

### 3. Access

- **Dashboard**: http://localhost:3000
- **API Docs** (debug mode): http://localhost:8000/api/docs
- **API Health**: http://localhost:8000/api/health

## Environment Variables

Edit `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET_KEY` | auto-generated | Secret for JWT signing (CHANGE for production!) |
| `JWT_EXPIRE_MINUTES` | `480` | Token expiry (8 hours) |
| `WAZUH_API_URL` | `https://10.10.56.199:55000` | Wazuh Manager API URL |
| `WAZUH_VERIFY_SSL` | `false` | Verify Wazuh API SSL cert |
| `INDEXER_URL` | `https://10.10.56.199:9200` | Wazuh Indexer / Elasticsearch URL |
| `INDEXER_VERIFY_SSL` | `false` | Verify Indexer SSL cert |
| `NVD_API_KEY` | *(empty)* | Optional NVD API key for higher rate limits |
| `DATA_DIR` | `./data` | Directory for JSON storage files |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |
| `APP_DEBUG` | `false` | Enable debug mode (shows /api/docs) |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login with Wazuh credentials |
| `POST` | `/api/auth/logout` | Invalidate session |
| `GET` | `/api/auth/status` | Check auth status |

### Agents (Wazuh Proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `GET` | `/api/agents/summary/status` | Agent status summary |

### Vulnerabilities (Wazuh Proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/vulnerability` | All vulnerabilities |
| `GET` | `/api/vulnerability/{agent_id}` | Agent vulnerabilities |
| `GET` | `/api/vulnerability/{agent_id}/summary/severity` | Severity summary |

### Syscollector (Wazuh Proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/syscollector/{id}/packages` | Installed packages |
| `GET` | `/api/syscollector/{id}/hardware` | Hardware info |
| `GET` | `/api/syscollector/{id}/os` | OS info |
| `GET` | `/api/syscollector/{id}/netaddr` | Network addresses |
| `GET` | `/api/syscollector/{id}/hotfixes` | Installed hotfixes |
| `GET` | `/api/sca/{id}` | SCA policies |

### Indexer (Elasticsearch Proxy)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/indexer/alerts/summary` | Alert aggregation |
| `GET` | `/api/indexer/alerts/{agent_id}` | Alert history details |
| `GET` | `/api/indexer/vulnerabilities/{agent_id}` | Active vulns |
| `GET` | `/api/indexer/fim/{agent_id}` | FIM history |
| `GET` | `/api/indexer/sca/{agent_id}` | SCA history |

### Tickets (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tickets` | List (with filters) |
| `POST` | `/api/tickets` | Create |
| `GET` | `/api/tickets/{id}` | Get by ID |
| `PUT` | `/api/tickets/{id}` | Update |
| `DELETE` | `/api/tickets/{id}` | Delete |
| `GET` | `/api/tickets/stats` | Statistics |
| `GET` | `/api/tickets/export` | Export JSON |
| `POST` | `/api/tickets/import` | Import JSON |

### Playbooks (CRUD)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/playbooks` | List all |
| `POST` | `/api/playbooks` | Create |
| `PUT` | `/api/playbooks/{id}` | Update |
| `DELETE` | `/api/playbooks/{id}` | Delete |
| `POST` | `/api/playbooks/match` | Match to ticket |
| `POST` | `/api/playbooks/seed` | Seed defaults |

### NVD
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/nvd/cves` | Search recent CVEs |
| `POST` | `/api/nvd/clear-cache` | Clear CVE cache |

## Security

- **JWT tokens stored in memory** — never in localStorage (XSS-safe)
- **Credentials never reach the browser** — Wazuh/Indexer creds stay server-side
- **Server-side session store** — JWT maps to a session on the backend
- **Auto 401 redirect** — expired sessions redirect to login

## Production Deployment

For production, use a process manager and reverse proxy:

```bash
# Backend with Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend build
npm run build
# Serve dist/ with Nginx
```

### Nginx Config Example

```nginx
server {
    listen 443 ssl;
    server_name patchops.internal;

    # Frontend
    location / {
        root /var/www/patchops/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Future: Database Migration

The storage layer (`backend/app/storage/`) uses a clean interface. To migrate to
PostgreSQL or another database, re-implement the functions in `tickets.py` and
`playbooks.py` with SQLAlchemy or another ORM — no other code changes needed.

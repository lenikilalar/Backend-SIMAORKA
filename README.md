# SIMAORKA Backend

**Sistem Manajemen Organisasi Kampus** - A comprehensive campus organization management system with Web3 integration.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis (optional, for caching)

### Installation

```bash
# Clone repository
git clone https://github.com/lenikilalar/Backend-SIMAORKA.git
cd Backend-SIMAORKA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Seed RBAC roles & permissions
python manage.py seed_rbac

# Run development server
python manage.py runserver
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `DEBUG` | Debug mode | `True` |
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@localhost:5432/simaorka` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000` |
| `STORAGE_BACKEND` | Storage type | `local`, `s3`, or `supabase` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJ...` |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name | `simaorka` |
| `AWS_ACCESS_KEY_ID` | S3/MinIO access key | `minioadmin` |
| `AWS_SECRET_ACCESS_KEY` | S3/MinIO secret | `minioadmin` |
| `AWS_STORAGE_BUCKET_NAME` | Storage bucket | `simaorka` |
| `AWS_S3_ENDPOINT_URL` | S3 endpoint | `http://localhost:9000` |
| `GOOGLE_CLIENT_ID` | Google OAuth client | `xxx.apps.googleusercontent.com` |
| `SEPOLIA_RPC_URL` | Ethereum RPC | `https://sepolia.infura.io/v3/xxx` |


---

## 📁 Project Structure

```
Backend-SIMAORKA/
├── apps/
│   ├── accounts/        # User authentication & profiles
│   ├── organizations/   # Organization management
│   ├── rbac/           # Role-based access control
│   ├── content/        # Announcements & news
│   ├── events/         # Event management
│   ├── finance/        # Financial transactions
│   ├── documents/      # Document management
│   ├── voting/         # Voting system
│   ├── notifications/  # Notification system
│   ├── communication/  # Discussions & chat
│   ├── org_requests/   # Organization requests
│   ├── web3layer/      # Web3 wallet & NFT
│   ├── audit/          # Audit logging
│   └── adminpanel/     # Admin dashboard
├── common/
│   ├── exceptions.py   # Custom exceptions
│   ├── permissions.py  # RBAC permissions
│   ├── business.py     # Business logic
│   └── storage.py      # File storage
├── config/
│   ├── settings/
│   │   ├── base.py     # Base settings
│   │   └── prod.py     # Production settings
│   └── urls.py         # URL configuration
├── requirements.txt
└── manage.py
```

---

## 🔐 Authentication

### JWT Authentication

All protected endpoints require the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Login Flow

1. **Email/Password Login**
   ```bash
   POST /api/v1/auth/login
   {"email": "user@example.com", "password": "password123"}
   ```

2. **Google OAuth**
   ```bash
   POST /api/v1/auth/google
   {"id_token": "google-id-token"}
   ```

3. **Refresh Token**
   ```bash
   POST /api/v1/auth/refresh
   # Uses HttpOnly cookie
   ```

---

## 🔒 RBAC (Role-Based Access Control)

### System Roles

| Role | Scope | Description |
|------|-------|-------------|
| `SUPERADMIN` | System | Full system access |
| `CAMPUS_ADMIN` | System | Campus-wide admin |
| `ORG_ADMIN` | Organization | Organization admin |
| `ORG_SECRETARY` | Organization | Secretary duties |
| `ORG_TREASURER` | Organization | Finance duties |
| `ORG_MEMBER` | Organization | Regular member |

### Permission Codes

```
ORG_VIEW, ORG_EDIT, ORG_DELETE
ORG_MANAGE_MEMBERS, ORG_APPROVE_MEMBERS
ANNOUNCEMENT_VIEW, ANNOUNCEMENT_CREATE, ANNOUNCEMENT_EDIT, ANNOUNCEMENT_DELETE
NEWS_VIEW, NEWS_CREATE, NEWS_EDIT, NEWS_DELETE, NEWS_PUBLISH
EVENT_VIEW, EVENT_CREATE, EVENT_EDIT, EVENT_DELETE
FINANCE_VIEW, FINANCE_CREATE, FINANCE_EDIT, FINANCE_APPROVE
DOCUMENT_VIEW, DOCUMENT_CREATE, DOCUMENT_EDIT, DOCUMENT_DELETE
VOTE_VIEW, VOTE_CREATE, VOTE_CAST
```

### Seeding Roles

```bash
python manage.py seed_rbac
```

---

## 🌐 Web3 Integration (Optional)

> Web3 is an **optional feature**. Set `WEB3_ENABLED=True` in `.env` to activate.

### Features
- Wallet verification (Sign-in with Ethereum)
- Role NFT (Soulbound tokens for org roles)
- Web3 Payments (ETH dues collection)
- Token-weighted voting

### Smart Contracts

See [`contracts/`](./contracts/) folder for Solidity files:
- `SimaorkaRoleNFT.sol` - Soulbound NFT for roles
- `SimaorkaGovToken.sol` - Non-transferable voting token
- `SimaorkaDues.sol` - ETH payment contract

### Setup

See [docs/SETUP_WEB3.md](./docs/SETUP_WEB3.md) for full setup guide.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SETUP_WEB3.md](./docs/SETUP_WEB3.md) | Web3 setup guide |
| [SETUP_EMAIL.md](./docs/SETUP_EMAIL.md) | Email configuration |

### Interactive Docs

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI JSON**: `http://localhost:8000/api/schema/`

---

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.rbac
python manage.py test apps.web3layer

# Run with coverage
coverage run manage.py test
coverage report
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `Django 5.0` | Web framework |
| `djangorestframework` | REST API |
| `djangorestframework-simplejwt` | JWT auth |
| `drf-spectacular` | OpenAPI docs |
| `django-cors-headers` | CORS support |
| `django-storages` | S3 file storage |
| `web3` | Ethereum integration |
| `eth-account` | Wallet signatures |
| `google-auth` | Google OAuth |
| `psycopg2-binary` | PostgreSQL |

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL
- [ ] Setup S3/MinIO storage
- [ ] Configure CORS origins
- [ ] Setup HTTPS
- [ ] Run `collectstatic`

### Docker

```bash
docker build -t simaorka-backend .
docker run -p 8000:8000 --env-file .env simaorka-backend
```

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

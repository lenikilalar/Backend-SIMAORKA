## PROMPT PAKET — AI AGENT BACKEND (Django + DRF) SIMAORKA

Kamu adalah AI agent backend engineer. Tugas kamu membangun backend API untuk **SIMAORKA (Sistem Manajemen Organisasi Kampus)** menggunakan **Django + Django REST Framework + PostgreSQL**. Frontend Next.js sudah dirancang, jadi API harus konsisten dan siap dipakai FE.

### 0) Goal & Output

Bangun repo backend lengkap yang:

1. Menyediakan REST API `/api/v1/*` untuk semua fitur inti SIMAORKA + patch Web3 governance.
2. Mengimplementasikan RBAC yang kuat (SYSTEM roles & ORG roles) dan **wajib enforced di backend**.
3. Mendukung file storage (local dev + S3/MinIO prod) dan signed URL untuk dokumen private.
4. Memiliki dokumentasi OpenAPI (Swagger) dan test suite minimal.

**Output akhir yang wajib kamu hasilkan:**

* Django project siap run (dev) + migrations
* API endpoints lengkap dengan serializers, permissions, services layer
* Seed roles + permissions default
* OpenAPI docs
* Test suite (pytest atau Django tests) yang memverifikasi RBAC & fitur kritikal

---

### 1) Tech Stack Wajib

* Python 3.12+
* Django 5.x
* Django REST Framework
* PostgreSQL
* SimpleJWT (access + refresh rotation)
* Google login: verifikasi `id_token` Google (pakai library resmi `google-auth` atau setara)
* Storage: `django-storages` + boto3 (S3-compatible). Dev boleh local storage.
* API docs: `drf-spectacular`
* Rate limiting minimal untuk auth endpoints (opsional tapi direkomendasikan)
* Web3 RPC calls: `web3.py` atau `eth-account` + JSON-RPC (Sepolia)

---

### 2) Struktur Folder (harus mengikuti)

Buat struktur project seperti ini (jangan satukan semuanya ke 1 app):

```
backend/
  config/
    settings/
      base.py
      dev.py
      prod.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    accounts/
    organizations/
    rbac/
    content/
    events/
    notifications/
    finance/
    discussions/
    chat/
    documents/
    voting/
    org_requests/
    audit/
    web3layer/
    adminpanel/
  common/
    responses.py         # envelope response helper
    exceptions.py        # error codes + handlers
    permissions.py       # HasOrgPermission etc
    pagination.py
    storage.py
    middleware.py        # audit log
    utils.py
  manage.py
```

---

### 3) Database: Model & Migrations

Gunakan PostgreSQL. Buat models yang mencerminkan schema berikut (core + patch web3 governance). Pastikan migration berjalan.

**Core tables:**

* users, student_profiles
* organizations
* roles, permissions, role_permissions
* organization_members, member_roles
* organization_positions, member_positions
* announcements, news_posts
* events, event_attendance, event_reminders
* notifications
* finance_ledgers, finance_transactions
* discussion_threads, discussion_posts
* chat_threads, chat_participants, chat_messages
* membership_applications
* organization_requests
* audit_logs
* user_wallets
* web3_payments

**Patch web3 governance tables:**

* web3_contracts
* org_periods
* org_roles_catalog
* org_role_assignments
* documents, document_versions, document_access_rules
* votes, vote_casts

Upgrade `user_wallets`:

* verification_nonce, verification_message, is_primary, last_verified_at
* unique partial index: one primary wallet per user

Jika kamu butuh referensi DDL, anggap sudah ada sesuai yang kita sepakati sebelumnya.

---

### 4) API Style & Response Envelope (Wajib)

Semua endpoint harus mengembalikan format:

**Success**

```json
{ "data": ..., "meta": ... }
```

**Error**

```json
{ "error": { "code": "CODE", "message": "msg", "details": {...} } }
```

Implement helper `common/responses.py` dan exception handler global di `common/exceptions.py`.

---

### 5) Auth (Wajib)

Implement endpoint:

* `POST /api/v1/auth/google`
  Input `{ "id_token": "..." }`
  Verifikasi id_token Google → create/get user → return access token + set refresh cookie (httpOnly).
* `POST /api/v1/auth/refresh`
* `POST /api/v1/auth/logout`
* `GET /api/v1/me`

`GET /me` harus mengembalikan:

* user profile
* `profile_complete: boolean`
* daftar ringkas membership organisasi (orgId, slug, name, role badges, status)

---

### 6) RBAC (Paling penting)

Implement RBAC:

* SYSTEM roles (scope SYSTEM): CAMPUS_ADMIN, SUPERADMIN
* ORG roles via organization_members + member_roles (scope ORG)

Buat permission classes di `common/permissions.py`:

* `IsSystemAdmin` (campus/super)
* `IsOrgMemberActive`
* `HasOrgPermission(permission_code, org_kwarg='org_id')`

Seed minimal:

* Roles: MEMBER, ORG_ADMIN, TREASURER, SECRETARY, CAMPUS_ADMIN, SUPERADMIN
* Permissions codes minimal:

  * ORG_EDIT_PROFILE
  * MEMBER_VIEW, MEMBER_MANAGE
  * ANNOUNCEMENT_CREATE
  * NEWS_CREATE, NEWS_PUBLISH
  * EVENT_CREATE, EVENT_MANAGE
  * FINANCE_VIEW, FINANCE_WRITE
  * DOCUMENT_VIEW, DOCUMENT_EDIT, DOCUMENT_APPROVE
  * APPLICATION_REVIEW
  * VOTE_CREATE, VOTE_MANAGE
  * (optional) WEB3_ROLE_MINT, WEB3_ROLE_REVOKE

---

### 7) File Storage (Wajib)

Implement:

* local storage untuk dev
* S3-compatible untuk prod (MinIO/AWS)
* upload via multipart endpoints:

  * profile photo
  * org logo
  * news cover
  * finance attachment
  * document versions (private)

Untuk dokumen private, backend harus memberikan signed URL:

* `GET /api/v1/documents/{docId}/download` → signed url (kalau allowed)

---

### 8) Endpoints yang wajib dibuat (Checklist)

Base path: `/api/v1`

#### Public

* `GET /public/organizations` (non-private & active)
* `GET /public/organizations/{slug}`
* `GET /public/news`
* `GET /public/events`
* `POST /public/org-requests` (create request + notify campus admins)

#### Organization (member/admin)

* `GET /orgs/{orgId}/dashboard`
* `PUT /orgs/{orgId}` (ORG_EDIT_PROFILE)
* `GET /orgs/{orgId}/members` (MEMBER_VIEW)
* `PATCH /orgs/{orgId}/members/{memberId}` (MEMBER_MANAGE)
* `DELETE /orgs/{orgId}/members/{memberId}` (MEMBER_MANAGE)

#### Membership applications

* `POST /orgs/{orgId}/apply` (only if open_member true)
* `GET /orgs/{orgId}/applications` (APPLICATION_REVIEW)
* `POST /orgs/{orgId}/applications/{id}/accept`
* `POST /orgs/{orgId}/applications/{id}/reject`

#### Announcements + Notifications

* `POST /orgs/{orgId}/announcements` (ANNOUNCEMENT_CREATE) → fanout notifications to active members
* `GET /orgs/{orgId}/announcements`
* `GET /notifications`
* `POST /notifications/{id}/read`

#### News

* `POST /orgs/{orgId}/news` (NEWS_CREATE)
* `PATCH /orgs/{orgId}/news/{id}`
* `POST /orgs/{orgId}/news/{id}/publish` (NEWS_PUBLISH)
* `GET /public/organizations/{slug}/news` (public published)

#### Events

* `POST /orgs/{orgId}/events` (EVENT_CREATE) with `also_announce` option
* `GET /orgs/{orgId}/events`
* `POST /events/{eventId}/attendance`
* `POST /events/{eventId}/reminders`

#### Finance

* `GET /orgs/{orgId}/finance/ledgers`
* `POST /orgs/{orgId}/finance/transactions` (FINANCE_WRITE)
* `GET /orgs/{orgId}/finance/transactions` (FINANCE_VIEW)

#### Discussions

* `POST /orgs/{orgId}/discussions`
* `GET /orgs/{orgId}/discussions`
* `POST /discussions/{threadId}/posts`

#### Chat (MVP)

* `POST /orgs/{orgId}/chats/direct` (create/get thread)
* `GET /chats/{threadId}/messages`
* `POST /chats/{threadId}/messages`

#### Documents (Web3 gated)

* `GET /orgs/{orgId}/documents`
* `POST /orgs/{orgId}/documents` (admin)
* `GET /documents/{docId}`
* `POST /documents/{docId}/versions` (upload + hash)
* `GET /documents/{docId}/download` (signed url; enforce access rules + nft validity if enabled)

#### Voting (hybrid token weighted)

* `GET /orgs/{orgId}/votes`
* `POST /orgs/{orgId}/votes` (VOTE_CREATE)
* `GET /votes/{voteId}`
* `POST /votes/{voteId}/cast` (verified wallet required; snapshot gov token balance)
* `GET /votes/{voteId}/results`

#### Web3 Wallet Verification

* `GET /web3/nonce`
* `POST /web3/verify-wallet`

#### Web3 Contract Registry

* `GET /web3/contracts?chain=sepolia`

#### Web3 Role NFT Assignment (client mint record)

* `POST /admin/orgs/{orgId}/periods/{periodId}/roles/record-mint`

  * backend verify tx logs on-chain and store assignment
* `POST /admin/org-role-assignments/{id}/revoke` (record revoke tx + verify)

#### Kas Web3 (dues contract)

* `POST /orgs/{orgId}/finance/web3/submit`

  * verify tx receipt/event and mark payment confirmed

#### Admin campus/system

* `GET /admin/orgs`
* `PATCH /admin/orgs/{orgId}/set-admin`
* `GET /admin/org-requests`
* `PATCH /admin/org-requests/{id}`
* `GET /admin/audit-logs`
* `GET /admin/stats`

---

### 9) Business Logic Rules (Wajib)

* User profile incomplete → return error code `PROFILE_INCOMPLETE` untuk endpoint tertentu (apply/join)
* `org.apply` hanya jika `open_member=true` dan dalam window jika diset.
* Announcement create:

  * create announcement
  * create notifications untuk semua member active (bulk insert)
* Event create:

  * jika `also_announce=true`: buat announcement otomatis + notifications
* Document download:

  * hanya jika lolos RBAC + document_access_rules + web3 role validity jika web3 enabled
* Voting cast:

  * enforce unique (voteId, wallet_address)
  * snapshot token balance
* Admin set org admin:

  * ensure target user is org member
  * assign ORG_ADMIN role
* Audit log untuk action sensitif

---

### 10) Web3 Verification Rules (Wajib)

Semua web3 berbasis Sepolia RPC:

* Env: `SEPOLIA_RPC_URL`
* Contract addresses dibaca dari DB `web3_contracts` atau env fallback.

**Wallet verify**

* nonce -> sign message -> recover address -> store verified

**record-mint Role NFT**
Backend verify:

* tx receipt success
* tx logs include RoleMinted with:

  * to == wallet_address
  * orgId/periodId match request
  * roleCode matches (bytes32 keccak256(role_code))
  * tokenId matches
* store org_role_assignments = active

**NFT validity check**

* ownerOf(tokenId) == wallet
* roleOf(tokenId).revoked false
* roleOf(tokenId).expiresAt >= now

**GovToken weight snapshot**

* balanceOf(wallet) at time of cast

**Kas web3 submit**

* receipt success
* to == dues_contract_address
* logs include DuesPaid(orgId,payer,amountWei, note)
* mark payment confirmed

Jika verifikasi gagal: return `WEB3_TX_INVALID`

---

### 11) Coding Rules (Wajib)

* Semua write operation di service layer, bukan viewset.
* Gunakan transactions untuk operasi multi-insert (announcement + notifications).
* Jangan hardcode orgId dari request tanpa permission check.
* Jangan expose internal IDs yang tidak perlu.
* Gunakan `select_related`/`prefetch_related` untuk list besar.

---

### 12) Testing (Wajib)

Buat minimal tests:

1. RBAC: member tidak bisa create announcement; admin bisa.
2. Apply membership hanya saat open_member.
3. Announcement fanout notifications count = active members.
4. Document download denied without required role.
5. Vote cast: duplicate prevented.
6. Wallet verification signature test.
7. Admin endpoints restricted.

---

### 13) OpenAPI Docs (Wajib)

Implement drf-spectacular:

* `/api/schema/`
* `/api/docs/`
  Tagging endpoint: Auth/Public/Org/Admin/Web3/Documents/Voting.

---

### 14) Deliverables Checklist

* Repo build + run with Postgres
* migrations ready
* endpoints available
* storage configured
* swagger docs
* tests pass
* seed data ready

---

## Tambahan: Env vars yang harus didokumentasikan

Backend `.env` minimal:

* `DJANGO_SECRET_KEY`
* `DEBUG`
* `DATABASE_URL`
* `CORS_ALLOWED_ORIGINS`
* `JWT_SIGNING_KEY` / simplejwt settings
* `SEPOLIA_RPC_URL`
* storage creds (S3/MinIO)
* optional: `GOOGLE_CLIENT_ID` (untuk verify audience)

---

### FORMAT OUTPUT SAAT AGENT LAPOR

Setiap kali kamu selesai sebuah phase, laporkan:

* daftar endpoint yang sudah aktif
* contoh request/response minimal untuk 2 endpoint utama
* status migrations
* status tests

---

## End of Prompt Paket
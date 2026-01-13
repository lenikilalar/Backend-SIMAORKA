Berikut **Technical Specification Document (TSD)** untuk SIMAORKA dengan:

* **Frontend:** Next.js (utama)
* **Backend API:** Django + Django REST Framework
* **File Storage:** object storage (S3-compatible; bisa AWS S3 / MinIO) + opsi Supabase Storage
* **Frontend multi-backend:**

  1. **serverless-dummy** (tanpa URL backend, untuk ngetes UI/flow)
  2. **server API** (DRF)
  3. **serverless Supabase** (Auth/DB/Storage via Supabase, sebagai alternatif)

Server dipilih via `.env`.

---

# Technical Specification Document (TSD) — SIMAORKA

## 1. Scope & Non-Goals

### In Scope

* Arsitektur sistem end-to-end (Next.js + DRF + storage)
* Kontrak API (endpoint, payload, status codes)
* Strategi auth & RBAC
* Storage file & media handling
* Desain multi-backend di frontend (adapter + switching via env)
* Observability: audit log, monitoring dasar
* Testing strategy

### Non-Goals (untuk versi ini)

* Implementasi blockchain/web3 detail on-chain (kita definisikan interface-nya saja)
* Real-time chat via WebSocket detail (disiapkan untuk fase berikut)
* Full CI/CD pipeline detail vendor-specific (kita beri blueprint)

---

## 2. High-Level Architecture

### 2.1 Komponen Utama

1. **Next.js Frontend**

* App Router
* SSR/SSG untuk halaman publik (landing, explore, org detail, news publik)
* Client rendering untuk dashboard user (notif, chat, diskusi, event attendance)

2. **Django REST Framework API**

* Menyediakan endpoint CRUD + business rules + RBAC enforcement
* Mengeluarkan JWT + refresh token
* Menulis audit logs untuk aksi administratif

3. **Storage File**

* Untuk: logo organisasi, cover berita, attachment bukti transaksi, foto profil, dll
* Strategi: signed upload URL / direct-to-storage upload (opsional), atau upload via API (lebih simpel)

4. **Database**

* PostgreSQL (sesuai schema sebelumnya)

5. **Optional Supabase Backend**

* Untuk mode “serverless Supabase”: auth + DB + storage melalui Supabase
* Frontend memakai Supabase client + tetap menjaga domain model yang sama

---

## 3. Environment Switching: Multi-Backend Frontend

### 3.1 Tujuan

Frontend bisa jalan dengan 3 sumber data:

1. **Dummy serverless**: tanpa backend, untuk menguji UI/UX & flow
2. **DRF API**: backend utama
3. **Supabase**: alternatif serverless (buat demo cepat / fallback)

### 3.2 Design Pattern: Backend Adapter

Frontend wajib punya satu interface yang sama untuk semua backend.

**Konsep:**

* `DataProvider` interface: method-method seperti `auth.login`, `org.list`, `org.get`, `announcement.list`, dst.
* Implementasi:

  * `DummyProvider` → Next.js route handlers / in-memory JSON / file mock
  * `ApiProvider` → fetch ke DRF
  * `SupabaseProvider` → supabase-js query

**Switching via env:**

* `NEXT_PUBLIC_BACKEND_MODE=dummy|api|supabase`
* `NEXT_PUBLIC_API_BASE_URL=https://...` (untuk api mode)
* `NEXT_PUBLIC_SUPABASE_URL=...` + `NEXT_PUBLIC_SUPABASE_ANON_KEY=...` (supabase mode)

**Rule:**

* UI tidak boleh tahu backend apa yang dipakai.
* Semua halaman memanggil provider yang sama.

---

## 4. Authentication & Authorization (RBAC)

### 4.1 Auth Methods

* **Primary:** Google OAuth (frontend) → backend menerima token Google dan menukarnya menjadi token sistem
* **Secondary:** Email/password opsional (disiapkan)
* **Supabase mode:** Supabase Auth (Google) + RLS policies

### 4.2 Token Strategy (API mode)

* JWT Access Token (short-lived) + Refresh Token (rotating)
* Access token disimpan:

  * **Prefer:** httpOnly cookies (lebih aman)
  * Alternative: in-memory + refresh cookie
* Refresh token hanya lewat cookie httpOnly

### 4.3 RBAC enforcement

RBAC harus **di-backend**, bukan cuma di frontend.

**Sumber role:**

* `member_roles` + `organization_members.status=active`
* `roles.scope=SYSTEM` untuk admin kampus/superadmin

**Permission check:**

* Per endpoint, backend cek permission:

  * contoh: `ORG_EDIT_PROFILE` untuk update profil organisasi
  * `MEMBER_KICK` untuk mengeluarkan anggota
  * `FINANCE_WRITE` untuk input transaksi
  * `ANNOUNCEMENT_CREATE` untuk publish pengumuman

---

## 5. Data Model Mapping (Backend)

Backend memakai model yang selaras dengan schema:

* User, StudentProfile
* Organization
* OrganizationMember, Role, Permission, MemberRole
* Announcement, NewsPost
* Event, Attendance, Reminder
* Notification
* FinanceLedger, FinanceTransaction
* DiscussionThread, DiscussionPost
* ChatThread, ChatParticipant, ChatMessage
* MembershipApplication
* OrganizationRequest
* AuditLog
* UserWallet, Web3Payment

Catatan: beberapa field JSON (mis. socials) tetap sebagai `JSONField`.

---

## 6. API Design (DRF)

### 6.1 Conventions

* Base path: `/api/v1/`
* JSON format konsisten:

  * response sukses: `{ "data": ..., "meta": ... }`
  * error: `{ "error": { "code": "...", "message": "...", "details": ... } }`
* Pagination: cursor atau page-based (pilih salah satu; rekomendasi: cursor untuk feed)
* Filtering: query params (`?org_id=&status=&q=`)

### 6.2 Core Endpoints (ringkas tapi lengkap)

#### Auth

* `POST /api/v1/auth/google`
  Input: `{ id_token }`
  Output: tokens + user profile completion status
* `POST /api/v1/auth/refresh`
* `POST /api/v1/auth/logout`
* `GET /api/v1/me` (profil + roles ringkas)

#### Profile

* `PUT /api/v1/me/profile` (lengkapi NIM, jurusan, dll)
* `POST /api/v1/me/avatar` (upload foto profil)

#### Public: Explore

* `GET /api/v1/public/organizations` (hanya non-private + active)
* `GET /api/v1/public/organizations/{slug}`
* `GET /api/v1/public/organizations/{slug}/news`
* `GET /api/v1/public/news` (feed publik, optional)
* `GET /api/v1/public/events` (acara publik)

#### Organization Admin / Member

* `GET /api/v1/orgs/{org_id}/dashboard` (ringkasan untuk member)
* `PUT /api/v1/orgs/{org_id}` (edit profil, butuh permission)
* `GET /api/v1/orgs/{org_id}/members`
* `PATCH /api/v1/orgs/{org_id}/members/{member_id}` (ubah status/jabatan)
* `DELETE /api/v1/orgs/{org_id}/members/{member_id}` (kick)

#### Membership application

* `POST /api/v1/orgs/{org_id}/apply`
* `GET /api/v1/orgs/{org_id}/applications` (admin)
* `POST /api/v1/orgs/{org_id}/applications/{app_id}/accept`
* `POST /api/v1/orgs/{org_id}/applications/{app_id}/reject`

#### Announcements + Notifications

* `POST /api/v1/orgs/{org_id}/announcements`
* `GET /api/v1/orgs/{org_id}/announcements` (member only)
* `GET /api/v1/notifications`
* `POST /api/v1/notifications/{id}/read`

#### News

* `POST /api/v1/orgs/{org_id}/news`
* `GET /api/v1/orgs/{org_id}/news` (admin sees draft)
* `PATCH /api/v1/orgs/{org_id}/news/{id}`

#### Events

* `POST /api/v1/orgs/{org_id}/events` (opsi: “also_announce”: true)
* `GET /api/v1/orgs/{org_id}/events`
* `POST /api/v1/events/{event_id}/attendance` (going/interested/not_going)
* `POST /api/v1/events/{event_id}/reminders` (create reminder)

#### Finance

* `GET /api/v1/orgs/{org_id}/finance/ledgers`
* `POST /api/v1/orgs/{org_id}/finance/transactions`
* `GET /api/v1/orgs/{org_id}/finance/transactions`

#### Discussions

* `POST /api/v1/orgs/{org_id}/discussions`
* `GET /api/v1/orgs/{org_id}/discussions`
* `POST /api/v1/discussions/{thread_id}/posts`

#### Chat (MVP: direct, non-realtime)

* `POST /api/v1/orgs/{org_id}/chats/direct` (create/get thread with user)
* `GET /api/v1/chats/{thread_id}/messages`
* `POST /api/v1/chats/{thread_id}/messages`

#### Org requests (public -> campus admin)

* `POST /api/v1/public/org-requests`
* `GET /api/v1/admin/org-requests` (campus admin)
* `PATCH /api/v1/admin/org-requests/{id}`

#### Admin campus

* `GET /api/v1/admin/orgs`
* `PATCH /api/v1/admin/orgs/{org_id}/set-admin` (assign org admin)
* `GET /api/v1/admin/audit-logs`
* `GET /api/v1/admin/stats` (high-level metrics)

---

## 7. Storage & File Handling

### 7.1 Requirement

* Menyimpan:

  * Foto profil user (opsional)
  * Logo organisasi
  * Cover berita
  * Lampiran bukti transaksi
* Mendukung:

  * Private vs public objects (minimal: publik untuk logo/cover; private untuk bukti transaksi)
  * Size limit & mime validation

### 7.2 API Mode (DRF)

**Pilihan recommended:** S3-compatible via `django-storages`.

* Bucket `simaorka-public` (logo, cover)
* Bucket `simaorka-private` (attachments bukti, dokumen internal)
* URL disimpan di DB (field `*_url`)

**Upload options**

1. **Upload via API** (simple): FE POST file -> DRF -> DRF upload ke storage
2. **Signed URL** (lebih scalable): FE minta signed URL -> FE upload langsung ke storage -> FE submit metadata ke API

Untuk MVP: pilih (1) dulu biar cepat.

### 7.3 Supabase Mode

* Gunakan Supabase Storage bucket:

  * `public-assets`
  * `private-assets`
* Public URL untuk assets public
* Signed URL untuk private

---

## 8. Frontend (Next.js) Technical Plan

### 8.1 App Structure

* `/` landing (SSG)
* `/explore` list organisasi publik (SSR/SSG)
* `/org/[slug]` detail organisasi publik (SSR)
* `/org/[slug]/news` (SSR)
* `/login` auth
* `/app` (protected)

  * `/app/dashboard` (ringkasan user)
  * `/app/org/[orgId]` dashboard organisasi
  * `/app/org/[orgId]/members`
  * `/app/org/[orgId]/announcements`
  * `/app/org/[orgId]/events`
  * `/app/org/[orgId]/finance`
  * `/app/org/[orgId]/discussions`
  * `/app/org/[orgId]/chat`

### 8.2 Data Layer

* `src/data/provider.ts` interface
* `src/data/providers/dummy.ts`
* `src/data/providers/api.ts`
* `src/data/providers/supabase.ts`
* `src/data/index.ts` memilih provider berdasarkan env

### 8.3 Serverless Dummy

Implementasi dummy untuk ngetes frontend tanpa backend:

* Next.js Route Handlers:

  * `/api/dummy/*` mengembalikan JSON statis / in-memory store
* Provider dummy memanggil endpoint lokal tersebut (atau langsung import data JSON)
* Cocok untuk:

  * UI navigation
  * state transitions (apply membership, mark attendance)
  * notifikasi simulasi

> Dummy harus meniru response shape API asli biar migrasi mulus.

### 8.4 Protected Routes

* Middleware Next.js memeriksa session token (cookie)
* Jika tidak ada token → redirect `/login`
* Di supabase mode, pakai supabase session check

---

## 9. Backend (Django + DRF) Technical Plan

### 9.1 Project Layout (recommended)

* `apps/accounts` (users, auth)
* `apps/organizations`
* `apps/rbac`
* `apps/content` (announcements, news)
* `apps/events`
* `apps/notifications`
* `apps/finance`
* `apps/discussions`
* `apps/chat`
* `apps/adminpanel` (org requests, stats)
* `apps/audit`

### 9.2 RBAC Implementation

* DRF permission classes:

  * `IsSystemRole(SUPERADMIN|CAMPUS_ADMIN)`
  * `HasOrgPermission(org_id, permission_code)`
* Utility untuk fetch role/permissions efisien (cache per-request)

### 9.3 Notifications fan-out

Saat announcement dibuat:

* Query semua `organization_members` status active
* Bulk create `notifications`
* Bisa async (Celery) untuk skala besar; MVP boleh sync tapi bulk.

### 9.4 Audit logging

* Middleware menangkap request untuk endpoint admin + actions sensitif
* Simpan `actor_id`, action code, entity, ip, user-agent

---

## 10. Supabase Mode Specification

Supabase mode adalah alternatif backend:

* Auth: Supabase Auth (Google)
* DB: Supabase Postgres (schema sama)
* RLS: enforce akses per org membership
* Storage: Supabase Storage

Catatan penting:

* RLS akan jadi “RBAC layer” utama
* Frontend provider supabase harus memetakan query ke domain model yang sama

---

## 11. Web3 Kas (Interface Only)

MVP: simpan bukti transaksi on-chain sebagai record:

* FE mengirim `tx_hash`, `chain`, `amount`, `token`
* Backend:

  * Buat `finance_transaction` (source=web3)
  * Buat `web3_payment` status=pending
* Worker/cron (fase berikut):

  * Verifikasi tx_hash dan update status=confirmed

---

## 12. Security Requirements

* Rate limiting: login, apply membership, posting konten
* File upload validation: size, mime, virus scan optional
* CORS ketat untuk API
* JWT rotation & revoke
* Prevent IDOR:

  * Semua endpoint org harus cek membership/role
* Logging tanpa data sensitif

---

## 13. Testing Strategy

### Frontend

* Unit test provider interface (dummy/api/supabase)
* Component tests (React Testing Library)
* E2E (Playwright):

  * explore org → view detail → apply → login → join flow
  * create announcement → notif appears

### Backend

* Unit test permission checks
* API integration tests:

  * RBAC scenarios (admin vs member vs public)
  * file upload endpoints
  * notification fan-out

---

## 14. Deployment Blueprint

### API Mode (recommended production)

* Next.js: Vercel / Node server
* DRF: containerized (Docker) di VPS / ECS / Cloud Run
* Postgres: managed
* Storage: S3-compatible
* Background jobs: Celery + Redis (optional phase 2)

### Supabase Mode (demo/fast)

* Next.js: Vercel
* Supabase project: auth + db + storage
* RLS policies enforced

---

## 15. Environment Variables

### Next.js

* `NEXT_PUBLIC_BACKEND_MODE=dummy|api|supabase`
* `NEXT_PUBLIC_API_BASE_URL=...`
* `NEXT_PUBLIC_SUPABASE_URL=...`
* `NEXT_PUBLIC_SUPABASE_ANON_KEY=...`

### Django

* `DATABASE_URL=...`
* `JWT_SECRET=...` (atau keypair)
* `CORS_ALLOWED_ORIGINS=...`
* `STORAGE_DRIVER=s3|minio|local`
* `AWS_ACCESS_KEY_ID=...`
* `AWS_SECRET_ACCESS_KEY=...`
* `AWS_S3_BUCKET_PUBLIC=...`
* `AWS_S3_BUCKET_PRIVATE=...`

---

## 16. Acceptance Criteria (teknis)

* Frontend bisa switch backend mode tanpa ubah kode UI
* Dummy mode mampu menjalankan flow utama (explore → login → join → view announcements/events)
* API mode:

  * RBAC bekerja (admin bisa edit org, member tidak)
  * Pengumuman menghasilkan notifikasi ke anggota
  * File upload tersimpan di storage dan URL tersimpan di DB
* Supabase mode:

  * Auth Google berjalan
  * RLS membatasi data sesuai membership


-- SIMAORKA - PostgreSQL DDL (v1)
-- Notes:
-- - Uses UUID PKs + timestamps
-- - Enum types for status fields
-- - RBAC: roles + permissions; per-org via organization_members + member_roles
-- - Chat, discussions, events, notifications, finance, web3, audit logs included

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- If you prefer gen_random_uuid(), use:
-- CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================
-- ENUM TYPES
-- =========================
DO $$ BEGIN
  CREATE TYPE org_status AS ENUM ('draft','active','suspended');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE role_scope AS ENUM ('SYSTEM','ORG');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE membership_status AS ENUM ('pending','active','rejected','removed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE post_status AS ENUM ('draft','published','archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE attendance_status AS ENUM ('going','interested','not_going');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE reminder_channel AS ENUM ('in_app','email');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE notification_type AS ENUM ('announcement','event','org_application','system');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE finance_tx_type AS ENUM ('income','expense');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE finance_visibility AS ENUM ('members_only','public_summary');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE finance_source AS ENUM ('manual','web3');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE discussion_lock_status AS ENUM ('open','locked');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE chat_thread_type AS ENUM ('direct');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE org_request_status AS ENUM ('submitted','in_review','approved','rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE application_status AS ENUM ('submitted','accepted','rejected','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE web3_chain AS ENUM ('ethereum','polygon','bsc','other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE web3_payment_status AS ENUM ('pending','confirmed','failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =========================
-- CORE: USERS & PROFILES
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email           citext UNIQUE NOT NULL,
  google_sub      text UNIQUE,
  password_hash   text,
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  last_login_at   timestamptz
);

CREATE TABLE IF NOT EXISTS student_profiles (
  user_id            uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  nim                text UNIQUE NOT NULL,
  full_name          text NOT NULL,
  faculty            text NOT NULL,
  major              text NOT NULL,
  entry_year         int  NOT NULL CHECK (entry_year >= 1900 AND entry_year <= 3000),
  profile_photo_url  text,
  avatar_bg_color    text,  -- e.g. '#AABBCC' (validate at app layer)
  avatar_initials    text,
  mini_photo_url     text,
  bio                text,
  phone              text,
  updated_at         timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- ORGANIZATIONS
-- =========================
CREATE TABLE IF NOT EXISTS organizations (
  id                    uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug                  text UNIQUE NOT NULL,
  name                  text NOT NULL,
  description           text,
  vision                text,
  mission               text,
  contact_email         text,
  contact_phone         text,
  contact_socials_json  jsonb,
  logo_url              text,
  is_private            boolean NOT NULL DEFAULT false,
  open_member           boolean NOT NULL DEFAULT false,
  open_member_start_at  timestamptz,
  open_member_end_at    timestamptz,
  status                org_status NOT NULL DEFAULT 'draft',
  created_by            uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT open_member_window_check
    CHECK (
      (open_member = false)
      OR (open_member_start_at IS NULL OR open_member_end_at IS NULL OR open_member_start_at <= open_member_end_at)
    )
);

-- =========================
-- RBAC: roles, permissions
-- =========================
CREATE TABLE IF NOT EXISTS roles (
  id      bigserial PRIMARY KEY,
  code    text UNIQUE NOT NULL, -- e.g. ORG_ADMIN, TREASURER, MEMBER, CAMPUS_ADMIN, SUPERADMIN
  name    text NOT NULL,
  scope   role_scope NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
  id      bigserial PRIMARY KEY,
  code    text UNIQUE NOT NULL, -- e.g. ORG_EDIT_PROFILE, MEMBER_KICK, FINANCE_VIEW
  name    text NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id        bigint NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id  bigint NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- Memberships (per org)
CREATE TABLE IF NOT EXISTS organization_members (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status           membership_status NOT NULL DEFAULT 'pending',
  joined_at        timestamptz,
  left_at          timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, user_id),
  CONSTRAINT membership_dates_check CHECK (
    (joined_at IS NULL OR left_at IS NULL OR joined_at <= left_at)
  )
);

CREATE TABLE IF NOT EXISTS member_roles (
  member_id  uuid NOT NULL REFERENCES organization_members(id) ON DELETE CASCADE,
  role_id    bigint NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  PRIMARY KEY (member_id, role_id)
);

-- Public-facing positions (e.g. Ketua Umum)
CREATE TABLE IF NOT EXISTS organization_positions (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name             text NOT NULL,
  rank             int  NOT NULL DEFAULT 0,
  is_core          boolean NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS member_positions (
  member_id    uuid NOT NULL REFERENCES organization_members(id) ON DELETE CASCADE,
  position_id  uuid NOT NULL REFERENCES organization_positions(id) ON DELETE CASCADE,
  start_at     timestamptz,
  end_at       timestamptz,
  PRIMARY KEY (member_id, position_id, start_at),
  CONSTRAINT member_position_dates_check CHECK (
    (start_at IS NULL OR end_at IS NULL OR start_at <= end_at)
  )
);

-- =========================
-- CONTENT: announcements (internal) & news (public)
-- =========================
CREATE TABLE IF NOT EXISTS announcements (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title            text NOT NULL,
  content          text NOT NULL,
  created_by       uuid REFERENCES users(id) ON DELETE SET NULL,
  pinned           boolean NOT NULL DEFAULT false,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_posts (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title            text NOT NULL,
  summary          text,
  content          text NOT NULL,
  cover_image_url  text,
  status           post_status NOT NULL DEFAULT 'draft',
  published_at     timestamptz,
  created_by       uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT published_at_check
    CHECK ((status <> 'published') OR (published_at IS NOT NULL))
);

-- =========================
-- EVENTS & CALENDAR
-- =========================
CREATE TABLE IF NOT EXISTS events (
  id                     uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id         uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title                  text NOT NULL,
  description            text,
  location               text,
  start_at               timestamptz NOT NULL,
  end_at                 timestamptz NOT NULL,
  is_public              boolean NOT NULL DEFAULT false,
  max_attendees          int CHECK (max_attendees IS NULL OR max_attendees > 0),
  created_by             uuid REFERENCES users(id) ON DELETE SET NULL,
  linked_announcement_id uuid REFERENCES announcements(id) ON DELETE SET NULL,
  created_at             timestamptz NOT NULL DEFAULT now(),
  updated_at             timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT event_time_check CHECK (start_at <= end_at)
);

CREATE TABLE IF NOT EXISTS event_attendance (
  event_id   uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status     attendance_status NOT NULL DEFAULT 'interested',
  marked_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (event_id, user_id)
);

CREATE TABLE IF NOT EXISTS event_reminders (
  id         uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id   uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  remind_at  timestamptz NOT NULL,
  sent_at    timestamptz,
  channel    reminder_channel NOT NULL DEFAULT 'in_app',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (event_id, user_id, remind_at)
);

-- =========================
-- NOTIFICATIONS
-- =========================
CREATE TABLE IF NOT EXISTS notifications (
  id         uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       notification_type NOT NULL,
  title      text NOT NULL,
  message    text,
  data       jsonb,
  is_read    boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  read_at    timestamptz,
  CONSTRAINT read_at_check CHECK (
    (is_read = false AND read_at IS NULL) OR (is_read = true)
  )
);

-- =========================
-- FINANCE (transparency)
-- =========================
CREATE TABLE IF NOT EXISTS finance_ledgers (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name            text NOT NULL,
  currency        text NOT NULL DEFAULT 'IDR',
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, name)
);

CREATE TABLE IF NOT EXISTS finance_transactions (
  id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  ledger_id     uuid NOT NULL REFERENCES finance_ledgers(id) ON DELETE CASCADE,
  type          finance_tx_type NOT NULL,
  category      text,
  amount        numeric(18,2) NOT NULL CHECK (amount >= 0),
  description   text,
  occurred_at   timestamptz NOT NULL DEFAULT now(),
  created_by    uuid REFERENCES users(id) ON DELETE SET NULL,
  attachment_url text,
  visibility    finance_visibility NOT NULL DEFAULT 'members_only',
  source        finance_source NOT NULL DEFAULT 'manual',
  created_at    timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- DISCUSSIONS
-- =========================
CREATE TABLE IF NOT EXISTS discussion_threads (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title            text NOT NULL,
  created_by       uuid REFERENCES users(id) ON DELETE SET NULL,
  lock_status      discussion_lock_status NOT NULL DEFAULT 'open',
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS discussion_posts (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  thread_id   uuid NOT NULL REFERENCES discussion_threads(id) ON DELETE CASCADE,
  created_by  uuid REFERENCES users(id) ON DELETE SET NULL,
  content     text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  edited_at   timestamptz
);

-- =========================
-- CHAT (direct within org)
-- =========================
CREATE TABLE IF NOT EXISTS chat_threads (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  type             chat_thread_type NOT NULL DEFAULT 'direct',
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_participants (
  thread_id  uuid NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  joined_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (thread_id, user_id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id         uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  thread_id  uuid NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
  sender_id  uuid REFERENCES users(id) ON DELETE SET NULL,
  content    text NOT NULL,
  sent_at    timestamptz NOT NULL DEFAULT now(),
  edited_at  timestamptz,
  deleted_at timestamptz
);

-- =========================
-- OPEN MEMBER APPLICATIONS
-- =========================
CREATE TABLE IF NOT EXISTS membership_applications (
  id               uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id  uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status           application_status NOT NULL DEFAULT 'submitted',
  note             text,
  submitted_at     timestamptz NOT NULL DEFAULT now(),
  reviewed_by      uuid REFERENCES users(id) ON DELETE SET NULL,
  reviewed_at      timestamptz,
  UNIQUE (organization_id, user_id),
  CONSTRAINT reviewed_at_check CHECK (
    (reviewed_at IS NULL AND reviewed_by IS NULL)
    OR (reviewed_at IS NOT NULL)
  )
);

-- =========================
-- PUBLIC ORG REQUESTS -> CAMPUS ADMIN
-- =========================
CREATE TABLE IF NOT EXISTS organization_requests (
  id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  proposed_name        text NOT NULL,
  proposed_description text,
  requester_name       text NOT NULL,
  requester_email      text NOT NULL,
  requester_phone      text,
  status              org_request_status NOT NULL DEFAULT 'submitted',
  admin_note           text,
  handled_by           uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- AUDIT LOGS (campus/admin activity log)
-- =========================
CREATE TABLE IF NOT EXISTS audit_logs (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  actor_id    uuid REFERENCES users(id) ON DELETE SET NULL,
  action      text NOT NULL,
  entity_type text NOT NULL,
  entity_id   uuid,
  metadata    jsonb,
  ip_address  text,
  user_agent  text,
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- WEB3 (Metamask payments)
-- =========================
CREATE TABLE IF NOT EXISTS user_wallets (
  id             uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  wallet_address text NOT NULL UNIQUE,
  chain          web3_chain NOT NULL DEFAULT 'other',
  label          text,
  verified_at    timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS web3_payments (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  transaction_id  uuid NOT NULL UNIQUE REFERENCES finance_transactions(id) ON DELETE CASCADE,
  wallet_address  text NOT NULL,
  chain           web3_chain NOT NULL DEFAULT 'other',
  tx_hash         text NOT NULL UNIQUE,
  amount          numeric(18,2) NOT NULL CHECK (amount >= 0),
  token_symbol    text,
  status          web3_payment_status NOT NULL DEFAULT 'pending',
  confirmed_at    timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- INDEXES (performance basics)
-- =========================
CREATE INDEX IF NOT EXISTS idx_org_members_org_user
  ON organization_members (organization_id, user_id);

CREATE INDEX IF NOT EXISTS idx_member_roles_member
  ON member_roles (member_id);

CREATE INDEX IF NOT EXISTS idx_announcements_org_created
  ON announcements (organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_org_published
  ON news_posts (organization_id, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_org_start
  ON events (organization_id, start_at);

CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
  ON notifications (user_id, is_read, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_finance_tx_ledger_date
  ON finance_transactions (ledger_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_sent
  ON chat_messages (thread_id, sent_at);

CREATE INDEX IF NOT EXISTS idx_discussion_posts_thread_created
  ON discussion_posts (thread_id, created_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
  ON audit_logs (entity_type, entity_id, created_at DESC);

COMMIT;

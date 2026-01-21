# Organizations API

---

## List Organizations (Public)

`GET /api/v1/organizations/public_list`

**Query**: `?page=1&limit=20&search=teknik`

---

## Create Organization

`POST /api/v1/organizations`

**Permission**: Authenticated user

**Request**
```json
{
  "name": "Himpunan Mahasiswa Informatika",
  "slug": "hmi",
  "description": "..."
}
```

---

## Get Organization

`GET /api/v1/organizations/{slug}`

---

## Update Organization

`PUT /api/v1/organizations/{slug}`

**Permission**: `ORG_EDIT`

---

## List Members

`GET /api/v1/organizations/{slug}/members`

---

## Apply for Membership

`POST /api/v1/organizations/{slug}/apply`

---

# Announcements

## List Announcements

`GET /api/v1/announcements?org_id=uuid`

## Create Announcement

`POST /api/v1/announcements`

**Permission**: `ANNOUNCEMENT_CREATE`

```json
{
  "organization": "org-uuid",
  "title": "Rapat Bulanan",
  "content": "...",
  "is_pinned": false
}
```

---

# News

## List News

`GET /api/v1/news?org_id=uuid`

## Create News

`POST /api/v1/news`

**Permission**: `NEWS_CREATE`

## Publish News

`PATCH /api/v1/news/{id}`

```json
{ "status": "published" }
```

---

# Events

## List Events

`GET /api/v1/events?org_id=uuid`

## Create Event

`POST /api/v1/events`

**Permission**: `EVENT_CREATE`

```json
{
  "organization": "org-uuid",
  "title": "Workshop",
  "start_at": "2026-02-01T09:00:00Z",
  "end_at": "2026-02-01T17:00:00Z",
  "location": "Gedung A"
}
```

## Mark Attendance

`POST /api/v1/events/{id}/attendance`

```json
{ "status": "attending" }
```

---

# Discussions

## List Threads

`GET /api/v1/discussions?org_id=uuid`

## Create Thread

`POST /api/v1/discussions`

## Get Posts

`GET /api/v1/discussions/{id}/posts`

## Create Post

`POST /api/v1/discussions/{id}/posts`

---

# Chat

## List Chats

`GET /api/v1/chats`

## Send Message

`POST /api/v1/chats/{id}/send`

---

# Notifications

## List Notifications

`GET /api/v1/notifications?is_read=false&type=announcement`

**Types**: `announcement`, `event`, `application`, `finance`, `system`

## Mark as Read

`POST /api/v1/notifications/{id}/read`

## Mark All as Read

`POST /api/v1/notifications/read-all`

---

# Documents

## List Documents

`GET /api/v1/orgs/{org_id}/documents?status=published`

**Permission**: `DOCUMENT_VIEW`

## Create Document

`POST /api/v1/orgs/{org_id}/documents`

**Permission**: `DOCUMENT_CREATE`

## Upload Version

`POST /api/v1/orgs/{org_id}/documents/{id}/upload`

**Content-Type**: `multipart/form-data`

## Download Document

`GET /api/v1/orgs/{org_id}/documents/{id}/download`

## List Versions

`GET /api/v1/orgs/{org_id}/documents/{id}/versions`

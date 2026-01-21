# Admin API

**Permission**: System Admin (SUPERADMIN, CAMPUS_ADMIN)

---

## Dashboard Stats

`GET /api/v1/admin/stats`

**Response (200)**
```json
{
  "data": {
    "users": { "total": 1000, "active": 950, "new_last_30_days": 50 },
    "organizations": { "total": 25, "active": 23 },
    "org_requests": { "pending": 3, "in_review": 1, "total": 50 }
  }
}
```

---

## List Organizations

`GET /api/v1/admin/orgs?status=active`

---

## Update Organization

`PATCH /api/v1/admin/orgs/{id}`

```json
{
  "status": "suspended",
  "admin_note": "..."
}
```

---

## List Org Requests

`GET /api/v1/admin/org-requests?status=pending`

## Process Org Request

`PATCH /api/v1/admin/org-requests/{id}`

```json
{
  "action": "approve",
  "admin_note": "..."
}
```

| Action | Description |
|--------|-------------|
| `approve` | Approve and create organization |
| `reject` | Reject with reason |
| `request_revision` | Ask for more info |

---

## List Users

`GET /api/v1/admin/users`

**Query**: `?search=john&status=active&page=1&limit=20`

---

## User Detail

`GET /api/v1/admin/users/{id}`

---

## Update User

`PATCH /api/v1/admin/users/{id}`

```json
{
  "is_active": false,
  "admin_note": "..."
}
```

---

## Audit Logs

`GET /api/v1/admin/audit-logs`

**Query**: `?user_id=uuid&action=login&from=2026-01-01`

# Authentication API

**Base URL**: `/api/v1/auth`

---

## Register

`POST /api/v1/auth/register`

**Request**
```json
{
  "email": "user@example.com",
  "password": "securePass123",
  "full_name": "John Doe"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| email | string | ✅ | Valid email format |
| password | string | ✅ | Min 8 characters |
| full_name | string | ❌ | Max 100 chars |

**Response (201)**
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "access_token": "eyJ..."
  }
}
```

---

## Login

`POST /api/v1/auth/login`

**Request**
```json
{
  "email": "user@example.com",
  "password": "securePass123"
}
```

**Response (200)**
```json
{
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

---

## Google OAuth

`POST /api/v1/auth/google`

**Request**
```json
{ "id_token": "google-id-token" }
```

---

## Refresh Token

`POST /api/v1/auth/refresh`

Uses HttpOnly cookie. No body required.

---

## Logout

`POST /api/v1/auth/logout`

---

## Forgot Password

`POST /api/v1/auth/forgot-password`

**Request**
```json
{ "email": "user@example.com" }
```

---

## Reset Password

`POST /api/v1/auth/reset-password`

**Request**
```json
{
  "token": "token-from-email",
  "password": "newPassword123"
}
```

---

## Get Current User

`GET /api/v1/me`

**Headers**: `Authorization: Bearer {token}`

**Response (200)**
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "memberships": [...]
  }
}
```

---

## Update Profile

`PATCH /api/v1/me`

**Request**
```json
{
  "full_name": "Updated Name",
  "phone": "+62...",
  "nim": "2023001"
}
```

---

## Email Preferences

`GET /api/v1/me/email-preferences`
`PUT /api/v1/me/email-preferences`

**Options**: `instant`, `daily`, `weekly`, `none`

---

## Upload Profile Photo

`POST /api/v1/uploads/profile-photo`

**Content-Type**: `multipart/form-data`
**Max Size**: 5MB
**Allowed**: jpg, png, gif, webp

# SIMAORKA API Documentation

**Base URL**: `/api/v1`

## Response Format

### Success
```json
{
  "data": { ... },
  "meta": { "timestamp": "2026-01-21T08:00:00Z" }
}
```

### Error
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## API Reference

| Document | Description |
|----------|-------------|
| [API_AUTH.md](API_AUTH.md) | Authentication, Users, Profile |
| [API_ORGS.md](API_ORGS.md) | Organizations, Announcements, Events, Discussions, Documents |
| [API_FINANCE.md](API_FINANCE.md) | Finance Transactions, Summary, Public Transparency |
| [API_ADMIN.md](API_ADMIN.md) | Admin Dashboard, User Management, Audit |
| [API_WEB3.md](API_WEB3.md) | Web3 Wallet, NFT, Payments, Voting |

---

## Interactive Docs

- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
- **OpenAPI JSON**: `/api/schema/`

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `ALREADY_EXISTS` | 409 | Duplicate resource |
| `RATE_LIMITED` | 429 | Too many requests |

### Auth Errors

| Code | Description |
|------|-------------|
| `INVALID_CREDENTIALS` | Wrong email/password |
| `TOKEN_EXPIRED` | JWT or reset token expired |
| `EMAIL_NOT_VERIFIED` | Email not yet verified |

### Organization Errors

| Code | Description |
|------|-------------|
| `ALREADY_MEMBER` | Already a member or pending |
| `ORG_SUSPENDED` | Organization is suspended |

### Finance Errors

| Code | Description |
|------|-------------|
| `FINANCE_PRIVATE` | Finance is private (403) |
| `TRANSPARENCY_LEVEL_INSUFFICIENT` | Need full transparency |

### Web3 Errors

| Code | Description |
|------|-------------|
| `WALLET_NOT_VERIFIED` | Wallet signature invalid |
| `WEB3_NOT_CONFIGURED` | Web3 not enabled |
| `VOTE_ALREADY_CAST` | Already voted |
| `PAYMENT_DUPLICATE` | tx_hash already submitted |

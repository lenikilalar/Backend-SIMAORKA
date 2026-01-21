# Finance API

---

## List Transactions

`GET /api/v1/transactions?org_id=uuid`

**Permission**: `FINANCE_VIEW`

**Response (200)**
```json
{
  "data": [
    {
      "id": "tx-uuid",
      "ledger": { "id": "...", "name": "Kas Umum" },
      "type": "income",
      "category": "Iuran Anggota",
      "amount": "50000.00",
      "description": "...",
      "occurred_at": "2026-01-15"
    }
  ]
}
```

---

## Create Transaction

`POST /api/v1/transactions`

**Permission**: `FINANCE_CREATE`

```json
{
  "ledger": "ledger-uuid",
  "type": "income",
  "category": "Iuran Anggota",
  "amount": "50000.00",
  "description": "..."
}
```

---

## Finance Summary

`GET /api/v1/orgs/{org_id}/finance/summary`

**Permission**: `FINANCE_VIEW`

**Response (200)**
```json
{
  "data": {
    "totals": {
      "income": 15000000.00,
      "expense": 8500000.00,
      "balance": 6500000.00
    },
    "recent": { "income": 2500000, "expense": 1200000, "net": 1300000 },
    "web3": { "total_confirmed": 0.25, "pending_count": 2, "currency": "ETH" },
    "categories": {...},
    "monthly_trend": [...],
    "ledgers": [...]
  }
}
```

---

## Public Finance (Keterbukaan)

### Get Public Summary

`GET /api/v1/organizations/{slug}/finance/public`

**No authentication** (if org allows)

Requires `finance_transparency = 'summary'` or `'full'`

**Response (200)**
```json
{
  "data": {
    "organization": "BEM FT",
    "transparency_level": "summary",
    "totals": { "income": 15000000, "expense": 8500000, "balance": 6500000 },
    "categories": {...}
  }
}
```

---

### Get Public Transactions

`GET /api/v1/organizations/{slug}/finance/public/transactions`

**No authentication**

Requires `finance_transparency = 'full'`

---

## Web3 Payments

See [API_WEB3.md](API_WEB3.md) for Web3 payment endpoints.

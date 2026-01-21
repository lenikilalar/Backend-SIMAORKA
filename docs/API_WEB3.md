# Web3 API Documentation

> **Note**: Web3 features are **optional**. Check `/api/v1/web3/status` to see if Web3 is enabled.

---

## Web3 Status

`GET /api/v1/web3/status`

Check if Web3 features are enabled on this server.

**Response (200)**
```json
{
  "data": {
    "enabled": true,
    "chain": "sepolia",
    "chain_id": 11155111,
    "contracts": {
      "role_nft": "0x...",
      "gov_token": "0x...",
      "dues": "0x..."
    }
  }
}
```

**If disabled:**
```json
{
  "data": {
    "enabled": false,
    "message": "Web3 features are not configured on this server."
  }
}
```

---

## Wallet Verification

### Request Nonce

`POST /api/v1/web3/wallet/nonce`

**Request**
```json
{
  "wallet_address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12",
  "chain": "sepolia"
}
```

**Response (200)**
```json
{
  "data": {
    "wallet_address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12",
    "message": "SIMAORKA Wallet Verification\n\nPlease sign this message...\n\nNonce: a1b2c3d4e5f6\nTimestamp: 2026-01-21T08:00:00Z",
    "nonce": "a1b2c3d4e5f6"
  }
}
```

### Verify Wallet

`POST /api/v1/web3/wallet/verify`

**Headers**: `Authorization: Bearer {access_token}`

**Request**
```json
{
  "wallet_address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12",
  "signature": "0x1234567890abcdef..."
}
```

**Response (200)**
```json
{
  "data": {
    "verified": true,
    "wallet_id": "wallet-uuid",
    "message": "Wallet verified successfully"
  }
}
```

---

## User Wallets

### List Wallets

`GET /api/v1/web3/wallets`

**Response (200)**
```json
{
  "data": [
    {
      "id": "wallet-uuid",
      "address": "0xAbCdEf1234...",
      "chain": "sepolia",
      "is_primary": true,
      "is_verified": true,
      "verified_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Set Primary Wallet

`POST /api/v1/web3/wallets/{id}/set_primary`

---

## Contract Registry

`GET /api/v1/web3/contracts?org_id=uuid`

**Response (200)**
```json
{
  "data": [
    {
      "id": "contract-uuid",
      "name": "BEM FT Role NFT",
      "address": "0x1234...",
      "chain": "sepolia",
      "contract_type": "role_nft",
      "abi_url": "https://storage/abis/role-nft.json"
    }
  ]
}
```

---

## Role NFT

### Check Role NFT

`GET /api/v1/web3/check-role?wallet=0x...&org_id=uuid&role_code=ORG_ADMIN`

**Response (200)**
```json
{
  "data": {
    "has_role": true,
    "token_id": 5,
    "assigned_at": "2026-01-01T00:00:00Z"
  }
}
```

### List Role Assignments

`GET /api/v1/orgs/{org_id}/role-nfts/`

**Query**: `is_active=true`

**Response (200)**
```json
{
  "data": [
    {
      "id": "assignment-uuid",
      "wallet_address": "0x...",
      "role": { "role_code": "KETUA", "role_name": "Ketua" },
      "period": { "name": "2025/2026" },
      "token_id": 1,
      "tx_hash": "0x...",
      "is_active": true,
      "expires_at": "2026-12-31T23:59:59Z"
    }
  ]
}
```

### Record Role NFT Mint

`POST /api/v1/orgs/{org_id}/role-nfts/record_mint`

**Request**
```json
{
  "period_id": "period-uuid",
  "role_code": "ORG_ADMIN",
  "wallet_address": "0xAbCdEf...",
  "token_id": 5,
  "tx_hash": "0x1234...",
  "user_id": "user-uuid"
}
```

### Revoke Role NFT

`POST /api/v1/orgs/{org_id}/role-nfts/revoke`

**Request**
```json
{
  "assignment_id": "assignment-uuid",
  "revoke_tx_hash": "0x5678..."
}
```

---

## Web3 Payments (Kas)

### Submit Payment

`POST /api/v1/orgs/{org_id}/finance/web3/submit`

**Request**
```json
{
  "tx_hash": "0x...",
  "wallet_address": "0x...",
  "amount_wei": "50000000000000000",
  "chain": "sepolia",
  "contract_address": "0x...",
  "note": "Iuran Semester Genap"
}
```

**Response (201)**
```json
{
  "id": "payment-uuid",
  "status": "pending",
  "tx_hash": "0x...",
  "amount_eth": "0.05",
  "message": "Pembayaran dicatat, menunggu verifikasi blockchain."
}
```

### My Payments

`GET /api/v1/orgs/{org_id}/finance/web3/my-payments`

**Response (200)**
```json
{
  "data": [
    {
      "id": "payment-uuid",
      "tx_hash": "0x...",
      "amount": "0.05",
      "status": "confirmed",
      "confirmed_at": "2026-01-21T10:00:00Z"
    }
  ]
}
```

### All Payments (Admin)

`GET /api/v1/orgs/{org_id}/finance/web3/payments`

**Query**: `status=pending&page=1&limit=20`

### Verify Payment

`POST /api/v1/orgs/{org_id}/finance/web3/verify/{payment_id}`

**Request (auto)**
```json
{}
```

**Request (manual)**
```json
{ "manual": true }
```

**Response (200)**
```json
{
  "status": "confirmed",
  "verified_at": "2026-01-21T10:00:00Z",
  "verification_data": {
    "tx_hash": "0x...",
    "block_number": 12345678,
    "payer": "0x...",
    "amount_eth": "0.05"
  }
}
```

---

## Finance Summary (includes Web3)

`GET /api/v1/orgs/{org_id}/finance/summary`

**Permission**: `FINANCE_VIEW`

**Response (200)** *(Web3 section)*
```json
{
  "data": {
    "...other fields...",
    
    "web3": {
      "total_confirmed": 0.25,
      "pending_count": 2,
      "currency": "ETH"
    }
  }
}
```

---

## Voting (Token Weighted)

### List Votes

`GET /api/v1/orgs/{org_id}/votes?is_active=true`

**Response (200)**
```json
{
  "data": [
    {
      "id": "vote-uuid",
      "title": "Pemilihan Ketua BEM 2026",
      "type": "token_weighted",
      "options": ["Kandidat A", "Kandidat B", "Kandidat C"],
      "start_at": "2026-01-20T00:00:00Z",
      "end_at": "2026-01-25T23:59:59Z",
      "is_active": true,
      "total_votes": 75
    }
  ]
}
```

### Create Vote

`POST /api/v1/orgs/{org_id}/votes`

**Permission**: `VOTE_CREATE`

**Request**
```json
{
  "title": "Pemilihan Ketua BEM 2026",
  "description": "Voting untuk memilih ketua BEM periode 2026-2027",
  "options": ["Kandidat A", "Kandidat B", "Kandidat C"],
  "type": "token_weighted",
  "start_at": "2026-01-20T00:00:00Z",
  "end_at": "2026-01-25T23:59:59Z"
}
```

| Type | Description |
|------|-------------|
| `simple` | 1 person = 1 vote |
| `token_weighted` | Vote weight based on token balance |

### Get Vote Results

`GET /api/v1/orgs/{org_id}/votes/{id}`

**Response (200)**
```json
{
  "data": {
    "id": "vote-uuid",
    "title": "Pemilihan Ketua BEM 2026",
    "results": {
      "Kandidat A": 45,
      "Kandidat B": 30,
      "Kandidat C": 25
    },
    "total_votes": 100,
    "status": "closed",
    "winner": "Kandidat A"
  }
}
```

### Cast Vote

`POST /api/v1/orgs/{org_id}/votes/{id}/cast`

**Permission**: `VOTE_CAST`

**Request**
```json
{
  "option_index": 0,
  "wallet_address": "0xAbC123..."
}
```

**Response (201)**
```json
{
  "data": {
    "message": "Vote cast successfully",
    "option": "Kandidat A"
  }
}
```

**Error (400)**
```json
{
  "error": {
    "code": "VOTE_ALREADY_CAST",
    "message": "You have already voted"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `WALLET_NOT_VERIFIED` | Wallet not verified or signature invalid |
| `WEB3_NOT_CONFIGURED` | Web3 features not enabled |
| `VOTE_CLOSED` | Voting is not active or time has passed |
| `VOTE_ALREADY_CAST` | Already voted on this proposal |
| `PAYMENT_DUPLICATE` | Transaction hash already submitted |
| `PAYMENT_VERIFICATION_FAILED` | On-chain verification failed |

# SIMAORKA – Web3 Kas API Specification

Dokumen ini menjelaskan spesifikasi API backend (Django Rest Framework) untuk fitur **Kas Web3** pada sistem **SIMAORKA**.

---

## 1. Konsep API Kas Web3

### Prinsip Utama

* Blockchain **bukan** sumber laporan keuangan
* Blockchain = bukti pembayaran
* Database backend = ledger resmi organisasi

### Entitas Utama

* **FinanceTransaction** → catatan kas organisasi
* **Web3Payment** → bukti pembayaran blockchain
* **Organization** → pemilik kas
* **User** → pembayar (anggota)

---

## 2. Permission & Role

| Role             | Hak                                   |
| ---------------- | ------------------------------------- |
| Anggota          | Membayar kas, melihat riwayat pribadi |
| Bendahara        | Melihat semua pembayaran, laporan kas |
| Admin Organisasi | Monitoring & audit internal           |
| Superadmin       | Audit global & statistik              |

---

## 3. Ringkasan Endpoint

```
POST   /api/v1/orgs/{org_id}/finance/web3/submit
GET    /api/v1/orgs/{org_id}/finance/web3/my-payments
GET    /api/v1/orgs/{org_id}/finance/web3/payments
POST   /api/v1/orgs/{org_id}/finance/web3/verify/{payment_id}
GET    /api/v1/orgs/{org_id}/finance/summary
```

---

## 4. Model (Konseptual)

### FinanceTransaction

* id
* organization
* user
* amount
* currency (ETH)
* source (web3)
* status (pending, confirmed, failed)
* created_at

### Web3Payment

* id
* finance_transaction
* tx_hash
* wallet_address
* chain (sepolia)
* contract_address
* amount_wei
* status (pending, confirmed, failed)
* verified_at
* raw_event (JSON)

---

## 5. API Detail

### 5.1 Submit Pembayaran Web3

**Endpoint**

```
POST /api/v1/orgs/{org_id}/finance/web3/submit
```

**Auth**

* Login required
* Harus anggota organisasi

**Request Body**

```json
{
  "tx_hash": "0xabc123...",
  "wallet_address": "0xUserWallet",
  "amount_wei": "1000000000000000",
  "note": "Kas Januari"
}
```

**Response**

```json
{
  "id": "uuid-payment",
  "status": "pending",
  "tx_hash": "0xabc123...",
  "message": "Pembayaran dicatat, menunggu verifikasi blockchain"
}
```

---

### 5.2 Verifikasi Pembayaran Web3

**Endpoint**

```
POST /api/v1/orgs/{org_id}/finance/web3/verify/{payment_id}
```

**Auth**

* Bendahara / Admin Organisasi / Superadmin

**Response (Success)**

```json
{
  "status": "confirmed",
  "verified_at": "2026-01-12T09:00:00Z"
}
```

**Response (Failed)**

```json
{
  "status": "failed",
  "reason": "Event DuesPaid tidak ditemukan"
}
```

---

### 5.3 Riwayat Pembayaran Pribadi

**Endpoint**

```
GET /api/v1/orgs/{org_id}/finance/web3/my-payments
```

---

### 5.4 Daftar Semua Pembayaran Web3

**Endpoint**

```
GET /api/v1/orgs/{org_id}/finance/web3/payments
```

Query Param:

```
?status=pending|confirmed|failed
```

---

### 5.5 Ringkasan Kas Organisasi

**Endpoint**

```
GET /api/v1/orgs/{org_id}/finance/summary
```

---

## 6. Keamanan & Audit

* Semua verifikasi dilakukan backend
* Tx hash immutable
* Event log disimpan
* Semua aksi admin tercatat pada Activity Log Kampus

---

## 7. Integrasi Frontend

Frontend hanya bertugas:

* Connect wallet (MetaMask)
* Kirim transaksi
* Submit tx hash ke backend
* Polling status pembayaran

Private key **tidak pernah** masuk backend.

---

## 8. Catatan Penting

> Pembayaran dianggap sah hanya jika:
>
> * Tx confirmed
> * Event valid
> * Contract address sesuai


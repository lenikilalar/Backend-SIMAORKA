# Web3 Integration Setup Guide

Complete guide for setting up Web3 features in SIMAORKA Backend.

> **Note**: Web3 is an **optional feature**. Set `WEB3_ENABLED=True` in `.env` to activate.

## Prerequisites

- MetaMask or compatible Web3 wallet
- Sepolia ETH for testnet transactions
- Infura/Alchemy API key for RPC access

---

## Arsitektur Web3 Layer

Web3 layer dipakai untuk **3 hal utama**:

1. **Legalitas pengurus & struktur periode** → NFT jabatan (soulbound, ada masa berlaku, bisa dicabut)
2. **Akses & update dokumen penting** → akses dikunci oleh kepemilikan NFT jabatan + validitas periode
3. **Voting keputusan** → token hak suara (non-transferable), voting hybrid

### Smart Contracts

Contracts tersedia di folder [`contracts/`](../contracts/):

| File | Contract | Fungsi |
|------|----------|--------|
| `SimaorkaRoleNFT.sol` | ERC-721 Soulbound | NFT jabatan organisasi |
| `SimaorkaGovToken.sol` | ERC-20 Non-transferable | Token voting weight |
| `SimaorkaDues.sol` | Payment Contract | Pembayaran kas ETH |

Target jaringan: **Sepolia testnet** (chainId `11155111`).

---

## Quick Setup

### 1. Install Dependencies

```bash
pip install web3 eth-account
```

### 2. Configure Environment

```env
# Enable Web3 features
WEB3_ENABLED=True
WEB3_CHAIN=sepolia
WEB3_CHAIN_ID=11155111

# RPC Provider
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

# Contract Addresses (after deployment)
ROLE_NFT_ADDRESS=0x...
GOV_TOKEN_ADDRESS=0x...
DUES_CONTRACT_ADDRESS=0x...
```

### 3. Deploy Contracts

See [`contracts/README.md`](../contracts/README.md) for deployment instructions.

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Check Status

```bash
curl http://localhost:8000/api/v1/web3/status
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Wallet Verification** | Sign-in-with-Ethereum style wallet ownership proof |
| **Role NFT** | Soulbound tokens for organization roles |
| **Governance Token** | Non-transferable voting weight tokens |
| **Web3 Payments** | Cryptocurrency dues collection |
| **Document Gating** | Access control by Role NFT ownership |
| **Hybrid Voting** | Token-weighted voting with off-chain UX |

---

## Wallet Verification

### Flow

1. Frontend requests nonce: `POST /api/v1/web3/wallet/nonce`
2. User signs message with MetaMask
3. Frontend verifies: `POST /api/v1/web3/wallet/verify`

### Sign Message (Frontend)

```javascript
import { BrowserProvider } from 'ethers';

const provider = new BrowserProvider(window.ethereum);
const signer = await provider.getSigner();
const signature = await signer.signMessage(message);
```

---

## Role NFT

Role NFTs are soulbound tokens for organizational roles:
- Prove membership during a specific period
- Have expiration dates and can be revoked
- Gate access to documents and voting

### Frontend: Mint NFT

After admin mints on-chain, notify backend:

```javascript
POST /api/v1/orgs/{org_id}/role-nfts/record_mint
{ period_id, role_code, wallet_address, token_id, tx_hash }
```

### Check Role

```javascript
GET /api/v1/web3/check-role?wallet=0x...&org_id=uuid&role_code=KETUA
```

---

## Web3 Payments

### Flow

```
MetaMask → SimaorkaDues.sol → Backend records → Verification
```

### Frontend: Pay

```typescript
import { BrowserProvider, Contract, parseEther } from "ethers";

const contract = new Contract(contractAddress, DUES_ABI, signer);
const tx = await contract.payDues(orgId, note, { value: parseEther(amount) });
```

### Backend: Submit

```javascript
POST /api/v1/orgs/{org_id}/finance/web3/submit
{ tx_hash, wallet_address, amount_wei, chain, note }
```

### Backend: Verify

```javascript
POST /api/v1/orgs/{org_id}/finance/web3/verify/{payment_id}
// Auto-verifies on blockchain
// Use { manual: true } for manual verification
```

---

## Voting

### Hybrid Voting Flow

1. Admin creates vote with options and time range
2. Vote weight = `balanceOf(wallet)` on GovToken
3. Members cast votes (one wallet = one vote)
4. Results calculated from database

### Create Vote

```javascript
POST /api/v1/orgs/{org_id}/votes
{ title, description, options, type, start_at, end_at }
```

### Cast Vote

```javascript
POST /api/v1/orgs/{org_id}/votes/{vote_id}/cast
{ option_index, wallet_address }
```

---

## Document Gating

Documents can require Role NFT ownership for access.

| Field | Description |
|-------|-------------|
| `requires_nft` | If true, requires Role NFT |
| `required_role_code` | Which role is needed (e.g., `KETUA`) |

Backend checks wallet ownership before granting access.

---

## Database Models

| Model | Description |
|-------|-------------|
| `Web3Contract` | Deployed contract registry |
| `UserWallet` | User's verified wallets |
| `OrgPeriod` | Organization periods |
| `OrgRoleCatalog` | Role definitions |
| `OrgRoleAssignment` | Minted Role NFT records |

---

## API Reference

See the **Swagger UI** at `/api/schema/swagger-ui/` (grouped under `Web3`) for full API documentation.

### Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/web3/status` | GET | Check if Web3 enabled |
| `/web3/wallet/nonce` | POST | Get verification nonce |
| `/web3/wallet/verify` | POST | Verify wallet signature |
| `/web3/check-role` | GET | Check wallet role NFT |
| `/orgs/{id}/role-nfts/` | GET | List role assignments |
| `/orgs/{id}/finance/web3/submit` | POST | Submit payment |
| `/orgs/{id}/votes` | POST | Create vote |
| `/orgs/{id}/votes/{id}/cast` | POST | Cast vote |

---

## Testing

### Get Sepolia ETH

1. Go to https://sepoliafaucet.com/
2. Enter your wallet address
3. Request test ETH

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Invalid signature | Ensure exact message is signed, check address case |
| RPC connection failed | Check `SEPOLIA_RPC_URL` in .env |
| Contract not found | Verify contract deployed to correct network |

---

## Security

1. **Private Keys**: Never store in backend
2. **Nonce Expiry**: Should expire after 5-10 minutes
3. **Contract Admin**: Use multisig for production
4. **Rate Limiting**: Limit nonce requests

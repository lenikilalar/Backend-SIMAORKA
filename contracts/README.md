# SIMAORKA Smart Contracts

Solidity smart contracts untuk fitur Web3 SIMAORKA.

## Contracts

| File | Contract | Fungsi |
|------|----------|--------|
| `SimaorkaRoleNFT.sol` | ERC-721 Soulbound | NFT jabatan organisasi dengan expiry & revoke |
| `SimaorkaGovToken.sol` | ERC-20 Non-transferable | Token voting weight |
| `SimaorkaDues.sol` | Payment Contract | Pembayaran kas dalam ETH |

## Deployment (Sepolia Testnet)

### Prerequisites

- MetaMask dengan Sepolia ETH
- [Remix IDE](https://remix.ethereum.org)

### Steps

1. Buka Remix IDE
2. Buat file baru dengan nama sesuai (e.g., `SimaorkaRoleNFT.sol`)
3. Copy-paste kode dari file ini
4. Compile dengan Solidity 0.8.20
5. Deploy:
   - Environment: **Injected Provider - MetaMask**
   - Network: **Sepolia** (chainId 11155111)
6. Copy contract address ke `.env`:
   ```env
   ROLE_NFT_ADDRESS=0x...
   GOV_TOKEN_ADDRESS=0x...
   DUES_CONTRACT_ADDRESS=0x...
   ```

## Post-Deployment

### SimaorkaRoleNFT
- Deploy dengan `initialOwner` = deployer address
- Owner dapat `mintRole()` dan `revoke()`

### SimaorkaGovToken
- Deploy dengan `initialOwner` = deployer address
- Owner dapat `mint()` dan `burn()`

### SimaorkaDues
- Setelah deploy, jalankan `setTreasurer(orgId, treasurerAddress)` untuk setiap organisasi
- Treasurer dapat `withdraw()` dana

## Notes

- Semua contract menggunakan OpenZeppelin v5.x
- Transfer NFT diblokir (Soulbound)
- Transfer token diblokir (Non-transferable)
- Gunakan Sepolia untuk testing, mainnet untuk production

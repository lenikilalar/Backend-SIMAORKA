// SPDX-License-Identifier: MIT
// File: SimaorkaRoleNFT.sol
// Soulbound NFT for organization roles with expiry and revocation
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SimaorkaRoleNFT is ERC721, Ownable {
    struct RoleData {
        uint256 orgId;
        uint256 periodId;
        bytes32 roleCode;     // e.g. keccak256("KETUA")
        uint64  expiresAt;    // unix timestamp
        bool    revoked;
    }

    uint256 public nextTokenId = 1;
    mapping(uint256 => RoleData) public roleOf;

    event RoleMinted(uint256 indexed tokenId, address indexed to, uint256 orgId, uint256 periodId, bytes32 roleCode, uint64 expiresAt);
    event RoleRevoked(uint256 indexed tokenId);

    constructor(address initialOwner) ERC721("SIMAORKA Role", "SROLE") Ownable(initialOwner) {}

    function mintRole(
        address to,
        uint256 orgId,
        uint256 periodId,
        bytes32 roleCode,
        uint64 expiresAt
    ) external onlyOwner returns (uint256) {
        require(to != address(0), "zero address");
        require(expiresAt > block.timestamp, "expiresAt must be future");

        uint256 tokenId = nextTokenId++;
        _safeMint(to, tokenId);
        roleOf[tokenId] = RoleData(orgId, periodId, roleCode, expiresAt, false);

        emit RoleMinted(tokenId, to, orgId, periodId, roleCode, expiresAt);
        return tokenId;
    }

    function revoke(uint256 tokenId) external onlyOwner {
        require(_ownerOf(tokenId) != address(0), "not minted");
        roleOf[tokenId].revoked = true;
        emit RoleRevoked(tokenId);
    }

    function isValidToken(uint256 tokenId) public view returns (bool) {
        address owner = _ownerOf(tokenId);
        if (owner == address(0)) return false;
        RoleData memory r = roleOf[tokenId];
        if (r.revoked) return false;
        if (block.timestamp > r.expiresAt) return false;
        return true;
    }

    // Soulbound: block transfers
    function _update(address to, uint256 tokenId, address auth)
        internal override returns (address)
    {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) revert("Soulbound");
        return super._update(to, tokenId, auth);
    }
}

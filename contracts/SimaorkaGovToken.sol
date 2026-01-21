// SPDX-License-Identifier: MIT
// File: SimaorkaGovToken.sol
// Non-transferable ERC-20 token for voting weight
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SimaorkaGovToken is ERC20, Ownable {
    constructor(address initialOwner) ERC20("SIMAORKA Vote Power", "SVP") Ownable(initialOwner) {}

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external onlyOwner {
        _burn(from, amount);
    }

    // Non-transferable: block transfers except mint/burn
    function _update(address from, address to, uint256 value) internal override {
        if (from != address(0) && to != address(0)) revert("Non-transferable");
        super._update(from, to, value);
    }
}

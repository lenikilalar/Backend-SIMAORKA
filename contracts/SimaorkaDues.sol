// SPDX-License-Identifier: MIT
// File: SimaorkaDues.sol
// Payment contract for organization dues collection in ETH
pragma solidity ^0.8.20;

contract SimaorkaDues {
    address public owner;
    mapping(uint256 => address) public orgTreasurer;

    event TreasurerSet(uint256 indexed orgId, address indexed treasurer);
    event DuesPaid(uint256 indexed orgId, address indexed payer, uint256 amountWei, string note);
    event Withdrawn(uint256 indexed orgId, address indexed to, uint256 amountWei);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyTreasurer(uint256 orgId) {
        require(msg.sender == orgTreasurer[orgId], "Not treasurer");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setTreasurer(uint256 orgId, address treasurer) external onlyOwner {
        require(treasurer != address(0), "Zero address");
        orgTreasurer[orgId] = treasurer;
        emit TreasurerSet(orgId, treasurer);
    }

    function payDues(uint256 orgId, string calldata note) external payable {
        require(msg.value > 0, "No value");
        emit DuesPaid(orgId, msg.sender, msg.value, note);
    }

    function withdraw(uint256 orgId, uint256 amountWei, address payable to) external onlyTreasurer(orgId) {
        require(address(this).balance >= amountWei, "Insufficient balance");
        (bool ok, ) = to.call{value: amountWei}("");
        require(ok, "Transfer failed");
        emit Withdrawn(orgId, to, amountWei);
    }

    function contractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}

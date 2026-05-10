// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/// @title Nexus Game Theory Token
/// @notice Nexus-authored protocol token surface tracked under the Nexus Encryption Standard (NES).
/// @dev NES is the repository designation for Nexus-owned security, signing, and protected-message
/// conventions documented in docs/NEXUS_ENCRYPTION_STANDARD.md. Third-party imports retain their
/// original licensing and ownership terms.
contract NexusGameTheoryToken is ERC20, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * 10**18;
    uint256 public constant BTC_BACKING_RATIO = 100;
    uint256 public profitPool;
    uint256 public totalDistributed;
    
    struct MCPGroup {
        string name;
        address[] members;
        uint256 totalTokens;
        uint256 gamesPlayed;
        uint256 profitShare;
        bool active;
    }
    
    mapping(uint256 => MCPGroup) public mcpGroups;
    mapping(address => uint256) public userToGroup;
    mapping(address => uint256) public userProfits;
    Counters.Counter private groupIdCounter;
    
    mapping(address => uint256) public gamesCompleted;
    mapping(address => uint256) public skillLevel;
    mapping(address => uint256) public lastPlayTimestamp;
    
    event MCPGroupCreated(uint256 indexed groupId, string name);
    event GameCompleted(address indexed player, uint256 reward, uint256 skillIncrease);
    event ProfitDistributed(address indexed recipient, uint256 amount);
    event BTCValueUpdated(uint256 newBtcValue);
    event BoostActivated(address indexed user, uint256 multiplier);
    
    constructor() ERC20("Nexus Game Theory Token", "NGTT") {
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    function createMCPGroup(string memory _name, address[] memory _members) external onlyOwner returns (uint256) {
        require(_members.length > 0, "Members list cannot be empty");
        for (uint256 i = 0; i < _members.length; i++) {
            require(_members[i] != address(0), "Member address cannot be zero");
        }

        groupIdCounter.increment();
        uint256 newGroupId = groupIdCounter.current();
        
        MCPGroup storage newGroup = mcpGroups[newGroupId];
        newGroup.name = _name;
        newGroup.members = _members;
        newGroup.active = true;
        
        for (uint256 i = 0; i < _members.length; i++) {
            userToGroup[_members[i]] = newGroupId;
        }
        
        emit MCPGroupCreated(newGroupId, _name);
        return newGroupId;
    }
    
    function completeGame(address _player, uint256 _baseReward, uint256 _ageGroupId) external onlyOwner nonReentrant {
        require(_player != address(0), "Player address cannot be zero");
        require(_baseReward > 0, "Reward must be positive");
        
        uint256 skillMultiplier = 100 + (skillLevel[_player] / 10);
        uint256 reward = (_baseReward * skillMultiplier) / 100;
        
        if (_ageGroupId <= 2) {
            reward = (reward * 120) / 100;
        }
        
        gamesCompleted[_player]++;
        skillLevel[_player] += 10;
        lastPlayTimestamp[_player] = block.timestamp;
        
        uint256 groupId = userToGroup[_player];
        if (groupId > 0) {
            mcpGroups[groupId].gamesPlayed++;
            mcpGroups[groupId].totalTokens += reward;
        }
        
        _mint(_player, reward);
        emit GameCompleted(_player, reward, 10);
    }
    
    function distributeProfits() external onlyOwner nonReentrant {
        require(profitPool > 0, "No profits to distribute");
        
        uint256 totalActivity = 0;
        for (uint256 i = 1; i <= groupIdCounter.current(); i++) {
            if (mcpGroups[i].active) {
                totalActivity += mcpGroups[i].gamesPlayed;
            }
        }
        
        require(totalActivity > 0, "No activity recorded");
        
        for (uint256 i = 1; i <= groupIdCounter.current(); i++) {
            if (mcpGroups[i].active && mcpGroups[i].gamesPlayed > 0) {
                uint256 groupShare = (profitPool * mcpGroups[i].gamesPlayed) / totalActivity;
                mcpGroups[i].profitShare += groupShare;
                
                uint256 perMember = groupShare / mcpGroups[i].members.length;
                for (uint256 j = 0; j < mcpGroups[i].members.length; j++) {
                    address member = mcpGroups[i].members[j];
                    userProfits[member] += perMember;
                    emit ProfitDistributed(member, perMember);
                }
            }
        }
        
        totalDistributed += profitPool;
        profitPool = 0;
    }
    
    function claimProfits() external nonReentrant {
        uint256 amount = userProfits[msg.sender];
        require(amount > 0, "No profits to claim");
        
        userProfits[msg.sender] = 0;
        _mint(msg.sender, amount);
        
        emit ProfitDistributed(msg.sender, amount);
    }
    
    function addProfitPool(uint256 _amount) external onlyOwner {
        profitPool += _amount;
    }
    
    function activateBoost(address _user, uint256 _multiplier) external onlyOwner {
        require(_user != address(0), "User address cannot be zero");
        require(_multiplier >= 100 && _multiplier <= 500, "Invalid multiplier");
        skillLevel[_user] += (_multiplier - 100);
        emit BoostActivated(_user, _multiplier);
    }
    
    function getUserStats(address _user) external view returns (uint256 games, uint256 skill, uint256 profits, uint256 groupId) {
        return (gamesCompleted[_user], skillLevel[_user], userProfits[_user], userToGroup[_user]);
    }
    
    function getGroupStats(uint256 _groupId) external view returns (string memory name, uint256 memberCount, uint256 totalTokens, uint256 gamesPlayed, uint256 profitShare) {
        MCPGroup memory group = mcpGroups[_groupId];
        return (group.name, group.members.length, group.totalTokens, group.gamesPlayed, group.profitShare);
    }
}

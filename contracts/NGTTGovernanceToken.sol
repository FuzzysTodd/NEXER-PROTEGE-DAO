// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/extensions/draft-ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/// @title NGTT Governance Token
/// @notice Nexus Game Theory Token with on-chain snapshot voting and delegation.
/// @dev Extends the original NGTT design with ERC20Votes and ERC20Permit so that
///      token holders can delegate voting weight to themselves or to a trusted
///      delegate, enabling trustless participation in the NexusDAOGovernor.
///      NES: this contract is a Nexus-authored surface governed by the
///      Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
///      Third-party imports retain their original licensing and ownership terms.
contract NGTTGovernanceToken is ERC20Votes, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;

    // -------------------------------------------------------------------------
    // Constants
    // -------------------------------------------------------------------------

    /// @notice Total tokens minted at genesis (1 billion NGTT, 18 decimals).
    uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * 10 ** 18;

    /// @notice BTC-backing ratio encoded in the protocol (1 NGTT : 100 satoshi-units).
    uint256 public constant BTC_BACKING_RATIO = 100;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    /// @notice Accumulated profit available for distribution.
    uint256 public profitPool;

    /// @notice Lifetime total of distributed profits.
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
    Counters.Counter private _groupIdCounter;

    mapping(address => uint256) public gamesCompleted;
    mapping(address => uint256) public skillLevel;
    mapping(address => uint256) public lastPlayTimestamp;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when a new MCP group is created.
    event MCPGroupCreated(uint256 indexed groupId, string name);

    /// @notice Emitted when a player completes a game session.
    event GameCompleted(address indexed player, uint256 reward, uint256 skillIncrease);

    /// @notice Emitted when profits are distributed to a recipient.
    event ProfitDistributed(address indexed recipient, uint256 amount);

    /// @notice Emitted when the BTC reference value is updated.
    event BTCValueUpdated(uint256 newBtcValue);

    /// @notice Emitted when a skill boost is applied to a user.
    event BoostActivated(address indexed user, uint256 multiplier);

    /// @notice Emitted when tokens are added to the profit pool.
    event ProfitPoolIncreased(uint256 amount, uint256 newTotal);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the token, mints the full initial supply to the deployer,
    ///         and self-delegates so the deployer's voting power is active immediately.
    constructor() ERC20("Nexus Game Theory Token", "NGTT") ERC20Permit("Nexus Game Theory Token") {
        _mint(msg.sender, INITIAL_SUPPLY);
        // Self-delegate so the deployer's votes are active without an extra tx.
        _delegate(msg.sender, msg.sender);
    }

    // -------------------------------------------------------------------------
    // MCP Group management
    // -------------------------------------------------------------------------

    /// @notice Creates a new MCP group with the given members.
    /// @param _name Human-readable group name.
    /// @param _members Array of member addresses (must be non-empty, no zero addresses).
    /// @return groupId The unique identifier assigned to the new group.
    function createMCPGroup(string memory _name, address[] memory _members)
        external
        onlyOwner
        returns (uint256)
    {
        require(_members.length > 0, "NGTT: empty member list");
        for (uint256 i = 0; i < _members.length; i++) {
            require(_members[i] != address(0), "NGTT: zero member address");
        }

        _groupIdCounter.increment();
        uint256 newGroupId = _groupIdCounter.current();

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

    // -------------------------------------------------------------------------
    // Game rewards
    // -------------------------------------------------------------------------

    /// @notice Records a completed game session and mints skill-adjusted rewards.
    /// @param _player The player who completed the game.
    /// @param _baseReward Base reward amount in NGTT tokens (18 decimals).
    /// @param _ageGroupId Age group identifier; groups ≤ 2 receive a 20% bonus.
    function completeGame(address _player, uint256 _baseReward, uint256 _ageGroupId)
        external
        onlyOwner
        nonReentrant
    {
        require(_player != address(0), "NGTT: zero player address");
        require(_baseReward > 0, "NGTT: reward must be positive");

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

    // -------------------------------------------------------------------------
    // Profit pool
    // -------------------------------------------------------------------------

    /// @notice Distributes the accumulated profit pool proportionally across
    ///         active MCP groups (weighted by games played).
    function distributeProfits() external onlyOwner nonReentrant {
        require(profitPool > 0, "NGTT: no profits to distribute");

        uint256 totalActivity = 0;
        uint256 groupCount = _groupIdCounter.current();
        for (uint256 i = 1; i <= groupCount; i++) {
            if (mcpGroups[i].active) {
                totalActivity += mcpGroups[i].gamesPlayed;
            }
        }
        require(totalActivity > 0, "NGTT: no activity recorded");

        uint256 snapshot = profitPool;
        profitPool = 0;
        totalDistributed += snapshot;

        for (uint256 i = 1; i <= groupCount; i++) {
            if (mcpGroups[i].active && mcpGroups[i].gamesPlayed > 0) {
                uint256 groupShare = (snapshot * mcpGroups[i].gamesPlayed) / totalActivity;
                mcpGroups[i].profitShare += groupShare;

                uint256 memberCount = mcpGroups[i].members.length;
                uint256 perMember = groupShare / memberCount;
                for (uint256 j = 0; j < memberCount; j++) {
                    address member = mcpGroups[i].members[j];
                    userProfits[member] += perMember;
                    emit ProfitDistributed(member, perMember);
                }
            }
        }
    }

    /// @notice Lets a member claim their allocated profits by minting the owed tokens.
    function claimProfits() external nonReentrant {
        uint256 amount = userProfits[msg.sender];
        require(amount > 0, "NGTT: no profits to claim");

        userProfits[msg.sender] = 0;
        _mint(msg.sender, amount);

        emit ProfitDistributed(msg.sender, amount);
    }

    /// @notice Increases the profit pool by the specified amount (accounting unit only;
    ///         no token transfer occurs here — caller is responsible for ensuring
    ///         backing tokens have been transferred to the treasury).
    /// @param _amount Amount to add to the profit pool.
    function addProfitPool(uint256 _amount) external onlyOwner {
        require(_amount > 0, "NGTT: amount must be positive");
        profitPool += _amount;
        emit ProfitPoolIncreased(_amount, profitPool);
    }

    // -------------------------------------------------------------------------
    // Skill boosts
    // -------------------------------------------------------------------------

    /// @notice Applies a skill multiplier boost to the target user.
    /// @param _user The user to boost.
    /// @param _multiplier Boost multiplier in basis points (100 = 1×, 500 = 5×).
    function activateBoost(address _user, uint256 _multiplier) external onlyOwner {
        require(_user != address(0), "NGTT: zero user address");
        require(_multiplier >= 100 && _multiplier <= 500, "NGTT: invalid multiplier");
        skillLevel[_user] += (_multiplier - 100);
        emit BoostActivated(_user, _multiplier);
    }

    // -------------------------------------------------------------------------
    // View helpers
    // -------------------------------------------------------------------------

    /// @notice Returns aggregated stats for the given user.
    /// @param _user The user address to query.
    /// @return games Number of games completed.
    /// @return skill Current skill level.
    /// @return profits Unclaimed profit balance.
    /// @return groupId MCP group the user belongs to (0 = no group).
    function getUserStats(address _user)
        external
        view
        returns (uint256 games, uint256 skill, uint256 profits, uint256 groupId)
    {
        return (gamesCompleted[_user], skillLevel[_user], userProfits[_user], userToGroup[_user]);
    }

    /// @notice Returns aggregated stats for a given MCP group.
    /// @param _groupId The group identifier to query.
    /// @return name Group name.
    /// @return memberCount Number of members.
    /// @return totalTokens Total tokens earned by the group.
    /// @return gamesPlayed Total games played within the group.
    /// @return profitShare Cumulative profit distributed to the group.
    function getGroupStats(uint256 _groupId)
        external
        view
        returns (
            string memory name,
            uint256 memberCount,
            uint256 totalTokens,
            uint256 gamesPlayed,
            uint256 profitShare
        )
    {
        MCPGroup memory group = mcpGroups[_groupId];
        return (group.name, group.members.length, group.totalTokens, group.gamesPlayed, group.profitShare);
    }

    // -------------------------------------------------------------------------
    // ERC20Votes / ERC20Permit required overrides
    // -------------------------------------------------------------------------

    /// @dev Hook called after every token transfer to update vote checkpoints.
    function _afterTokenTransfer(address from, address to, uint256 amount)
        internal
        override(ERC20, ERC20Votes)
    {
        super._afterTokenTransfer(from, to, amount);
    }

    /// @dev Mint override required by ERC20Votes.
    function _mint(address to, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._mint(to, amount);
    }

    /// @dev Burn override required by ERC20Votes.
    function _burn(address account, uint256 amount) internal override(ERC20, ERC20Votes) {
        super._burn(account, amount);
    }
}

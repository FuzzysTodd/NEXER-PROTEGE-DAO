// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title NexusLPStaking
 * @notice Stake Uniswap-v2-style LP tokens, earn NGTT rewards.
 *         Reward rate is set by the owner (DAO executor via governance).
 *         Standard MasterChef-style per-second accumulator.
 *
 * Events match nexus-signal-bus.js LP_STAKING_ABI exactly.
 *
 * Agent assignments:
 *   mcp-002 Token Economics Manager  — sets reward rates
 *   nexus-defi-architect             — AMM / yield optimisation
 *
 * @author Nexus Protocol DAO  (nexus-defi-architect)
 */
contract NexusLPStaking is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------
    IERC20  public immutable lpToken;
    IERC20  public immutable rewardToken;

    uint256 public rewardRate;          // NGTT per second (18-decimal)
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;
    uint256 public totalStaked;

    struct UserInfo {
        uint256 balance;
        uint256 rewardPerTokenPaid;
        uint256 rewards;
    }

    mapping(address => UserInfo) public userInfo;

    // -----------------------------------------------------------------------
    // Events (match signal-bus ABI)
    // -----------------------------------------------------------------------
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 reward);
    event RewardRateUpdated(uint256 oldRate, uint256 newRate);

    // -----------------------------------------------------------------------
    // Constructor
    // -----------------------------------------------------------------------
    constructor(address _lpToken, address _rewardToken, uint256 _rewardRate, address owner_) Ownable(owner_) {
        lpToken     = IERC20(_lpToken);
        rewardToken = IERC20(_rewardToken);
        rewardRate  = _rewardRate;
        lastUpdateTime = block.timestamp;
    }

    // -----------------------------------------------------------------------
    // Accumulator
    // -----------------------------------------------------------------------
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) return rewardPerTokenStored;
        return rewardPerTokenStored
            + ((block.timestamp - lastUpdateTime) * rewardRate * 1e18 / totalStaked);
    }

    function earned(address account) public view returns (uint256) {
        UserInfo storage u = userInfo[account];
        return u.balance * (rewardPerToken() - u.rewardPerTokenPaid) / 1e18 + u.rewards;
    }

    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime       = block.timestamp;
        if (account != address(0)) {
            userInfo[account].rewards          = earned(account);
            userInfo[account].rewardPerTokenPaid = rewardPerTokenStored;
        }
        _;
    }

    // -----------------------------------------------------------------------
    // Staking
    // -----------------------------------------------------------------------
    function deposit(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0, "NexusLPStaking: zero amount");
        totalStaked += amount;
        userInfo[msg.sender].balance += amount;
        lpToken.safeTransferFrom(msg.sender, address(this), amount);
        emit Deposited(msg.sender, amount);
    }

    function withdraw(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0 && userInfo[msg.sender].balance >= amount, "NexusLPStaking: invalid amount");
        totalStaked -= amount;
        userInfo[msg.sender].balance -= amount;
        lpToken.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    function claimReward() external nonReentrant updateReward(msg.sender) {
        uint256 reward = userInfo[msg.sender].rewards;
        if (reward > 0) {
            userInfo[msg.sender].rewards = 0;
            rewardToken.safeTransfer(msg.sender, reward);
            emit RewardClaimed(msg.sender, reward);
        }
    }

    // -----------------------------------------------------------------------
    // Admin
    // -----------------------------------------------------------------------
    function setRewardRate(uint256 newRate) external onlyOwner updateReward(address(0)) {
        emit RewardRateUpdated(rewardRate, newRate);
        rewardRate = newRate;
    }
}

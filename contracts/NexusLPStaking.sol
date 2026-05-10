// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title NexusLPStaking
/// @notice Liquidity-provider staking contract.  Users deposit LP tokens and
///         earn NGTT rewards proportional to their share and time staked.
///
/// Reward mechanics (per-second accumulator pattern):
///   - Owner sets a `rewardRate` (NGTT per second distributed across all stakers).
///   - On every deposit/withdraw/harvest the global `rewardPerTokenStored`
///     accumulator is updated.
///   - Each user's earned balance is tracked via their `rewardPerTokenPaid`
///     snapshot and a `pendingRewards` cache.
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
contract NexusLPStaking is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    // -------------------------------------------------------------------------
    // Tokens
    // -------------------------------------------------------------------------

    /// @notice The LP token that users deposit.
    IERC20 public immutable stakingToken;

    /// @notice The NGTT reward token that users earn.
    IERC20 public immutable rewardToken;

    // -------------------------------------------------------------------------
    // Reward state
    // -------------------------------------------------------------------------

    /// @notice NGTT reward tokens distributed per second across all stakers.
    uint256 public rewardRate;

    /// @notice Timestamp of the last reward accumulator update.
    uint256 public lastUpdateTime;

    /// @notice Accumulated reward per staked LP token (scaled by 1e18).
    uint256 public rewardPerTokenStored;

    // -------------------------------------------------------------------------
    // User state
    // -------------------------------------------------------------------------

    struct UserInfo {
        uint256 amount;              // LP tokens deposited
        uint256 rewardPerTokenPaid;  // rewardPerTokenStored snapshot at last settlement
        uint256 pendingRewards;      // Accrued but not yet claimed rewards
    }

    mapping(address => UserInfo) public userInfo;

    /// @notice Total LP tokens deposited across all users.
    uint256 public totalStaked;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when a user deposits LP tokens.
    event Deposited(address indexed user, uint256 amount);

    /// @notice Emitted when a user withdraws LP tokens.
    event Withdrawn(address indexed user, uint256 amount);

    /// @notice Emitted when a user claims NGTT rewards.
    event RewardClaimed(address indexed user, uint256 reward);

    /// @notice Emitted when the owner updates the reward rate.
    event RewardRateUpdated(uint256 oldRate, uint256 newRate);

    /// @notice Emitted when the owner refills the reward pool.
    event RewardPoolRefilled(uint256 amount);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Deploys the staking contract.
    /// @param _stakingToken Address of the LP token users deposit.
    /// @param _rewardToken  Address of the NGTT reward token.
    constructor(address _stakingToken, address _rewardToken) {
        require(_stakingToken != address(0), "NexusLPStaking: zero staking token");
        require(_rewardToken != address(0), "NexusLPStaking: zero reward token");
        stakingToken = IERC20(_stakingToken);
        rewardToken = IERC20(_rewardToken);
        lastUpdateTime = block.timestamp;
    }

    // -------------------------------------------------------------------------
    // Modifiers
    // -------------------------------------------------------------------------

    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = block.timestamp;
        if (account != address(0)) {
            UserInfo storage user = userInfo[account];
            user.pendingRewards = earned(account);
            user.rewardPerTokenPaid = rewardPerTokenStored;
        }
        _;
    }

    // -------------------------------------------------------------------------
    // Core functions
    // -------------------------------------------------------------------------

    /// @notice Returns the current accumulated reward per staked LP token.
    /// @return Reward per token (scaled by 1e18).
    function rewardPerToken() public view returns (uint256) {
        if (totalStaked == 0) {
            return rewardPerTokenStored;
        }
        return rewardPerTokenStored + (
            (block.timestamp - lastUpdateTime) * rewardRate * 1e18 / totalStaked
        );
    }

    /// @notice Returns the total earned (but unclaimed) NGTT for an account.
    /// @param account The user address.
    /// @return Total earned NGTT (in 18-decimal units).
    function earned(address account) public view returns (uint256) {
        UserInfo storage user = userInfo[account];
        return (user.amount * (rewardPerToken() - user.rewardPerTokenPaid)) / 1e18 + user.pendingRewards;
    }

    /// @notice Deposits LP tokens into the staking contract.
    /// @param amount Number of LP tokens to stake (caller must approve first).
    function deposit(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0, "NexusLPStaking: zero amount");
        userInfo[msg.sender].amount += amount;
        totalStaked += amount;
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        emit Deposited(msg.sender, amount);
    }

    /// @notice Withdraws LP tokens from the staking contract.
    /// @param amount Number of LP tokens to withdraw.
    function withdraw(uint256 amount) external nonReentrant updateReward(msg.sender) {
        require(amount > 0, "NexusLPStaking: zero amount");
        require(userInfo[msg.sender].amount >= amount, "NexusLPStaking: insufficient balance");
        userInfo[msg.sender].amount -= amount;
        totalStaked -= amount;
        stakingToken.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Claims all accumulated NGTT rewards.
    function claimRewards() external nonReentrant updateReward(msg.sender) {
        uint256 reward = userInfo[msg.sender].pendingRewards;
        require(reward > 0, "NexusLPStaking: no rewards");
        userInfo[msg.sender].pendingRewards = 0;
        rewardToken.safeTransfer(msg.sender, reward);
        emit RewardClaimed(msg.sender, reward);
    }

    /// @notice Withdraws all LP tokens and claims all pending rewards in one call.
    function exitAll() external nonReentrant updateReward(msg.sender) {
        uint256 amount = userInfo[msg.sender].amount;
        uint256 reward = userInfo[msg.sender].pendingRewards;

        userInfo[msg.sender].amount = 0;
        userInfo[msg.sender].pendingRewards = 0;
        totalStaked -= amount;

        if (amount > 0) {
            stakingToken.safeTransfer(msg.sender, amount);
            emit Withdrawn(msg.sender, amount);
        }
        if (reward > 0) {
            rewardToken.safeTransfer(msg.sender, reward);
            emit RewardClaimed(msg.sender, reward);
        }
    }

    // -------------------------------------------------------------------------
    // Owner controls
    // -------------------------------------------------------------------------

    /// @notice Sets the NGTT reward distribution rate.
    /// @param _rewardRate New rate in NGTT per second (18 decimals).
    function setRewardRate(uint256 _rewardRate) external onlyOwner updateReward(address(0)) {
        uint256 old = rewardRate;
        rewardRate = _rewardRate;
        emit RewardRateUpdated(old, _rewardRate);
    }

    /// @notice Deposits NGTT reward tokens into this contract to fund future rewards.
    /// @param amount Amount of NGTT to deposit (owner must approve first).
    function refillRewardPool(uint256 amount) external onlyOwner {
        require(amount > 0, "NexusLPStaking: zero amount");
        rewardToken.safeTransferFrom(msg.sender, address(this), amount);
        emit RewardPoolRefilled(amount);
    }
}

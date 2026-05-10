// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title NexusFractionalize
/// @notice Wraps a single NexusRWA (ERC-721) token into transferable ERC-20
///         fractional shares.  Each share represents proportional beneficial
///         ownership of the underlying real-world asset.
///
/// Flow:
///   1. The RWA NFT owner deploys this contract (or calls a factory).
///   2. They call fractionalize(), transferring the NFT to this contract
///      and receiving the full supply of ERC-20 shares.
///   3. Shares can be traded freely on any ERC-20-compatible exchange.
///   4. Any shareholder holding 100 % of shares can call redeem() to
///      receive the underlying NFT back.
///
/// NES: this contract is a Nexus-authored surface governed by the
/// Nexus Encryption Standard as documented in docs/NEXUS_ENCRYPTION_STANDARD.md.
contract NexusFractionalize is ERC20, Ownable, ReentrancyGuard {

    // -------------------------------------------------------------------------
    // Immutables
    // -------------------------------------------------------------------------

    /// @notice The NFT contract address.
    IERC721 public immutable nftContract;

    /// @notice The NFT token ID held in this vault.
    uint256 public immutable nftTokenId;

    // -------------------------------------------------------------------------
    // State
    // -------------------------------------------------------------------------

    /// @notice Whether the NFT has been deposited and shares have been issued.
    bool public fractionalised;

    /// @notice Whether the vault has been redeemed (NFT returned to last holder).
    bool public redeemed;

    // -------------------------------------------------------------------------
    // Events
    // -------------------------------------------------------------------------

    /// @notice Emitted when the NFT is deposited and shares are issued.
    event Fractionalised(address indexed owner, uint256 shares);

    /// @notice Emitted when all shares are burned and the NFT is returned.
    event Redeemed(address indexed redeemer);

    // -------------------------------------------------------------------------
    // Constructor
    // -------------------------------------------------------------------------

    /// @notice Creates a fractionalization vault for a specific NFT.
    /// @param _nftContract    Address of the NexusRWA contract.
    /// @param _nftTokenId     Token ID to fractionalize.
    /// @param _shareName      ERC-20 name for the fractional shares.
    /// @param _shareSymbol    ERC-20 symbol for the fractional shares.
    /// @param _totalShares    Total supply of fractional shares to mint (18 decimals).
    constructor(
        address _nftContract,
        uint256 _nftTokenId,
        string memory _shareName,
        string memory _shareSymbol,
        uint256 _totalShares
    ) ERC20(_shareName, _shareSymbol) {
        require(_nftContract != address(0), "NexusFractionalize: zero NFT contract");
        require(_totalShares > 0, "NexusFractionalize: zero total shares");
        nftContract = IERC721(_nftContract);
        nftTokenId = _nftTokenId;
        // Mint total supply to deployer; deployer then deposits the NFT.
        _mint(msg.sender, _totalShares);
    }

    // -------------------------------------------------------------------------
    // Core functions
    // -------------------------------------------------------------------------

    /// @notice Deposits the NFT into this vault and activates fractional shares.
    ///         Caller must own the NFT and have approved this contract.
    function fractionalize() external nonReentrant {
        require(!fractionalised, "NexusFractionalize: already fractionalised");
        require(!redeemed, "NexusFractionalize: vault redeemed");
        require(
            nftContract.ownerOf(nftTokenId) == msg.sender,
            "NexusFractionalize: caller does not own NFT"
        );

        fractionalised = true;
        nftContract.transferFrom(msg.sender, address(this), nftTokenId);

        emit Fractionalised(msg.sender, totalSupply());
    }

    /// @notice Burns all outstanding shares and returns the underlying NFT.
    ///         Caller must hold 100 % of the total share supply.
    function redeem() external nonReentrant {
        require(fractionalised, "NexusFractionalize: not yet fractionalised");
        require(!redeemed, "NexusFractionalize: already redeemed");
        require(
            balanceOf(msg.sender) == totalSupply(),
            "NexusFractionalize: must hold 100% of shares"
        );

        redeemed = true;
        _burn(msg.sender, totalSupply());
        nftContract.transferFrom(address(this), msg.sender, nftTokenId);

        emit Redeemed(msg.sender);
    }

    // -------------------------------------------------------------------------
    // View helpers
    // -------------------------------------------------------------------------

    /// @notice Returns the address that currently holds the NFT in custody.
    /// @return custodian This contract's address if fractionalised, address(0) if redeemed.
    function custodian() external view returns (address) {
        if (fractionalised && !redeemed) {
            return address(this);
        }
        return address(0);
    }

    /// @notice Returns the ownership percentage held by an account in basis points.
    /// @param account The address to query.
    /// @return bps Ownership percentage in basis points (10 000 = 100 %).
    function ownershipBps(address account) external view returns (uint256 bps) {
        uint256 supply = totalSupply();
        if (supply == 0) return 0;
        return (balanceOf(account) * 10_000) / supply;
    }
}

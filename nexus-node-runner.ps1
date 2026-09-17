#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Nexus Protocol — GPU-enabled local node + full service launcher.

.DESCRIPTION
    Starts ALL Nexus backend services on the local RTX 5060 Ti machine:
      1. nexus-signal-bus    (WebSocket event relay,      :8790)
      2. financial-ops-rest  (Financial REST API,         :8788)
      3. expert-registry     (Expert registry API,        :8789)
      4. nexus-signal-relay  (MCP → signal-bus bridge,    :8792)
      5. nexus-p2p-node      (P2P mesh node,              :9000/:9001 REST:8791)
      6. hardhat node        (GPU devnet,                 :8546)
      7. nexus-dao-mcp       (Bob MCP server,             stdio)

    GPU environment variables are set for CUDA sm_120 (RTX 5060 Ti / WDDM).
    All services write logs to .nexus-logs/<service>.log.

.PARAMETER RpcUrl
    Ethereum WebSocket RPC URL for the signal bus (e.g. wss://mainnet.infura.io/...)

.PARAMETER GovernorAddress
    Deployed NexusGovernor contract address.

.PARAMETER TreasuryAddress
    Deployed NexusTreasury contract address.

.PARAMETER TokenAddress
    Deployed NexusToken (NGTT) contract address.

.PARAMETER SkipHardhat
    Skip starting the local Hardhat devnet node.

.EXAMPLE
    .\nexus-node-runner.ps1 -RpcUrl "wss://mainnet.infura.io/ws/v3/YOUR_KEY" `
        -GovernorAddress "0x..." -TreasuryAddress "0x..." -TokenAddress "0x..."
#>
param(
    [string] $RpcUrl          = $env:NEXUS_RPC_URL,
    [string] $GovernorAddress = $env:NEXUS_GOVERNOR_ADDRESS,
    [string] $TreasuryAddress = $env:NEXUS_TREASURY_ADDRESS,
    [string] $TokenAddress    = $env:NEXUS_TOKEN_ADDRESS,
    [switch] $SkipHardhat
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$RepoRoot  = $PSScriptRoot
$LogDir    = Join-Path $RepoRoot ".nexus-logs"
$McpBuild  = "C:\Users\Administrator\source\repos\FuzzysTodd\nexus-dao-mcp\build\index.js"
$NodeExe   = "node"
$HardhatBin = Join-Path $RepoRoot "node_modules\.bin\hardhat.cmd"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# ---------------------------------------------------------------------------
# GPU / CUDA environment (RTX 5060 Ti, sm_120, CUDA 13.3, WDDM)
# ---------------------------------------------------------------------------
$env:CUDA_VISIBLE_DEVICES          = "0"
$env:CUDA_DEVICE_ORDER             = "PCI_BUS_ID"
$env:TF_FORCE_GPU_ALLOW_GROWTH     = "true"
$env:PYTORCH_CUDA_ALLOC_CONF       = "max_split_size_mb:512"
$env:NEXUS_GPU_DEVICE              = "RTX_5060_Ti"
$env:NEXUS_GPU_VRAM_MB             = "8192"
$env:NEXUS_GPU_COMPUTE_CAP         = "sm_120"
$env:NEXUS_GPU_DRIVER              = "610.88"
$env:NEXUS_GPU_CUDA_VERSION        = "13.3"

# ---------------------------------------------------------------------------
# Nexus service environment
# ---------------------------------------------------------------------------
$env:NEXUS_RPC_URL                 = $RpcUrl
$env:NEXUS_GOVERNOR_ADDRESS        = $GovernorAddress
$env:NEXUS_TREASURY_ADDRESS        = $TreasuryAddress
$env:NEXUS_TOKEN_ADDRESS           = $TokenAddress
$env:NEXUS_SIGNAL_BUS_PORT         = "8790"
$env:NEXUS_RELAY_PORT              = "8792"
$env:NEXUS_P2P_PORT                = "9000"
$env:NEXUS_P2P_WS_PORT             = "9001"
$env:NEXUS_P2P_API_PORT            = "8791"
$env:NEXUS_SIGNAL_BUS_URL          = "ws://localhost:8790"
$env:NEXUS_DEVNET_RPC              = "http://127.0.0.1:8546"

# ---------------------------------------------------------------------------
# Helper: start a background Node.js process and return its job
# ---------------------------------------------------------------------------
function Start-NexusService {
    param(
        [string] $Name,
        [string] $Script,
        [string] $Args = "",
        [string] $Cwd  = $RepoRoot
    )
    $logFile = Join-Path $LogDir "$Name.log"
    Write-Host "  ▶ $Name" -ForegroundColor Cyan
    $cmd = if ($Args) { "$NodeExe $Script $Args" } else { "$NodeExe $Script" }
    $job = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c $cmd >> `"$logFile`" 2>&1" `
        -WorkingDirectory $Cwd `
        -PassThru `
        -WindowStyle Hidden
    Start-Sleep -Milliseconds 800
    return $job
}

# ---------------------------------------------------------------------------
# Start services
# ---------------------------------------------------------------------------
$jobs = @()

Write-Host "`n╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   NEXUS PROTOCOL — NODE RUNNER               ║" -ForegroundColor Green
Write-Host "║   GPU: RTX 5060 Ti  │  CUDA sm_120  │ 8 GiB  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝`n" -ForegroundColor Green

# 1. Signal Bus
$busScript = Join-Path $RepoRoot "nexus-signal-bus.js"
if (-not (Test-Path $busScript)) {
    $busScript = "C:\Users\Administrator\source\repos\FuzzysTodd\The-Nexus-Protocol-Token-DAO\nexus-signal-bus.js"
}
if (Test-Path $busScript) {
    $jobs += Start-NexusService -Name "nexus-signal-bus"   -Script $busScript
}

# 2. Signal Relay (MCP → signal-bus bridge)
$relayScript = Join-Path $RepoRoot "nexus-signal-relay.js"
if (Test-Path $relayScript) {
    $jobs += Start-NexusService -Name "nexus-signal-relay" -Script $relayScript
}

# 3. P2P Node
$p2pScript = Join-Path $RepoRoot "nexus-p2p-node.js"
if (Test-Path $p2pScript) {
    $jobs += Start-NexusService -Name "nexus-p2p-node"     -Script $p2pScript
}

# 4. Financial-ops REST server
$finOpsScript = "C:\Users\Administrator\source\repos\FuzzysTodd\NEXER-PROTEGE-DAO\mcp\financial-ops-server.js"
if (Test-Path $finOpsScript) {
    $jobs += Start-NexusService -Name "financial-ops-rest" -Script $finOpsScript
}

# 5. Expert registry server
$expertScript = "C:\Users\Administrator\source\repos\FuzzysTodd\NEXER-PROTEGE-DAO\mcp\expert-registry-server.js"
if (Test-Path $expertScript) {
    $jobs += Start-NexusService -Name "expert-registry"    -Script $expertScript
}

# 6. Hardhat GPU devnet (optional)
if (-not $SkipHardhat) {
    if (Test-Path $HardhatBin) {
        $hhLog = Join-Path $LogDir "hardhat-devnet.log"
        Write-Host "  ▶ hardhat-devnet (GPU :8546)" -ForegroundColor Cyan
        $jobs += Start-Process -FilePath "cmd.exe" `
            -ArgumentList "/c `"$HardhatBin`" node --port 8546 >> `"$hhLog`" 2>&1" `
            -WorkingDirectory $RepoRoot `
            -PassThru -WindowStyle Hidden
        Start-Sleep -Milliseconds 1200
    } else {
        Write-Host "  ⚠ hardhat not found — run: npm install (skipping devnet)" -ForegroundColor Yellow
    }
}

# 7. MCP server (stdio — launched by Bob, shown here for reference)
if (Test-Path $McpBuild) {
    Write-Host "  ℹ nexus-dao-mcp is started by Bob via stdio (see .bob/mcp.json)" -ForegroundColor DarkCyan
}

# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  SERVICE              PORT      LOG                ║" -ForegroundColor Green
Write-Host "╠════════════════════════════════════════════════════╣" -ForegroundColor Green
$services = @(
    @("nexus-signal-bus",   "8790 (WS)",  "nexus-signal-bus.log"),
    @("nexus-signal-relay", "8792 (REST)", "nexus-signal-relay.log"),
    @("nexus-p2p-node",     "9000/9001/8791", "nexus-p2p-node.log"),
    @("financial-ops-rest", "8788 (REST)", "financial-ops-rest.log"),
    @("expert-registry",    "8789 (REST)", "expert-registry.log"),
    @("hardhat-devnet",     "8546 (RPC)",  "hardhat-devnet.log"),
    @("nexus-dao-mcp",      "stdio",       "(Bob MCP)")
)
foreach ($s in $services) {
    Write-Host ("║  {0,-22}{1,-12}{2,-20}║" -f $s[0], $s[1], $s[2]) -ForegroundColor White
}
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Logs: $LogDir" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop all services.`n" -ForegroundColor DarkGray

# Keep alive — wait for interrupt
try {
    while ($true) { Start-Sleep -Seconds 10 }
} finally {
    Write-Host "`n[runner] Stopping all services…" -ForegroundColor Yellow
    foreach ($job in $jobs) {
        try { Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    Write-Host "[runner] Done." -ForegroundColor Green
}

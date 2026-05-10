# MCP Gateway Quick Reference Guide

## Quick Start

### Run MCP Gateway Orchestrator

**Manual Trigger**:
1. Go to Actions tab in GitHub
2. Select "MCP/MFC Gateway - FPGA GPU Swarm Hive Orchestrator"
3. Click "Run workflow"
4. Select mode: `full`, `mcp-only`, `gpu-only`, or `hive-only`
5. Click "Run workflow" button

**Automatic Trigger**:
- Runs every 15 minutes automatically
- Triggers after other workflow completions
- Triggers on push to main/copilot/agent branches

### Check Workflow Status

```bash
# View workflow runs
gh run list --workflow=mcp-gateway-orchestrator.yml

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

## MCP Agents Quick Reference

| ID | Role | Use Case |
|---|---|---|
| mcp-001 | Game Theory Coordinator | Game session management |
| mcp-002 | Token Economics Manager | Token distribution & Bitcoin backing |
| mcp-003 | DAO Governance Agent | Proposal processing & voting |
| mcp-004 | AI Data Pipeline Manager | ML model training & optimization |
| mcp-005 | GPU Rendering Engine | Graphics rendering & VR/AR |
| mcp-006 | VPN Node Manager | VPN security & routing |
| mcp-007 | NFT Minting & Trading | NFT marketplace operations |
| mcp-008 | Marketing & Promotion | Social media & partnerships |
| mcp-009 | Cloud-Local Sync Manager | Data backup & recovery |
| mcp-010 | Financial Analytics | Revenue tracking & optimization |

## Common Commands

### Testing

```bash
# Run all tests
pytest -q

# Run MCP Gateway tests only
pytest nexus/test_mcp_gateway_orchestration.py -v

# Run with coverage
pytest --cov=nexus --cov-report=html

# Run specific test class
pytest nexus/test_mcp_gateway_orchestration.py::TestMCPGatewayConfiguration -v
```

### Validation

```bash
# Lint code
flake8 .

# Check workflow syntax
actionlint .github/workflows/*.yml

# Validate MCP configuration
python -c "import json; json.load(open('mcp/agents/mig-network-config.json'))"
```

## Workflow Artifacts

### Generated Artifacts

1. **mcp-gateway-status** - MCP Gateway initialization status
2. **gpu-fpga-status** - GPU and FPGA gateway status
3. **hive-mind-status** - Hive Mind coordination status
4. **mcp-orchestration-report** - Agent task orchestration report
5. **integration-validation-report** - Integration validation results
6. **workflow-completion-summary** - Comprehensive summary (retained 365 days)

### Artifact Locations

```
.mcp/
├── status/gateway.json          # MCP Gateway status
├── gpu/status.json              # GPU status
├── fpga/gateway.json            # FPGA gateway status
├── hive/coordination.json       # Hive Mind coordination
├── agents/orchestration_report.json  # Orchestration report
└── validation/integration_report.json  # Validation report
```

## Status Indicators

### Component Status

| Symbol | Meaning |
|---|---|
| ✅ | Operational / Passed |
| 🔄 | In Progress |
| ⏳ | Pending |
| ❌ | Failed |
| ⚠️ | Warning |

### Health Metrics

- **100%** - All systems operational
- **99.99%** - MPC server uptime target
- **85%** - GPU utilization target
- **<1ms** - FPGA gateway latency target
- **<50ms** - AI inference latency target

## Troubleshooting

### Workflow Failed

1. **Check logs**: View workflow run logs in GitHub Actions
2. **Review artifacts**: Download and inspect artifact JSON files
3. **Validate config**: Ensure `mcp/agents/mig-network-config.json` is valid
4. **Re-run**: Click "Re-run all jobs" in GitHub Actions

### Agent Not Responding

```bash
# Check agent configuration
cat mcp/agents/mig-network-config.json | jq '.migNetwork.mcpAgents[] | select(.id=="mcp-001")'

# Verify agent tasks
cat mcp/agents/mig-network-config.json | jq '.migNetwork.mcpAgents[] | {id, role, tasks}'
```

### GPU Issues

```bash
# Check GPU specs
cat mcp/agents/mig-network-config.json | jq '.migNetwork.gpuSpecs'

# Review telemetry (if available locally)
python -c "from nexus import telemetry_monitor; telemetry_monitor.run_monitoring()"
```

## Integration Checklist

- [ ] MCP Gateway initialized (10 agents)
- [ ] MPC Servers online (2 servers at 99.99% uptime)
- [ ] GPU Swarm operational (RTX 4060)
- [ ] FPGA Gateway active (<1ms latency)
- [ ] Hive Mind consensus achieved
- [ ] All 254 tests passing
- [ ] Validation reports show 100% accuracy

## Contact & Support

- **Authority**: FuzzysTodd
- **Email**: fuzzystodd@gmail.com
- **Documentation**: `MCP_GATEWAY_DOCUMENTATION.md`
- **Tests**: `nexus/test_mcp_gateway_orchestration.py`
- **Configuration**: `mcp/agents/mig-network-config.json`

## Additional Resources

- **Main Workflow**: `.github/workflows/main.yml`
- **Progress Report**: `.github/workflows/progress-report-email.yml`
- **MCP Orchestrator**: `.github/workflows/mcp-gateway-orchestrator.yml`
- **GPU Telemetry**: `nexus/telemetry_monitor.py`
- **Anomaly Detection**: `nexus/anomaly_detector.py`

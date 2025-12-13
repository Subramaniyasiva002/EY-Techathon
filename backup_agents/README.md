# Backup Agents Directory

This directory contains backup versions of all agents for the intelligent failover system.

## Files

- `diagnosis_agent_backup.py` - Backup diagnosis agent with safe mode
- `scheduling_agent_backup.py` - Backup scheduling agent
- `feedback_agent_backup.py` - Backup feedback agent
- `rca_capa_agent_backup.py` - Backup RCA/CAPA agent

## Usage

These backup agents are automatically started by the `agent_supervisor.py` when:
1. Primary agent fails to restart after 3 attempts
2. Primary agent dies with suspicious activity (started in SAFE MODE)

## Safe Mode

Backup agents can run in SAFE MODE (read-only) by passing `--safe-mode` flag:

```bash
python backup_agents/diagnosis_agent_backup.py --safe-mode
```

In safe mode:
- No database writes
- Read-only operations
- Limited permissions
- Predictions only (for DiagnosisAgent)

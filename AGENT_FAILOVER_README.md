# Intelligent Agent Failover System

## Overview
This system provides **intelligent agent failover** with **UEBA-based security**. It automatically replaces dead agents with backups, but only if the failure is accidental (not suspicious/malicious).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Agent Supervisor                            │
│  (Monitors all agents, classifies failures)             │
└────────────┬────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────┬────────────┐
    │                 │            │            │
┌───▼───┐      ┌─────▼────┐  ┌───▼────┐  ┌───▼────┐
│Diagno-│      │Schedul-  │  │Feed-   │  │RCA/    │
│sis    │      │ing       │  │back    │  │CAPA    │
│Agent  │      │Agent     │  │Agent   │  │Agent   │
└───┬───┘      └─────┬────┘  └───┬────┘  └───┬────┘
    │                │            │            │
    └────────┬───────┴────────────┴────────────┘
             │
      ┌──────▼──────┐
      │  UEBA       │
      │  Security   │
      └─────────────┘
```

## Features

### 1. **Failure Classification**
- **Accidental**: Crashes, OOM, network issues → Auto-restart
- **Suspicious**: UEBA violations, unauthorized actions → Quarantine
- **Manual**: User-initiated shutdown → No action

### 2. **Auto-Recovery**
- Restart primary agent (up to 3 attempts)
- Failover to backup agent if restart fails
- Safe mode for critical agents with suspicious failures

### 3. **Security Integration**
- Uses UEBA to detect malicious behavior
- Quarantines agents with security violations
- Logs all security incidents
- Prevents auto-restart of compromised agents

### 4. **Backup Agents**
- Each agent has a backup version
- Backups can run in **SAFE MODE** (read-only)
- Automatic failover when primary fails

## Files Created

1. **agent_supervisor.py** - Main supervisor with failover logic
2. **backup_agents/diagnosis_agent_backup.py** - Backup diagnosis agent
3. **backup_agents/scheduling_agent_backup.py** - Backup scheduling agent
4. **backup_agents/feedback_agent_backup.py** - Backup feedback agent
5. **backup_agents/rca_capa_agent_backup.py** - Backup RCA/CAPA agent
6. **supervisor_daemon.py** - Run supervisor as background service
7. **test_agent_failover.py** - Test failover system
8. **backup_agents/README.md** - Backup agents documentation

## Usage

### Start Supervisor
```bash
python supervisor_daemon.py
```

This will:
1. Start all agents under supervision
2. Monitor their health every 10 seconds
3. Auto-recover on failures
4. Log security incidents

### Test Failover
```bash
python test_agent_failover.py
```

This will:
1. Start agents normally
2. Simulate accidental failure (auto-restart)
3. Simulate suspicious failure (quarantine)
4. Verify failover behavior

## Failure Scenarios

### Scenario 1: Accidental Failure
```
Agent crashes → Supervisor detects → Classifies as ACCIDENTAL
→ Restart primary (attempt 1/3) → Success ✓
```

### Scenario 2: Repeated Failures
```
Agent crashes → Restart fails 3 times
→ Failover to backup agent → Backup starts ✓
```

### Scenario 3: Suspicious Failure
```
Agent has UEBA violations → Agent dies
→ Classified as SUSPICIOUS → QUARANTINE
→ Start backup in SAFE MODE (read-only) ✓
→ Alert sent to admin
```

## Configuration

Edit `agent_supervisor.py` to configure:

```python
self.max_restart_attempts = 3  # Max restart attempts
self.agent_configs = {
    "DiagnosisAgent": {
        "primary_cmd": "python diagnosis_agent.py",
        "backup_cmd": "python backup_agents/diagnosis_agent_backup.py",
        "critical": True  # Start backup in safe mode if suspicious
    }
}
```

## Security Incidents

All security incidents are logged to `security_incidents.json`:

```json
{
  "timestamp": "2025-12-13T06:18:34",
  "agent": "DiagnosisAgent",
  "pid": 12345,
  "uptime": 45.2,
  "reason": "suspicious_failure",
  "action": "quarantined"
}
```

## Monitoring

Check supervisor status:
```python
from agent_supervisor import AgentSupervisor
supervisor = AgentSupervisor()
status = supervisor.get_status()
print(status)
```

Output:
```json
{
  "agents": {
    "DiagnosisAgent": {
      "status": "running",
      "pid": 12345,
      "uptime": 120.5,
      "restart_count": 1,
      "using_backup": false
    }
  },
  "quarantined": [],
  "timestamp": "2025-12-13T06:18:34"
}
```

## Integration with Dashboard

The supervisor status can be displayed in the dashboard to show:
- Agent health status
- Backup usage
- Quarantined agents
- Security incidents

## Best Practices

1. **Monitor Logs**: Check `security_incidents.json` regularly
2. **Review Quarantines**: Investigate quarantined agents before restarting
3. **Test Failover**: Run `test_agent_failover.py` after changes
4. **Backup Models**: Ensure backup agents have valid models
5. **Alert Integration**: Add email/Slack alerts for critical failures

## Troubleshooting

**Agent won't restart?**
- Check if quarantined: `supervisor.quarantine_list`
- Check UEBA logs: `ueba_log.json`
- Review security incidents: `security_incidents.json`

**Backup agent not starting?**
- Verify backup script exists
- Check command in `agent_configs`
- Ensure dependencies are installed

**Too many restarts?**
- Increase `max_restart_attempts`
- Check agent logs for root cause
- Fix underlying issue before restarting

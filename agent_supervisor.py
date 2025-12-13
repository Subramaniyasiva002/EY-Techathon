# agent_supervisor.py - Intelligent Agent Failover with UEBA Security
import time
import subprocess
import psutil
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from ueba_agent import UEBAAgent

class FailureReason(Enum):
    ACCIDENTAL = "accidental"      # Crash, OOM, network issue
    SUSPICIOUS = "suspicious"      # UEBA violation, unauthorized action
    MANUAL = "manual"              # User-initiated shutdown

class AgentStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    QUARANTINED = "quarantined"    # Blocked due to suspicious activity

class AgentSupervisor:
    """Supervises agent lifecycle with intelligent failover"""
    
    def __init__(self):
        self.agents = {}
        self.backup_agents = {}
        self.ueba = UEBAAgent()
        self.max_restart_attempts = 3
        self.quarantine_list = set()
        
        # Define agent configurations
        self.agent_configs = {
            "DiagnosisAgent": {
                "primary_cmd": "python diagnosis_agent.py",
                "backup_cmd": "python backup_agents/diagnosis_agent_backup.py",
                "port": 8001,
                "critical": True
            },
            "SchedulingAgent": {
                "primary_cmd": "python scheduling_agent.py",
                "backup_cmd": "python backup_agents/scheduling_agent_backup.py",
                "port": 8002,
                "critical": True
            },
            "FeedbackAgent": {
                "primary_cmd": "python feedback_agent.py",
                "backup_cmd": "python backup_agents/feedback_agent_backup.py",
                "port": 8003,
                "critical": False
            },
            "RCACAPAAgent": {
                "primary_cmd": "python rca_capa_agent.py",
                "backup_cmd": "python backup_agents/rca_capa_agent_backup.py",
                "port": 8004,
                "critical": False
            }
        }
        
        print("[AgentSupervisor] Initialized with intelligent failover")
    
    def start_agent(self, agent_name):
        """Start an agent"""
        if agent_name in self.quarantine_list:
            print(f"[SECURITY] {agent_name} is QUARANTINED. Cannot start.")
            return False
        
        config = self.agent_configs.get(agent_name)
        if not config:
            print(f"[ERROR] Unknown agent: {agent_name}")
            return False
        
        try:
            process = subprocess.Popen(config["primary_cmd"].split())
            self.agents[agent_name] = {
                "process": process,
                "pid": process.pid,
                "status": AgentStatus.RUNNING,
                "start_time": time.time(),
                "restart_count": 0,
                "using_backup": False
            }
            print(f"[AgentSupervisor] Started {agent_name} (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start {agent_name}: {e}")
            return False
    
    def monitor_and_recover(self):
        """Main monitoring loop with intelligent failover"""
        print("[AgentSupervisor] Starting monitoring loop...")
        
        while True:
            for agent_name, agent_info in list(self.agents.items()):
                if not self._is_agent_alive(agent_info):
                    print(f"\n[ALERT] {agent_name} is DEAD!")
                    self._handle_agent_failure(agent_name, agent_info)
            
            time.sleep(10)  # Check every 10 seconds
    
    def _is_agent_alive(self, agent_info):
        """Check if agent process is alive"""
        try:
            process = psutil.Process(agent_info["pid"])
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _handle_agent_failure(self, agent_name, agent_info):
        """Intelligent failure handling with UEBA analysis"""
        
        # Step 1: Classify failure reason
        failure_reason = self._classify_failure(agent_name, agent_info)
        
        print(f"[Analysis] Failure reason: {failure_reason.value}")
        
        # Step 2: Take action based on failure reason
        if failure_reason == FailureReason.SUSPICIOUS:
            self._handle_suspicious_failure(agent_name, agent_info)
        elif failure_reason == FailureReason.ACCIDENTAL:
            self._handle_accidental_failure(agent_name, agent_info)
        else:
            print(f"[INFO] {agent_name} stopped manually. No action taken.")
    
    def _classify_failure(self, agent_name, agent_info):
        """Classify failure as accidental or suspicious using UEBA"""
        
        # Check UEBA logs for suspicious activity
        ueba_report = self.ueba.get_security_report()
        
        # Check if agent had recent security violations
        recent_violations = [
            attempt for attempt in ueba_report.get("blocked_details", [])
            if attempt.get("agent") == agent_name
            and self._is_recent(attempt.get("timestamp"))
        ]
        
        if recent_violations:
            print(f"[SECURITY] {agent_name} had {len(recent_violations)} security violations before death")
            return FailureReason.SUSPICIOUS
        
        # Check for abnormal behavior patterns
        if self._check_abnormal_behavior(agent_name):
            return FailureReason.SUSPICIOUS
        
        # Check for resource exhaustion (accidental)
        if self._check_resource_exhaustion(agent_info):
            print(f"[INFO] {agent_name} died due to resource exhaustion (OOM/CPU)")
            return FailureReason.ACCIDENTAL
        
        # Default to accidental
        return FailureReason.ACCIDENTAL
    
    def _is_recent(self, timestamp_str, threshold_minutes=5):
        """Check if timestamp is recent"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return datetime.utcnow() - timestamp < timedelta(minutes=threshold_minutes)
        except:
            return False
    
    def _check_abnormal_behavior(self, agent_name):
        """Check for abnormal behavior patterns"""
        ueba_report = self.ueba.get_security_report()
        
        # If total events > 1000 in last check, suspicious
        if ueba_report.get("total_events", 0) > 1000:
            print(f"[SECURITY] {agent_name} showed abnormal activity (high request rate)")
            return True
        
        return False
    
    def _check_resource_exhaustion(self, agent_info):
        """Check if agent died due to resource exhaustion"""
        uptime = time.time() - agent_info["start_time"]
        
        # If died within 30 seconds, likely a crash (accidental)
        if uptime < 30:
            return True
        
        return False
    
    def _handle_suspicious_failure(self, agent_name, agent_info):
        """Handle suspicious failure - QUARANTINE and ALERT"""
        print("\n" + "!" * 70)
        print(f"[SECURITY ALERT] {agent_name} QUARANTINED!")
        print("!" * 70)
        print(f"Reason: Suspicious activity detected before failure")
        print(f"Action: Agent will NOT be restarted automatically")
        print(f"Manual intervention required!")
        print("!" * 70 + "\n")
        
        # Quarantine the agent
        self.quarantine_list.add(agent_name)
        agent_info["status"] = AgentStatus.QUARANTINED
        
        # Log to security incident file
        self._log_security_incident(agent_name, agent_info)
        
        # If critical agent, start backup in SAFE MODE
        if self.agent_configs[agent_name].get("critical"):
            print(f"[SECURITY] Starting backup {agent_name} in SAFE MODE")
            self._start_backup_agent_safe_mode(agent_name)
    
    def _handle_accidental_failure(self, agent_name, agent_info):
        """Handle accidental failure - AUTO-RESTART or FAILOVER"""
        restart_count = agent_info["restart_count"]
        
        if restart_count < self.max_restart_attempts:
            # Try restarting primary agent
            print(f"[RECOVERY] Attempting to restart {agent_name} (attempt {restart_count + 1}/{self.max_restart_attempts})")
            
            if self._restart_primary_agent(agent_name, agent_info):
                print(f"[SUCCESS] {agent_name} restarted successfully")
                agent_info["restart_count"] += 1
            else:
                print(f"[FAILED] Could not restart {agent_name}")
                self._failover_to_backup(agent_name, agent_info)
        else:
            # Max restarts exceeded, failover to backup
            print(f"[RECOVERY] Max restart attempts exceeded for {agent_name}")
            self._failover_to_backup(agent_name, agent_info)
    
    def _restart_primary_agent(self, agent_name, agent_info):
        """Restart the primary agent"""
        try:
            config = self.agent_configs[agent_name]
            process = subprocess.Popen(config["primary_cmd"].split())
            
            agent_info["process"] = process
            agent_info["pid"] = process.pid
            agent_info["status"] = AgentStatus.RUNNING
            agent_info["start_time"] = time.time()
            
            # Wait a bit and verify it started
            time.sleep(5)
            return self._is_agent_alive(agent_info)
        except Exception as e:
            print(f"[ERROR] Restart failed: {e}")
            return False
    
    def _failover_to_backup(self, agent_name, agent_info):
        """Failover to backup agent"""
        print(f"\n{'='*70}")
        print(f"[FAILOVER] Switching {agent_name} to BACKUP agent")
        print(f"{'='*70}\n")
        
        try:
            config = self.agent_configs[agent_name]
            backup_process = subprocess.Popen(config["backup_cmd"].split())
            
            self.backup_agents[agent_name] = {
                "process": backup_process,
                "pid": backup_process.pid,
                "status": AgentStatus.RUNNING,
                "start_time": time.time()
            }
            
            agent_info["using_backup"] = True
            agent_info["status"] = AgentStatus.STOPPED
            
            print(f"[SUCCESS] Backup {agent_name} started (PID: {backup_process.pid})")
            
            # Send notification
            self._send_failover_notification(agent_name)
            
        except Exception as e:
            print(f"[CRITICAL] Backup failover failed for {agent_name}: {e}")
            self._send_critical_alert(agent_name)
    
    def _start_backup_agent_safe_mode(self, agent_name):
        """Start backup agent in read-only/safe mode"""
        print(f"[SAFE MODE] Starting {agent_name} backup with restricted permissions")
        try:
            config = self.agent_configs[agent_name]
            backup_process = subprocess.Popen(config["backup_cmd"].split() + ["--safe-mode"])
            
            self.backup_agents[agent_name] = {
                "process": backup_process,
                "pid": backup_process.pid,
                "status": AgentStatus.RUNNING,
                "start_time": time.time(),
                "safe_mode": True
            }
            print(f"[SAFE MODE] Backup {agent_name} started in restricted mode")
        except Exception as e:
            print(f"[ERROR] Failed to start backup in safe mode: {e}")
    
    def _log_security_incident(self, agent_name, agent_info):
        """Log security incident to file"""
        incident = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "pid": agent_info["pid"],
            "uptime": time.time() - agent_info["start_time"],
            "reason": "suspicious_failure",
            "action": "quarantined"
        }
        
        incidents = []
        if os.path.exists("security_incidents.json"):
            with open("security_incidents.json", "r") as f:
                incidents = json.load(f)
        
        incidents.append(incident)
        
        with open("security_incidents.json", "w") as f:
            json.dump(incidents, f, indent=4)
    
    def _send_failover_notification(self, agent_name):
        """Send failover notification"""
        print(f"[NOTIFICATION] Failover completed for {agent_name}")
    
    def _send_critical_alert(self, agent_name):
        """Send critical alert"""
        print(f"[CRITICAL ALERT] Both primary and backup failed for {agent_name}")
    
    def get_status(self):
        """Get supervisor status"""
        return {
            "agents": {
                name: {
                    "status": info["status"].value if isinstance(info["status"], AgentStatus) else info["status"],
                    "pid": info["pid"],
                    "uptime": time.time() - info["start_time"],
                    "restart_count": info["restart_count"],
                    "using_backup": info["using_backup"]
                }
                for name, info in self.agents.items()
            },
            "quarantined": list(self.quarantine_list),
            "timestamp": datetime.utcnow().isoformat()
        }

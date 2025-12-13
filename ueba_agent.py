# ueba_agent.py - Whitelist-Based Security for Agentic Workflows
import time
import json
import os
from datetime import datetime

class UEBAAgent:
    def __init__(self, log_path="ueba_log.json"):
        self.log_path = log_path
        
        # WHITELIST: Exact allowed actions per agent
        self.allowed_actions = {
            "MasterAgent": [
                "call_scheduler",
                "call_customer",
                "call_booking",
                "call_feedback",
                "call_rca",
                "trigger_outer_loop"
            ],
            "SchedulingAgent": [
                "get_slots",
                "recommend_slot",
                "infer_demand"
            ],
            "CustomerInteractionAgent": [
                "generate_message",
                "send_notification"
            ],
            "BookingAgent": [
                "book",
                "get_slots",
                "complete_service"
            ],
            "FeedbackAgent": [
                "record_service",
                "record_rejection",
                "collect_feedback",
                "update_true_label",
                "mark_service_completed",
                "should_trigger_outer_loop"
            ],
            "RCACAPAAgent": [
                "generate_outer_loop_insight",
                "analyze"
            ],
            "DiagnosisAgent": [
                "predict",
                "diagnosis_complete"
            ],
            "DataAnalysisAgent": [
                "compute_features",
                "send_window"
            ]
        }
        
        # Event tracking for anomaly detection
        self.event_times = []
        self.blocked_attempts = []
        
        # Initialize log file
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                json.dump([], f)
        
        print("[UEBA] Whitelist-based security module initialized.")
        print(f"[UEBA] Monitoring {len(self.allowed_actions)} agent types")

    def log_event(self, agent, action):
        """
        Log and validate agent action against whitelist.
        Returns: dict with 'allowed' (bool) and optional 'alert' info
        """
        timestamp = time.time()
        self.event_times.append(timestamp)
        
        # Check whitelist
        is_allowed = action in self.allowed_actions.get(agent, [])
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action,
            "allowed": is_allowed
        }
        
        # Log to file
        try:
            with open(self.log_path, "r") as f:
                logs = json.load(f)
        except:
            logs = []
        
        logs.append(event)
        
        with open(self.log_path, "w") as f:
            json.dump(logs, f, indent=4)
        
        # Security Analysis
        if not is_allowed:
            return self._block_action(agent, action)
        
        # Check for rate anomalies (even for allowed actions)
        rate_check = self._check_rate_anomaly(agent, action)
        if rate_check["alert"]:
            return rate_check
        
        # Action allowed
        return {"allowed": True, "alert": False}
    
    def _block_action(self, agent, action):
        """Block unauthorized action and raise alert"""
        self.blocked_attempts.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action
        })
        
        alert_msg = f"{agent} attempted UNAUTHORIZED action: '{action}'"
        
        print("\n" + "!" * 70)
        print("[SECURITY ALERT] UEBA - UNAUTHORIZED ACTION BLOCKED")
        print("!" * 70)
        print(f"Agent: {agent}")
        print(f"Action: {action}")
        print(f"Status: BLOCKED")
        print(f"Allowed actions for {agent}:")
        for allowed in self.allowed_actions.get(agent, ["NONE"]):
            print(f"  - {allowed}")
        print("!" * 70)
        
        return {
            "allowed": False,
            "alert": True,
            "type": "UNAUTHORIZED_ACTION",
            "message": alert_msg,
            "severity": "CRITICAL"
        }
    
    def _check_rate_anomaly(self, agent, action):
        """Detect abnormal request frequency"""
        if len(self.event_times) > 10:
            # Check if 10 events happened in < 2 seconds
            if self.event_times[-1] - self.event_times[-10] < 2:
                print("\n" + "!" * 70)
                print("[WARNING] UEBA RATE ANOMALY DETECTED")
                print("!" * 70)
                print(f"Agent: {agent}")
                print(f"Action: {action}")
                print(f"Rate: 10 events in < 2 seconds")
                print("Status: SUSPICIOUS (allowed but flagged)")
                print("!" * 70)
                
                return {
                    "allowed": True,  # Don't block, just warn
                    "alert": True,
                    "type": "RATE_SPIKE",
                    "message": f"{agent} showing abnormal activity rate",
                    "severity": "WARNING"
                }
        
        return {"alert": False}
    
    def get_security_report(self):
        """Generate security summary"""
        try:
            with open(self.log_path, "r") as f:
                logs = json.load(f)
        except:
            logs = []
        
        total_events = len(logs)
        blocked_events = sum(1 for e in logs if not e.get("allowed", True))
        
        return {
            "total_events": total_events,
            "blocked_attempts": blocked_events,
            "blocked_details": self.blocked_attempts,
            "security_status": "SECURE" if blocked_events == 0 else "VIOLATIONS_DETECTED"
        }
    
    def check_agent_behavior(self, agent_name):
        """Check if agent behavior is suspicious"""
        try:
            with open(self.log_path, "r") as f:
                logs = json.load(f)
        except:
            return {"suspicious": False}
        
        # Get recent events for this agent
        recent_events = [
            e for e in logs[-100:]  # Last 100 events
            if e.get("agent") == agent_name
        ]
        
        if not recent_events:
            return {"suspicious": False}
        
        # Check for suspicious patterns
        blocked_actions = sum(1 for e in recent_events if not e.get("allowed", True))
        
        # If > 30% of actions were blocked, suspicious
        if len(recent_events) > 10 and blocked_actions / len(recent_events) > 0.3:
            return {
                "suspicious": True,
                "reason": f"High block rate: {blocked_actions}/{len(recent_events)}",
                "blocked_actions": blocked_actions
            }
        
        return {"suspicious": False}

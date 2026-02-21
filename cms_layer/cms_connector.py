import time
import requests
from config.settings import SystemConfig

class CMSConnector:
    def __init__(self, intersection_id, server_url=None):
        self.intersection_id = intersection_id
        # Use CMS_SERVER_URL from .env (points to Python FastAPI on port 8000)
        self.server_url = server_url or SystemConfig.CMS_SERVER_URL
        self.connected = False
        self.active_overrides = {}  # {lane_name: command_dict}

        print(f"[CMS] Initializing Edge Node: {self.intersection_id} -> {self.server_url}")

    def send_data(self, lane_status, decisions, green_times, directional_counts=None):
        """
        Push Heartbeat to CMS Server.

        Args:
            lane_status:        Dict of per-phase lane stats (D_i, Event, etc.)
            decisions:          Dict of current decisions (kept for API compat)
            green_times:        Dict of {phase: green_time_seconds}
            directional_counts: Optional Camera 5 directional counts dict
                                e.g. {"Straight": 5, "Left": 2, "Right": 1}
        """
        payload = {
            "junction_id": self.intersection_id,
            "timestamp": time.time(),
            "lanes": {}
        }

        lanes = list(lane_status.keys())
        for i, lane in enumerate(lanes):
            lane_data = lane_status.get(lane, {})
            saturation = lane_data.get("D_i", 0) * 100

            lane_payload = {
                "saturation_level": round(saturation, 1),
                "current_green_time": green_times.get(lane, 0),
                "event": lane_data.get("Event", "NORMAL"),
            }

            # Attach directional counts to the primary (first) phase only
            if i == 0 and directional_counts:
                lane_payload["directional_counts"] = directional_counts

            payload["lanes"][lane] = lane_payload

        try:
            response = requests.post(
                f"{self.server_url}/heartbeat",
                json=payload,
                timeout=2
            )
            print(f"[CMS HB] Status: {response.status_code}")

            if response.status_code == 200:
                self.connected = True
                resp_data = response.json()

                # FAIL-SAFE: Server says not throttled -> clear local memory
                if resp_data.get("server_says_throttled") is False:
                    if self.active_overrides:
                        print("[CMS SYNC] Server says clear. Removing stuck throttle.")
                        self.active_overrides = {}

                return True

        except requests.exceptions.RequestException as e:
            print(f"[CMS HB ERROR] {e}")
            self.connected = False
            return False

    def check_for_updates(self):
        """
        Poll for commands from server.
        Returns active_overrides: {lane_name: command_dict}

        Phase 7: Server returns a LIST of commands (multi-lane throttle).
        Handles both old-style single dict and new list format.
        """
        if not self.connected:
            return self.active_overrides

        try:
            response = requests.get(
                f"{self.server_url}/commands/{self.intersection_id}",
                timeout=2
            )

            if response.status_code == 200:
                data = response.json()

                # Handle list (Phase 7 multi-lane) or single dict (legacy)
                command_list = data if isinstance(data, list) else [data]

                for cmd in command_list:
                    cmd_type = cmd.get("command_type", "NO_OP")

                    if cmd_type == "THROTTLE_ADJUST":
                        target_lane = cmd.get("target_lane")
                        if target_lane:
                            self.active_overrides[target_lane] = cmd
                            val = cmd.get("value", "?")
                            reason = cmd.get("reason", "")
                            print(f"[CMS CMD] THROTTLE: {target_lane} by {val}s | {reason}")

                    elif cmd_type == "RESTORE_NORMAL":
                        target_lane = cmd.get("target_lane")
                        if target_lane and target_lane in self.active_overrides:
                            del self.active_overrides[target_lane]
                            print(f"[CMS CMD] RESTORE: {target_lane}")

        except requests.exceptions.RequestException:
            pass

        return self.active_overrides

    def get_active_override(self, lane):
        return self.active_overrides.get(lane, None)

    # ── CARLA Integration ────────────────────────────────────────
    def push_to_carla(self, decision_result, lane_combinations=None):
        """
        Forward the DecisionMaker result to the CARLA bridge server.
        Non-blocking: silently fails if bridge is not running.

        Args:
            decision_result: dict from DecisionMaker.decide_signals()
            lane_combinations: dict from lane_combinations.json (optional)
        """
        try:
            scores = decision_result.get("priority_scores", {})
            times = decision_result.get("allocated_times", {})
            state = decision_result.get("system_state", "SAFE")
            details = decision_result.get("details", {})

            if not scores:
                return

            winner = max(scores, key=scores.get)

            # Resolve allowed lanes from conflict matrix
            allowed = [f"{winner}_All"]
            if lane_combinations:
                phase_combos = lane_combinations.get(winner, {})
                allowed = phase_combos.get(state, [f"{winner}_All"])

            # Build saturation info from Grid_Raw values
            saturations = {}
            for phase, d in details.items():
                saturations[phase] = d.get("Grid_Raw", 1.0)

            payload = {
                "winner_phase": winner,
                "allowed_lanes": allowed,
                "allocated_times": times,
                "priority_scores": scores,
                "system_state": state,
                "phase_saturations": saturations,
            }

            carla_url = getattr(SystemConfig, 'CARLA_BRIDGE_URL', 'http://localhost:8100')
            requests.post(
                f"{carla_url}/carla/decision",
                json=payload,
                timeout=0.5
            )
        except Exception:
            pass  # CARLA bridge not running = non-critical
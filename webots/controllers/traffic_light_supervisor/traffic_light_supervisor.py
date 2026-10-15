"""
Cyberbotics Webots Controller: VAC V-BOT Traffic Light Supervisor.
Controls 3D traffic lights and physical sensor arrays (S1, S2, S3) using
Vehicle-Actuated Control & Dilemma Zone Protection.
"""
import sys
import math
from controller import Supervisor

# Traffic Light Phase Enums
PHASE_NS_GREEN = 0
PHASE_NS_YELLOW = 1
PHASE_EW_GREEN = 2
PHASE_EW_YELLOW = 3


class WebotsVacVBot:
    """
    VAC V-BOT Controller inside Cyberbotics Webots.
    """

    def __init__(self, supervisor, time_step):
        self.supervisor = supervisor
        self.time_step = time_step
        self.time_step_sec = time_step / 1000.0

        # 1. Initialize 3D Traffic Light LEDs
        self.led_ns_red = supervisor.getDevice("led_ns_red")
        self.led_ns_yellow = supervisor.getDevice("led_ns_yellow")
        self.led_ns_green = supervisor.getDevice("led_ns_green")

        self.led_ew_red = supervisor.getDevice("led_ew_red")
        self.led_ew_yellow = supervisor.getDevice("led_ew_yellow")
        self.led_ew_green = supervisor.getDevice("led_ew_green")

        # 2. Initialize Physical Sensor Arrays (S1, S2, S3)
        self.sensors_s1 = {
            "North": supervisor.getDevice("ds_n_s1"),
            "South": supervisor.getDevice("ds_s_s1"),
            "East": supervisor.getDevice("ds_e_s1"),
            "West": supervisor.getDevice("ds_w_s1"),
        }
        self.sensors_s2 = {
            "North": supervisor.getDevice("ds_n_s2"),
            "South": supervisor.getDevice("ds_s_s2"),
            "East": supervisor.getDevice("ds_e_s2"),
            "West": supervisor.getDevice("ds_w_s2"),
        }
        self.radars_s3 = {
            "North": supervisor.getDevice("radar_n_s3"),
            "South": supervisor.getDevice("radar_s_s3"),
            "East": supervisor.getDevice("radar_e_s3"),
            "West": supervisor.getDevice("radar_w_s3"),
        }

        # Enable all sensors
        for dev in list(self.sensors_s1.values()) + list(self.sensors_s2.values()):
            if dev:
                dev.enable(time_step)
        for dev in self.radars_s3.values():
            if dev:
                dev.enable(time_step)

        # 3. VAC V-BOT Control Parameters
        self.min_green = 10.0      # Minimum green duration (s)
        self.max_green = 60.0      # Maximum green duration (s)
        self.yellow_time = 4.0     # Yellow clearance time (s)
        self.gap_out_time = 3.0    # Gap-out empty threshold (s)

        self.current_phase = PHASE_NS_GREEN
        self.phase_timer = 0.0
        self.gap_timer = 0.0
        self.yellow_timer = 0.0
        self.pending_phase = None

        self.dilemma_holds_count = 0
        self.total_vehicles_cleared = 0

    def set_lights(self, phase):
        """Actuate 3D physical traffic light LEDs in Webots."""
        # North-South lights
        if phase == PHASE_NS_GREEN:
            if self.led_ns_red: self.led_ns_red.set(0)
            if self.led_ns_yellow: self.led_ns_yellow.set(0)
            if self.led_ns_green: self.led_ns_green.set(1)

            if self.led_ew_red: self.led_ew_red.set(1)
            if self.led_ew_yellow: self.led_ew_yellow.set(0)
            if self.led_ew_green: self.led_ew_green.set(0)

        elif phase == PHASE_NS_YELLOW:
            if self.led_ns_red: self.led_ns_red.set(0)
            if self.led_ns_yellow: self.led_ns_yellow.set(1)
            if self.led_ns_green: self.led_ns_green.set(0)

            if self.led_ew_red: self.led_ew_red.set(1)
            if self.led_ew_yellow: self.led_ew_yellow.set(0)
            if self.led_ew_green: self.led_ew_green.set(0)

        elif phase == PHASE_EW_GREEN:
            if self.led_ns_red: self.led_ns_red.set(1)
            if self.led_ns_yellow: self.led_ns_yellow.set(0)
            if self.led_ns_green: self.led_ns_green.set(0)

            if self.led_ew_red: self.led_ew_red.set(0)
            if self.led_ew_yellow: self.led_ew_yellow.set(0)
            if self.led_ew_green: self.led_ew_green.set(1)

        elif phase == PHASE_EW_YELLOW:
            if self.led_ns_red: self.led_ns_red.set(1)
            if self.led_ns_yellow: self.led_ns_yellow.set(0)
            if self.led_ns_green: self.led_ns_green.set(0)

            if self.led_ew_red: self.led_ew_red.set(0)
            if self.led_ew_yellow: self.led_ew_yellow.set(1)
            if self.led_ew_green: self.led_ew_green.set(0)

    def read_sensors(self):
        """Read S1, S2, S3 data from 3D environment."""
        state = {}
        for app in ["North", "South", "East", "West"]:
            # S1: Stopline loop (distance sensor: lower value = vehicle present)
            ds1 = self.sensors_s1.get(app)
            s1_present = bool(ds1 and ds1.getValue() < 800.0)

            # S2: Dilemma zone (50m)
            ds2 = self.sensors_s2.get(app)
            s2_present = bool(ds2 and ds2.getValue() < 800.0)

            # S3: Doppler radar (100m)
            radar = self.radars_s3.get(app)
            s3_count = radar.getNumberOfTargets() if radar else 0
            s3_speed = 0.0
            if radar and s3_count > 0:
                target = radar.getTargets()[0]
                s3_speed = abs(target.speed)

            state[app] = {
                "s1": 1 if s1_present else 0,
                "s2": 1 if s2_present else 0,
                "s3": s3_count,
                "speed": s3_speed,
                "dilemma_risk": bool(s2_present and s3_speed > 6.0)
            }
        return state

    def run_step(self):
        """Single control cycle execution."""
        sensors = self.read_sensors()
        self.phase_timer += self.time_step_sec

        # 1. Handle Yellow Clearance Transition
        if self.yellow_timer > 0:
            self.yellow_timer -= self.time_step_sec
            if self.yellow_timer <= 0:
                # Yellow completed -> Switch to target Green phase
                self.current_phase = self.pending_phase
                self.pending_phase = None
                self.phase_timer = 0.0
                self.set_lights(self.current_phase)
            return

        # 2. Check Dilemma Zone Protection (DZP)
        dilemma_hold = False
        if self.current_phase == PHASE_NS_GREEN:
            if sensors["North"]["dilemma_risk"] or sensors["South"]["dilemma_risk"]:
                if self.phase_timer < self.max_green:
                    dilemma_hold = True
                    self.dilemma_holds_count += 1
        elif self.current_phase == PHASE_EW_GREEN:
            if sensors["East"]["dilemma_risk"] or sensors["West"]["dilemma_risk"]:
                if self.phase_timer < self.max_green:
                    dilemma_hold = True
                    self.dilemma_holds_count += 1

        if dilemma_hold:
            return  # Hold Green phase for safety!

        # 3. Minimum Green Enforcement
        if self.phase_timer < self.min_green:
            return

        # 4. Maximum Green Enforcement
        if self.phase_timer >= self.max_green:
            self.trigger_switch()
            return

        # 5. Gap-Out & Urgency Decision Logic: f(R,G,R,G) = g(sum(x_i * S_i))
        ns_urgency = (
            sensors["North"]["s1"] * 4.0 + sensors["North"]["s2"] * 6.0 + sensors["North"]["s3"] * 2.5 +
            sensors["South"]["s1"] * 4.0 + sensors["South"]["s2"] * 6.0 + sensors["South"]["s3"] * 2.5
        )
        ew_urgency = (
            sensors["East"]["s1"] * 4.0 + sensors["East"]["s2"] * 6.0 + sensors["East"]["s3"] * 2.5 +
            sensors["West"]["s1"] * 4.0 + sensors["West"]["s2"] * 6.0 + sensors["West"]["s3"] * 2.5
        )

        if self.current_phase == PHASE_NS_GREEN:
            ns_active = sensors["North"]["s1"] + sensors["South"]["s1"] + sensors["North"]["s3"] + sensors["South"]["s3"]
            if ns_active == 0:
                self.gap_timer += self.time_step_sec
            else:
                self.gap_timer = 0.0

            if (self.gap_timer >= self.gap_out_time and ew_urgency > 0) or (ew_urgency - ns_urgency > 4.0):
                self.trigger_switch()

        elif self.current_phase == PHASE_EW_GREEN:
            ew_active = sensors["East"]["s1"] + sensors["West"]["s1"] + sensors["East"]["s3"] + sensors["West"]["s3"]
            if ew_active == 0:
                self.gap_timer += self.time_step_sec
            else:
                self.gap_timer = 0.0

            if (self.gap_timer >= self.gap_out_time and ns_urgency > 0) or (ns_urgency - ew_urgency > 4.0):
                self.trigger_switch()

    def trigger_switch(self):
        """Initiate safe yellow clearance transition."""
        if self.current_phase == PHASE_NS_GREEN:
            self.current_phase = PHASE_NS_YELLOW
            self.pending_phase = PHASE_EW_GREEN
        else:
            self.current_phase = PHASE_EW_YELLOW
            self.pending_phase = PHASE_NS_GREEN

        self.yellow_timer = self.yellow_time
        self.gap_timer = 0.0
        self.set_lights(self.current_phase)


def main():
    supervisor = Supervisor()
    time_step = int(supervisor.getBasicTimeStep())

    bot = WebotsVacVBot(supervisor, time_step)
    bot.set_lights(PHASE_NS_GREEN)

    print("==========================================================")
    print("  🚦 Cyberbotics Webots: GREENWAVE VAC V-BOT Supervisor")
    print("  Sensors Active: S1 (Loop 15m), S2 (Dilemma 50m), S3 (Radar 100m)")
    print("==========================================================")

    step_cnt = 0
    while supervisor.step(time_step) != -1:
        bot.run_step()
        step_cnt += 1
        if step_cnt % 50 == 0:
            phase_name = "NS-GREEN" if bot.current_phase == 0 else "EW-GREEN" if bot.current_phase == 2 else "YELLOW"
            print(f"[Webots t={step_cnt*time_step/1000.0:.1f}s] Phase: {phase_name} | DZP Holds: {bot.dilemma_holds_count}")


if __name__ == "__main__":
    main()

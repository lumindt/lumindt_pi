#!/usr/bin/env python3
import can
import cantools
import os
import unicodedata
from datetime import datetime

# Mapping raw signal names to human-friendly labels
FRIENDLY_NAMES = {
    "state": "Blower State",
    "speed": "Blower Speed",
    "Speed_Ref_readBack": "Speed Setpoint (readback)",
    "Iph": "Phase Current",
    "Iph_ref": "Phase Current Reference",
    "P_out": "Output Power",
    "Uin_LV": "Input Voltage (Low)",
    "Uin_HV": "Input Voltage (High)",
    "Uph": "Phase Voltage",
    "T_conv": "Converter Temperature",
    "T_ptc": "Motor Temperature (PTC)",
    "T_thc": "Motor Temperature (THC)",
    "Info_GasBearing3": "Info: Gas Bearing 3",
    "Info_LVInputUV": "Info: LV Input Undervoltage",
    "Info_LVInputOV": "Info: LV Input Overvoltage",
    "Info_CompSurge": "Info: Compressor Surge",
    "Info_MotOT": "Info: Motor Overtemperature",
    "Info_ConvOT": "Info: Converter Overtemperature",
    "Info_power_limit": "Info: Power Limit",
    "Info_iph_limit": "Info: Current Limit",
    "Info_uph_limit": "Info: Phase Voltage Limit",
    "Info_HVInputUV": "Info: HV Input Undervoltage",
    "Info_HVInputOV": "Info: HV Input Overvoltage",
    "Warn_power_limit": "Warning: Power Limit",
    "Warn_iph_limit": "Warning: Current Limit",
    "Warn_uph_limit": "Warning: Phase Voltage Limit",
}

def interpret_state(state: int) -> str:
    """Convert numeric state to human-readable text."""
    if state == 2:
        return "Running"
    elif state == 1:
        return "Ready (not running)"
    elif state == 0:
        return "Init/Not Ready"
    elif state == 3:
        return "Degraded Operation"
    elif state == 4:
        return "Blocked"
    else:
        return f"Unknown ({state})"

def clean_unit(unit: str | None) -> str:
    """Normalize and clean up unit strings (fixes 'Â°C' → '°C')."""
    if not unit:
        return ""
    u = unicodedata.normalize("NFKD", unit).replace("Â", "").replace("̂", "").strip()
    if "C" in u and "°" in u:
        return "°C"
    if u.lower() in ("degc", "celsius"):
        return "°C"
    if "V" in u:
        return "V"
    if "A" in u:
        return "A"
    if "rpm" in u.lower():
        return "rpm"
    return u

def format_value(sig_name: str, value, unit: str) -> str:
    """Format values nicely depending on signal type or unit."""
    if isinstance(value, float):
        if unit in ["°C", "V"] or sig_name.lower().startswith("t_"):
            return f"{value:.1f}"
        if unit == "A":
            return f"{value:.2f}"
        if unit.lower() == "rpm":
            return f"{int(round(value))}"
        return f"{value:.3f}"
    return str(value)

def main():
    dbc_file = "celeroton.dbc"
    if not os.path.exists(dbc_file):
        raise FileNotFoundError("DBC file not found")

    db = cantools.database.load_file(dbc_file)
    bus = can.interface.Bus(channel="can0", bustype="socketcan")

    print("Listening on can0 (Ctrl+C to stop)\n")

    try:
        while True:
            msg = bus.recv()
            if msg is None:
                continue

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            try:
                msg_obj = db.get_message_by_frame_id(msg.arbitration_id)
                decoded = db.decode_message(msg.arbitration_id, msg.data)

                print(f"\n[{timestamp}] ({msg_obj.name})")

                for sig_name, value in decoded.items():
                    sig = msg_obj.get_signal_by_name(sig_name)
                    unit = clean_unit(sig.unit if sig.unit else "")

                    # Use friendly name if available
                    display_name = FRIENDLY_NAMES.get(sig_name, sig_name)

                    # Special formatting for state
                    if msg_obj.name == "Status" and sig_name == "state":
                        formatted_value = interpret_state(value)
                    else:
                        formatted_value = format_value(sig_name, value, unit)

                    if unit:
                        print(f"  {display_name}: {formatted_value} {unit}")
                    else:
                        print(f"  {display_name}: {formatted_value}")

            except Exception:
                print(f"\n[{timestamp}] ID {msg.arbitration_id:03X} Raw: {msg.data.hex().upper()}")

    except KeyboardInterrupt:
        print("\nStopped listening.")

if __name__ == "__main__":
    main()

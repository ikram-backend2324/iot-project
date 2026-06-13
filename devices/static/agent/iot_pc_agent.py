#!/usr/bin/env python3
"""
IoT Analyzer — Local PC Agent
=============================
Reads REAL hardware telemetry the browser cannot access (CPU temperature,
exact RAM, disk usage, per-core load) and prints it as JSON so you can paste
it into the "Check My PC" page for a full AI diagnosis.

USAGE
-----
1) Install the one dependency:
       pip install psutil
2) Run:
       python iot_pc_agent.py
3) Copy the JSON it prints and paste it into the website when asked,
   OR run with --serve to expose it on http://127.0.0.1:8731/stats
   so the website can fetch it automatically.

Nothing is uploaded by this script itself. You stay in control.
"""

import json
import platform
import shutil
import sys

try:
    import psutil
except ImportError:
    print(json.dumps({"error": "psutil not installed. Run: pip install psutil"}))
    sys.exit(1)


def read_temperature():
    try:
        temps = psutil.sensors_temperatures()
    except (AttributeError, NotImplementedError):
        return None
    if not temps:
        return None
    for name in ('coretemp', 'cpu_thermal', 'k10temp', 'acpitz'):
        if name in temps and temps[name]:
            return round(temps[name][0].current, 1)
    for entries in temps.values():
        if entries:
            return round(entries[0].current, 1)
    return None


def collect():
    vm = psutil.virtual_memory()
    du = shutil.disk_usage("/")
    battery = None
    try:
        b = psutil.sensors_battery()
        if b is not None:
            battery = {"percent": b.percent, "plugged": b.power_plugged}
    except (AttributeError, NotImplementedError):
        pass

    return {
        "source": "native-agent",
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "processor": platform.processor() or platform.machine(),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_logical_cores": psutil.cpu_count(logical=True),
        "cpu_load_percent": psutil.cpu_percent(interval=0.8),
        "cpu_temperature_c": read_temperature(),
        "ram_total_gb": round(vm.total / (1024 ** 3), 2),
        "ram_used_gb": round(vm.used / (1024 ** 3), 2),
        "ram_available_gb": round(vm.available / (1024 ** 3), 2),
        "ram_used_percent": vm.percent,
        "disk_total_gb": round(du.total / (1024 ** 3), 2),
        "disk_used_gb": round(du.used / (1024 ** 3), 2),
        "disk_free_gb": round(du.free / (1024 ** 3), 2),
        "disk_free_percent": round(du.free / du.total * 100, 1),
        "battery": battery,
    }


def serve():
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            if self.path.rstrip("/") in ("/stats", ""):
                body = json.dumps(collect()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors()
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self._cors()
                self.end_headers()

        def log_message(self, *a):
            pass

    port = 8731
    print(f"IoT PC Agent serving telemetry at http://127.0.0.1:{port}/stats")
    print("Leave this running, then click 'Use Local Agent' on the website. Ctrl+C to stop.")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print(json.dumps(collect(), indent=2))

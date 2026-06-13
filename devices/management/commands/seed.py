import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from devices.models import Device, DeviceMetric, AIAnalysis


SAMPLE_DEVICES = [
    {
        "name": "Temperature Sensor — Server Room",
        "device_type": "sensor",
        "location": "Server Room A, Floor 2",
        "ip_address": "192.168.1.10",
        "status": "online",
        "description": "Monitors ambient temperature and humidity in the main server room.",
    },
    {
        "name": "Smart Gateway Hub",
        "device_type": "gateway",
        "location": "Network Cabinet, Floor 1",
        "ip_address": "192.168.1.1",
        "status": "online",
        "description": "Central IoT gateway routing data from 24 edge devices.",
    },
    {
        "name": "HVAC Controller Unit",
        "device_type": "controller",
        "location": "Rooftop, Building B",
        "ip_address": "192.168.1.25",
        "status": "online",
        "description": "Controls HVAC system based on temperature and occupancy sensors.",
    },
    {
        "name": "Security Camera #03",
        "device_type": "camera",
        "location": "Parking Lot, East Entrance",
        "ip_address": "192.168.2.13",
        "status": "online",
        "description": "4K outdoor security camera with night vision and motion detection.",
    },
    {
        "name": "Vibration Sensor — CNC Machine",
        "device_type": "sensor",
        "location": "Factory Floor, Zone C",
        "ip_address": "192.168.3.5",
        "status": "error",
        "description": "Detects abnormal vibration patterns in the CNC milling machine.",
    },
    {
        "name": "Smart Valve Actuator #7",
        "device_type": "actuator",
        "location": "Water Treatment Plant",
        "ip_address": "192.168.4.7",
        "status": "maintenance",
        "description": "Electronically controlled valve for water flow regulation.",
    },
    {
        "name": "Air Quality Monitor",
        "device_type": "sensor",
        "location": "Open Office, Floor 3",
        "ip_address": "192.168.1.42",
        "status": "online",
        "description": "Tracks CO2, VOCs, PM2.5 and temperature in office environment.",
    },
    {
        "name": "Power Meter — Main Panel",
        "device_type": "sensor",
        "location": "Electrical Room, Basement",
        "ip_address": "192.168.1.55",
        "status": "offline",
        "description": "Monitors energy consumption across all building circuits.",
    },
]

SAMPLE_METRICS = {
    "sensor": [
        ("temperature", [(22.1, "°C"), (23.4, "°C"), (24.8, "°C"), (21.9, "°C"), (22.5, "°C"), (26.3, "°C"), (25.0, "°C")]),
        ("humidity", [(48.2, "%"), (51.0, "%"), (47.5, "%"), (52.8, "%"), (50.1, "%")]),
        ("cpu_usage", [(12.5, "%"), (18.3, "%"), (22.1, "%"), (15.7, "%"), (9.8, "%")]),
    ],
    "gateway": [
        ("packets_per_sec", [(1245, "pps"), (1380, "pps"), (992, "pps"), (1567, "pps"), (1102, "pps")]),
        ("connected_devices", [(22, ""), (24, ""), (23, ""), (21, ""), (24, "")]),
        ("latency_ms", [(4.2, "ms"), (3.8, "ms"), (5.1, "ms"), (4.9, "ms"), (3.3, "ms")]),
    ],
    "controller": [
        ("setpoint_temp", [(21.0, "°C"), (21.5, "°C"), (22.0, "°C"), (21.0, "°C"), (20.5, "°C")]),
        ("fan_speed", [(60, "%"), (72, "%"), (55, "%"), (68, "%"), (80, "%")]),
        ("power_draw", [(3.2, "kW"), (4.1, "kW"), (3.8, "kW"), (3.5, "kW"), (4.4, "kW")]),
    ],
    "camera": [
        ("fps", [(25, "fps"), (25, "fps"), (24, "fps"), (25, "fps"), (23, "fps")]),
        ("storage_used", [(72, "%"), (74, "%"), (76, "%"), (78, "%"), (80, "%")]),
    ],
    "actuator": [
        ("valve_position", [(45, "%"), (60, "%"), (30, "%"), (75, "%"), (50, "%")]),
        ("flow_rate", [(12.3, "L/min"), (15.8, "L/min"), (8.4, "L/min"), (18.2, "L/min"), (11.0, "L/min")]),
    ],
}

SAMPLE_ANALYSIS = {
    "online": (
        False,
        {"health": 88, "performance": 84, "reliability": 90, "efficiency": 79, "security": 82, "risk": "Low", "anomaly": False},
        "## Overall Health Status\n"
        "The device is rated Good. It is operating within normal parameters and every monitored "
        "metric falls inside its expected range with no significant deviation.\n\n"
        "## Anomaly Detection\n"
        "No anomalies detected. Readings are smooth and consistent with the historical baseline, "
        "which is exactly what a healthy unit of this type should show.\n\n"
        "## Performance Assessment\n"
        "Performance is stable with comfortable headroom. Metric trends track prior weeks closely "
        "and there are no signs of thermal or load stress.\n\n"
        "## Metric-by-Metric Breakdown\n"
        "1) Temperature sits mid-range and well below any warning threshold.\n"
        "2) Signal and connectivity readings are steady, indicating a reliable link.\n"
        "3) Power draw is nominal for this device class.\n\n"
        "## Root Cause & Reasoning\n"
        "Nothing is wrong. Consistent telemetry and a stable environment are keeping the device healthy.\n\n"
        "## Recommendations\n"
        "1) Continue the regular monitoring schedule.\n"
        "2) Check for a firmware update in the next maintenance window.\n"
        "3) Archive older metric data to optimise storage.\n"
        "4) Keep a baseline snapshot for future anomaly comparison.\n\n"
        "## Predictive Outlook\n"
        "If conditions hold, the device should continue operating normally for the foreseeable future. "
        "Watch for any gradual upward drift in temperature as an early-warning sign.\n\n"
        "## Risk Level\n"
        "Risk Level: Low because the device is healthy and fully operational."
    ),
    "error": (
        True,
        {"health": 32, "performance": 38, "reliability": 28, "efficiency": 45, "security": 60, "risk": "High", "anomaly": True},
        "## Overall Health Status\n"
        "The device is rated Critical. It is reporting an error state and needs immediate attention.\n\n"
        "## Anomaly Detection\n"
        "ANOMALY DETECTED: Abnormal readings observed. Values exceed safe operating thresholds by "
        "roughly 34%, which points to sensor calibration drift or a developing hardware fault.\n\n"
        "## Performance Assessment\n"
        "Performance is degraded. Erratic spikes in the metric stream suggest connection instability "
        "or a failing component rather than a transient blip.\n\n"
        "## Metric-by-Metric Breakdown\n"
        "1) Primary metric is 34% above its safe ceiling — the main red flag.\n"
        "2) Reading variance is high, consistent with an intermittent fault.\n"
        "3) Uptime pattern shows repeated short drops.\n\n"
        "## Root Cause & Reasoning\n"
        "The combination of an over-threshold value and high variance most likely indicates a "
        "calibration drift or a loose/failing sensor connection feeding bad data.\n\n"
        "## Recommendations\n"
        "1) Inspect the device hardware immediately.\n"
        "2) Check the power supply and cable connections.\n"
        "3) Run a diagnostic self-test if supported.\n"
        "4) Replace the unit if the fault persists after a reset and recalibration.\n\n"
        "## Predictive Outlook\n"
        "Left unresolved, the error is likely to escalate into full downtime. Rising variance or a "
        "complete loss of readings would be the signal that failure is imminent.\n\n"
        "## Risk Level\n"
        "Risk Level: High because unresolved errors may cause system downtime."
    ),
}


class Command(BaseCommand):
    help = "Seeds the database with a default admin user and sample IoT data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing seed data before re-seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write("🗑  Clearing existing data...")
            DeviceMetric.objects.all().delete()
            AIAnalysis.objects.all().delete()
            Device.objects.all().delete()
            User.objects.filter(username__in=['admin', 'demo']).delete()

        # ── Create admin user ──
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@iotanalyzer.com',
                password='admin1234',
            )
            self.stdout.write(self.style.SUCCESS("✅ Admin created  →  username: admin  /  password: admin1234"))
        else:
            admin = User.objects.get(username='admin')
            self.stdout.write("ℹ️  Admin already exists, skipping.")

        # ── Create demo user ──
        if not User.objects.filter(username='demo').exists():
            demo = User.objects.create_user(
                username='demo',
                email='demo@iotanalyzer.com',
                password='demo1234',
            )
            self.stdout.write(self.style.SUCCESS("✅ Demo user created  →  username: demo  /  password: demo1234"))
        else:
            demo = User.objects.get(username='demo')
            self.stdout.write("ℹ️  Demo user already exists, skipping.")

        # ── Create devices ──
        created_devices = []
        # Spread devices around Tashkent so the map has points
        coords = [
            (41.3111, 69.2797), (41.2995, 69.2401), (41.3275, 69.2817),
            (41.2856, 69.2034), (41.3380, 69.3340), (41.2700, 69.2200),
            (41.3500, 69.2500), (41.2950, 69.3100),
        ]
        for i, d in enumerate(SAMPLE_DEVICES):
            owner = admin if i % 2 == 0 else demo
            lat, lng = coords[i % len(coords)]
            device, created = Device.objects.get_or_create(
                name=d["name"],
                owner=owner,
                defaults={
                    "device_type": d["device_type"],
                    "location": d["location"],
                    "latitude": lat,
                    "longitude": lng,
                    "ip_address": d["ip_address"],
                    "status": d["status"],
                    "description": d["description"],
                },
            )
            if created:
                created_devices.append(device)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_devices)} devices"))

        # ── Create metrics ──
        metric_count = 0
        for device in Device.objects.all():
            metric_groups = SAMPLE_METRICS.get(device.device_type, SAMPLE_METRICS["sensor"])
            for metric_name, readings in metric_groups:
                for value, unit in readings:
                    # Add small random jitter to make data look realistic
                    jittered_value = round(value + random.uniform(-value * 0.05, value * 0.05), 2)
                    DeviceMetric.objects.create(
                        device=device,
                        metric_name=metric_name,
                        value=jittered_value,
                        unit=unit,
                    )
                    metric_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {metric_count} metric readings"))

        # ── Create sample AI analyses ──
        analysis_count = 0
        for device in Device.objects.filter(status__in=['online', 'error']):
            status_key = device.status if device.status in SAMPLE_ANALYSIS else 'online'
            anomaly, scores, result_text = SAMPLE_ANALYSIS[status_key]
            AIAnalysis.objects.get_or_create(
                device=device,
                defaults={
                    "prompt_used": f"Analyze IoT device: {device.name} ({device.device_type}) at {device.location}",
                    "result": result_text,
                    "anomalies_detected": anomaly,
                    "language": "en",
                    "scores": scores,
                },
            )
            analysis_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {analysis_count} AI analyses"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🚀 Seed complete! You can now log in:"))
        self.stdout.write("   Admin panel  →  /admin/      admin / admin1234")
        self.stdout.write("   Client app   →  /auth/login/ demo  / demo1234")

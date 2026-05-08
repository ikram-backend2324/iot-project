import requests
from django.conf import settings


LANGUAGE_INSTRUCTIONS = {
    'en': 'Respond entirely in English.',
    'ru': 'Отвечай полностью на русском языке.',
    'uz': "To'liq o'zbek tilida javob bering.",
}

LANGUAGE_NAMES = {
    'en': 'English',
    'ru': 'Russian',
    'uz': 'Uzbek',
}


def format_metrics(metrics):
    if not metrics:
        return "No metrics available."
    lines = []
    for m in metrics:
        lines.append(f"  - {m.metric_name}: {m.value} {m.unit} (at {m.recorded_at.strftime('%Y-%m-%d %H:%M')})")
    return "\n".join(lines)


def analyze_device_with_ai(device, metrics, language='en'):
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])
    metrics_text = format_metrics(metrics)

    prompt = f"""{lang_instruction}

You are an expert IoT systems analyst. Analyze the following IoT device data and provide a detailed report.

Device Information:
- Name: {device.name}
- Type: {device.get_device_type_display()}
- Location: {device.location or 'Not specified'}
- IP Address: {device.ip_address or 'Not specified'}
- Current Status: {device.get_status_display()}
- Description: {device.description or 'None'}

Recent Metrics (last readings):
{metrics_text}

Please provide your analysis in the following structure:
1. **Overall Health Status** - Rate the device health (Good/Warning/Critical) and explain why
2. **Anomaly Detection** - If anomalies exist, write exactly "ANOMALY DETECTED:" followed by details. If none, write "No anomalies detected."
3. **Performance Assessment** - Evaluate the device performance based on metrics
4. **Recommendations** - Provide specific actionable recommendations
5. **Risk Level** - Write exactly "Risk Level: Low", "Risk Level: Medium", or "Risk Level: High"

Be concise but thorough. If no metrics are available, provide general recommendations based on device type and status.
"""

    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:8000',
        'X-Title': 'IoT Analyzer',
    }

    payload = {
        'model': settings.OPENROUTER_MODEL,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 1000,
        'temperature': 0.3,
    }

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data['choices'][0]['message']['content']

        # Detect anomalies keyword based on language
        # Detect based on the explicit markers we asked the AI to use
        anomaly_keywords = [
            'anomaly detected:',
            'risk level: high',
            'risk level: critical',
        ]
        anomalies_detected = any(kw.lower() in result_text.lower() for kw in anomaly_keywords)

        return {
            'success': True,
            'result': result_text,
            'prompt': prompt,
            'anomalies_detected': anomalies_detected,
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out. Please try again.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'API request failed: {str(e)}'}
    except (KeyError, IndexError) as e:
        return {'success': False, 'error': f'Unexpected API response format: {str(e)}'}
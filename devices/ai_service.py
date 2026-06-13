import re
import requests
from django.conf import settings


LANGUAGE_INSTRUCTIONS = {
    'en': 'You MUST write your ENTIRE response in English. Every word, heading and sentence must be in English.',
    'ru': 'Ты ДОЛЖЕН написать ВЕСЬ ответ полностью на русском языке. Каждое слово, заголовок и предложение должны быть на русском.',
    'uz': "Siz BUTUN javobni faqat o'zbek tilida yozishingiz SHART. Har bir so'z, sarlavha va gap o'zbek tilida bo'lishi kerak.",
}

LANGUAGE_NAMES = {
    'en': 'English',
    'ru': 'Russian',
    'uz': 'Uzbek',
}

# Localized section headers used when we render the structured report.
SECTION_LABELS = {
    'en': {
        'health': 'Overall Health Status',
        'anomaly': 'Anomaly Detection',
        'performance': 'Performance Assessment',
        'metrics': 'Metric-by-Metric Breakdown',
        'root': 'Root Cause & Reasoning',
        'recommend': 'Recommendations',
        'forecast': 'Predictive Outlook',
        'risk': 'Risk Level',
    },
    'ru': {
        'health': 'Общее состояние устройства',
        'anomaly': 'Обнаружение аномалий',
        'performance': 'Оценка производительности',
        'metrics': 'Разбор по каждому показателю',
        'root': 'Первопричина и обоснование',
        'recommend': 'Рекомендации',
        'forecast': 'Прогноз на будущее',
        'risk': 'Уровень риска',
    },
    'uz': {
        'health': 'Umumiy holat',
        'anomaly': 'Anomaliyalarni aniqlash',
        'performance': 'Unumdorlik bahosi',
        'metrics': "Har bir ko'rsatkich tahlili",
        'root': 'Asosiy sabab va izoh',
        'recommend': 'Tavsiyalar',
        'forecast': 'Kelajak bashorati',
        'risk': 'Xavf darajasi',
    },
}


def format_metrics(metrics):
    if not metrics:
        return "No metrics available."
    lines = []
    for m in metrics:
        lines.append(f"  - {m.metric_name}: {m.value} {m.unit} (at {m.recorded_at.strftime('%Y-%m-%d %H:%M')})")
    return "\n".join(lines)


def build_prompt(device, metrics, language='en'):
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])
    metrics_text = format_metrics(metrics)

    prompt = f"""{lang_instruction}

You are a senior IoT systems reliability engineer with deep expertise in predictive
maintenance, anomaly detection and embedded telemetry. You write thorough, professional
diagnostic reports. Be detailed and specific: explain WHY, quantify where possible, and
give concrete, actionable engineering advice. Aim for a rich, multi-paragraph report.

=== DEVICE UNDER ANALYSIS ===
- Name: {device.name}
- Type: {device.get_device_type_display()}
- Location: {device.location or 'Not specified'}
- IP Address: {device.ip_address or 'Not specified'}
- Current Status: {device.get_status_display()}
- Description: {device.description or 'None'}

=== RECENT TELEMETRY (most recent first) ===
{metrics_text}

=== OUTPUT FORMAT (FOLLOW EXACTLY) ===
First, output a machine-readable scorecard block, EXACTLY in this format and nothing else
inside it (numbers are 0-100 integers):

<SCORES>
health: <0-100>
performance: <0-100>
reliability: <0-100>
efficiency: <0-100>
security: <0-100>
risk: <Low|Medium|High>
anomaly: <yes|no>
</SCORES>

Then write the full narrative report. Use these EXACT section headings on their own line,
each prefixed with "## " (two hash marks and a space). Do NOT use any other markdown such as
**bold**, bullet asterisks, or tables. Write in clean flowing paragraphs. Where you list
items, write them as short numbered lines like "1) ...". Sections:

## {SECTION_LABELS['en']['health']}
Two to four sentences rating the device (Good / Warning / Critical) and explaining why,
referencing the actual metric values.

## {SECTION_LABELS['en']['anomaly']}
If anomalies exist, begin this section with the exact token "ANOMALY DETECTED:" then describe
each anomaly, the metric involved, expected vs observed range, and severity. If none, write
"No anomalies detected." and briefly explain what normal looks like here.

## {SECTION_LABELS['en']['performance']}
A detailed paragraph evaluating performance trends, stability and headroom.

## {SECTION_LABELS['en']['metrics']}
Go through each metric individually. For each one state the value, whether it is healthy,
the typical/expected range for this device type, and what it implies.

## {SECTION_LABELS['en']['root']}
Explain the likely root cause of any issue and your engineering reasoning. If healthy,
explain which factors are keeping it healthy.

## {SECTION_LABELS['en']['recommend']}
Provide at least 4 specific, prioritised, actionable recommendations as numbered lines.

## {SECTION_LABELS['en']['forecast']}
Predict how this device is likely to behave over the next days/weeks if nothing changes,
and what early-warning signs to watch for.

## {SECTION_LABELS['en']['risk']}
Write exactly one of: "Risk Level: Low", "Risk Level: Medium", or "Risk Level: High",
followed by a one sentence justification.

Remember: write EVERYTHING (all headings and all prose) in {LANGUAGE_NAMES.get(language, 'English')}.
The <SCORES> block keys stay in English but is the only English allowed if the language is not English.
If no metrics are available, still produce the full report using general engineering knowledge
for this device type and status, and say clearly that telemetry is missing.
"""
    return prompt


def parse_scores(text):
    """Extract the <SCORES> block. Returns (scores_dict, cleaned_text)."""
    scores = {
        'health': None, 'performance': None, 'reliability': None,
        'efficiency': None, 'security': None, 'risk': None, 'anomaly': None,
    }
    match = re.search(r'<SCORES>(.*?)</SCORES>', text, re.DOTALL | re.IGNORECASE)
    block = ''
    if match:
        block = match.group(1)
        text = (text[:match.start()] + text[match.end():]).strip()

    for line in block.splitlines():
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip().lower()
        val = val.strip()
        if key in ('health', 'performance', 'reliability', 'efficiency', 'security'):
            num = re.search(r'\d+', val)
            if num:
                scores[key] = max(0, min(100, int(num.group())))
        elif key == 'risk':
            low = val.lower()
            if 'high' in low or 'critical' in low:
                scores['risk'] = 'High'
            elif 'med' in low:
                scores['risk'] = 'Medium'
            else:
                scores['risk'] = 'Low'
        elif key == 'anomaly':
            scores['anomaly'] = 'yes' in val.lower()

    return scores, text


def analyze_device_with_ai(device, metrics, language='en'):
    prompt = build_prompt(device, metrics, language)

    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:8000',
        'X-Title': 'IoT Analyzer',
    }

    payload = {
        'model': settings.OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 2600,
        'temperature': 0.4,
    }

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data['choices'][0]['message']['content']

        scores, cleaned = parse_scores(result_text)

        anomaly_keywords = ['anomaly detected:', 'risk level: high', 'risk level: critical',
                            'аномалия обнаружена', 'уровень риска: высокий',
                            'anomaliya aniqlandi', 'xavf darajasi: yuqori']
        anomalies_detected = any(kw in cleaned.lower() for kw in anomaly_keywords)
        if scores.get('anomaly') is not None:
            anomalies_detected = anomalies_detected or scores['anomaly']

        return {
            'success': True,
            'result': cleaned,
            'prompt': prompt,
            'anomalies_detected': anomalies_detected,
            'scores': scores,
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out. Please try again.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'API request failed: {str(e)}'}
    except (KeyError, IndexError) as e:
        return {'success': False, 'error': f'Unexpected API response format: {str(e)}'}


# ──────────────────────────────────────────────────────────────────────────
#  PC HEALTH ANALYSIS  (for the "Check My PC" feature)
# ──────────────────────────────────────────────────────────────────────────

def build_pc_prompt(stats, language='en'):
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])

    lines = []
    for k, v in stats.items():
        lines.append(f"  - {k}: {v}")
    stats_text = "\n".join(lines) if lines else "No data provided."

    prompt = f"""{lang_instruction}

You are a senior computer hardware and systems diagnostics expert. A user has shared live
telemetry from their computer. Produce a thorough, professional health diagnosis.

=== COLLECTED SYSTEM TELEMETRY ===
{stats_text}

Note: some values may be browser-estimated (RAM, cores, GPU) while others (CPU temperature,
disk usage, exact RAM) may come from a native agent. Treat clearly labelled values accordingly
and note when a value is an estimate or unavailable.

=== OUTPUT FORMAT (FOLLOW EXACTLY) ===
Output a machine-readable scorecard first (integers 0-100):

<SCORES>
health: <0-100>
performance: <0-100>
reliability: <0-100>
efficiency: <0-100>
security: <0-100>
risk: <Low|Medium|High>
anomaly: <yes|no>
</SCORES>

Then the narrative, using these EXACT headings each on their own line prefixed with "## ".
No other markdown. Clean paragraphs; lists as "1) ..." numbered lines.

## {SECTION_LABELS['en']['health']}
## {SECTION_LABELS['en']['anomaly']}
## {SECTION_LABELS['en']['performance']}
## {SECTION_LABELS['en']['metrics']}
## {SECTION_LABELS['en']['root']}
## {SECTION_LABELS['en']['recommend']}
## {SECTION_LABELS['en']['forecast']}
## {SECTION_LABELS['en']['risk']}

For ## {SECTION_LABELS['en']['metrics']}, comment specifically on temperature (if present,
flag >80C as hot), RAM pressure, storage headroom (flag <10% free), CPU load and battery.
Give concrete advice for this specific machine. Write EVERYTHING in
{LANGUAGE_NAMES.get(language, 'English')} (except the <SCORES> keys).
"""
    return prompt


def analyze_pc_with_ai(stats, language='en'):
    prompt = build_pc_prompt(stats, language)

    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:8000',
        'X-Title': 'IoT Analyzer',
    }
    payload = {
        'model': settings.OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 2600,
        'temperature': 0.4,
    }
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers, json=payload, timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        result_text = data['choices'][0]['message']['content']
        scores, cleaned = parse_scores(result_text)
        return {
            'success': True,
            'result': cleaned,
            'scores': scores,
        }
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out. Please try again.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'API request failed: {str(e)}'}
    except (KeyError, IndexError) as e:
        return {'success': False, 'error': f'Unexpected API response format: {str(e)}'}

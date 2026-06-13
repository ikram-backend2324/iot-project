import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

SECTION_ICONS = ['🩺', '⚠️', '⚡', '📊', '🔬', '✅', '🔮', '🎯']


def _strip_inline(s):
    s = escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = s.replace('**', '').replace('`', '')
    return s


@register.filter(name='render_analysis')
def render_analysis(text):
    """Turn the AI's structured text into clean formatted HTML cards.
    Removes the raw markdown / 'dropdown asterisk' look entirely."""
    if not text:
        return ''
    text = text.replace('\r\n', '\n').strip()
    lines = text.split('\n')

    # First pass: split into sections by '## heading'
    sections = []
    current = {'title': None, 'lines': []}
    for raw in lines:
        line = raw.rstrip()
        m = re.match(r'^\s*#{1,4}\s*(.+?)\s*#*\s*$', line)
        # also catch a leading "**Heading**" only line
        if not m:
            mb = re.match(r'^\s*\*\*(.+?)\*\*\s*:?\s*$', line)
            if mb:
                m = mb
        if m:
            if current['title'] is not None or current['lines']:
                sections.append(current)
            current = {'title': m.group(1).strip().strip('*').strip(), 'lines': []}
        else:
            current['lines'].append(line)
    if current['title'] is not None or current['lines']:
        sections.append(current)

    html = []
    idx = 0
    for sec in sections:
        body_html = _render_body(sec['lines'])
        if sec['title'] is None:
            # preamble text with no heading
            if body_html.strip():
                html.append(f'<div class="an-section"><div class="an-body">{body_html}</div></div>')
            continue
        icon = SECTION_ICONS[idx % len(SECTION_ICONS)]
        idx += 1
        title_low = sec['title'].lower()
        flag_cls = ' an-section--risk' if ('risk' in title_low or 'риск' in title_low or 'xavf' in title_low) else ''
        html.append(
            f'<div class="an-section{flag_cls}">'
            f'<div class="an-h"><span class="an-h-ic">{icon}</span>{_strip_inline(sec["title"])}</div>'
            f'<div class="an-body">{body_html}</div></div>'
        )

    result = '\n'.join(html)
    result = re.sub(
        r'(ANOMALY DETECTED:|АНОМАЛИЯ ОБНАРУЖЕНА:|ANOMALIYA ANIQLANDI:)',
        r'<span class="an-flag">\1</span>', result, flags=re.IGNORECASE)
    # Risk level pill
    result = re.sub(
        r'(Risk Level|Уровень риска|Xavf darajasi)\s*:\s*(High|Medium|Low|Высокий|Средний|Низкий|Yuqori|O\'rta|Past)',
        lambda mm: f'<span class="an-risk an-risk--{_risk_class(mm.group(2))}">{mm.group(0)}</span>',
        result, flags=re.IGNORECASE)
    return mark_safe(result)


def _risk_class(word):
    w = word.lower()
    if w in ('high', 'высокий', 'yuqori'):
        return 'high'
    if w in ('medium', 'средний', "o'rta"):
        return 'med'
    return 'low'


def _render_body(lines):
    out = []
    para = []
    in_list = False

    def flush_para():
        nonlocal para
        if para:
            j = ' '.join(para).strip()
            if j:
                out.append(f'<p class="an-p">{_strip_inline(j)}</p>')
            para = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append('</ol>')
            in_list = False

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            close_list()
            continue
        nm = re.match(r'^(\d+)[\)\.]\s+(.*)$', line)
        bm = re.match(r'^[-*•]\s+(.*)$', line)
        if nm:
            flush_para()
            if not in_list:
                out.append('<ol class="an-list">')
                in_list = True
            out.append(f'<li>{_strip_inline(nm.group(2))}</li>')
        elif bm:
            flush_para()
            if not in_list:
                out.append('<ol class="an-list">')
                in_list = True
            out.append(f'<li>{_strip_inline(bm.group(1))}</li>')
        else:
            close_list()
            para.append(line)
    flush_para()
    close_list()
    return '\n'.join(out)

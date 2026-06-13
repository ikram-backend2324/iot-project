import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, get_language
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import Device, DeviceMetric, AIAnalysis, PCAnalysis
from .forms import DeviceForm, MetricForm
from .ai_service import analyze_device_with_ai, analyze_pc_with_ai


def _current_lang(request):
    # The user's explicit choice is stored in the django_language cookie by set_language.
    # We prefer it over request.LANGUAGE_CODE because unprefixed URLs (default language)
    # always resolve LANGUAGE_CODE to 'en' even when the user has chosen ru/uz.
    language = (
        request.COOKIES.get('django_language')
        or request.session.get('django_language')
        or getattr(request, 'LANGUAGE_CODE', None)
        or get_language()
        or 'en'
    )
    language = language.split('-')[0].lower()
    return language if language in ('en', 'ru', 'uz') else 'en'


@login_required
def dashboard(request):
    devices = Device.objects.filter(owner=request.user)
    total_devices = devices.count()
    online_count = devices.filter(status='online').count()
    error_count = devices.filter(status='error').count()
    recent_analyses = AIAnalysis.objects.filter(device__owner=request.user).order_by('-analyzed_at')[:5]
    recent_metrics = DeviceMetric.objects.filter(device__owner=request.user).order_by('-recorded_at')[:10]

    status_data = {
        'online': online_count,
        'offline': devices.filter(status='offline').count(),
        'error': error_count,
        'maintenance': devices.filter(status='maintenance').count(),
    }

    # Data for the 3D network globe / scene
    scene_devices = [{
        'name': d.name,
        'type': d.device_type,
        'status': d.status,
        'lat': d.latitude,
        'lng': d.longitude,
    } for d in devices]

    context = {
        'devices': devices[:6],
        'total_devices': total_devices,
        'online_count': online_count,
        'error_count': error_count,
        'recent_analyses': recent_analyses,
        'recent_metrics': recent_metrics,
        'status_data': status_data,
        'status_data_json': json.dumps(status_data),
        'scene_devices_json': json.dumps(scene_devices),
    }
    return render(request, 'devices/dashboard.html', context)


@login_required
def device_list(request):
    devices = Device.objects.filter(owner=request.user)
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    if status_filter:
        devices = devices.filter(status=status_filter)
    if type_filter:
        devices = devices.filter(device_type=type_filter)

    # Map markers (only devices with coordinates)
    map_devices = [{
        'name': d.name,
        'type': d.get_device_type_display(),
        'status': d.status,
        'status_label': str(d.get_status_display()),
        'lat': d.latitude,
        'lng': d.longitude,
        'location': d.location,
        'url': f'/devices/{d.pk}/',
    } for d in devices if d.latitude is not None and d.longitude is not None]

    context = {
        'devices': devices,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'device_types': Device.DEVICE_TYPES,
        'status_choices': Device.STATUS_CHOICES,
        'map_devices_json': json.dumps(map_devices),
        'has_map_devices': len(map_devices) > 0,
    }
    return render(request, 'devices/device_list.html', context)


@login_required
def device_detail(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    metrics = device.metrics.order_by('-recorded_at')[:20]
    analyses = device.analyses.order_by('-analyzed_at')[:5]

    chart_metrics = {}
    for m in reversed(list(metrics)):
        if m.metric_name not in chart_metrics:
            chart_metrics[m.metric_name] = {'labels': [], 'values': [], 'unit': m.unit}
        chart_metrics[m.metric_name]['labels'].append(m.recorded_at.strftime('%m/%d %H:%M'))
        chart_metrics[m.metric_name]['values'].append(m.value)

    context = {
        'device': device,
        'metrics': metrics,
        'analyses': analyses,
        'chart_metrics': chart_metrics,
        'chart_metrics_json': json.dumps(chart_metrics),
        'device_json': json.dumps({
            'name': device.name, 'type': device.device_type, 'status': device.status,
            'lat': device.latitude, 'lng': device.longitude, 'location': device.location,
        }),
    }
    return render(request, 'devices/device_detail.html', context)


@login_required
def add_device(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.owner = request.user
            device.save()
            messages.success(request, _('Device added successfully!'))
            return redirect('device_detail', pk=device.pk)
    else:
        form = DeviceForm()
    return render(request, 'devices/device_form.html', {'form': form, 'action': _('Add Device')})


@login_required
def edit_device(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, _('Device updated successfully!'))
            return redirect('device_detail', pk=device.pk)
    else:
        form = DeviceForm(instance=device)
    return render(request, 'devices/device_form.html', {'form': form, 'action': _('Edit Device'), 'device': device})


@login_required
def delete_device(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    if request.method == 'POST':
        device.delete()
        messages.success(request, _('Device deleted successfully!'))
        return redirect('device_list')
    return render(request, 'devices/device_confirm_delete.html', {'device': device})


@login_required
def add_metric(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MetricForm(request.POST)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.device = device
            metric.save()
            messages.success(request, _('Metric logged successfully!'))
            return redirect('device_detail', pk=device.pk)
    else:
        form = MetricForm()
    return render(request, 'devices/metric_form.html', {'form': form, 'device': device})


@login_required
def analyze_device(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    if request.method == 'POST':
        language = _current_lang(request)
        metrics = list(device.metrics.order_by('-recorded_at')[:15])
        result = analyze_device_with_ai(device, metrics, language)

        if result['success']:
            analysis = AIAnalysis.objects.create(
                device=device,
                prompt_used=result['prompt'],
                result=result['result'],
                anomalies_detected=result['anomalies_detected'],
                language=language,
                scores=result.get('scores', {}),
            )
            messages.success(request, _('Analysis completed!'))
            return redirect('analysis_detail', pk=analysis.pk)
        else:
            messages.error(request, f"{_('Analysis failed')}: {result['error']}")
            return redirect('device_detail', pk=device.pk)

    return render(request, 'devices/analyze_loading.html', {'device': device})


@login_required
def analysis_detail(request, pk):
    analysis = get_object_or_404(AIAnalysis, pk=pk, device__owner=request.user)
    return render(request, 'devices/analysis_detail.html', {
        'analysis': analysis,
        'scores_json': json.dumps(analysis.scores or {}),
    })


@login_required
def analysis_list(request):
    analyses = AIAnalysis.objects.filter(device__owner=request.user).order_by('-analyzed_at')
    return render(request, 'devices/analysis_list.html', {'analyses': analyses})


# ──────────────────────────────────────────────────────────────────────────
#  CHECK MY PC
# ──────────────────────────────────────────────────────────────────────────

@login_required
def pc_check(request):
    """Landing page with the 'Check My PC' button + 3D system scene."""
    recent = PCAnalysis.objects.filter(owner=request.user).order_by('-analyzed_at')[:5]
    return render(request, 'devices/pc_check.html', {'recent': recent})


@login_required
@require_POST
def pc_analyze(request):
    """Receive collected browser/agent stats as JSON, run AI diagnosis, store + return."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

    stats = payload.get('stats', {})
    if not isinstance(stats, dict) or not stats:
        return JsonResponse({'success': False, 'error': 'No stats provided'}, status=400)

    language = _current_lang(request)
    result = analyze_pc_with_ai(stats, language)
    if not result['success']:
        return JsonResponse({'success': False, 'error': result['error']}, status=502)

    record = PCAnalysis.objects.create(
        owner=request.user,
        stats=stats,
        result=result['result'],
        scores=result.get('scores', {}),
        language=language,
    )
    return JsonResponse({
        'success': True,
        'id': record.pk,
        'redirect': f'/pc-check/result/{record.pk}/',
    })


@login_required
def pc_result(request, pk):
    record = get_object_or_404(PCAnalysis, pk=pk, owner=request.user)
    return render(request, 'devices/pc_result.html', {
        'record': record,
        'scores_json': json.dumps(record.scores or {}),
        'stats_json': json.dumps(record.stats or {}),
    })


@login_required
def pc_agent_download(request):
    """Serve the optional native Python agent script."""
    from django.conf import settings
    script_path = settings.BASE_DIR / 'devices' / 'static' / 'agent' / 'iot_pc_agent.py'
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except OSError:
        content = "# Agent script not found."
    resp = HttpResponse(content, content_type='text/x-python')
    resp['Content-Disposition'] = 'attachment; filename="iot_pc_agent.py"'
    return resp

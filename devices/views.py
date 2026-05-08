from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from .models import Device, DeviceMetric, AIAnalysis
from .forms import DeviceForm, MetricForm
from .ai_service import analyze_device_with_ai


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

    context = {
        'devices': devices[:6],
        'total_devices': total_devices,
        'online_count': online_count,
        'error_count': error_count,
        'recent_analyses': recent_analyses,
        'recent_metrics': recent_metrics,
        'status_data': status_data,
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
    context = {
        'devices': devices,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'device_types': Device.DEVICE_TYPES,
        'status_choices': Device.STATUS_CHOICES,
    }
    return render(request, 'devices/device_list.html', context)


@login_required
def device_detail(request, pk):
    device = get_object_or_404(Device, pk=pk, owner=request.user)
    metrics = device.metrics.order_by('-recorded_at')[:20]
    analyses = device.analyses.order_by('-analyzed_at')[:5]

    # Prepare chart data
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
        language = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'en'
        # Also allow override from session
        language = request.session.get('django_language', language)
        if language not in ['en', 'ru', 'uz']:
            language = 'en'

        metrics = list(device.metrics.order_by('-recorded_at')[:15])
        result = analyze_device_with_ai(device, metrics, language)

        if result['success']:
            analysis = AIAnalysis.objects.create(
                device=device,
                prompt_used=result['prompt'],
                result=result['result'],
                anomalies_detected=result['anomalies_detected'],
                language=language,
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
    return render(request, 'devices/analysis_detail.html', {'analysis': analysis})


@login_required
def analysis_list(request):
    analyses = AIAnalysis.objects.filter(device__owner=request.user).order_by('-analyzed_at')
    return render(request, 'devices/analysis_list.html', {'analyses': analyses})
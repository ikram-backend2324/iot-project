from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    DEVICE_TYPES = [
        ('sensor', _('Sensor')),
        ('actuator', _('Actuator')),
        ('gateway', _('Gateway')),
        ('camera', _('Camera')),
        ('controller', _('Controller')),
        ('other', _('Other')),
    ]
    STATUS_CHOICES = [
        ('online', _('Online')),
        ('offline', _('Offline')),
        ('error', _('Error')),
        ('maintenance', _('Maintenance')),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', verbose_name=_('Owner'))
    name = models.CharField(max_length=200, verbose_name=_('Device Name'))
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, default='sensor', verbose_name=_('Device Type'))
    location = models.CharField(max_length=300, blank=True, verbose_name=_('Location'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('IP Address'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline', verbose_name=_('Status'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

    def latest_metrics(self):
        return self.metrics.order_by('-recorded_at')[:10]


class DeviceMetric(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='metrics', verbose_name=_('Device'))
    metric_name = models.CharField(max_length=100, verbose_name=_('Metric Name'))
    value = models.FloatField(verbose_name=_('Value'))
    unit = models.CharField(max_length=50, blank=True, verbose_name=_('Unit'))
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Recorded At'))

    class Meta:
        verbose_name = _('Device Metric')
        verbose_name_plural = _('Device Metrics')
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.device.name} - {self.metric_name}: {self.value} {self.unit}"


class AIAnalysis(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='analyses', verbose_name=_('Device'))
    prompt_used = models.TextField(verbose_name=_('Prompt Used'))
    result = models.TextField(verbose_name=_('Analysis Result'))
    anomalies_detected = models.BooleanField(default=False, verbose_name=_('Anomalies Detected'))
    language = models.CharField(max_length=10, default='en', verbose_name=_('Language'))
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Analyzed At'))

    class Meta:
        verbose_name = _('AI Analysis')
        verbose_name_plural = _('AI Analyses')
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Analysis of {self.device.name} at {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

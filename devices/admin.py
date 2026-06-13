from django.contrib import admin
from .models import Device, DeviceMetric, AIAnalysis


class DeviceMetricInline(admin.TabularInline):
    model = DeviceMetric
    extra = 0
    readonly_fields = ('recorded_at',)


class AIAnalysisInline(admin.StackedInline):
    model = AIAnalysis
    extra = 0
    readonly_fields = ('analyzed_at', 'prompt_used', 'result', 'anomalies_detected', 'language')
    can_delete = False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_type', 'status', 'owner', 'location', 'ip_address', 'created_at')
    list_filter = ('status', 'device_type', 'created_at')
    search_fields = ('name', 'location', 'ip_address', 'owner__username')
    inlines = [DeviceMetricInline, AIAnalysisInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DeviceMetric)
class DeviceMetricAdmin(admin.ModelAdmin):
    list_display = ('device', 'metric_name', 'value', 'unit', 'recorded_at')
    list_filter = ('metric_name', 'recorded_at')
    search_fields = ('device__name', 'metric_name')
    readonly_fields = ('recorded_at',)


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('device', 'anomalies_detected', 'language', 'analyzed_at')
    list_filter = ('anomalies_detected', 'language', 'analyzed_at')
    search_fields = ('device__name',)
    readonly_fields = ('analyzed_at', 'prompt_used', 'result')


from .models import PCAnalysis


@admin.register(PCAnalysis)
class PCAnalysisAdmin(admin.ModelAdmin):
    list_display = ('owner', 'language', 'analyzed_at')
    list_filter = ('language', 'analyzed_at')
    search_fields = ('owner__username',)
    readonly_fields = ('analyzed_at', 'stats', 'result', 'scores')

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Device, DeviceMetric


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': ' '}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': ' '}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': ' '}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' ', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': ' '}))


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ('name', 'device_type', 'location', 'latitude', 'longitude', 'ip_address', 'status', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
            'device_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': ' ', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': ' ', 'step': 'any'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': ' ', 'rows': 3}),
        }


class MetricForm(forms.ModelForm):
    class Meta:
        model = DeviceMetric
        fields = ('metric_name', 'value', 'unit')
        widgets = {
            'metric_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
            'value': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': ' ', 'step': 'any'}),
            'unit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
        }

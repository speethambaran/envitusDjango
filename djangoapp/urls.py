from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('livedata', views.processLiveData, name="processLiveData"),
    path('devices', views.devices, name="devices"),
    path('device/deviceFamily', views.deviceFamily, name="deviceFamily"),
    path('device/device_params', views.addDeviceParams, name="addDeviceParams")
]

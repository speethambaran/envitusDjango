from django.urls import path

from . import views

urlpatterns = [
    path('livedata', views.processLiveData, name="processLiveData"),
    path('adddevices', views.adddevices, name="adddevices"),
    path('getdevice', views.getdevice, name="getdevice"),
    path('device/addDeviceFamily', views.addDeviceFamily, name="addDeviceFamily"),
    path('device/device_params', views.addDeviceParams, name="addDeviceParams"),
    path('sensor/add-sensor', views.addSensor, name="addSensor"),
    path('sensor/getsensor', views.getsensor, name="getsensor"),
    path('device/getDeviceFamily', views.getDeviceFamily, name="getDeviceFamily"),
]

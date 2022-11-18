from django.urls import path

from . import views

urlpatterns = [
    path('sensor/add-sensor', views.addSensor, name="addSensor"),
    path('sensor/getsensor', views.getsensor, name="getsensor"),
    path('sensor/updatesensor', views.updatesensor, name="updatesensor"),
    path('sensor/deletesensor', views.deletesensor, name="deletesensor"),
    path('device/addDeviceFamily', views.addDeviceFamily, name="addDeviceFamily"),
    path('device/getDeviceFamily', views.getDeviceFamily, name="getDeviceFamily"),
    path('adddevices', views.adddevices, name="adddevices"),
    path('device/device_params', views.addDeviceParams, name="addDeviceParams"),
    path('getdevice', views.getdevice, name="getdevice"),
    path('livedata', views.processLiveData, name="processLiveData"),
]

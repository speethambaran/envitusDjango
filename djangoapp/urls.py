from django.urls import path

from . import views

urlpatterns = [
    path('livedata', views.processLiveData, name="processLiveData"),
    path('adddevices', views.adddevices, name="adddevices"),
    path('device/addDeviceFamily', views.addDeviceFamily, name="addDeviceFamily"),
    path('device/device_params', views.addDeviceParams, name="addDeviceParams"),
    path('sensor/add-sensor', views.addSensor, name="addSensor"),
    path('sensor/get-sensor', views.getSensor, name="getSensor"),
    path('device/getdeviceFamily', views.getDeviceFamily, name="getDeviceFamily"),
]

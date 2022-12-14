from django.urls import path

from . import views

urlpatterns = [
    path('sensor/addsensor', views.addsensor, name="addsensor"),
    path('sensor/getsensor', views.getsensor, name="getsensor"),
    path('sensor/updatesensor', views.updatesensor, name="updatesensor"),
    path('sensor/deletesensor', views.deletesensor, name="deletesensor"),
    path('device/adddevicefamily', views.adddevicefamily, name="adddevicefamily"),
    path('device/getdevicefamily', views.getdevicefamily, name="getdevicefamily"),
    path('adddevices', views.adddevices, name="adddevices"),
    path('updatedevice', views.updatedevice, name="updatedevice"),
    path('deletedevice', views.deletedevice, name="deletedevice"),
    path('device/device_params', views.addDeviceParams, name="addDeviceParams"),
    path('getdevice', views.getdevice, name="getdevice"),
    path('livedata', views.processLiveData, name="processLiveData"),
    path('postlivedata', views.postlivedata, name="postlivedata"),
    path('postdevicelivedata', views.postdevicelivedata, name="postdevicelivedata"),
    path('getlivedata', views.getlivedata, name="getlivedata"),
    path('statistics/<str:deviceId>', views.dashboardStatistics, name="dashboardStatistics"),
    path('device/sensor/stats', views.fetchSensorData, name="fetchSensorData"),
]

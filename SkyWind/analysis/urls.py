from django.urls import path
from . import views
from .views import zones_geojson, zones_geojson_detailed, region_center

urlpatterns = [
    path('api/points/', views.points_list, name='points_list'),
    path('api/zones-geojson/', zones_geojson, name='zones_geojson'),
    path('api/region-center/', region_center, name='region_center'),
    path('api/zones-geojson-detailed/', zones_geojson_detailed, name='zones_geojson_detailed'),
]
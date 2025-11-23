from django.urls import path
from .views import *

urlpatterns = [
    # REGION
    path("regions/<int:region_id>/", get_region_details),
    path("regions/<int:region_id>/zones/", get_region_zones),
    path("regions/compute/", compute_region),


    # ZONE
    path("zones/<int:zone_id>/", get_zone_details),
]

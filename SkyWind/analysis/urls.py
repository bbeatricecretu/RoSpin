from django.urls import path
from . import views

urlpatterns = [
    # REGION
    path("regions/<int:region_id>/", views.get_region_details),
    path("regions/<int:region_id>/zones/", views.get_region_zones),
    path("regions/compute/", views.compute_region),

    # ZONE
    path("zones/<int:zone_id>/", views.get_zone_details),

    # ZONE POWERS BY TURBINE
    path(
        "regions/<int:region_id>/zone-powers/",
        views.get_region_zone_powers,
        name="region_zone_powers",
    ),
    path("regions/<int:region_id>/water/", views.get_water),

    path("regions/<int:region_id>/grid/", views.get_region_grid),

]

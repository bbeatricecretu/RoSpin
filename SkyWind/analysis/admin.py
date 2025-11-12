from django.contrib import admin
from .models import Region, Zone, Point, Infrastructure, EnergyStorage

admin.site.register(Region)
admin.site.register(Zone)
admin.site.register(Point)
admin.site.register(Infrastructure)
admin.site.register(EnergyStorage)

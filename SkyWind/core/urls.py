from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # All analysis APIs:
    path('api/', include('analysis.urls')),
]

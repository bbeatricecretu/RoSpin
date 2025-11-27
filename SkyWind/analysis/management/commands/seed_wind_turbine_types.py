from django.core.management.base import BaseCommand

from analysis.models import WindTurbineType


class Command(BaseCommand):
    help = "Seed the database with reference data for wind turbine types."

    def handle(self, *args, **options):
        data = [
            {
                "type_name": "Small Wind Turbine",
                "category": WindTurbineType.CATEGORY_ONSHORE,
                "rotor_diameter_min_m": 1.0,
                "rotor_diameter_max_m": 10.0,
                "swept_area_min_m2": 1.0,
                "swept_area_max_m2": 80.0,
                "rated_power_min_kw": 1.0,
                "rated_power_max_kw": 20.0,
            },
            {
                "type_name": "Utility-Scale Onshore Turbine",
                "category": WindTurbineType.CATEGORY_ONSHORE,
                "rotor_diameter_min_m": 70.0,
                "rotor_diameter_max_m": 150.0,
                "swept_area_min_m2": 4000.0,
                "swept_area_max_m2": 18000.0,
                "rated_power_min_kw": 1000.0,
                "rated_power_max_kw": 6000.0,
            },
            {
                "type_name": "Utility-Scale Offshore Turbine",
                "category": WindTurbineType.CATEGORY_OFFSHORE,
                "rotor_diameter_min_m": 150.0,
                "rotor_diameter_max_m": 240.0,
                "swept_area_min_m2": 18000.0,
                "swept_area_max_m2": 45000.0,
                "rated_power_min_kw": 8000.0,
                "rated_power_max_kw": 18000.0,
            },
        ]

        for item in data:
            obj, created = WindTurbineType.objects.update_or_create(
                type_name=item["type_name"],
                defaults=item,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {obj}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Updated {obj}"))
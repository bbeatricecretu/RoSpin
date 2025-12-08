# Generated migration for land_type CharField -> JSONField

from django.db import migrations, models
import json


def convert_land_type_to_dict(apps, schema_editor):
    """Convert existing string land_type values to dict format"""
    Zone = apps.get_model('analysis', 'Zone')
    
    for zone in Zone.objects.all():
        if zone.land_type and isinstance(zone.land_type, str):
            # Convert "Tree cover, Grassland" to {"Tree cover": 50.0, "Grassland": 50.0}
            if zone.land_type.strip():
                land_types = [lt.strip() for lt in zone.land_type.split(',')]
                # Give equal percentage to each type for simplicity
                percentage = round(100.0 / len(land_types), 1) if land_types else 0
                zone.land_type = json.dumps({lt: percentage for lt in land_types if lt})
            else:
                zone.land_type = json.dumps({})
        else:
            zone.land_type = json.dumps({})
        zone.save()


def reverse_land_type_to_string(apps, schema_editor):
    """Reverse: Convert dict land_type values back to string format"""
    Zone = apps.get_model('analysis', 'Zone')
    
    for zone in Zone.objects.all():
        if zone.land_type:
            try:
                land_dict = json.loads(zone.land_type) if isinstance(zone.land_type, str) else zone.land_type
                if land_dict:
                    zone.land_type = ', '.join(land_dict.keys())
                else:
                    zone.land_type = ''
            except:
                zone.land_type = ''
        else:
            zone.land_type = ''
        zone.save()


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        # Step 1: Convert existing string data to JSON strings (still in CharField)
        migrations.RunPython(convert_land_type_to_dict, reverse_land_type_to_string),
        
        # Step 2: Change field type to JSONField
        migrations.AlterField(
            model_name='zone',
            name='land_type',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

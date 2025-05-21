from django.db import migrations

def clean_duplicates(apps, schema_editor):
    DataPraktikum = apps.get_model('mylabapp', 'DataPraktikum')
    from django.db.models import Min
    
    # Dapatkan semua kode yang duplikat
    duplicate_codes = DataPraktikum.objects.values('kode').annotate(
        min_id=Min('id')
    ).values('kode', 'min_id')
    
    # Hapus semua record kecuali yang memiliki ID terkecil untuk setiap kode
    for item in duplicate_codes:
        DataPraktikum.objects.filter(kode=item['kode']).exclude(id=item['min_id']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('mylabapp', '0002_alter_datapraktikum_options_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_duplicates),
    ] 
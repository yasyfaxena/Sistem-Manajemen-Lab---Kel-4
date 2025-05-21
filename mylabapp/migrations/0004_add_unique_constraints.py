from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('mylabapp', '0003_clean_datapraktikum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datapraktikum',
            name='kode',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='datapraktikum',
            unique_together={('kode', 'nama')},
        ),
    ] 
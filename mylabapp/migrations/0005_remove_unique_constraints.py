from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('mylabapp', '0004_add_unique_constraints'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='datapraktikum',
            unique_together=set(),
        ),
    ] 
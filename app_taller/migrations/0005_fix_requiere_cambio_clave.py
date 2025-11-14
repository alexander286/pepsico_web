from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app_taller", "0004_ordentrabajo_total_mano_obra_ordentrabajo_total_ot"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="requiere_cambio_clave",
            field=models.BooleanField(default=False),
        ),
    ]

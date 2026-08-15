from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_auto_20231208_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='uid',
            field=models.BigIntegerField(blank=True, help_text='VNC用户UID', null=True),
        ),
    ]
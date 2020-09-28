# Generated by Django 3.1.1 on 2020-09-28 10:43

import datetime
from django.db import migrations, models
from django.utils.timezone import utc
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0013_auto_20200928_1042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='expire_time',
            field=models.DateTimeField(default=datetime.datetime(2020, 9, 28, 10, 43, 54, 681968, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='voter',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True),
        ),
        migrations.AlterField(
            model_name='voter',
            name='uuid',
            field=models.CharField(default='71b4be62', editable=False, max_length=64),
        ),
    ]

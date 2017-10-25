# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-24 17:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0030_formquestion_meta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formquestion',
            name='type',
            field=models.TextField(choices=[('checkbox', 'checkbox'), ('radiobutton', 'radiobutton'), ('singlelinetext', 'singlelinetext'), ('textarea', 'textarea')], default='singlelinetext', null=True),
        ),
    ]

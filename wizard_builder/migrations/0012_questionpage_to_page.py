# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-02 22:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0011_rename_questionpage_attrs'),
    ]

    operations = [
        migrations.RenameModel('QuestionPage', 'Page'),
        migrations.RenameField('FormQuestion', 'page_id', 'pagebase_id'),
    ]

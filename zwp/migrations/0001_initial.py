# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadBatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('key', models.CharField(verbose_name='unique key', unique=True, max_length=40)),
                ('created_at', models.DateTimeField(verbose_name='created at', auto_now_add=True)),
                ('updated_at', models.DateTimeField(verbose_name='updated at', null=True)),
                ('state', models.IntegerField(verbose_name='state', default=0)),
                ('zip_file', models.CharField(verbose_name='zip file', max_length=255, null=True)),
                ('user', models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='PartDownload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('added_at', models.DateTimeField(verbose_name='added at', auto_now_add=True)),
                ('download_batch', models.ForeignKey(to='zwp.DownloadBatch', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='PartModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('ds_name', models.CharField(verbose_name='data source', max_length=50)),
                ('dir_path', models.CharField(verbose_name='directory', max_length=500)),
                ('name', models.CharField(verbose_name='part', max_length=255)),
                ('hash', models.CharField(verbose_name='hash', unique=True, max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='partdownload',
            name='part_model',
            field=models.ForeignKey(to='zwp.PartModel', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='partdownload',
            unique_together=set([('download_batch', 'part_model')]),
        ),
    ]

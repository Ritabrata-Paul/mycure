# Generated by Django 5.2.1 on 2025-05-09 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('total_users', models.IntegerField(default=0)),
                ('total_authorities', models.IntegerField(default=0)),
                ('total_appointments', models.IntegerField(default=0)),
                ('authorities_verified', models.IntegerField(default=0)),
                ('authorities_pending', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Admin Metric',
                'verbose_name_plural': 'Admin Metrics',
                'db_table': 'admin_metrics',
            },
        ),
    ]

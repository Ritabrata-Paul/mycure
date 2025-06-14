# Generated by Django 5.2.1 on 2025-05-09 10:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authorities', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField()),
                ('appointment_time', models.TimeField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=10)),
                ('notes', models.TextField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('authority', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='authorities.authority')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='authorities.doctor')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='authorities.service')),
                ('time_slot', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to='authorities.timeslot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Appointment',
                'verbose_name_plural': 'Appointments',
                'db_table': 'appointments',
                'ordering': ['-appointment_date', '-appointment_time'],
            },
        ),
        migrations.CreateModel(
            name='AppointmentSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('is_available', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='booked_slot', to='appointments.appointment')),
                ('time_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booked_slots', to='authorities.timeslot')),
            ],
            options={
                'verbose_name': 'Appointment Slot',
                'verbose_name_plural': 'Appointment Slots',
                'db_table': 'appointment_slots',
                'unique_together': {('time_slot', 'date')},
            },
        ),
    ]

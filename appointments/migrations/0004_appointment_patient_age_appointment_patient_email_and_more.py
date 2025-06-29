# Generated by Django 5.2.1 on 2025-06-06 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_alter_appointment_authority_alter_appointment_doctor_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='patient_age',
            field=models.PositiveIntegerField(default=25),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient_email',
            field=models.EmailField(default='unknown@example.com', max_length=254),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient_gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='M', max_length=1),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient_name',
            field=models.CharField(default='Unknown Patient', max_length=100),
        ),
        migrations.AddField(
            model_name='appointment',
            name='patient_phone',
            field=models.CharField(default='0000000000', max_length=15),
        ),
    ]

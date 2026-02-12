from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("age", models.PositiveSmallIntegerField()),
                ("country", models.CharField(max_length=64)),
                ("city", models.CharField(max_length=128)),
                ("account_age_days", models.PositiveIntegerField()),
                ("purchases_last_12_months", models.PositiveIntegerField()),
                ("canceled_orders", models.PositiveIntegerField()),
                ("tickets_per_order_avg", models.FloatField()),
                ("distance_to_venue_km", models.FloatField()),
                ("payment_failures_ratio", models.FloatField()),
                ("event_affinity_score", models.FloatField()),
                ("night_purchase_ratio", models.FloatField()),
                ("resale_reports_count", models.PositiveIntegerField()),
                ("attendance_rate", models.FloatField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Prediction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attendance_probability", models.FloatField()),
                ("reseller_probability", models.FloatField()),
                ("risk_label", models.CharField(max_length=32)),
                ("model_version", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="predictions", to="scoring.userprofile"),
                ),
            ],
        ),
    ]

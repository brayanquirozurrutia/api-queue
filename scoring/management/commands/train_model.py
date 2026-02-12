from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler



class Command(BaseCommand):
    help = "Train attendance scoring model with mock data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--size",
            type=int,
            default=120000,
            help="Number of mock records used for training.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducible datasets.",
        )

    def handle(self, *args, **kwargs):
        size = kwargs["size"]
        seed = kwargs["seed"]

        if size < 1000:
            raise CommandError("--size must be at least 1000")

        rng = np.random.default_rng(seed)

        data = pd.DataFrame(
            {
                "age": rng.integers(16, 75, size),
                "country": rng.choice(
                    ["CL", "AR", "PE", "MX", "CO", "UY", "EC", "BR", "US", "ES"],
                    size=size,
                    p=[0.2, 0.15, 0.12, 0.16, 0.12, 0.05, 0.06, 0.06, 0.04, 0.04],
                ),
                "city": rng.choice(
                    [
                        "Santiago",
                        "Valparaiso",
                        "Lima",
                        "Bogota",
                        "Medellin",
                        "CDMX",
                        "Monterrey",
                        "BuenosAires",
                        "Cordoba",
                        "Montevideo",
                        "Quito",
                        "SaoPaulo",
                        "Miami",
                        "Madrid",
                    ],
                    size=size,
                ),
                "account_age_days": rng.integers(1, 3650, size),
                "purchases_last_12_months": rng.poisson(6, size),
                "canceled_orders": rng.poisson(1.2, size),
                "tickets_per_order_avg": rng.uniform(1, 6, size),
                "distance_to_venue_km": rng.uniform(0.2, 400, size),
                "payment_failures_ratio": rng.uniform(0, 0.35, size),
                "event_affinity_score": rng.uniform(0, 1, size),
                "night_purchase_ratio": rng.uniform(0, 1, size),
                "resale_reports_count": rng.poisson(0.8, size),
                "attendance_rate": rng.uniform(0, 1, size),
            }
        )

        trusted_segment = rng.random(size) < 0.3
        risky_segment = rng.random(size) < 0.15

        data.loc[trusted_segment, "account_age_days"] = rng.integers(900, 3650, trusted_segment.sum())
        data.loc[trusted_segment, "attendance_rate"] = rng.uniform(0.65, 1, trusted_segment.sum())
        data.loc[trusted_segment, "event_affinity_score"] = rng.uniform(0.6, 1, trusted_segment.sum())
        data.loc[trusted_segment, "payment_failures_ratio"] = rng.uniform(0, 0.08, trusted_segment.sum())

        data.loc[risky_segment, "tickets_per_order_avg"] = rng.uniform(3.2, 8.5, risky_segment.sum())
        data.loc[risky_segment, "night_purchase_ratio"] = rng.uniform(0.45, 1, risky_segment.sum())
        data.loc[risky_segment, "resale_reports_count"] = rng.poisson(3.3, risky_segment.sum())
        data.loc[risky_segment, "payment_failures_ratio"] = rng.uniform(0.12, 0.55, risky_segment.sum())
        data.loc[risky_segment, "attendance_rate"] = rng.uniform(0, 0.45, risky_segment.sum())

        risk_index = (
            (data["tickets_per_order_avg"] - 1.8) * 0.30
            + data["payment_failures_ratio"] * 2.3
            + data["night_purchase_ratio"] * 0.85
            + data["resale_reports_count"] * 0.35
            - data["event_affinity_score"] * 1.7
            - data["attendance_rate"] * 2.1
            - np.log1p(data["account_age_days"]) * 0.12
        )

        probability = 1 / (1 + np.exp(risk_index))
        labels = rng.binomial(1, probability)

        numeric_features = [
            "age",
            "account_age_days",
            "purchases_last_12_months",
            "canceled_orders",
            "tickets_per_order_avg",
            "distance_to_venue_km",
            "payment_failures_ratio",
            "event_affinity_score",
            "night_purchase_ratio",
            "resale_reports_count",
            "attendance_rate",
        ]
        categorical_features = ["country", "city"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("numeric", StandardScaler(), numeric_features),
                ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ]
        )

        model = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=16,
                        min_samples_leaf=3,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

        x_train, x_test, y_train, y_test = train_test_split(
            data,
            labels,
            test_size=0.2,
            random_state=42,
            stratify=labels,
        )

        model.fit(x_train, y_train)
        score = model.score(x_test, y_test)

        settings.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, settings.MODEL_PATH)

        self.stdout.write(self.style.SUCCESS(f"Model trained. Validation accuracy={score:.4f}"))
        self.stdout.write(self.style.SUCCESS(f"Saved at {settings.MODEL_PATH}"))
        self.stdout.write(self.style.SUCCESS(f"Training records generated: {size}"))

"""
Management Command: Train AI models from Kaggle Resume Dataset.

Usage:
    python manage.py train_from_kaggle
    python manage.py train_from_kaggle --csv path/to/file.csv
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train XGBoost, Random Forest, and Logistic Regression from Kaggle Resume Dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=None,
            help='Path to the Kaggle CSV file (default: ml_models/kaggle_data/UpdatedResumeDataSet.csv)',
        )

    def handle(self, *args, **options):
        from ml_models.kaggle_trainer import train_all_models

        csv_path = options.get('csv')
        results = train_all_models(csv_path)

        if 'error' in results:
            self.stderr.write(self.style.ERROR(results['error']))
            return

        self.stdout.write('\n')
        for model_name, result in results.items():
            if 'error' in result:
                self.stdout.write(self.style.ERROR(f'  ❌ {model_name}: {result["error"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ {model_name}: Accuracy={result.get("accuracy", 0):.1f}%'
                ))

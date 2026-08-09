"""
Management command: train_ml_models
====================================
Train 5 ML classifiers on the Kaggle resume dataset from the terminal.

Usage:
    python manage.py train_ml_models
    python manage.py train_ml_models --csv path/to/custom.csv
"""
import time
import uuid
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train 5 ML models (LR, RF, SVM, XGBoost, NB) on the Kaggle resume dataset'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, default=None, help='Path to a custom CSV file')
        parser.add_argument('--no-db', action='store_true', help='Skip loading DB resumes')

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('  🤖  ML MODEL TRAINING PIPELINE'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))

        csv_path = options.get('csv')
        include_db = not options.get('no_db', False)

        # ── Step 1: Build Dataset ──────────────────────────────────
        self.stdout.write('📁 Step 1/4: Loading dataset...')
        start_total = time.time()

        from ml.dataset_builder import build_training_dataset
        try:
            df = build_training_dataset(csv_path=csv_path, include_db=include_db)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  ❌ Failed to load dataset: {e}'))
            return

        dataset_size = len(df)
        n_categories = df['category'].nunique()
        self.stdout.write(self.style.SUCCESS(f'  ✅ Loaded {dataset_size} resumes across {n_categories} categories'))
        self.stdout.write(f'  Top categories:')
        for cat, count in df['category'].value_counts().head(5).items():
            self.stdout.write(f'    • {cat}: {count}')
        self.stdout.write('')

        if dataset_size < 10:
            self.stderr.write(self.style.ERROR(f'  ❌ Not enough data. Need at least 10, found {dataset_size}.'))
            return

        # ── Step 2: Feature Engineering ────────────────────────────
        self.stdout.write('🔧 Step 2/4: TF-IDF Vectorization...')

        from ml.feature_engineering import build_tfidf_features
        X, vectorizer = build_tfidf_features(df['text'].tolist(), fit=True)
        y = df['category'].values

        self.stdout.write(self.style.SUCCESS(f'  ✅ Feature matrix: {X.shape[0]} samples × {X.shape[1]} features\n'))

        # ── Step 3: Train Models ───────────────────────────────────
        self.stdout.write('🏋 Step 3/4: Training 5 models...')
        self.stdout.write('  ' + '-'*50)

        from ml.model_trainer import train_all_models
        results = train_all_models(X, y)

        for r in results:
            if r.get('error'):
                self.stdout.write(self.style.ERROR(f'  ❌ {r["model_name"]}: FAILED — {r["error"]}'))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ {r["model_name"]:.<30} {r["training_time"]:.1f}s  '
                    f'CV Acc: {r.get("cv_accuracy", 0):.4f}'
                ))
        self.stdout.write('  ' + '-'*50 + '\n')

        # ── Step 4: Evaluate & Save ───────────────────────────────
        self.stdout.write('📊 Step 4/4: Evaluating models...')

        from ml.model_evaluator import evaluate_all
        metrics, best_name = evaluate_all(results)

        from recruiter.models import ModelTrainingReport

        # Clear old best flags
        ModelTrainingReport.objects.filter(is_best=True).update(is_best=False)

        session_id = uuid.uuid4().hex[:8]

        for m in metrics:
            ModelTrainingReport.objects.create(
                model_name=m['model_name'],
                training_dataset_size=dataset_size,
                accuracy=m['accuracy'],
                precision=m['precision'],
                recall=m['recall'],
                f1_score=m['f1_score'],
                roc_auc=m['roc_auc'],
                cv_accuracy=m.get('cv_accuracy', 0),
                confusion_matrix=m['confusion_matrix'],
                training_time=m['training_time'],
                is_best=(m['model_name'] == best_name),
                model_file_path=m.get('model_path', ''),
                training_session=session_id,
            )

        total_time = time.time() - start_total

        # ── Final Report ──────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(self.style.WARNING('  📊  TRAINING RESULTS'))
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write('')
        self.stdout.write(f'  {"Model":<28} {"Acc":>7} {"Prec":>7} {"Rec":>7} {"F1":>7} {"AUC":>7}')
        self.stdout.write('  ' + '-'*67)

        for m in metrics:
            marker = ' 🏆' if m['model_name'] == best_name else '   '
            line = (
                f'  {m["model_name"]:<28} '
                f'{m["accuracy"]:>6.2%} '
                f'{m["precision"]:>6.2%} '
                f'{m["recall"]:>6.2%} '
                f'{m["f1_score"]:>6.2%} '
                f'{m["roc_auc"]:>6.2%}'
                f'{marker}'
            )
            if m['model_name'] == best_name:
                self.stdout.write(self.style.SUCCESS(line))
            else:
                self.stdout.write(line)

        self.stdout.write('  ' + '-'*67)
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  🏆 Best Model: {best_name}'))
        self.stdout.write(f'  📦 Dataset Size: {dataset_size}')
        self.stdout.write(f'  ⏱  Total Time: {total_time:.1f}s')
        self.stdout.write(f'  💾 Session ID: {session_id}')
        self.stdout.write(f'  📂 Models saved to: ml/trained/')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('  ✅ All models trained and saved to database!\n'))

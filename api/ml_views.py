"""
ML Training API Views
=====================
Recruiter-only endpoints for manual model training and report viewing.
"""
import uuid
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def _check_recruiter(request):
    """Returns True if user is a recruiter, else False."""
    try:
        return request.user.profile.is_recruiter
    except Exception:
        return False


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_model(request):
    """POST /api/recruiter/train-model/ — Trigger full training pipeline."""
    if not _check_recruiter(request):
        return Response({"error": "Recruiter access only."}, status=403)

    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')

        from ml.dataset_builder import build_training_dataset
        from ml.feature_engineering import build_tfidf_features
        from ml.model_trainer import train_all_models
        from ml.model_evaluator import evaluate_all
        from recruiter.models import ModelTrainingReport

        # 1. Build dataset
        df = build_training_dataset()
        dataset_size = len(df)

        if dataset_size < 10:
            return Response({"error": f"Not enough data to train. Found {dataset_size} samples, need at least 10."}, status=400)

        # 2. Feature engineering
        X, vectorizer = build_tfidf_features(df['text'].tolist(), fit=True)
        y = df['category'].values

        # 3. Train models
        results = train_all_models(X, y)

        # 4. Evaluate
        metrics, best_name = evaluate_all(results)

        # 5. Save to DB
        session_id = uuid.uuid4().hex[:8]

        # Clear old best flags
        ModelTrainingReport.objects.filter(is_best=True).update(is_best=False)

        saved_reports = []
        for m in metrics:
            report = ModelTrainingReport.objects.create(
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
            saved_reports.append({
                'id': report.id,
                'model_name': report.model_name,
                'accuracy': report.accuracy,
                'f1_score': report.f1_score,
                'is_best': report.is_best,
            })

        return Response({
            "status": "training_complete",
            "session_id": session_id,
            "dataset_size": dataset_size,
            "models_trained": len(saved_reports),
            "best_model": best_name,
            "reports": saved_reports,
        })

    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=400)
    except Exception as e:
        logger.exception("Model training failed")
        return Response({"error": f"Training failed: {str(e)}"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_reports(request):
    """GET /api/recruiter/model-reports/ — List all training reports."""
    if not _check_recruiter(request):
        return Response({"error": "Recruiter access only."}, status=403)

    from recruiter.models import ModelTrainingReport

    reports = ModelTrainingReport.objects.all()
    data = [{
        'id': r.id,
        'model_name': r.model_name,
        'dataset_size': r.training_dataset_size,
        'accuracy': r.accuracy,
        'precision': r.precision,
        'recall': r.recall,
        'f1_score': r.f1_score,
        'roc_auc': r.roc_auc,
        'cv_accuracy': r.cv_accuracy,
        'training_time': r.training_time,
        'is_best': r.is_best,
        'session': r.training_session,
        'created_at': r.created_at.isoformat(),
    } for r in reports]

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_report_detail(request, pk):
    """GET /api/recruiter/model-reports/<id>/ — Single report detail."""
    if not _check_recruiter(request):
        return Response({"error": "Recruiter access only."}, status=403)

    from recruiter.models import ModelTrainingReport
    try:
        r = ModelTrainingReport.objects.get(pk=pk)
    except ModelTrainingReport.DoesNotExist:
        return Response({"error": "Report not found."}, status=404)

    return Response({
        'id': r.id,
        'model_name': r.model_name,
        'dataset_size': r.training_dataset_size,
        'accuracy': r.accuracy,
        'precision': r.precision,
        'recall': r.recall,
        'f1_score': r.f1_score,
        'roc_auc': r.roc_auc,
        'cv_accuracy': r.cv_accuracy,
        'confusion_matrix': r.confusion_matrix,
        'training_time': r.training_time,
        'is_best': r.is_best,
        'model_file_path': r.model_file_path,
        'session': r.training_session,
        'created_at': r.created_at.isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def best_model(request):
    """GET /api/recruiter/best-model/ — Return the current best model metrics."""
    if not _check_recruiter(request):
        return Response({"error": "Recruiter access only."}, status=403)

    from recruiter.models import ModelTrainingReport
    best = ModelTrainingReport.objects.filter(is_best=True).first()
    if not best:
        return Response({"error": "No best model found. Train models first."}, status=404)

    return Response({
        'best_model': best.model_name,
        'accuracy': best.accuracy,
        'precision': best.precision,
        'recall': best.recall,
        'f1_score': best.f1_score,
        'roc_auc': best.roc_auc,
        'dataset_size': best.training_dataset_size,
        'trained_at': best.created_at.isoformat(),
    })

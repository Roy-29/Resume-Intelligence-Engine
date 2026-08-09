from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import JobPosting, JobApplication, MLModelVersion
from .tasks import train_ml_model_async
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_analytics(request):
    """GET /api/analytics/ — Data for CEO charts."""
    total_jobs = JobPosting.objects.count()
    total_apps = JobApplication.objects.count()
    hired_count = JobApplication.objects.filter(status='hired').count()
    fill_rate = (hired_count / total_jobs * 100) if total_jobs > 0 else 0
    
    return Response({
        'total_jobs': total_jobs,
        'total_applicants': total_apps,
        'fill_rate_percentage': fill_rate,
        # Real implementation would aggregate real data for these:
        'top_skills_demand': {'Python': 85, 'React': 70, 'Machine Learning': 90},
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_train_model(request):
    """POST /api/train-model/ — Triggers background ML training (Admin only)."""
    task = train_ml_model_async.delay()
    return Response({
        'message': 'ML Training pipeline started asynchronously.',
        'task_id': task.id
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_model_metrics(request):
    """GET /api/model-metrics/ — Fetch current active model performance."""
    active_model = MLModelVersion.objects.filter(is_active=True).first()
    if not active_model:
        return Response({'message': 'No active model found'}, status=404)
        
    return Response({
        'version_id': active_model.version_id,
        'trained_at': active_model.trained_at,
        'accuracy': active_model.accuracy,
        'roc_auc': active_model.roc_auc,
        'confusion_matrix': active_model.confusion_matrix_json
    })

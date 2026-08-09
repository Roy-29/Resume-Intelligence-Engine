from celery import shared_task
from .models import JobApplication
from .ml_pipeline import train_selection_model
import logging

logger = logging.getLogger(__name__)

@shared_task
def train_ml_model_async():
    """
    Background task to retrain the XGBoost selection model based on latest data.
    """
    applications = JobApplication.objects.all()
    result = train_selection_model(applications)
    return result

@shared_task
def async_retrain_model(csv_path: str):
    """
    Background Celery task to retrain the ML model from Kaggle dataset.
    Prevents the recruiter dashboard from freezing during long training cycles.
    """
    from ml_models.kaggle_trainer import train_all_models
    
    logger.info(f"Starting background ML retraining using dataset: {csv_path}")
    
    try:
        results = train_all_models(csv_path)
        if 'error' in results:
            logger.error(f"Background ML retraining failed: {results['error']}")
        else:
            successes = [k for k, v in results.items() if 'error' not in v]
            logger.info(f"Successfully trained {len(successes)} model(s): {', '.join(successes)}")
            
    except Exception as e:
        logger.error(f"Critical error in background ML retraining: {str(e)}")

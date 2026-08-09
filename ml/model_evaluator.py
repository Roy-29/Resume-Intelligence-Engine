"""
Model Evaluator
===============
Computes detailed metrics for each trained model.
"""
import numpy as np
import logging
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix
)

logger = logging.getLogger(__name__)


def evaluate_model(result_dict):
    """
    Evaluate a single trained model and return metrics dict.
    
    Args:
        result_dict: one item from model_trainer.train_all_models() output
    
    Returns:
        dict with accuracy, precision, recall, f1_score, roc_auc, confusion_matrix
    """
    if result_dict.get('error') or result_dict.get('model') is None:
        return {
            'model_name': result_dict['model_name'],
            'accuracy': 0, 'precision': 0, 'recall': 0,
            'f1_score': 0, 'roc_auc': 0,
            'confusion_matrix': [],
            'training_time': 0,
            'error': result_dict.get('error', 'Training failed'),
        }

    y_test = result_dict['y_test']
    y_pred = result_dict['y_pred']
    model = result_dict['model']

    # Determine averaging strategy
    n_classes = len(np.unique(y_test))
    avg = 'binary' if n_classes == 2 else 'weighted'

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average=avg, zero_division=0)
    rec = recall_score(y_test, y_pred, average=avg, zero_division=0)
    f1 = f1_score(y_test, y_pred, average=avg, zero_division=0)

    # ROC AUC — only works for binary or if model has predict_proba
    roc = 0.0
    try:
        from sklearn.metrics import roc_auc_score
        # Handle dense requirement for Hist Gradient Boosting
        X_test_eval = result_dict['X_test']
        if result_dict['model_name'] == 'Hist Gradient Boosting':
            X_test_eval = X_test_eval.toarray() if hasattr(X_test_eval, 'toarray') else X_test_eval

        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test_eval)
            if n_classes == 2:
                roc = roc_auc_score(y_test, y_proba[:, 1])
            else:
                roc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
        elif hasattr(model, 'decision_function'):
            y_dec = model.decision_function(X_test_eval)
            if n_classes == 2:
                roc = roc_auc_score(y_test, y_dec)
            else:
                roc = roc_auc_score(y_test, y_dec, multi_class='ovr', average='weighted')
    except Exception as e:
        logger.warning(f"ROC AUC calculation failed for {result_dict['model_name']}: {e}")

    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        'model_name': result_dict['model_name'],
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'roc_auc': round(roc, 4),
        'confusion_matrix': cm,
        'training_time': result_dict['training_time'],
        'cv_accuracy': result_dict.get('cv_accuracy', 0),
        'model_path': result_dict.get('model_path', ''),
    }


def evaluate_all(results_list):
    """
    Evaluate all trained models and identify the best one.
    Returns: (list_of_metrics, best_model_name)
    """
    metrics = []
    for r in results_list:
        m = evaluate_model(r)
        metrics.append(m)

    # Find best by F1 score
    valid = [m for m in metrics if m['f1_score'] > 0]
    if valid:
        best = max(valid, key=lambda x: x['f1_score'])
        best_name = best['model_name']
    else:
        best_name = None

    return metrics, best_name

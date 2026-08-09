"""
Model Trainer
=============
Trains 5 classifiers on TF-IDF resume features.
"""
import os
import time
import joblib
import logging
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import RandomizedSearchCV
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

TRAINED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained')
os.makedirs(TRAINED_DIR, exist_ok=True)

# Model definitions
MODEL_CONFIGS = {
    'Logistic Regression': lambda: LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs'),
    'Random Forest': lambda: RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42),
    'Support Vector Machine': lambda: CalibratedClassifierCV(LinearSVC(max_iter=2000, C=1.0, random_state=42)),
    'XGBoost': lambda: _get_xgboost(),
    'Naive Bayes': lambda: MultinomialNB(alpha=1.0),
    'Neural Network (MLP)': lambda: MLPClassifier(hidden_layer_sizes=(50,), max_iter=30, early_stopping=True, random_state=42),
    'Hist Gradient Boosting': lambda: HistGradientBoostingClassifier(max_iter=200, random_state=42),
    'K-Nearest Neighbors': lambda: KNeighborsClassifier(n_neighbors=5, n_jobs=-1)
}


def _get_xgboost():
    """Lazy import XGBoost to avoid hard dependency."""
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric='mlogloss',
            random_state=42,
        )
    except ImportError:
        logger.warning("XGBoost not installed, falling back to GradientBoosting")
        from sklearn.ensemble import GradientBoostingClassifier
        return GradientBoostingClassifier(n_estimators=200, max_depth=6, random_state=42)


def train_all_models(X, y, test_size=0.2):
    """
    Train all 5 models on the given features and labels.
    
    Args:
        X: TF-IDF sparse matrix
        y: array of category labels (strings)
        test_size: fraction for test split
    
    Returns:
        list of dicts with keys:
            model_name, model, accuracy, training_time, 
            X_test, y_test, y_pred, label_encoder, model_path
    """
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    le_path = os.path.join(TRAINED_DIR, 'label_encoder.joblib')
    joblib.dump(le, le_path)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
    )

    # SMOTE Data Augmentation / Balancing
    try:
        from imblearn.over_sampling import SMOTE
        logger.info("Applying SMOTE to balance the dataset...")
        # Determine the minimum class count to set k_neighbors dynamically safely
        from collections import Counter
        class_counts = Counter(y_train)
        min_class_count = min(class_counts.values())
        k_neighbors = min(3, min_class_count - 1) if min_class_count > 1 else 1

        if min_class_count <= 1:
            logger.warning("A class has 1 or fewer samples; SMOTE might skip those or fail. Proceeding with caution.")

        smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        logger.info(f"Dataset Balanced. New training shape: {X_train.shape}")
    except ImportError:
        logger.warning("imbalanced-learn not installed. Skipping SMOTE.")
    except Exception as e:
        logger.warning(f"SMOTE failed (possibly due to small class size). Proceeding without it: {e}")

    results = []

    for model_name, model_factory in MODEL_CONFIGS.items():
        logger.info(f"Training {model_name}...")
        try:
            model = model_factory()
            
            start = time.time()
            
            if model_name == 'Hist Gradient Boosting':
                # Convert sparse to dense for HistGradientBoosting
                X_train_dense = X_train.toarray() if hasattr(X_train, 'toarray') else X_train
                model.fit(X_train_dense, y_train)
            else:
                model.fit(X_train, y_train)
            
            training_time = time.time() - start

            # Predict
            if model_name == 'Hist Gradient Boosting':
                X_test_dense = X_test.toarray() if hasattr(X_test, 'toarray') else X_test
                y_pred = model.predict(X_test_dense)
            else:
                y_pred = model.predict(X_test)

            # Cross-validation (use 3-fold for speed on large datasets)
            try:
                cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='accuracy', n_jobs=-1)
                cv_mean = float(cv_scores.mean())
            except Exception:
                cv_mean = 0.0

            # Save model
            safe_name = model_name.lower().replace(' ', '_')
            model_path = os.path.join(TRAINED_DIR, f'{safe_name}.joblib')
            joblib.dump(model, model_path)

            results.append({
                'model_name': model_name,
                'model': model,
                'training_time': round(training_time, 2),
                'X_test': X_test,
                'y_test': y_test,
                'y_pred': y_pred,
                'label_encoder': le,
                'model_path': model_path,
                'cv_accuracy': round(cv_mean, 4),
            })

            logger.info(f"  {model_name} trained in {training_time:.2f}s — CV Accuracy: {cv_mean:.4f}")

        except Exception as e:
            logger.error(f"  Failed to train {model_name}: {e}")
            results.append({
                'model_name': model_name,
                'model': None,
                'training_time': 0,
                'error': str(e),
            })

    return results

from django.urls import path
from . import api_views

urlpatterns = [
    path('analytics/', api_views.api_analytics, name='api_analytics'),
    path('train-model/', api_views.api_train_model, name='api_train_model'),
    path('model-metrics/', api_views.api_model_metrics, name='api_model_metrics'),
]

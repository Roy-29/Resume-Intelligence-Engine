from candidate.engine import analyse_resume
from api.models import CentralizedResume
from api.services.ocr_service import OCRService
import logging
import os

logger = logging.getLogger(__name__)

class BulkAnalysisService:
    @classmethod
    def analyze_batch(cls, job, resume_ids):
        """
        Loops through selected CentralizedResumes, parses them, 
        extracts skills, and calculates fit for the target job.
        """
        job_skills = set([s.lower() for s in job.role.required_skills])
        
        results = {
            "processed": 0,
            "high_fit": 0,
            "medium_fit": 0,
            "low_fit": 0,
            "errors": []
        }

        # Validate we only process resumes attached to exactly this job
        resumes_to_process = CentralizedResume.objects.filter(
            id__in=resume_ids, 
            job=job, 
            status__in=['New', 'Analyzed']
        )

        for cv in resumes_to_process:
            file_path = cv.resume_file.path
            ext = os.path.splitext(file_path)[1].lower()
            text = ""

            try:
                # 1. Extraction / OCR
                try:
                    # Leverage the unified candidate engine
                    result = analyse_resume(file_path, job.role.title if job.role else '')
                    
                    text = result.get('text', '')
                    entities = result.get('entities', {})
                    skills_dict = result.get('skills', {})
                    scores_dict = result.get('scores', {})
                    
                    if not cv.candidate_name and entities.get('name'):
                        cv.candidate_name = entities['name']
                    if not cv.email and entities.get('email'):
                        cv.email = entities['email']
                    if not cv.phone and entities.get('phone'):
                        cv.phone = entities['phone']

                    cv.extracted_text = text

                    if text.strip():
                        # Extract metrics
                        cv.extracted_skills = skills_dict.get('all', [])
                        cv.score = scores_dict.get('overall', 0)
                    else:
                        cv.score = 0
                        logger.warning(f"No text extracted for {cv.id}.")
                        
                except Exception as parse_error:
                    logger.error(f"Failed to parse inner Resume #{cv.id}: {str(parse_error)}")
                    cv.score = 0
                    cv.extracted_skills = []

                # 2. ML Prediction
                try:
                    from ml.model_loader import predict_resume
                    ml_result = predict_resume(text)
                    cv.ml_predicted_score = ml_result.get('predicted_score')
                    cv.ml_fit_category = ml_result.get('fit_category')
                    cv.ml_model_used = ml_result.get('model_used')
                except Exception as ml_err:
                    logger.warning(f"ML prediction failed for {cv.id}: {str(ml_err)}")

                # 3. Categorize Fit Level (Standard)
                if cv.score >= 80:
                    cv.fit_level = "Excellent Fit"
                    results["high_fit"] += 1
                elif cv.score >= 60:
                    cv.fit_level = "Good Fit"
                    results["medium_fit"] += 1
                else:
                    cv.fit_level = "Low Fit"
                    results["low_fit"] += 1

                # 4. Finalize
                cv.status = 'Analyzed'
                cv.save()
                results["processed"] += 1

                # 5. Broadcast generic Dashboard Notification natively
                cls._notify_dashboard_analysis_complete(cv)

            except Exception as e:
                logger.error(f"Failed to analyze Resume #{cv.id}: {str(e)}")
                results["errors"].append(str(e))

        return results

    @classmethod
    def _notify_dashboard_analysis_complete(cls, cv):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'dashboard',
                {
                    'type': 'dashboard_message',
                    'message': {
                        'event': 'bulk_analysis_completed',
                        'job_id': cv.job.id,
                        'resume_id': cv.id,
                        'name': cv.candidate_name,
                        'score': cv.score
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast websocket notification: {str(e)}")

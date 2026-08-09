from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import CandidateAnalysis, JobRole
from .engine import analyse_resume
from .data import JOB_ROLE_SKILLS

@shared_task
def process_resume_async(analysis_id, job_role_title):
    """
    Background worker task to parse resume and run heavy NLP/Sentence-BERT semantic matching.
    """
    try:
        analysis = CandidateAnalysis.objects.get(pk=analysis_id)
    except CandidateAnalysis.DoesNotExist:
        return "Analysis not found"

    result = analyse_resume(analysis.resume_file.path, job_role_title)
    
    if 'error' in result:
        analysis.delete()
        return f"Error: {result['error']}"

    # Persist
    analysis.full_text = result['text']
    analysis.candidate_name = result['entities'].get('name', '')
    analysis.email = result['entities'].get('email', '')
    analysis.phone = result['entities'].get('phone', '')
    analysis.extracted_skills = result['skills']['all']
    analysis.experience_years = result['experience_years']
    analysis.education_level = result['education_level']
    analysis.resume_category = result['category']

    scores = result['scores']
    analysis.overall_score = scores['overall']
    analysis.skill_score = scores['skill']
    analysis.experience_score = scores['experience']
    analysis.keyword_score = scores['keyword']
    analysis.education_score = scores['education']
    analysis.completeness_score = scores['completeness']

    jm = result.get('job_match', {})
    analysis.job_match_percentage = jm.get('match_pct', 0)
    analysis.matched_skills = jm.get('matched', [])
    analysis.missing_skills = jm.get('missing', [])
    analysis.suggestions = result['suggestions']
    analysis.career_paths = result['career_paths']
    analysis.save()
    
    # Broadcast to Real-Time Dashboard
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'dashboard_message',
            'message': {
                'event': 'candidate_score_updated',
                'candidate_id': analysis.id,
                'new_score': float(analysis.overall_score)
            }
        }
    )
    
    return f"Success: Processed Analysis {analysis_id}"

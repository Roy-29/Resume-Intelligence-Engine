"""REST API views for the Candidate module."""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from .models import CandidateAnalysis, JobRole
from .serializers import CandidateAnalysisSerializer, ResumeUploadSerializer
from .engine import analyse_resume, match_job, get_market_insights, generate_suggestions
from .data import JOB_ROLE_SKILLS
from .tasks import process_resume_async

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@api_view(['POST'])
def api_upload_resume(request):
    """POST /api/upload-resume/ — Async upload endpoint (returns a Celery Task ID)."""
    ser = ResumeUploadSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    resume_file = ser.validated_data['resume']
    job_role_title = ser.validated_data.get('job_role', '')

    ext = resume_file.name.rsplit('.', 1)[-1].lower()
    if ext not in ('pdf', 'docx'):
        return Response({'error': 'Only PDF and DOCX files are accepted.'},
                        status=status.HTTP_400_BAD_REQUEST)

    analysis = CandidateAnalysis(resume_file=resume_file, original_filename=resume_file.name)
    if job_role_title:
        role_obj, _ = JobRole.objects.get_or_create(
            title=job_role_title,
            defaults={
                'required_skills': JOB_ROLE_SKILLS.get(job_role_title, {}).get('required', []),
                'description': JOB_ROLE_SKILLS.get(job_role_title, {}).get('description', ''),
                'category': JOB_ROLE_SKILLS.get(job_role_title, {}).get('category', ''),
            }
        )
        analysis.selected_job_role = role_obj
    analysis.save()
    
    if request.user.is_authenticated:
        analysis.user = request.user
        analysis.save()

    # Trigger Celery Task
    task = process_resume_async.delay(analysis.id, job_role_title)

    # Broadcast event for real-time dashboard
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'dashboard_message',
            'message': {
                'event': 'new_resume_uploaded',
                'analysis_id': analysis.id
            }
        }
    )

    return Response({
        'message': 'Resume upload accepted. Processing asynchronously.',
        'task_id': task.id,
        'analysis_id': analysis.id
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def api_report(request, pk):
    """GET /api/candidate/<id>/report/"""
    try:
        analysis = CandidateAnalysis.objects.get(pk=pk)
    except CandidateAnalysis.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(CandidateAnalysisSerializer(analysis).data)


@api_view(['GET'])
def api_job_match(request, pk):
    """GET /api/candidate/<id>/job-match/?job_role=..."""
    try:
        analysis = CandidateAnalysis.objects.get(pk=pk)
    except CandidateAnalysis.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    job_role_title = request.query_params.get('job_role', '')
    if not job_role_title and analysis.selected_job_role:
        job_role_title = analysis.selected_job_role.title

    if not job_role_title:
        return Response({'error': 'Provide a job_role query param.'}, status=400)

    result = match_job(analysis.full_text, analysis.extracted_skills, job_role_title)
    return Response(result)


@api_view(['GET'])
def api_market_insights(request, pk):
    """GET /api/candidate/<id>/market-insights/"""
    try:
        analysis = CandidateAnalysis.objects.get(pk=pk)
    except CandidateAnalysis.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    job_role_title = request.query_params.get('job_role', '')
    if not job_role_title and analysis.selected_job_role:
        job_role_title = analysis.selected_job_role.title

    data = get_market_insights(job_role_title)
    data = get_market_insights(job_role_title)
    return Response(data)

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout as auth_logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.conf import settings
from functools import wraps
from .models import JobPosting, JobApplication, MLModelVersion, Interview, RecruiterMessage, RecruiterProfile
from .forms import JobPostingForm, RecruiterProfileForm
from candidate.models import CandidateAnalysis, Notification, UserProfile
from candidate.forms import UserSignUpForm
import json
from collections import Counter
from api.models import CentralizedResume


# ── Access Control ────────────────────────────────────────────

def recruiter_required(view_func):
    """Decorator: user must be logged in AND have role='recruiter'."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('recruiter:login')
        try:
            if not request.user.profile.is_recruiter:
                messages.error(request, '🚫 Access denied. This area is for recruiters only.')
                return redirect('candidate:profile')
        except UserProfile.DoesNotExist:
            messages.error(request, '🚫 Access denied. Please sign up as a recruiter.')
            return redirect('recruiter:signup')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ── Recruiter Auth ────────────────────────────────────────────

def recruiter_signup(request):
    """Recruiter registration — sets role to 'recruiter'."""
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Set role to recruiter
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'recruiter'
            profile.save()
            login(request, user)
            messages.success(request, '🎉 Recruiter account created successfully!')
            return redirect('recruiter:ats_dashboard')
    else:
        form = UserSignUpForm()
    return render(request, 'recruiter/signup.html', {'form': form})


def recruiter_login(request):
    """Redirect to unified home login page."""
    return redirect('candidate:login')


def recruiter_logout(request):
    """Log the recruiter out and redirect to the recruiter login page."""
    auth_logout(request)
    messages.success(request, '✅ You have been logged out successfully.')
    return redirect('recruiter:login')

# ── Recruiter Profile ─────────────────────────────────────────

@recruiter_required
def recruiter_profile(request):
    """Recruiter profile page with editable personal/company info and hiring stats."""
    profile, _ = RecruiterProfile.objects.get_or_create(user=request.user)
    edit_mode = request.GET.get('edit') == '1'

    if request.method == 'POST':
        form = RecruiterProfileForm(request.POST, request.FILES, instance=profile)
        email = request.POST.get('email', '').strip()
        if form.is_valid():
            form.save()
            if email:
                request.user.email = email
                request.user.save(update_fields=['email'])
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('recruiter:profile')
    else:
        form = RecruiterProfileForm(instance=profile, initial={'email': request.user.email})

    # ── Hiring Statistics ──
    total_jobs = JobPosting.objects.filter(recruiter=request.user).count()
    active_jobs = JobPosting.objects.filter(recruiter=request.user, is_active=True).count()
    total_applications = JobApplication.objects.filter(job_posting__recruiter=request.user).count()
    hired_count = JobApplication.objects.filter(job_posting__recruiter=request.user, status='hired').count()
    shortlisted = JobApplication.objects.filter(job_posting__recruiter=request.user, status='shortlisted').count()
    interviews_done = Interview.objects.filter(job_application__job_posting__recruiter=request.user, status='completed').count()
    messages_sent = RecruiterMessage.objects.filter(job_application__job_posting__recruiter=request.user).count()

    return render(request, 'recruiter/profile.html', {
        'profile': profile,
        'form': form,
        'edit_mode': edit_mode,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'hired_count': hired_count,
        'shortlisted': shortlisted,
        'interviews_done': interviews_done,
        'messages_sent': messages_sent,
    })


@recruiter_required
def recruiter_dashboard(request):
    """
    Main ATS view. Shows active jobs, recent applications, and allows filtering.
    """
    jobs = JobPosting.objects.filter(is_active=True).annotate(app_count=Count('applications')).order_by('-created_at')
    inactive_jobs = JobPosting.objects.filter(is_active=False).annotate(app_count=Count('applications')).order_by('-created_at')
    recent_apps = JobApplication.objects.select_related('candidate_analysis', 'job_posting').order_by('-applied_at')[:20]

    # Quick stats
    total_applications = JobApplication.objects.count()
    total_candidates = CandidateAnalysis.objects.count()
    upcoming_interviews = Interview.objects.filter(status='scheduled', scheduled_at__gte=timezone.now()).count()
    shortlisted = JobApplication.objects.filter(status='shortlisted').count()

    context = {
        'jobs': jobs,
        'inactive_jobs': inactive_jobs,
        'recent_apps': recent_apps,
        'total_applications': total_applications,
        'total_candidates': total_candidates,
        'upcoming_interviews': upcoming_interviews,
        'shortlisted': shortlisted,
    }
    return render(request, 'recruiter/ats_dashboard.html', context)


@recruiter_required
def job_detail(request, pk):
    """
    Detailed view of a specific job posting, including all its applications
    sorted by AI Match Score / XGBoost predicted probability.
    """
    job = get_object_or_404(JobPosting, pk=pk)
    applications = job.applications.select_related('candidate_analysis').order_by('-ml_selection_probability')
    shortlist_threshold = 70.0
    
    centralized_resumes = CentralizedResume.objects.filter(job=job).order_by('-uploaded_at')

    context = {
        'job': job,
        'applications': applications,
        'threshold': shortlist_threshold,
        'centralized_resumes': centralized_resumes,
    }
    return render(request, 'recruiter/job_detail.html', context)


@recruiter_required
def job_create(request):
    """View to create a new Job Posting via ModelForm."""
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            return redirect('recruiter:ats_dashboard')
    else:
        form = JobPostingForm()

    return render(request, 'recruiter/job_create.html', {'form': form})


@recruiter_required
def job_edit(request, pk):
    """View to edit an existing Job Posting."""
    job = get_object_or_404(JobPosting, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{job.title}' updated successfully.")
            return redirect('recruiter:ats_dashboard')
    else:
        form = JobPostingForm(instance=job)

    return render(request, 'recruiter/job_edit.html', {'form': form, 'job': job})


@recruiter_required
@require_POST
def toggle_job_active(request, pk):
    """Toggle a job posting between active and inactive."""
    job = get_object_or_404(JobPosting, pk=pk)
    job.is_active = not job.is_active
    job.save()
    messages.success(request, f"'{job.title}' has been {'activated' if job.is_active else 'deactivated'}.")
    return redirect('recruiter:ats_dashboard')


@recruiter_required
@require_POST
def change_application_status(request, app_pk):
    """Change a job application's status and notify the candidate."""
    application = get_object_or_404(JobApplication, pk=app_pk)
    new_status = request.POST.get('status', '')
    valid = ['applied', 'shortlisted', 'rejected', 'hired']
    if new_status in valid:
        application.status = new_status
        application.save()
        # Notify candidate
        if application.candidate_analysis.user:
            emoji = {'shortlisted': '⭐', 'rejected': '❌', 'hired': '🎉'}.get(new_status, '📋')
            Notification.objects.create(
                user=application.candidate_analysis.user,
                message=f"{emoji} Your application for '{application.job_posting.title}' has been {new_status.title()}!",
                link="/candidate/profile/",
            )
        messages.success(request, f"{application.candidate_analysis.candidate_name} marked as {new_status.title()}.")
    return redirect('recruiter:job_detail', pk=application.job_posting.pk)


@recruiter_required
def ceo_analytics(request):
    """
    Executive dashboard with REAL aggregated metrics from the database.
    """
    total_jobs = JobPosting.objects.count()
    total_apps = JobApplication.objects.count()
    
    hired_count = JobApplication.objects.filter(status='hired').count()
    fill_rate = min(100.0, (hired_count / total_jobs * 100)) if total_jobs > 0 else 0

    # Real monthly application trend (last 6 months)
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_data = (
        JobApplication.objects
        .filter(applied_at__gte=six_months_ago)
        .annotate(month=TruncMonth('applied_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [entry['month'].strftime('%b %Y') for entry in monthly_data] if monthly_data else ['No Data']
    app_trend = [entry['count'] for entry in monthly_data] if monthly_data else [0]

    # Real top skills demand from all CandidateAnalysis records
    all_skills = []
    for ca in CandidateAnalysis.objects.values_list('extracted_skills', flat=True):
        if ca:
            all_skills.extend(ca)
    skill_counter = Counter(s.lower() for s in all_skills)
    top_skills = skill_counter.most_common(8)
    skill_labels = [s[0].title() for s in top_skills] if top_skills else ['No Data']
    skill_data = [s[1] for s in top_skills] if top_skills else [0]

    # Real domain distribution from resume_category
    domain_qs = (
        CandidateAnalysis.objects
        .values('resume_category')
        .annotate(count=Count('id'))
    )
    domain_dist = {entry['resume_category'].title(): entry['count'] for entry in domain_qs if entry['resume_category']}
    if not domain_dist:
        domain_dist = {'No Data': 0}

    # Average score
    avg_score = CandidateAnalysis.objects.aggregate(avg=Avg('overall_score'))['avg'] or 0

    context = {
        'total_jobs': total_jobs,
        'total_apps': total_apps,
        'fill_rate': fill_rate,
        'hired_count': hired_count,
        'avg_score': round(avg_score, 1),
        'months_json': json.dumps(months),
        'app_trend_json': json.dumps(app_trend),
        'skill_labels_json': json.dumps(skill_labels),
        'skill_data_json': json.dumps(skill_data),
        'domain_labels_json': json.dumps(list(domain_dist.keys())),
        'domain_data_json': json.dumps(list(domain_dist.values())),
    }
    
    return render(request, 'recruiter/ceo_analytics.html', context)


@recruiter_required
def ml_model_metrics(request):
    """View to evaluate the ML training pipeline performance."""
    active_model = MLModelVersion.objects.filter(is_active=True).first()
    history = MLModelVersion.objects.order_by('-trained_at')[:10]

    # Check which trained models exist on disk
    import os
    models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
    trained_models = []
    for fname in ['rf_resume_classifier.joblib', 'logistic_regression.joblib']:
        fpath = os.path.join(models_dir, fname)
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            trained_models.append({'name': fname, 'size_kb': round(size_kb, 1)})

    context = {
        'active_model': active_model,
        'history': history,
        'trained_models': trained_models,
    }
    return render(request, 'recruiter/ml_metrics.html', context)


@recruiter_required
@require_POST
def retrain_model(request):
    """Trigger real model training from Kaggle dataset."""
    import os
    csv_path = os.path.join(settings.BASE_DIR, 'ml_models', 'kaggle_data', 'UpdatedResumeDataSet.csv')

    if not os.path.exists(csv_path):
        messages.error(request,
            f'Dataset not found! Download from kaggle.com/datasets/gauravduttakiit/resume-dataset '
            f'and place UpdatedResumeDataSet.csv in ml_models/kaggle_data/'
        )
        return redirect('recruiter:ml_metrics')

    try:
        from recruiter.tasks import async_retrain_model
        # Fix: Run the heavy ML training in the background using Celery
        async_retrain_model.delay(csv_path)
        messages.success(request, f"✅ ML Training has been queued in the background. The models will be updated shortly.")
    except Exception as e:
        messages.error(request, f"Failed to start training task: {str(e)}")

    return redirect('recruiter:ml_metrics')


@recruiter_required
def download_model_weights(request):
    """Download the active model's .joblib file."""
    import os
    from django.http import FileResponse
    active_model = MLModelVersion.objects.filter(is_active=True).first()
    if active_model and os.path.exists(active_model.file_path):
        return FileResponse(
            open(active_model.file_path, 'rb'),
            as_attachment=True,
            filename=f"{active_model.version_id}.joblib"
        )
    messages.error(request, "No trained model available to download.")
    return redirect('recruiter:ml_metrics')


# ── Feature 1: Interview Scheduling ──────────────────────────

@recruiter_required
def schedule_interview(request, app_pk):
    """Schedule an interview for a specific job application."""
    application = get_object_or_404(JobApplication, pk=app_pk)

    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        interview_type = request.POST.get('interview_type', 'video')
        meeting_link = request.POST.get('meeting_link', '')
        notes = request.POST.get('notes', '')

        if not scheduled_at:
            messages.error(request, 'Please select a date and time.')
        else:
            Interview.objects.create(
                job_application=application,
                scheduled_at=scheduled_at,
                interview_type=interview_type,
                meeting_link=meeting_link,
                notes=notes,
            )
            # Fire notification to candidate
            if application.candidate_analysis.user:
                Notification.objects.create(
                    user=application.candidate_analysis.user,
                    message=f"📅 Interview scheduled for {application.job_posting.title} ({interview_type.title()})",
                    link=f"/candidate/profile/",
                )
            messages.success(request, f"Interview scheduled for {application.candidate_analysis.candidate_name}!")
            return redirect('recruiter:job_detail', pk=application.job_posting.pk)

    return render(request, 'recruiter/interview_schedule.html', {
        'application': application,
        'type_choices': Interview.TYPE_CHOICES,
    })


@recruiter_required
def interview_calendar(request):
    """List all upcoming and past interviews with stats."""
    upcoming = Interview.objects.filter(
        status='scheduled', scheduled_at__gte=timezone.now()
    ).select_related('job_application__candidate_analysis', 'job_application__job_posting')

    past = Interview.objects.exclude(
        status='scheduled', scheduled_at__gte=timezone.now()
    ).select_related('job_application__candidate_analysis', 'job_application__job_posting').order_by('-scheduled_at')[:30]

    # Stats
    total_scheduled = Interview.objects.filter(status='scheduled').count()
    total_completed = Interview.objects.filter(status='completed').count()
    total_cancelled = Interview.objects.filter(status='cancelled').count()
    total_no_show = Interview.objects.filter(status='no_show').count()

    return render(request, 'recruiter/interview_calendar.html', {
        'upcoming': upcoming,
        'past': past,
        'total_scheduled': total_scheduled,
        'total_completed': total_completed,
        'total_cancelled': total_cancelled,
        'total_no_show': total_no_show,
    })


@recruiter_required
def interview_detail(request, pk):
    """View full details of a specific interview."""
    interview = get_object_or_404(
        Interview.objects.select_related(
            'job_application__candidate_analysis',
            'job_application__job_posting'
        ), pk=pk
    )
    return render(request, 'recruiter/interview_detail.html', {
        'interview': interview,
    })


@recruiter_required
def interview_edit(request, pk):
    """Edit an existing interview (reschedule, change type, etc.)."""
    interview = get_object_or_404(Interview, pk=pk)

    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        interview_type = request.POST.get('interview_type', interview.interview_type)
        meeting_link = request.POST.get('meeting_link', '')
        notes = request.POST.get('notes', '')

        if not scheduled_at:
            messages.error(request, 'Please select a date and time.')
        else:
            interview.scheduled_at = scheduled_at
            interview.interview_type = interview_type
            interview.meeting_link = meeting_link
            interview.notes = notes
            interview.save()
            messages.success(request, f"Interview updated for {interview.job_application.candidate_analysis.candidate_name}!")
            return redirect('recruiter:interview_detail', pk=interview.pk)

    return render(request, 'recruiter/interview_schedule.html', {
        'application': interview.job_application,
        'type_choices': Interview.TYPE_CHOICES,
        'interview': interview,
        'edit_mode': True,
    })


@recruiter_required
@require_POST
def interview_cancel(request, pk):
    """Cancel a scheduled interview."""
    interview = get_object_or_404(Interview, pk=pk)
    interview.status = 'cancelled'
    interview.save()
    # Notify candidate
    app = interview.job_application
    if app.candidate_analysis.user:
        Notification.objects.create(
            user=app.candidate_analysis.user,
            message=f"❌ Your {interview.get_interview_type_display()} interview for {app.job_posting.title} has been cancelled.",
            link="/candidate/profile/",
        )
    messages.success(request, f"Interview for {app.candidate_analysis.candidate_name} has been cancelled.")
    return redirect('recruiter:interview_calendar')


@recruiter_required
@require_POST
def interview_complete(request, pk):
    """Mark an interview as completed."""
    interview = get_object_or_404(Interview, pk=pk)
    interview.status = 'completed'
    interview.save()
    messages.success(request, f"Interview for {interview.job_application.candidate_analysis.candidate_name} marked as completed.")
    return redirect('recruiter:interview_calendar')


# ── Feature 2: Resume Comparison Tool ────────────────────────

@recruiter_required
def compare_candidates(request):
    """Side-by-side comparison of multiple candidates."""
    ids = request.GET.getlist('ids')
    job_pk = request.GET.get('job')

    candidates = CandidateAnalysis.objects.none()
    selected_job = None
    job_applications = []

    if ids:
        candidates = CandidateAnalysis.objects.filter(pk__in=ids)
    elif job_pk:
        selected_job = get_object_or_404(JobPosting, pk=job_pk)
        job_applications = JobApplication.objects.filter(
            job_posting=selected_job
        ).select_related('candidate_analysis').order_by('-ml_selection_probability')[:10]
        candidates = CandidateAnalysis.objects.filter(
            pk__in=[ja.candidate_analysis_id for ja in job_applications]
        )

    # Build a map of application data keyed by candidate PK
    app_map = {}
    if job_applications:
        for ja in job_applications:
            app_map[ja.candidate_analysis_id] = ja

    jobs = JobPosting.objects.filter(is_active=True).order_by('-created_at')

    return render(request, 'recruiter/compare.html', {
        'candidates': candidates,
        'jobs': jobs,
        'selected_job': selected_job,
        'app_map': app_map,
    })


# ── Feature 5: Recruiter Messaging ───────────────────────────

@recruiter_required
def send_message(request, app_pk):
    """Send an in-app message to a candidate."""
    application = get_object_or_404(JobApplication, pk=app_pk)

    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        body = request.POST.get('body', '')

        if not subject or not body:
            messages.error(request, 'Subject and message body are required.')
        else:
            RecruiterMessage.objects.create(
                job_application=application,
                subject=subject,
                body=body,
            )
            # Fire notification to candidate
            if application.candidate_analysis.user:
                Notification.objects.create(
                    user=application.candidate_analysis.user,
                    message=f"📩 New message from recruiter: {subject}",
                    link="/candidate/inbox/",
                )
            messages.success(request, f"Message sent to {application.candidate_analysis.candidate_name}!")
            return redirect('recruiter:job_detail', pk=application.job_posting.pk)

    return render(request, 'recruiter/send_message.html', {
        'application': application,
    })


@recruiter_required
def messages_hub(request):
    """Recruiter inbox — all sent messages with stats."""
    from django.db.models.functions import TruncWeek
    all_messages = RecruiterMessage.objects.select_related(
        'job_application__candidate_analysis',
        'job_application__job_posting'
    ).order_by('-sent_at')

    total_sent = all_messages.count()
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    this_week = all_messages.filter(sent_at__gte=week_ago).count()
    candidates_reached = all_messages.values('job_application__candidate_analysis').distinct().count()

    return render(request, 'recruiter/messages_hub.html', {
        'all_messages': all_messages,
        'total_sent': total_sent,
        'this_week': this_week,
        'candidates_reached': candidates_reached,
    })


@recruiter_required
def message_detail(request, pk):
    """View full details of a sent message."""
    msg = get_object_or_404(
        RecruiterMessage.objects.select_related(
            'job_application__candidate_analysis',
            'job_application__job_posting'
        ), pk=pk
    )
    return render(request, 'recruiter/message_detail.html', {
        'msg': msg,
    })


@recruiter_required
def message_edit(request, pk):
    """Edit a previously sent message."""
    msg = get_object_or_404(RecruiterMessage, pk=pk)

    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        body = request.POST.get('body', '')

        if not subject or not body:
            messages.error(request, 'Subject and message body are required.')
        else:
            msg.subject = subject
            msg.body = body
            msg.save()
            messages.success(request, 'Message updated successfully!')
            return redirect('recruiter:message_detail', pk=msg.pk)

    return render(request, 'recruiter/send_message.html', {
        'application': msg.job_application,
        'msg': msg,
        'edit_mode': True,
    })


@recruiter_required
@require_POST
def message_delete(request, pk):
    """Delete a sent message."""
    msg = get_object_or_404(RecruiterMessage, pk=pk)
    candidate_name = msg.job_application.candidate_analysis.candidate_name
    msg.delete()
    messages.success(request, f"Message to {candidate_name} has been deleted.")
    return redirect('recruiter:messages_hub')


# ── Resume File Viewing ──────────────────────────────────────

@recruiter_required
def view_resume_file(request, pk, source='analysis'):
    """Serve the original uploaded resume file to the recruiter.
    source='analysis' → CandidateAnalysis.resume_file
    source='centralized' → CentralizedResume.resume_file
    """
    if source == 'centralized':
        resume = get_object_or_404(CentralizedResume, pk=pk)
        file_field = resume.resume_file
    else:
        analysis = get_object_or_404(CandidateAnalysis, pk=pk)
        file_field = analysis.resume_file

    if not file_field or not os.path.exists(file_field.path):
        messages.error(request, "No resume file found for this candidate.")
        return redirect(request.META.get('HTTP_REFERER', 'recruiter:ats_dashboard'))

    # Determine content type based on extension
    filename = os.path.basename(file_field.path)
    if filename.lower().endswith('.docx'):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    else:
        content_type = 'application/pdf'

    return FileResponse(open(file_field.path, 'rb'), content_type=content_type, filename=filename)


@recruiter_required
def recruiter_report(request, pk):
    """Full AI Resume Analysis Report page for recruiters."""
    from candidate.engine import get_market_insights
    from candidate.views import _build_skill_radar
    
    analysis = get_object_or_404(CandidateAnalysis, pk=pk)
    market = {}
    if analysis.selected_job_role:
        market = get_market_insights(analysis.selected_job_role.title)

    skill_categories = _build_skill_radar(analysis.extracted_skills)

    context = {
        'a': analysis,
        'market': market,
        'skill_categories': json.dumps(skill_categories),
        'market_json': json.dumps(market),
        'career_paths_json': json.dumps(analysis.career_paths),
    }
    return render(request, 'recruiter/report.html', context)

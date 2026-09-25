"""
Django views for the Candidate module.
Upload, Dashboard, Report, PDF download, Share.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction

from .models import CandidateAnalysis, JobRole, UserProfile
from .forms import UserSignUpForm
from .engine import analyse_resume, match_job, get_market_insights, generate_suggestions
from .data import JOB_ROLE_SKILLS
from .pdf_report import generate_pdf
from functools import wraps


# ── Access Control ──────────────────────────────────────────────────────────

def candidate_required(view_func):
    """Decorator: user must be logged in AND have role='candidate'.
    Recruiters are blocked from accessing candidate-only pages."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('candidate:login')
        role = request.session.get('user_role')
        if not role:
            try:
                role = request.user.profile.role
                request.session['user_role'] = role
            except Exception:
                role = 'candidate'
                request.session['user_role'] = role
        if role != 'candidate':
            messages.error(request, '🚫 This area is for candidates only. Please log in as a candidate.')
            return redirect('recruiter:ats_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def login_required_any_role(view_func):
    """Decorator: user must be logged in (candidate OR recruiter).
    Used for shared pages like reports that both roles need access to."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('candidate:login')
        return view_func(request, *args, **kwargs)
    return _wrapped


@candidate_required
def upload_resume(request):
    """GET  → show upload page.  POST → analyse & redirect to dashboard."""
    job_roles = sorted(JOB_ROLE_SKILLS.keys())

    # ── Allowed MIME types (magic-bytes validation) ──────────────
    ALLOWED_MIME = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        job_role_title = request.POST.get('job_role', '')

        if not resume_file:
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': 'Please upload a resume file.',
            })

        # Fix 12: File size check (before saving to disk)
        if resume_file.size > MAX_UPLOAD_SIZE:
            size_mb = resume_file.size / (1024 * 1024)
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': f'File is too large ({size_mb:.1f} MB). Maximum allowed is 10 MB.',
            })

        ext = resume_file.name.rsplit('.', 1)[-1].lower()
        if ext not in ('pdf', 'docx'):
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': 'Only PDF and DOCX files are accepted.',
            })

        # Fix 11: MIME-type validation using magic bytes
        import mimetypes
        guessed_type, _ = mimetypes.guess_type(resume_file.name)
        # Also read a few bytes to detect spoofed files
        header = resume_file.read(8)
        resume_file.seek(0)  # Reset for later use

        is_pdf = header[:5] == b'%PDF-'
        is_docx = header[:4] == b'PK\x03\x04'  # DOCX is a ZIP archive

        if ext == 'pdf' and not is_pdf:
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': 'This file does not appear to be a valid PDF. It may be a renamed non-PDF file.',
            })
        if ext == 'docx' and not is_docx:
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': 'This file does not appear to be a valid DOCX. It may be a renamed non-DOCX file.',
            })

        # Save record
        analysis = CandidateAnalysis(
            resume_file=resume_file,
            original_filename=resume_file.name,
        )
        if request.user.is_authenticated:
            analysis.user = request.user
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

        # Run analysis
        result = analyse_resume(analysis.resume_file.path, job_role_title)

        if 'error' in result:
            analysis.delete()
            return render(request, 'candidate/upload.html', {
                'job_roles': job_roles,
                'error': result['error'],
            })

        # Surface engine warning (Fix 4: fake CV detection)
        if result.get('warning'):
            messages.warning(request, result['warning'])

        # Persist results
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

        return redirect('candidate:dashboard', pk=analysis.pk)

    return render(request, 'candidate/upload.html', {'job_roles': job_roles})


@candidate_required
def dashboard(request, pk):
    """Card-based dashboard with scores, charts, job match, suggestions."""
    analysis = get_object_or_404(CandidateAnalysis, pk=pk)
    job_roles = sorted(JOB_ROLE_SKILLS.keys())

    # Market data
    market = {}
    if analysis.selected_job_role:
        market = get_market_insights(analysis.selected_job_role.title)

    # Skills for radar chart
    skill_categories = _build_skill_radar(analysis.extracted_skills)

    context = {
        'a': analysis,
        'job_roles': job_roles,
        'market': market,
        'skill_categories': json.dumps(skill_categories),
        'market_json': json.dumps(market),
        'matched_skills_json': json.dumps(analysis.matched_skills),
        'missing_skills_json': json.dumps(analysis.missing_skills),
        'career_paths_json': json.dumps(analysis.career_paths),
    }
    return render(request, 'candidate/dashboard.html', context)


@login_required_any_role
def report(request, pk):
    """Full AI Resume Analysis Report page. Accessible by both candidates and recruiters."""
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
    return render(request, 'candidate/report.html', context)


@login_required_any_role
def download_pdf(request, pk):
    """Generate and return PDF report. Accessible by both candidates and recruiters."""
    from django.utils.text import get_valid_filename
    
    analysis = get_object_or_404(CandidateAnalysis, pk=pk)
    market = {}
    if analysis.selected_job_role:
        market = get_market_insights(analysis.selected_job_role.title)

    pdf_buffer = generate_pdf(analysis, market)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    
    # Safely format the filename to prevent BadHeaderError from newlines
    raw_name = analysis.candidate_name or 'resume'
    safe_name = get_valid_filename(raw_name.replace(' ', '_').replace('\n', '_').replace('\r', ''))
    
    response['Content-Disposition'] = f'attachment; filename="AI_Report_{safe_name}.pdf"'
    return response


def share_report(request, token):
    """Public shareable report link."""
    analysis = get_object_or_404(CandidateAnalysis, share_token=token)
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
        'shared': True,
    }
    return render(request, 'candidate/report.html', context)


@login_required(login_url='candidate:login')
def rematch_job(request, pk):
    """Re-run job matching with a new role (AJAX-friendly)."""
    analysis = get_object_or_404(CandidateAnalysis, pk=pk)
    job_role_title = request.POST.get('job_role', '') or request.GET.get('job_role', '')

    if job_role_title:
        result = match_job(analysis.full_text, analysis.extracted_skills, job_role_title)
        analysis.job_match_percentage = result['match_pct']
        analysis.matched_skills = result['matched']
        analysis.missing_skills = result['missing']

        role_obj, _ = JobRole.objects.get_or_create(
            title=job_role_title,
            defaults={
                'required_skills': JOB_ROLE_SKILLS.get(job_role_title, {}).get('required', []),
                'description': JOB_ROLE_SKILLS.get(job_role_title, {}).get('description', ''),
                'category': JOB_ROLE_SKILLS.get(job_role_title, {}).get('category', ''),
            }
        )
        analysis.selected_job_role = role_obj

        # Regenerate suggestions for new role
        analysis.suggestions = generate_suggestions(
            analysis.extracted_skills,
            result['missing'],
            analysis.experience_years,
            analysis.completeness_score,
        )
        analysis.save()

    return redirect('candidate:dashboard', pk=pk)


# ── Auth & Profile ──────────────────────────────────────

def user_signup(request):
    """Candidate registration view — sets role to 'candidate'."""
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                # Set role to candidate
                from .models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role = 'candidate'
                profile.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('candidate:profile')
    else:
        form = UserSignUpForm()
    return render(request, 'candidate/signup.html', {'form': form})


def home_login(request):
    """Unified Home Login view — handles Candidate & Recruiter with role toggle."""
    # If already logged in, redirect to the appropriate portal
    if request.user.is_authenticated:
        try:
            if request.user.profile.is_recruiter:
                return redirect('recruiter:ats_dashboard')
        except Exception:
            pass
        return redirect('candidate:upload')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        role = request.POST.get('role', 'candidate')
        
        if form.is_valid():
            user = form.get_user()
            
            # Check role match
            is_recruiter = False
            try:
                is_recruiter = user.profile.is_recruiter
            except Exception:
                pass

            if role == 'recruiter' and not is_recruiter:
                messages.error(request, 'This account is a Candidate. Please select the Candidate role.')
                return render(request, 'core/home_login.html', {'form': AuthenticationForm(), 'selected_role': role})
            elif role == 'candidate' and is_recruiter:
                messages.error(request, 'This account is a Recruiter. Please select the Recruiter role.')
                return render(request, 'core/home_login.html', {'form': AuthenticationForm(), 'selected_role': role})

            # Validated - login and redirect
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            if is_recruiter:
                return redirect('recruiter:ats_dashboard')
            return redirect('candidate:upload')
    else:
        form = AuthenticationForm()
        
    return render(request, 'core/home_login.html', {'form': form, 'selected_role': 'candidate'})


def user_logout(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('candidate:upload')


@login_required
def user_profile(request):
    """User profile displaying history of analyses, global stats, applications, and editable personal info."""
    user = request.user
    
    # Get or create the candidate profile
    from .models import CandidateProfile
    from .forms import CandidateProfileForm
    cand_profile, _ = CandidateProfile.objects.get_or_create(user=user)
    edit_mode = request.GET.get('edit') == '1'
    
    if request.method == 'POST':
        form = CandidateProfileForm(request.POST, request.FILES, instance=cand_profile)
        email = request.POST.get('email', '').strip()
        if form.is_valid():
            form.save()
            if email:
                user.email = email
                user.save(update_fields=['email'])
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('candidate:profile')
    else:
        form = CandidateProfileForm(instance=cand_profile, initial={'email': user.email})
    
    analyses = list(CandidateAnalysis.objects.filter(user=user).order_by('-uploaded_at'))
    
    # Global AI Stats
    total_analyses = len(analyses)
    highest_score = 0
    avg_match = 0
    top_skills_count = {}
    
    if total_analyses > 0:
        highest_score = max([a.overall_score for a in analyses])
        match_pcts = [a.job_match_percentage for a in analyses if a.job_match_percentage > 0]
        avg_match = sum(match_pcts) / len(match_pcts) if match_pcts else 0
        
        # Aggregate skills
        for a in analyses:
            for skill in a.extracted_skills:
                top_skills_count[skill] = top_skills_count.get(skill, 0) + 1
                
    # Sort and pick top 10 skills
    top_skills = sorted(top_skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Application Tracker
    applications = []
    try:
        from django.apps import apps
        JobApplication = apps.get_model('recruiter', 'JobApplication')
        applications = JobApplication.objects.filter(
            candidate_analysis__user=user
        ).select_related('job_posting', 'candidate_analysis').order_by('-applied_at')
    except Exception:
        pass
    
    return render(request, 'candidate/profile.html', {
        'user': user,
        'cand_profile': cand_profile,
        'form': form,
        'edit_mode': edit_mode,
        'analyses': analyses,
        'total_analyses': total_analyses,
        'highest_score': highest_score,
        'avg_match': avg_match,
        'top_skills': top_skills,
        'applications': applications,
    })


# ── helpers ──────────────────────────────────────
def _build_skill_radar(skills_list: list) -> dict:
    """Group skills into categories for radar chart."""
    from .data import TECHNICAL_SKILLS, SOFT_SKILLS
    cats = {
        'Programming': 0,
        'Web Development': 0,
        'Data & ML': 0,
        'Cloud & DevOps': 0,
        'Soft Skills': 0,
        'Other': 0,
    }
    programming = {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c',
                   'ruby', 'go', 'golang', 'rust', 'swift', 'kotlin', 'scala', 'r',
                   'php', 'perl', 'dart'}
    web = {'html', 'css', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
           'fastapi', 'spring', 'express', 'next.js', 'bootstrap', 'jquery'}
    data_ml = {'sql', 'machine learning', 'deep learning', 'tensorflow', 'pytorch',
               'pandas', 'numpy', 'scikit-learn', 'nlp', 'data analysis',
               'data visualization', 'spark', 'hadoop', 'tableau', 'power bi',
               'statistics', 'computer vision', 'big data'}
    cloud = {'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
             'ci/cd', 'linux', 'bash', 'nginx', 'ansible', 'github actions'}

    for skill in skills_list:
        sl = skill.lower()
        if sl in programming:
            cats['Programming'] += 1
        elif sl in web:
            cats['Web Development'] += 1
        elif sl in data_ml:
            cats['Data & ML'] += 1
        elif sl in cloud:
            cats['Cloud & DevOps'] += 1
        elif sl in SOFT_SKILLS:
            cats['Soft Skills'] += 1
        else:
            cats['Other'] += 1

    return cats

# ── Job Application Flow ───────────────────────────────

def job_listings(request):
    """Candidate-facing job board to browse active job postings."""
    # Lazy load to avoid circular import if recruiter model is loaded first
    from recruiter.models import JobPosting
    jobs = JobPosting.objects.select_related('role').filter(is_active=True).order_by('-created_at')
    return render(request, 'candidate/jobs_list.html', {'jobs': jobs})


@login_required(login_url='candidate:login')
def apply_to_job(request, pk):
    """Allows a candidate to select a resume analysis and apply to a specific job."""
    from recruiter.models import JobPosting, JobApplication
    from recruiter.ml_pipeline import predict_selection_probability

    job = get_object_or_404(JobPosting, pk=pk)
    
    # Get user's available resumes
    analyses = CandidateAnalysis.objects.filter(user=request.user).order_by('-uploaded_at')

    if request.method == 'POST':
        selected_analysis_id = request.POST.get('analysis_id')
        if not selected_analysis_id:
            messages.error(request, "Please select an analyzed resume to apply.")
        else:
            analysis = get_object_or_404(CandidateAnalysis, pk=selected_analysis_id, user=request.user)
            
            # Prevent duplicate application with the SAME resume
            if JobApplication.objects.filter(job_posting=job, candidate_analysis=analysis).exists():
                messages.warning(request, "You have already applied to this job using this resume.")
            else:
                # Calculate ML selection probability to show immediately in the ATS dashboard
                ml_prob = predict_selection_probability(
                    skill_score=analysis.skill_score,
                    exp_score=analysis.experience_score,
                    semantic_sim=analysis.job_match_percentage,
                    edu_score=analysis.education_score
                )

                JobApplication.objects.create(
                    job_posting=job,
                    candidate_analysis=analysis,
                    status='applied',
                    ml_selection_probability=ml_prob
                )
                messages.success(request, f"Successfully applied for {job.title}!")
                return redirect('candidate:profile')

    return render(request, 'candidate/job_apply.html', {
        'job': job,
        'analyses': analyses
    })


# ── Unified Inbox ─────────────────────────────────────

@login_required(login_url='candidate:login')
def inbox(request):
    """Unified inbox — merges notifications and recruiter messages into one timeline."""
    from .models import Notification
    from recruiter.models import RecruiterMessage

    notifs_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifs_qs.filter(is_read=False).count()
    notifs = notifs_qs[:50]
    msgs = RecruiterMessage.objects.filter(
        job_application__candidate_analysis__user=request.user
    ).select_related('job_application__job_posting').order_by('-sent_at')[:50]

    # Build unified timeline
    timeline = []
    for n in notifs:
        timeline.append({
            'type': 'notification',
            'id': n.pk,
            'message': n.message,
            'link': n.link,
            'is_read': n.is_read,
            'date': n.created_at,
        })
    for m in msgs:
        timeline.append({
            'type': 'message',
            'id': m.pk,
            'subject': m.subject,
            'body': m.body,
            'job_title': m.job_application.job_posting.title,
            'is_read': True,  # Messages are always "read" (no is_read field)
            'date': m.sent_at,
        })

    timeline.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'candidate/inbox.html', {
        'timeline': timeline,
        'unread_count': unread_count,
    })


@login_required(login_url='candidate:login')
def notifications_list(request):
    """Redirect old notifications URL to inbox."""
    from django.shortcuts import redirect
    return redirect('candidate:inbox')


@login_required(login_url='candidate:login')
@require_POST
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    from .models import Notification
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect('candidate:inbox')


@login_required(login_url='candidate:login')
@require_POST
def mark_all_read(request):
    """Mark all notifications as read."""
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('candidate:inbox')


@login_required(login_url='candidate:login')
def recruiter_messages(request):
    """Redirect old messages URL to inbox."""
    from django.shortcuts import redirect
    return redirect('candidate:inbox')


# ── Smart Resume Builder ─────────────────────────────────────────────────────

@candidate_required
def resume_builder(request):
    """Render the AI-powered resume builder page."""
    from .data import JOB_ROLE_SKILLS
    job_roles = sorted(JOB_ROLE_SKILLS.keys())
    role_skills = {role: data.get('required', []) for role, data in JOB_ROLE_SKILLS.items()}
    return render(request, 'candidate/resume_builder.html', {
        'job_roles': job_roles,
        'role_skills_json': json.dumps(role_skills),
    })


@candidate_required
@require_POST
def ai_enhance_bullet(request):
    """AJAX endpoint: enhance a rough resume bullet with AI."""
    from django.http import JsonResponse
    from api.services.ai_service import enhance_resume_bullet
    try:
        data = json.loads(request.body)
        bullet = data.get('bullet', '').strip()
        role = data.get('role', 'Software Engineer').strip()
        if not bullet:
            return JsonResponse({'error': 'Bullet text is required.'}, status=400)
        result = enhance_resume_bullet(bullet, role)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── GitHub Analyzer ──────────────────────────────────────────────────────────

@candidate_required
def github_analyzer(request):
    """Render the GitHub profile analyzer page."""
    from .data import JOB_ROLE_SKILLS
    job_roles = sorted(JOB_ROLE_SKILLS.keys())
    return render(request, 'candidate/github_analyzer.html', {
        'job_roles': job_roles,
    })


@candidate_required
@require_POST
def fetch_github_data(request):
    """AJAX endpoint: fetch and analyze a public GitHub profile."""
    from django.http import JsonResponse
    from api.services.github_service import fetch_github_profile
    from .data import JOB_ROLE_SKILLS
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        selected_role = data.get('role', '').strip()
        if not username:
            return JsonResponse({'error': 'GitHub username is required.'}, status=400)

        profile = fetch_github_profile(username)
        if 'error' in profile:
            return JsonResponse({'error': profile['error']}, status=400)

        # Calculate skill match against selected job role
        if selected_role and selected_role in JOB_ROLE_SKILLS:
            required_skills = set(JOB_ROLE_SKILLS[selected_role].get('required', []))
            extracted = set(profile.get('extracted_skills', []))
            matched = list(required_skills & extracted)
            missing = list(required_skills - extracted)
            match_pct = round((len(matched) / len(required_skills)) * 100) if required_skills else 0
            profile['role_match'] = {
                'role': selected_role,
                'matched': matched,
                'missing': missing,
                'percent': match_pct,
            }

        # --- Dynamic Feedback & Scoring Generator ---
        activity = profile.get('activity_score', 0)
        stars = profile.get('total_stars', 0)
        repos = profile.get('public_repos', 0)
        followers = profile.get('followers', 0)
        
        # Base Score (Max 100)
        overall_score = activity * 0.4
        
        highlights = []
        if stars > 100:
            overall_score += 25
            highlights.append("Exceptional open-source impact (100+ stars).")
        elif stars > 10:
            overall_score += 15
            highlights.append("Growing community footprint (10+ stars).")
            
        if repos > 25:
            overall_score += 15
            highlights.append("Excellent portfolio volume (25+ repos).")
        elif repos > 5:
            overall_score += 10
            
        if followers > 30:
            overall_score += 10
            highlights.append("Strong peer network (>30 followers).")
            
        if 'role_match' in profile:
            overall_score += (profile['role_match']['percent'] * 0.3)
        else:
            overall_score += 20 # Add padding if not matching a role
            
        overall_score = min(100, int(overall_score))
        
        # Actionable Insights
        feedback = []
        if overall_score >= 80:
            feedback.append({"type": "success", "msg": "Outstanding GitHub presence! Your profile is highly attractive to engineering managers."})
        elif overall_score >= 50:
            feedback.append({"type": "warning", "msg": "Solid foundation. Increase your activity score by pushing commits more consistently."})
        else:
            feedback.append({"type": "danger", "msg": "Your profile looks inactive. Try building public showcase projects and pushing code weekly."})
            
        if 'role_match' in profile and profile['role_match']['missing']:
            missing_text = ', '.join(profile['role_match']['missing'][:3])
            feedback.append({"type": "warning", "msg": f"To align better as a {selected_role}, consider pinning projects built with: {missing_text}."})

        if not profile.get('bio') or len(profile.get('bio', '')) < 15:
            feedback.append({"type": "danger", "msg": "Your GitHub bio is empty or too short. Add a professional summary of your technical focus."})
            
        profile['ai_feedback'] = {
            'overall_score': overall_score,
            'highlights': highlights,
            'actionable': feedback
        }

        return JsonResponse(profile)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

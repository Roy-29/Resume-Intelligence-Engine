from django import forms
from .models import JobPosting, RecruiterProfile
from candidate.models import JobRole

class JobPostingForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=JobRole.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select bg-dark text-light border-secondary'}),
        empty_label="Select an AI Job Category"
    )

    class Meta:
        model = JobPosting
        fields = ['title', 'role', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control bg-dark text-light border-secondary',
                'placeholder': 'e.g. Senior Machine Learning Engineer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-dark text-light border-secondary',
                'rows': 5,
                'placeholder': 'Paste job requirements and responsibilities here...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input bg-dark border-secondary'
            }),
        }


INPUT_CLASS = 'profile-input'

class RecruiterProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'email@company.com'}))

    class Meta:
        model = RecruiterProfile
        fields = [
            'full_name', 'phone', 'bio', 'profile_image',
            'company_name', 'company_website', 'industry', 'company_size', 'company_location',
            'job_title', 'department', 'specialization', 'years_experience',
            'linkedin_url', 'twitter_url',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'John Doe'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+91 98765 43210'}),
            'bio': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Tell us about yourself...'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': INPUT_CLASS, 'accept': 'image/*'}),
            'company_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Acme Corp'}),
            'company_website': forms.URLInput(attrs={'class': INPUT_CLASS, 'placeholder': 'https://acme.com'}),
            'industry': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Technology / Finance / Healthcare'}),
            'company_size': forms.Select(attrs={'class': INPUT_CLASS}),
            'company_location': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Mumbai, India'}),
            'job_title': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Senior Technical Recruiter'}),
            'department': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Human Resources'}),
            'specialization': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Data Science, Backend Engineering'}),
            'years_experience': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
            'linkedin_url': forms.URLInput(attrs={'class': INPUT_CLASS, 'placeholder': 'https://linkedin.com/in/username'}),
            'twitter_url': forms.URLInput(attrs={'class': INPUT_CLASS, 'placeholder': 'https://twitter.com/username'}),
        }


from django import forms
from django.contrib.auth.models import User
from .models import CandidateProfile

class UserSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'autofocus': True}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


PI = 'profile-input'

class CandidateProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': PI, 'placeholder': 'email@example.com'}))

    class Meta:
        model = CandidateProfile
        fields = [
            'full_name', 'phone', 'date_of_birth', 'bio', 'location', 'profile_image',
            'highest_education', 'university', 'field_of_study', 'graduation_year',
            'current_job_title', 'current_company', 'years_experience', 'preferred_role', 'expected_salary', 'availability',
            'linkedin_url', 'github_url', 'portfolio_url', 'twitter_url',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': PI, 'placeholder': 'John Doe'}),
            'phone': forms.TextInput(attrs={'class': PI, 'placeholder': '+91 98765 43210'}),
            'date_of_birth': forms.DateInput(attrs={'class': PI, 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': PI, 'rows': 3, 'placeholder': 'A short summary about your career goals...'}),
            'location': forms.TextInput(attrs={'class': PI, 'placeholder': 'Mumbai, India'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': PI, 'accept': 'image/*'}),
            'highest_education': forms.Select(attrs={'class': PI}),
            'university': forms.TextInput(attrs={'class': PI, 'placeholder': 'MIT / IIT Delhi / Stanford'}),
            'field_of_study': forms.TextInput(attrs={'class': PI, 'placeholder': 'Computer Science'}),
            'graduation_year': forms.NumberInput(attrs={'class': PI, 'min': 1990, 'max': 2030}),
            'current_job_title': forms.TextInput(attrs={'class': PI, 'placeholder': 'Software Engineer'}),
            'current_company': forms.TextInput(attrs={'class': PI, 'placeholder': 'Google'}),
            'years_experience': forms.NumberInput(attrs={'class': PI, 'min': 0}),
            'preferred_role': forms.TextInput(attrs={'class': PI, 'placeholder': 'ML Engineer, Data Scientist'}),
            'expected_salary': forms.TextInput(attrs={'class': PI, 'placeholder': '$80k-$100k'}),
            'availability': forms.Select(attrs={'class': PI}),
            'linkedin_url': forms.URLInput(attrs={'class': PI, 'placeholder': 'https://linkedin.com/in/username'}),
            'github_url': forms.URLInput(attrs={'class': PI, 'placeholder': 'https://github.com/username'}),
            'portfolio_url': forms.URLInput(attrs={'class': PI, 'placeholder': 'https://myportfolio.com'}),
            'twitter_url': forms.URLInput(attrs={'class': PI, 'placeholder': 'https://twitter.com/username'}),
        }


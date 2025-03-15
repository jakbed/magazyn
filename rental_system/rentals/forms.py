from django import forms
from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):
    nickname = forms.CharField(max_length=50, required=False, label="Pseudonim")
    profile_picture = forms.ImageField(required=False, label="Zdjęcie profilowe")

    class Meta:
        model = User
        fields = ["username", "email"]

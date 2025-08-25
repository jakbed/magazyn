from django import forms
from django.contrib.auth.models import User


class ProfileForm(forms.ModelForm):
    nickname = forms.CharField(max_length=50, required=False, label="Pseudonim")
    avatar = forms.ImageField(required=False, label="Zdjęcie profilowe")

    class Meta:
        model = User
        fields = ["username", "email"]

    def save(self, commit=True):
        user = super().save(commit)
        profile = user.profile
        profile.nickname = self.cleaned_data.get("nickname", profile.nickname)
        avatar = self.cleaned_data.get("avatar")
        if avatar is not None:
            profile.avatar = avatar
        if commit:
            profile.save()
        return user

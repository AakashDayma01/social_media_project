from django import forms
from .models import SocialPost

class SocialPostForm(forms.ModelForm):
    class Meta:
        model = SocialPost
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': "What's on your mind?",
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }

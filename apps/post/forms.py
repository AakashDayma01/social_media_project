from django import forms
from .models import SocialPost

class SocialPostForm(forms.ModelForm):
    """
    Form for creating and publishing social posts.

    Handles text-based content validation and optional image attachments, 
    applying custom styling attributes to match the user interface.
    """
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

from django import forms
from .models import Community, CommunityPost, PostComment


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ('name', 'description', 'cover_image', 'is_public')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'is_public': forms.CheckboxInput(),
        }


class CommunityPostForm(forms.ModelForm):
    class Meta:
        model = CommunityPost
        fields = ('title', 'body', 'book')
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
            'book': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].required = False
        self.fields['book'].empty_label = 'No book linked'


class PostCommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'maxlength': 2000}),
        }

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if not body:
            raise forms.ValidationError('Comment cannot be empty.')
        return body

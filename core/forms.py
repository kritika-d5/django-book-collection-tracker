from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from shelves.models import UserShelf, ReviewComment


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Sign here', 'autocomplete': 'username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'you@example.com'})


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserShelf
        fields = ('rating', 'review')
        widgets = {
            'review': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your review here...'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = ReviewComment
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a comment...', 'maxlength': 2000}),
        }

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if not body:
            raise forms.ValidationError('Comment cannot be empty.')
        return body


class ReplyForm(CommentForm):
    pass

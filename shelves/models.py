from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from books.models import Book


class UserShelf(models.Model):
    SHELF_CHOICES = (
        ('read', 'Read'),
        ('reading', 'Currently Reading'),
        ('tbr', 'Want to Read'), 
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shelves")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="shelves")
    shelf_type = models.CharField(max_length=10, choices=SHELF_CHOICES)
    
    rating = models.IntegerField(blank=True, null=True)
    review = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'book')

    def save(self, *args, **kwargs):
        if self.rating is not None and self.reviewed_at is None:
            self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s shelf: {self.book.title} ({self.get_shelf_type_display()})"


class ReviewComment(models.Model):
    shelf = models.ForeignKey(UserShelf, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.shelf.book.title}"
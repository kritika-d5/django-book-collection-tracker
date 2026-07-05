from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from books.models import Book


class UserShelf(models.Model):
    READ = 'read'
    SHELF_CHOICES = (
        (READ, 'Read'),
        ('reading', 'Currently Reading'),
        ('tbr', 'Want to Read'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shelves")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="shelves")
    shelf_type = models.CharField(max_length=10, choices=SHELF_CHOICES)

    rating = models.IntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    review = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'book')
        constraints = [
            models.CheckConstraint(
                check=Q(rating__isnull=True) | Q(rating__gte=1, rating__lte=5),
                name='shelf_rating_1_to_5',
            ),
            # Only a 'read' book may carry a rating / review timestamp.
            models.CheckConstraint(
                check=Q(shelf_type='read')
                | (Q(rating__isnull=True) & Q(reviewed_at__isnull=True)),
                name='review_data_only_when_read',
            ),
        ]

    def clean(self):
        super().clean()
        if self.shelf_type != self.READ:
            stray = [
                label for value, label in (
                    (self.rating, 'rating'),
                    (self.review, 'review'),
                    (self.reviewed_at, 'review date'),
                ) if value
            ]
            if stray:
                raise ValidationError(
                    'A book must be on the "Read" shelf to have a '
                    f'{", ".join(stray)}.'
                )

    def save(self, *args, **kwargs):
        touched = []
        if self.shelf_type != self.READ:
            # Leaving the Read shelf clears any review data so 'reading'/'tbr'
            # rows never keep a stray rating or review. This also covers the
            # programmatic paths (e.g. add_to_shelf) that skip clean().
            self.rating = None
            self.review = None
            self.reviewed_at = None
            touched = ['rating', 'review', 'reviewed_at']
        elif self.rating is not None and self.reviewed_at is None:
            self.reviewed_at = timezone.now()
            touched = ['reviewed_at']

        # update_or_create() saves with a limited update_fields; make sure the
        # columns we just changed are actually written, or the DB row keeps
        # stale values and trips the review_data_only_when_read constraint.
        update_fields = kwargs.get('update_fields')
        if touched and update_fields is not None:
            kwargs['update_fields'] = set(update_fields).union(touched)

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
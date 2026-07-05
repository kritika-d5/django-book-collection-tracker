from django.db import models

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, related_name="books")
    genres = models.ManyToManyField(Genre, related_name="books")
    description = models.TextField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def primary_author(self):
        # Use .all()[0] rather than .first(): when authors are prefetched this
        # reads from the prefetch cache (no extra query), whereas .first()
        # re-orders the queryset and always hits the database (an N+1 in lists).
        authors = self.authors.all()
        return authors[0] if authors else None

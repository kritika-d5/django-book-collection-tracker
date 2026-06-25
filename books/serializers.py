from rest_framework import serializers
from .models import Book, Author, Genre

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name']

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    author_ids = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(),
        many=True, 
        write_only=True
    )
    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True, 
        write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id', 
            'title', 
            'description', 
            'cover_image',
            'authors',
            'genres',
            'author_ids',
            'genre_ids',
        ]

    def create(self, validated_data):
        author_ids = validated_data.pop('author_ids', [])
        genre_ids = validated_data.pop('genre_ids', [])
        
        book = Book.objects.create(**validated_data)
        
        book.authors.set(author_ids)
        book.genres.set(genre_ids)
        
        return book

    def update(self, instance, validated_data):
        if 'author_ids' in validated_data:
            author_ids = validated_data.pop('author_ids')
            instance.authors.set(author_ids)
            
        if 'genre_ids' in validated_data:
            genre_ids = validated_data.pop('genre_ids')
            instance.genres.set(genre_ids)
            
        instance = super().update(instance, validated_data)
        
        return instance
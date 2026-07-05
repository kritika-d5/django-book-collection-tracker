from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Count, Prefetch
from django.core.paginator import Paginator
from shelves.models import UserShelf, ReviewComment
from books.models import Book, Genre, Author
from .forms import SignUpForm, ReviewForm, CommentForm, ReplyForm


def home(request):
    from django.db.models import Count
    from communities.models import Community

    genres = (
        Genre.objects.annotate(book_total=Count('books'))
        .filter(book_total__gt=0)
        .order_by('-book_total', 'name')
        .prefetch_related(
            Prefetch(
                'books',
                queryset=Book.objects.only('id', 'title').order_by('id')[:12],
                to_attr='shelf_books',
            )
        )
    )
    popular_communities = (
        Community.objects.filter(is_public=True)
        .annotate(annotated_member_count=Count('memberships'))
        .order_by('-annotated_member_count')[:3]
    )

    context = {
        'genres': genres,
        'popular_communities': popular_communities,
    }
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    user_shelves = UserShelf.objects.filter(user=request.user).select_related('book').prefetch_related('book__authors')
    read_books = user_shelves.filter(shelf_type='read')
    reading_books = user_shelves.filter(shelf_type='reading')
    tbr_books = user_shelves.filter(shelf_type='tbr')

    context = {
        'read_books': read_books,
        'reading_books': reading_books,
        'tbr_books': tbr_books,
    }

    return render(request, 'core/dashboard.html', context)


@login_required
def review_book(request, shelf_id):
    shelf_item = get_object_or_404(UserShelf, id=shelf_id)

    if shelf_item.user != request.user:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=shelf_item)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ReviewForm(instance=shelf_item)

    context = {
        'form': form,
        'shelf_item': shelf_item
    }
    return render(request, 'core/review_book.html', context)


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    top_level_comments = ReviewComment.objects.filter(parent=None).select_related('user').prefetch_related(
        Prefetch('replies', queryset=ReviewComment.objects.select_related('user').order_by('created_at'))
    )
    reviews_qs = UserShelf.objects.filter(
        book=book, shelf_type='read', rating__isnull=False
    ).select_related('user').prefetch_related(
        Prefetch('comments', queryset=top_level_comments)
    ).order_by('-reviewed_at', '-id')

    avg_rating = reviews_qs.aggregate(Avg('rating'))['rating__avg']
    if avg_rating is not None:
        avg_rating = round(avg_rating, 1)

    paginator = Paginator(reviews_qs, 10)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)

    # For a logged-in user, show which of their communities have members who
    # have this book on a shelf — a tie-in between the shelves and communities
    # apps. Both `__in` clauses stay as lazy subqueries (no extra round-trips).
    community_shelf_counts = []
    if request.user.is_authenticated:
        from communities.models import CommunityMembership

        my_community_ids = CommunityMembership.objects.filter(
            user=request.user
        ).values_list('community_id', flat=True)
        shelver_ids = UserShelf.objects.filter(book=book).values_list('user_id', flat=True)
        community_shelf_counts = (
            CommunityMembership.objects
            .filter(community_id__in=my_community_ids, user_id__in=shelver_ids)
            .values('community__name', 'community__slug')
            .annotate(shelver_count=Count('user_id', distinct=True))
            .order_by('-shelver_count', 'community__name')
        )

    context = {
        'book': book,
        'reviews': reviews,
        'review_count': paginator.count,
        'avg_rating': avg_rating,
        'community_shelf_counts': community_shelf_counts,
    }
    return render(request, 'core/book_detail.html', context)


def search(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = Book.objects.filter(
            Q(title__icontains=query) |
            Q(authors__name__icontains=query)
        ).distinct().prefetch_related('authors')

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'core/search.html', context)


@login_required
@require_POST
def add_to_shelf(request):
    book_id = request.POST.get('book_id')
    shelf_type = request.POST.get('shelf_type')

    book = get_object_or_404(Book, id=book_id)

    UserShelf.objects.update_or_create(
        user=request.user,
        book=book,
        defaults={'shelf_type': shelf_type}
    )
    return redirect('dashboard')


@login_required
@require_POST
def add_comment(request, shelf_id):
    shelf_item = get_object_or_404(UserShelf, id=shelf_id, rating__isnull=False)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.shelf = shelf_item
        comment.user = request.user
        comment.save()
    return redirect('book_detail', book_id=shelf_item.book_id)


@login_required
@require_POST
def add_reply(request, comment_id):
    parent = get_object_or_404(ReviewComment, id=comment_id, parent=None)
    if parent.replies.exists():
        return redirect('book_detail', book_id=parent.shelf.book_id)

    form = ReplyForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.shelf = parent.shelf
        reply.user = request.user
        reply.parent = parent
        reply.save()
    return redirect('book_detail', book_id=parent.shelf.book_id)


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(ReviewComment, id=comment_id)
    if comment.user != request.user:
        return redirect('book_detail', book_id=comment.shelf.book_id)
    book_id = comment.shelf.book_id
    comment.delete()
    return redirect('book_detail', book_id=book_id)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'core/signup.html', {'form': form})


def genre_detail(request, genre_id):
    genre = get_object_or_404(Genre, id=genre_id)
    books = genre.books.all().prefetch_related('authors')

    context = {
        'genre': genre,
        'books': books,
    }
    return render(request, 'core/genre_detail.html', context)


def author_detail(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    books = author.books.all().prefetch_related('authors')

    context = {
        'author': author,
        'books': books,
    }
    return render(request, 'core/author_detail.html', context)

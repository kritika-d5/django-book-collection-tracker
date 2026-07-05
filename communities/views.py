from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Prefetch
from django.contrib import messages
from books.models import Book
from .models import Community, CommunityMembership, CommunityPost, PostComment
from .forms import CommunityForm, CommunityPostForm, PostCommentForm


def _get_membership(community, user):
    if not user.is_authenticated:
        return None
    return CommunityMembership.objects.filter(community=community, user=user).first()


def _is_moderator(membership):
    return membership and membership.role in ('admin', 'moderator')


def community_list(request):
    communities = (
        Community.objects.filter(is_public=True)
        .annotate(annotated_member_count=Count('memberships'))
        .order_by('name')
    )
    joined = []
    joined_ids = []
    if request.user.is_authenticated:
        joined = CommunityMembership.objects.filter(user=request.user).select_related('community')
        joined_ids = list(joined.values_list('community_id', flat=True))

    context = {
        'communities': communities,
        'joined_communities': [m.community for m in joined],
        'joined_ids': joined_ids,
    }
    return render(request, 'communities/community_list.html', context)


@login_required
def community_create(request):
    if request.method == 'POST':
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user
            community.save()
            CommunityMembership.objects.create(
                community=community, user=request.user, role='admin'
            )
            return redirect('community_detail', slug=community.slug)
    else:
        form = CommunityForm()

    return render(request, 'communities/community_form.html', {'form': form})


def community_detail(request, slug):
    community = get_object_or_404(
        Community.objects.annotate(annotated_member_count=Count('memberships')),
        slug=slug,
    )
    if not community.is_public and not _get_membership(community, request.user):
        messages.error(request, 'This community is private.')
        return redirect('community_list')

    membership = _get_membership(community, request.user)
    posts = community.posts.select_related('author', 'book').prefetch_related('book__authors')

    context = {
        'community': community,
        'posts': posts,
        'membership': membership,
        'is_member': membership is not None,
    }
    return render(request, 'communities/community_detail.html', context)


@login_required
@require_POST
def join_community(request, slug):
    community = get_object_or_404(Community, slug=slug, is_public=True)
    CommunityMembership.objects.get_or_create(
        community=community, user=request.user, defaults={'role': 'member'}
    )
    return redirect('community_detail', slug=slug)


@login_required
@require_POST
def leave_community(request, slug):
    community = get_object_or_404(Community, slug=slug)
    membership = _get_membership(community, request.user)
    if membership and membership.role != 'admin':
        membership.delete()
    elif membership and membership.role == 'admin':
        if community.memberships.count() == 1:
            membership.delete()
        else:
            messages.error(request, 'Transfer admin role before leaving, or delete the community.')
    return redirect('community_list')


@login_required
def post_create(request, slug):
    community = get_object_or_404(Community, slug=slug)
    membership = _get_membership(community, request.user)
    if not membership:
        return redirect('community_detail', slug=slug)

    if request.method == 'POST':
        form = CommunityPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.community = community
            post.author = request.user
            post.save()
            return redirect('post_detail', slug=slug, post_id=post.id)
    else:
        form = CommunityPostForm()
        form.fields['book'].queryset = Book.objects.all().order_by('title')

    return render(request, 'communities/post_form.html', {
        'form': form,
        'community': community,
    })


def post_detail(request, slug, post_id):
    community = get_object_or_404(Community, slug=slug)
    top_level = PostComment.objects.filter(parent=None).select_related('user').prefetch_related(
        Prefetch('replies', queryset=PostComment.objects.select_related('user').order_by('created_at'))
    )
    post = get_object_or_404(
        CommunityPost.objects.select_related('author', 'book').prefetch_related(
            Prefetch('comments', queryset=top_level),
            'book__authors',
        ),
        id=post_id,
        community=community,
    )

    membership = _get_membership(community, request.user)
    can_comment = membership is not None

    context = {
        'community': community,
        'post': post,
        'membership': membership,
        'can_comment': can_comment,
        'is_moderator': _is_moderator(membership),
    }
    return render(request, 'communities/post_detail.html', context)


@login_required
@require_POST
def add_post_comment(request, slug, post_id):
    community = get_object_or_404(Community, slug=slug)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    if not _get_membership(community, request.user):
        return redirect('post_detail', slug=slug, post_id=post_id)

    form = PostCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
    return redirect('post_detail', slug=slug, post_id=post_id)


@login_required
@require_POST
def add_post_reply(request, slug, comment_id):
    community = get_object_or_404(Community, slug=slug)
    parent = get_object_or_404(PostComment, id=comment_id, parent=None, post__community=community)
    if not _get_membership(community, request.user):
        return redirect('post_detail', slug=slug, post_id=parent.post_id)
    if parent.replies.exists():
        return redirect('post_detail', slug=slug, post_id=parent.post_id)

    form = PostCommentForm(request.POST)
    if form.is_valid():
        reply = form.save(commit=False)
        reply.post = parent.post
        reply.user = request.user
        reply.parent = parent
        reply.save()
    return redirect('post_detail', slug=slug, post_id=parent.post_id)


@login_required
@require_POST
def delete_post_comment(request, slug, comment_id):
    comment = get_object_or_404(PostComment, id=comment_id, post__community__slug=slug)
    membership = _get_membership(comment.post.community, request.user)
    if comment.user != request.user and not _is_moderator(membership):
        return redirect('post_detail', slug=slug, post_id=comment.post_id)
    post_id = comment.post_id
    comment.delete()
    return redirect('post_detail', slug=slug, post_id=post_id)


@login_required
@require_POST
def delete_post(request, slug, post_id):
    community = get_object_or_404(Community, slug=slug)
    post = get_object_or_404(CommunityPost, id=post_id, community=community)
    membership = _get_membership(community, request.user)
    if post.author != request.user and not _is_moderator(membership):
        return redirect('post_detail', slug=slug, post_id=post_id)
    post.delete()
    return redirect('community_detail', slug=slug)

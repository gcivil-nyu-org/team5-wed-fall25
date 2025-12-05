from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from profiles.models import Profile


class Community(models.Model):
    """
    Community model for student groups.
    Can be public, private, or university-restricted.
    """
    PRIVACY_CHOICES = [
        ('public', 'Public - Anyone can join'),
        ('private', 'Private - Approval required'),
        ('university', 'University - Restricted to specific .edu domain'),
    ]

    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(max_length=1000)
    cover_image = models.ImageField(upload_to='community_covers/', blank=True, null=True)

    # Privacy & Access
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    university = models.CharField(
        max_length=100,
        choices=Profile.UNIVERSITY_CHOICES,
        blank=True,
        null=True
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='communities_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats (denormalized for performance)
    member_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Communities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['privacy']),
            models.Index(fields=['university']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure unique slug
            while Community.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that university field is set for university-restricted communities"""
        if self.privacy == 'university' and not self.university:
            raise ValidationError({
                'university': 'University field is required for university-restricted communities.'
            })


class CommunityMember(models.Model):
    """
    Membership model linking users to communities with roles and status.
    """
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('banned', 'Banned'),
    ]

    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For join requests (private communities)
    request_message = models.TextField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membership_reviews'
    )

    class Meta:
        unique_together = ('community', 'user')
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['community', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['community', 'role']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.community.name} ({self.role})"


class Post(models.Model):
    """
    Post model for community content.
    Supports text posts with optional photo and file attachments.
    """
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts'
    )
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(max_length=10000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    # Moderation
    is_pinned = models.BooleanField(default=False)
    pinned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pinned_posts'
    )

    # Stats (denormalized for performance)
    comment_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-is_pinned', '-created_at']),
        ]

    def __str__(self):
        return f"{self.author.username} in {self.community.name}: {self.title or self.content[:50]}"


class PostImage(models.Model):
    """Images attached to posts"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='community_posts/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Image for post {self.post.id}"


class PostFile(models.Model):
    """Files attached to posts"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file = models.FileField(upload_to='community_posts/files/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.file_name} for post {self.post.id}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class Comment(models.Model):
    """
    Comment model for post replies.
    Supports nested comments (replies to comments).
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments'
    )
    content = models.TextField(max_length=2000)

    # For nested replies
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"

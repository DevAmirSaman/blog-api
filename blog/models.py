from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    published_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft'
    )
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def clean(self):
        super().clean()

        if self.status == 'published' and self.published_at is None:
            raise ValidationError(
                {
                    'published_at': 'Published posts must have a publication date set.'
                }
            )

        if self.published_at and self.published_at > timezone.now():
            raise ValidationError(
                {
                    'published_at': "The publication date cannot be in the future. Change status to 'draft' for scheduling."
                }
            )

        if self.status == 'draft' and self.published_at is not None:
            raise ValidationError(
                {
                    'status': "Cannot set a publication date while the status is 'draft'."
                }
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

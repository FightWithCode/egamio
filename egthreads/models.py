import string
import random
from django.db import models
from django.utils.text import slugify
from accounts.models import User
from games.models import Game

def generate_thread_id(length=9):
    characters = string.ascii_letters + string.digits  # Uppercase + lowercase + digits
    unique_id = ''.join(random.choice(characters) for _ in range(length))
    
    # Check if the generated ID already exists in the database
    while Thread.objects.filter(thread_id=unique_id).exists():
        unique_id = ''.join(random.choice(characters) for _ in range(length))
    
    return unique_id


class Thread(models.Model):
    thread_id = models.CharField(max_length=9, default=generate_thread_id, unique=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_threads', blank=True) 
    dislikes = models.ManyToManyField(User, related_name='disliked_threads', blank=True) 
    views = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['thread_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_description:
            # Create meta description from content
            self.meta_description = self.content[:157] + "..."
        super().save(*args, **kwargs)

class Comment(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.name} on {self.created_at}'



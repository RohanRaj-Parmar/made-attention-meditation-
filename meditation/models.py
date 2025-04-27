from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='categories/')
    image = models.ImageField(upload_to='category_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subcategories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Subcategories"
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Technique(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    TIME_OF_DAY_CHOICES = [
        ('morning', 'Morning (5 AM - 11:59 AM)'),
        ('afternoon', 'Afternoon (12 PM - 4:59 PM)'),
        ('evening', 'Evening (5 PM - 9:59 PM)'),
        ('night', 'Night (10 PM - 4:59 AM)'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='techniques')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, null=True, blank=True)
    summary = models.CharField(max_length=200)
    description = models.TextField()
    benefits = models.TextField()
    instructions = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    # video = models.FileField(upload_to='technique_videos/', null=True, blank=True)
    youtube_video_url = models.URLField(help_text="Enter YouTube video URL", blank=True, null=True)

    time_of_day = models.CharField(max_length=20, choices=TIME_OF_DAY_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('technique_detail', kwargs={'pk': self.pk})
    
    @classmethod
    def get_time_of_day(cls):
        """Return the current time of day category based on the current time"""
        current_hour = timezone.localtime(timezone.now()).hour
        
        if 5 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 17:
            return 'afternoon'
        elif 17 <= current_hour < 22:
            return 'evening'
        else:
            return 'night'


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    technique = models.ForeignKey(Technique, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'technique')
    
    def __str__(self):
        return f"{self.user.username} - {self.technique.name}"


class MeditationTechnique(models.Model):
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='techniques')
    name = models.CharField(max_length=100)
    short_description = models.TextField()
    benefits = models.TextField()
    instructions = models.TextField()
    duration = models.CharField(max_length=50, help_text="Recommended duration")
    difficulty_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ])
    image = models.ImageField(upload_to='techniques/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class ExpertProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expert_profile')
    bio = models.TextField()
    expertise = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='experts/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.email


class LiveSession(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    host = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name='hosted_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_participants = models.PositiveIntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    cover_image = models.ImageField(upload_to='sessions/', null=True, blank=True)
    google_meet_link = models.URLField(max_length=255, blank=True, null=True, 
                                      help_text="Google Meet link for this session")
    technique = models.CharField(max_length=255)
    room_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.title
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'live'
    
    @property
    def has_ended(self):
        return timezone.now() > self.end_time or self.status == 'completed'


class SessionRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_registrations')
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'session']
    
    def __str__(self):
        return f"{self.user.email} - {self.session.title}"


class ChatMessage(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email}: {self.message[:30]}..."


# This seems to be a custom User model - consider if you really need this 
# or if you can use Django's built-in User model
class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    favorite_techniques = models.ManyToManyField(MeditationTechnique, related_name='favorited_by', blank=True)
    
    def __str__(self):
        return self.username


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    technique = models.ForeignKey(MeditationTechnique, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.technique.name}"
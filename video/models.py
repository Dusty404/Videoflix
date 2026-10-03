from django.db import models

class Video(models.Model):
        created_at = models.DateTimeField(auto_now_add=True)
        title = models.CharField(max_length=100)
        description = models.TextField(max_length=1000)
        thumbnail_url = models.URLField()
        category = models.CharField(max_length=255)
        video_file = models.FileField(upload_to='videos', blank=True)
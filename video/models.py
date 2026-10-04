from pathlib import Path
from django.db import models
from django.utils.text import slugify

def video_upload_path(instance, filename):
    filename = Path(filename).name
    folder_name = slugify(Path(filename).stem) or "video"

    return f"videos/{folder_name}/{filename}"

class Video(models.Model):
        created_at = models.DateTimeField(auto_now_add=True)
        title = models.CharField(max_length=100)
        description = models.TextField(max_length=1000)
        thumbnail = models.ImageField(upload_to="thumbnails/", blank=True)
        category = models.CharField(max_length=255)
        video_file = models.FileField( upload_to=video_upload_path, blank=True)
import os
import shutil
from .models import Video
from pathlib import Path
from .tasks import convert_480p, convert_720p, convert_1080p
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import django_rq

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    if created and instance.video_file:
        queue = django_rq.get_queue("default", autocommit=True)
        queue.enqueue(convert_480p, instance.video_file.path)
        queue.enqueue(convert_720p, instance.video_file.path)
        queue.enqueue(convert_1080p, instance.video_file.path)

@receiver(post_delete, sender=Video)
def delete_files_on_delete(sender, instance, **kwargs):
    if not instance.video_file:
        return

    video_dir = Path(instance.video_file.path).resolve().parent
    videos_root = (Path(settings.MEDIA_ROOT) / "videos").resolve()

    # Nur einzelne Video-Ordner innerhalb von media/videos löschen.
    if video_dir == videos_root or videos_root not in video_dir.parents:
        return

    if video_dir.is_dir():
        shutil.rmtree(video_dir)
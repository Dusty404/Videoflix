import os
import shutil
from video_app.models import Video
from pathlib import Path
from .tasks import convert_480p, convert_720p, convert_1080p, generate_thumbnail
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import django_rq

@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    video_id = instance.pk
    video_path = instance.video_file.path

    """
    Enqueue three HLS conversion and a thumbnail creation job for a newly created video with a file.

    Args:
        sender (type[Video]): Model class emitting the post_save signal.
        instance (Video): Saved video record.
        created (bool): Whether the record was newly inserted.
        **kwargs: Additional Django signal arguments.
    """
    if created and instance.video_file:
        queue = django_rq.get_queue("default", autocommit=True)
        queue.enqueue(generate_thumbnail, video_id)
        queue.enqueue(convert_480p, video_path)
        queue.enqueue(convert_720p, video_path)
        queue.enqueue(convert_1080p, video_path)
        

@receiver(post_delete, sender=Video)
def delete_files_on_delete(sender, instance, **kwargs):
    """
    Remove a deleted video's source directory and generated HLS files.

    Only remove directories strictly below media/videos. Separate thumbnails
    are not removed.

    Args:
        sender (type[Video]): Model class emitting the post_delete signal.
        instance (Video): Deleted video record.
        **kwargs: Additional Django signal arguments.

    Raises:
        OSError: If removing an eligible directory fails.
    """
    if not instance.video_file:
        return

    video_dir = Path(instance.video_file.path).resolve().parent
    videos_root = (Path(settings.MEDIA_ROOT) / "videos").resolve()

    # Nur einzelne Video-Ordner innerhalb von media/videos löschen.
    if video_dir == videos_root or videos_root not in video_dir.parents:
        return

    if video_dir.is_dir():
        shutil.rmtree(video_dir)
from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = 'video'

    def ready(self):
        from . import signals
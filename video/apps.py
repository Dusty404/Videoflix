from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = 'video'

    def ready(self):
        """
        Import signal handlers when Django initializes the video application.

        Returns:
            None: This function does not return a value.
        """
        from . import signals
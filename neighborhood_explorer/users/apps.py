from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "neighborhood_explorer.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import neighborhood_explorer.users.signals  # noqa: F401
        except ImportError:
            pass

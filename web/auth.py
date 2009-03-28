# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth.backends import ModelBackend

from models import User

class PrklModelBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        """Use our derived User object but call superclass (contrib.auth)
        for check_password
        """

        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """User getter
        """

        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

# EOF


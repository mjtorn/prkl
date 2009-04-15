# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth.backends import ModelBackend

from prkl.web.models import User, PendingRegistration

import datetime

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


class PrklRegistrationBackend(ModelBackend):
    def authenticate(self, username=None, token=None):
        """Verify registration
        """

        week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        try:
            pend_reg = PendingRegistration.objects.select_related(depth=1).filter(token=token, confirmed_at__isnull=True, tstamp__gte=week_ago)[0]
            pend_reg.confirm()
            user = pend_reg.user
            return user
        except IndexError:
            return None

    def get_user(self, user_id):
        """User getter
        """

        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

# EOF


# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import  models as auth_models
from django.contrib.auth.models import UserManager

from django.db import models

import datetime

# Create your models here.

class User(auth_models.User):
    objects = UserManager()

    @property
    def vip_expiry(self):
        return VipExpiry.objects.filter(user=self).latest('expire_at') or None

    def set_vip(self, expire_at):
        if not isinstance(expire_at, datetime.datetime):
            raise TypeError('Need datetime')

        VipExpiry.objects.create(
            user = self,
            expire_at = expire_at
        )

    @property
    def is_vip(self):
        # NB latest() raises exception, it uses .get() in the background?
        try:
            x = VipExpiry.objects.filter(user=self).latest('expire_at')
        except VipExpiry.DoesNotExist:
            return False

        return x.expire_at > datetime.datetime.now()

    def extend_vip(self, time):
        if not isinstance(time, datetime.timedelta):
            raise TypeError('Need timedelta')

        expiry = self.vip_expiry
        if not expiry:
            raise AttributeError('Can not has vip fuck you')

        VipExpiry.objects.create(
            user = self,
            expire_at = expiry.expire_at + time
        )


class Category(models.Model):
    name = models.CharField(max_length=32, db_index=True)

    def __unicode__(self):
        return u'%s' % self.name


class Prkl(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=1024)
    user = models.ForeignKey(User, null=True)

    def __unicode__(self):
        return u'%s' % self.content


class VipExpiry(models.Model):
    user = models.ForeignKey(User)
    expire_at = models.DateTimeField()

# EOF


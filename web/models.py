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
    score = models.IntegerField(default=0)

    def __unicode__(self):
        return u'%s' % self.content

    def incr(self):
        assert self.id, 'Can not increment unsaved prkl'
        QRY_INCR = 'UPDATE %s SET score = score + 1 WHERE id=%d RETURNING score' % (self._meta.db_table, self.id)
 
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(QRY_INCR)
        self.score = cursor.fetchone()[0]
        cursor.connection.commit()

    def decr(self):
        assert self.id, 'Can not decrement unsaved prkl'
        QRY_DECR = 'UPDATE %s SET score = score - 1 WHERE id=%d RETURNING score' % (self._meta.db_table, self.id)
 
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(QRY_DECR)
        self.score = cursor.fetchone()[0]
        cursor.connection.commit()


class VipExpiry(models.Model):
    user = models.ForeignKey(User)
    expire_at = models.DateTimeField()


class ResetRequest(models.Model):
    """Log password reset requests
    """

    tstamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    token = models.CharField(max_length=255)
    reset_from_ip = models.IPAddressField(null=True, blank=True)
    reset_at = models.DateTimeField(null=True, blank=True)


class TrueId(models.Model):
    """Better-than-session cookie data
    """

    created_at = models.DateTimeField(auto_now_add=True)
    hash = models.CharField(max_length=40, db_index=True, unique=True)
    user = models.ForeignKey(User, null=True)


class PrklVote(models.Model):
    """Vote counts here
    Denormalize user and hash from TrueId, because TrueId can have
    an anonymous user or n+1 different users logging in one after the other.
    So we need to see who has voted already based on this data
    """

    created_at = models.DateTimeField(auto_now_add=True)
    prkl = models.ForeignKey(Prkl)
    trueid = models.ForeignKey(TrueId, null=True)
    user = models.ForeignKey(User, null=True)
    vote = models.IntegerField()

    class Meta:
        unique_together = (('prkl', 'trueid'), ('prkl', 'user'))

# EOF


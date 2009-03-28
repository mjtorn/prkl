# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import  models as auth_models

from django.utils.datastructures import SortedDict

from django.db import models
from django.db import transaction

from prkl import thumbs

import datetime

# Create your querysets here
class PrklQuerySet(models.query.QuerySet):
    def can_vote(self, votes):
        """Set vote status
        """

        voted_prkls = tuple([v.prkl_id for v in votes])

        # And take care of those in prkls
        if not voted_prkls:
            self = self.extra({
                'can_vote': 'SELECT true',
            })
        elif len(voted_prkls) == 1:
            self = self.extra({
                'can_vote': 'SELECT web_prkl.id <> %d' % voted_prkls[0]
            })
        else:
            self = self.extra({
                'can_vote': 'SELECT web_prkl.id NOT IN %s' % str(voted_prkls)
            })

        return self


class PrklVoteQuerySet(models.query.QuerySet):
    def your_votes(self, request):
        """Check an http request to see your votes
        """

        # Anonymous or not decides
        if request.user.id:
            your_votes = self.filter(user=request.user)
        else:
            your_votes = self.filter(trueid=request.true_id)

        # Then see which votes exactly were found
        return your_votes

QRY_LEVENSHTEIN = 'levenshtein(%s, %s)'

class LevenshteinQuerySet(models.query.QuerySet):
    """Queryset that allows us passing in a query for Levenshtein distances
    """

    def levenshtein(self, col, val):
        """Levenshtein attribute for objects, using extra, a subquery,
        so it's marginally slower than an extra column
        """

        select_dict = SortedDict()

        # Don't escape col or it goes bad
        select_dict['levenshtein'] = QRY_LEVENSHTEIN % (col, '%s')

        return self.extra(select=select_dict, select_params=(val,))

# Create your managers here
class PrklManager(models.Manager):
    def get_query_set(self):
        return PrklQuerySet(self.model)


class PrklVoteManager(models.Manager):
    def get_query_set(self):
        return PrklVoteQuerySet(self.model)

    def your_votes(self, request):
        return self.get_query_set().your_votes(request)


class UserManager(auth_models.UserManager):
    def get_query_set(self):
        return LevenshteinQuerySet(self.model)

    def search(self, name):
        return self.filter().levenshtein('auth_user.username', name).order_by('levenshtein')

# Create your models here.

class User(auth_models.User):
    phone = models.CharField(max_length=16, null=True, blank=True, unique=True)
    location = models.CharField(max_length=24, null=True, blank=True)
    birthday = models.DateField(null=True)
    is_male = models.BooleanField(null=True)
    # Denormalize here, partially because django and outer joins suck shit
    vip_expire_at = models.DateTimeField(null=True)

    pic = thumbs.ImageWithThumbsField(upload_to='user_pics', sizes=((250,250), (50, 50), (25, 25)), null=True, blank=True)

    objects = UserManager()

    @property
    def vip_expiry(self):
        raise DeprecationWarning('Use vip_expire_at instead')
        try:
            return VipExpiry.objects.filter(user=self).latest('expire_at')
        except VipExpiry.DoesNotExist:
            return None

    @transaction.commit_on_success
    def set_vip(self, expire_at):
        if not isinstance(expire_at, datetime.datetime):
            raise TypeError('Need datetime')

        VipExpiry.objects.create(
            user = self,
            expire_at = expire_at
        )
        self.vip_expire_at = expire_at

        self.save()

    @property
    def is_vip(self):
        if self.vip_expire_at:
            return self.vip_expire_at > datetime.datetime.now()

        return False

    @transaction.commit_on_success
    def extend_vip(self, time):
        if not isinstance(time, datetime.timedelta):
            raise TypeError('Need timedelta')

        expiry = self.vip_expire_at
        if not expiry:
            raise AttributeError('Can not has vip fuck you')

        VipExpiry.objects.create(
            user = self,
            expire_at = expiry.expire_at + time
        )
        self.vip_expire_at = expiry.expire_at + time

        self.save()


class Category(models.Model):
    name = models.CharField(max_length=32, db_index=True)

    def __unicode__(self):
        return u'%s' % self.name


class Prkl(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=1024)
    user = models.ForeignKey(User, null=True)
    score = models.IntegerField(default=0)

    objects = PrklManager()

    def __unicode__(self):
        return u'%s' % self.content

    def incr(self):
        assert self.id, 'Can not increment unsaved prkl'
        QRY_INCR = 'UPDATE %s SET score = score + 1 WHERE id=%d RETURNING score' % (self._meta.db_table, self.id)
 
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(QRY_INCR)
        self.score = cursor.fetchone()[0]
        transaction.commit_unless_managed()

    def decr(self):
        assert self.id, 'Can not decrement unsaved prkl'
        QRY_DECR = 'UPDATE %s SET score = score - 1 WHERE id=%d RETURNING score' % (self._meta.db_table, self.id)
 
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(QRY_DECR)
        self.score = cursor.fetchone()[0]
        transaction.commit_unless_managed()


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
    seen_intro = models.BooleanField(default=False)
    hash = models.CharField(max_length=40, db_index=True, unique=True)
    user = models.ForeignKey(User, null=True)

    def mark_seen_intro(self):
        self.seen_intro = True
        self.save()

    def __unicode__(self):
        return u'%s' % self.hash


class PrklVote(models.Model):
    """Vote counts here
    Denormalize user and hash from TrueId, because TrueId can have
    an anonymous user or n+1 different users logging in one after the other.
    So we need to see who has voted already based on this data
    """

    objects = PrklVoteManager()

    created_at = models.DateTimeField(auto_now_add=True)
    prkl = models.ForeignKey(Prkl)
    trueid = models.ForeignKey(TrueId, null=True)
    user = models.ForeignKey(User, null=True)
    vote = models.IntegerField()

    class Meta:
        unique_together = (('prkl', 'trueid'), ('prkl', 'user'))


class PrklComment(models.Model):
    tstamp = models.DateTimeField(auto_now_add=True)
    prkl = models.ForeignKey(Prkl)
    commenting_user = models.ForeignKey(User, null=True)
    content = models.CharField(max_length=512)

    def __unicode__(self):
        return '@%d: %s' % (self.prkl_id, self.content)


class FriendInvite(models.Model):
    invite_at = models.DateTimeField(auto_now_add=True)
    sent_by_user = models.ForeignKey(User)
    recipient = models.EmailField(unique=True)
    registered_at = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.invite_at, self.recipient)

# EOF


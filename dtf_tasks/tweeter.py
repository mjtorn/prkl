# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.utils import simplejson

from taskforce.base import BaseTask

from taskforce.exceptions import TaskFailed

from prkl import dqs_settings, taskforce_settings

from twyt import twitter, data

import datetime

import urllib
import urllib2

class Tweeter(BaseTask):
    def get_tweet(self, queue_name):
        """Support only one tweet for now
        """

        dqs_connstring = 'http://%s:%s' % (dqs_settings.DQS_HOST, dqs_settings.DQS_PORT)
        dqs_connstring = '%s/q/%s/json/' % (dqs_connstring, queue_name)
        try:
            conn = urllib2.urlopen(dqs_connstring)
        except IOError, msg:
            raise TaskFailed(msg)

        res = conn.read()

        tweet = simplejson.loads(res)

        return tweet

    def soft_delete(self, queue_name, message_id):
        dqs_connstring = 'http://%s:%s' % (dqs_settings.DQS_HOST, dqs_settings.DQS_PORT)
        dqs_connstring = '%s/q/%s/delete/' % (dqs_connstring, queue_name)
        data = {
            'message_id': message_id,
            'soft': 'true'
        }
        try:
            conn = urllib2.urlopen(dqs_connstring, urllib.urlencode(data))
        except IOError, msg:
            raise TaskFailed(msg)

        res = conn.read()

    def do_tweet(self, tweet):
        t = twitter.Twitter()
        t.set_auth(taskforce_settings.TWITTER_USERNAME, taskforce_settings.TWITTER_PASSWORD)

        try:
            res = t.status_update(tweet)
        except twitter.TwitterException:
            return False

        stat = data.Status()

        stat.load_json(res)

        # Hate returning booleans
        return True

    def run(self, *args, **kwargs):
        # Canary bailout
        started_at = datetime.datetime.now()
        #max_run = datetime.timedelta(minutes=3)
        max_run = datetime.timedelta(seconds=5)

        self.progress = 'Started'
        self.results = {}

        try:
            tweet = self.get_tweet('twitter')

            # Queue empty
            if not tweet:
                self.progress = 'Done'
                self.results = {
                    'status': 'QUEUEEMPTY',
                    'tweet': None,
                }
                return self.results

        except TaskFailed, msg:
            self.progress = 'TaskFailed: %s' % msg
            raise

        import time

        success = False
        while not success:
            self.progress = 'Tweeting id %s' % tweet['id']
            self.results = {
                'status': 'RUNNING',
                'tweet': tweet,
            }

            # Don't run too long
            if datetime.datetime.now() >= started_at + max_run:
                break

            time.sleep(1)

            success = self.do_tweet(tweet['message'])

        if not success:
            self.progress = 'TASKTIMEOUT'
            raise TaskFailed('Task timed out')
        else:
            self.soft_delete('twitter', tweet['id'])

        return self.results

# EOF


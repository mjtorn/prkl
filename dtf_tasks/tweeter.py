# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.utils import simplejson

from taskforce.base import BaseTask

from taskforce.exceptions import TaskFailed

from prkl import dqs_settings

import datetime

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

    def soft_delete(self):
        pass

    def run(self, *args, **kwargs):
        # Canary bailout
        started_at = datetime.datetime.now()
        #max_run = datetime.timedelta(minutes=3)
        max_run = datetime.timedelta(seconds=10)

        self.progress = 'Started'
        self.results = {}

        try:
            tweet = self.get_tweet('twitter')
        except TaskFailed, msg:
            self.progress = 'TaskFailed: %s' % msg
            raise

        import time

        success = False
        while not success:
            time.sleep(1)
            self.progress = 'Tweeting id %s' % tweet['id']
            self.results = {
                'status': 'RUNNING',
                'tweet': tweet,
            }

            # Don't run too long
            if datetime.datetime.now() >= started_at + max_run:
                break

        if not success:
            self.progress = 'TASKTIMEOUT'
            raise TaskFailed('Task timed out')

        return self.results

# EOF


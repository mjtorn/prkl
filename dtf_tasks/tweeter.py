# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from taskforce.base import BaseTask

class Tweeter(BaseTask):
    def run(self, *args, **kwargs):
        self.progress = 'Not implemented'
        self.results = ['ENOTIMPLEMENTED']

        return self.results

# EOF


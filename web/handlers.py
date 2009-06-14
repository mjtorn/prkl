# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from prkl.web import models

import datetime

VIP_DICT = {
    '1kk': (datetime.timedelta(days=30), '200'),
    '6kk': (datetime.timedelta(days=6*30), '900'),
    '12kk': (datetime.timedelta(days=12*30), '1500'),
}


class SmsHandler(object):
    """Handle incoming sms with some resemblance of grace
    """

    class SmsHandlerException(Exception):
        pass

    class InvalidVipWord(SmsHandlerException):
        pass

    class InvalidUserId(SmsHandlerException):
        pass

    def __init__(self, ctx):
        """Deal with sms context
        """

        self.ctx = ctx

        self.sms = self.ctx['sms']

        self.data = ctx['sms_form'].cleaned_data

        self.command = self.data['command'].lower()
        self.argument_list = self.data['argument'].split()

    def jrprkl(self, vip_word, user_id):
        """Deal with the command jrprkl
        """

        ## Validate input

        # Like period word
        if vip_word != '1kk':
            raise self.InvalidVipWord(u'Tänään ei tunnettu sanaa %s prkl' % vip_word)
        else:
            period, price = VIP_DICT.get(vip_word, None)

        # And user
        try:
            user = models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            raise self.InvalidUserId(u'Tarkistathan viestisi viimeisen numeron, %s ei toimi' % user_id)
        # Then actually do it
        user.extend_vip(period)

        return period, price

    def prkl(self, vip_word, user_id):
        """Deal with the command prkl
        """

        ## Input validation
        period, price = VIP_DICT.get(vip_word, None)

        if period is None:
            raise self.InvalidVipWord(u'Tänään ei tunnettu sanaa %s prkl' % vip_word)

        try:
            user = models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            raise self.InvalidUserId(u'Tarkistathan viestisi viimeisen numeron, %s ei toimi' % user_id)

        ## Doing it
        user.extend_vip(period)

        return period, price

    def tanaan(self):
        """Parse and return content
        Would be nice if the method could be called "tänään" :P
        """

        # Don't bounce texts because they're badly formed
        content = self.sms.content
        if not content.lower().endswith('prkl'):
            if content[-1] == '.' or content[-1] == '!':
                if not content[-5:-1].lower() == 'prkl':
                    content = '%s prkl' % content
            else:
                content = '%s prkl' % content


# EOF


# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.urlresolvers import reverse

from django.test import client

from noserun import test

class TestSms(test.TestCase):
    def setup(self):
        self.client = client.Client()

    def test_010_broken_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua prkl',
            # numberfrom missing
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '666',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua prkl</message></sms>',
        }

        path = reverse('sms_incoming')
        res = self.client.post(path, data=data)
        print res

    def test_020_ok_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua prkl',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '666',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua prkl</message></sms>',
        }

        path = reverse('sms_incoming')
        res = self.client.post(path, data=data)
        print res

# EOF



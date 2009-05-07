# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.urlresolvers import reverse

from django.test import client

from prkl.web import models

from mediator import models as mediator_models

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

        path = reverse('incoming_sms')
        res = self.client.post(path, data=data)
        print res

    def test_020_ok_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua prkl',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '667',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua prkl</message></sms>',
        }

        path = reverse('incoming_sms')
        res1 = self.client.post(path, data=data)
        res2 = self.client.post(path, data=data)
        print res1
        assert res1.content == res2.content, 'Two same posts should return same result'

    def test_030_count_sms(self):
        ret = mediator_models.Sms.objects.all().count()
        exp_ret = 2
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_035_count_prkl(self):
        ret = models.Prkl.objects.all().count()
        # Where the hell did this duplication come from?
        exp_ret = 2
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_040_test_sms_content(self):
        sms = mediator_models.Sms.objects.get(id=1)
        ret = sms.content
        exp_ret = 'Tänään haluan pillua prkl'
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_050_fail_receipt(self):
        data = {
            'type': 'receipt',
            'status': '1',
            # transactionid missing
        }
        path = reverse('incoming_receipt')
        res = self.client.post(path, data=data)
        ret = res.content
        exp_ret = ''
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_050_succeed_receipt(self):
        data = {
            'type': 'receipt',
            'status': '1',
            'transactionid': '0',
        }
        path = reverse('incoming_receipt')
        res = self.client.post(path, data=data)
        ret = res.content
        exp_ret = 'OK'
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)


class TestSmsVip(test.TestCase):
    fixtures = ('initial_data',)

    def setup(self):
        self.client = client.Client()

    def test_010_broken_command(self):
        data = {
            'command': 'Prkl',
            'argument': '',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '668',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Prkl</message></sms>',
        }

        path = reverse('incoming_sms')
        res = self.client.post(path, data=data)
        print res


    def test_020_broken_argument(self):
        data = {
            'command': 'Prkl',
            'argument': '36kk',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '669',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Prkl 36kk</message></sms>',
        }

        path = reverse('incoming_sms')
        res = self.client.post(path, data=data)
        print res

    def test_030_broken_userid_argument(self):
        data = {
            'command': 'Prkl',
            'argument': '12kk 666',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '670',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Prkl 36kk 666</message></sms>',
        }

        path = reverse('incoming_sms')
        res = self.client.post(path, data=data)
        print res

    def test_040_ok_vip_order(self):
        data = {
            'command': 'Prkl',
            'argument': '12kk 1',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '671',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Prkl 36kk 1</message></sms>',
        }

        path = reverse('incoming_sms')
        res = self.client.post(path, data=data)
        print res


# EOF



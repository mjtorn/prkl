# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.core.urlresolvers import reverse

from django.test import client

from prkl.web import models

from mediator import models as mediator_models

from noserun import test

from qs.queue import models as queue_models

from cStringIO import StringIO

import base64
import os

class Test010Sms(test.TestCase):
    def setup(self):
        self.client = client.Client(HTTP_HOST='should.i.use.server_name.prkl.es')
        twit_queue, created = queue_models.Queue.objects.get_or_create(name= 'twitter')

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

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_015_broken_fixed_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua', # This should be autofixed
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '665',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua</message></sms>',
        }

        path = reverse('incoming_message')
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

        path = reverse('incoming_message')
        res1 = self.client.post(path, data=data)
        res2 = self.client.post(path, data=data)
        print res1
        assert res1.content == res2.content, 'Two same posts should return same result'

    def test_021_ok_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua prkl.',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '667',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua prkl.</message></sms>',
        }

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_022_ok_sms(self):
        data = {
            'command': 'Tänään',
            'argument': 'haluan pillua prkl!',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '667',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Tänään haluan pillua prkl!</message></sms>',
        }

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_030_count_sms(self):
        ret = mediator_models.Sms.objects.all().count()
        exp_ret = 5
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_035_count_prkl(self):
        ret = models.Prkl.objects.all().count()
        # Where the hell did this duplication come from?
        exp_ret = 5
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_040_test_sms_content(self):
        sms = mediator_models.Sms.objects.get(id=1)
        ret = sms.content
        # The sms contains "broken" data
        exp_ret = 'Tänään haluan pillua'
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_045_test_sms_content(self):
        sms = mediator_models.Sms.objects.get(id=2)
        ret = sms.content
        exp_ret = 'Tänään haluan pillua prkl'
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_046_test_sms_content(self):
        sms = mediator_models.Sms.objects.get(id=4)
        ret = sms.content
        exp_ret = 'Tänään haluan pillua prkl.'
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

    def test_047_test_sms_content(self):
        sms = mediator_models.Sms.objects.get(id=5)
        ret = sms.content
        exp_ret = 'Tänään haluan pillua prkl!'
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


class Test020SmsVip(test.TestCase):
    def setup(self):
        self.client = client.Client(HTTP_HOST='should.i.use.server_name.prkl.es')

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

        path = reverse('incoming_message')
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

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_025_broken_jrprkl_argument(self):
        data = {
            'command': 'jrprkl',
            'argument': '36kk 1',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '669',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>jrprkl 36kk 1</message></sms>',
        }

        path = reverse('incoming_message')
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
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Prkl 12kk 666</message></sms>',
        }

        path = reverse('incoming_message')
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

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_050_ok_jr_vip_order(self):
        data = {
            'command': 'Jrprkl',
            'argument': '1kk 1',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '672',
            'sms': '<?xml version="1.0" encoding="utf-8"?><sms><message>Jrprkl 1kk 1</message></sms>',
        }

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res


class Test030Mms(test.TestCase):
    def setup(self):
        self.client = client.Client(HTTP_HOST='should.i.use.server_name.prkl.es')
        twit_queue, created = queue_models.Queue.objects.get_or_create(name= 'twitter')

    def test_010_mms(self):
        # This smil is based loosely on Mediator's specs
        raw_smil = """\
<?xml version="1.0" encoding="utf-8"?>
<mms numberto="666" numberfrom="+35850666" operator="Saunalahti" transactiond="700">
<subject><![CDATA[Te testiä]]></subject>
<presentation><![CDATA[
 <smil>
   <head>
    <layout>
      <root-layout width="176" height="208"/>
      <region id="Text" width="160" height="183" top="5" left="8" fit="scroll"/>
    </layout>
   </head>
   <body>
     <par dur="5000ms">
       <text region="Text" src="Te_testi.txt"/>
     </par>
   </body>
  </smil>
]]>
</presentation>
<media filename="Te_testi.txt" mimetype="text/plain">
   <text><![CDATA[Te testiä]]></text>
</media>
<media filename="%(filename)s" mimetype="%(mimetype)s">
  <data binlength="%(binlength)s">
  %(data)s
  </data>
</media>
</mms>
        """

        TEST_FILE = '/tmp/bath_kiss.jpg'
        if not os.path.exists(TEST_FILE):
            print 'FILE NOT FOUND AAAAIEEEEEE!!!'
            return True

        f = open(TEST_FILE)
        img_data = f.read()
        binlength = f.tell()
        f.close()

        img_data_base64 = base64.urlsafe_b64encode(img_data)

        smil_subst_dict = {
            'filename': f.name.rsplit('/', 1)[1],
            'mimetype': 'image/jpeg', # Wargh hardcode
            'binlength': binlength,
            'data': img_data_base64,
        }

        smil = raw_smil % smil_subst_dict

        data = {
            'type': 'mms',
            'command': 'Tänään',
            'argument': '',
            'numberfrom': '+35850666',
            'numberto': '666',
            'operator': 'Saunalahti',
            'transactionid': '700', # The spec does not say this is present
            'smildata': smil,
        }

        path = reverse('incoming_message')
        res = self.client.post(path, data=data)
        print res

    def test_020_count_messages(self):
        ret = mediator_models.Sms.objects.all().count()
        exp_ret = 12
        assert ret == exp_ret, 'Bad value %s vs %s' % (ret, exp_ret)

# EOF



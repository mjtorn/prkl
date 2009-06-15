# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from prkl.web import models

from mediator import utils as mediator_utils

import datetime

VIP_DICT = {
    '1kk': (datetime.timedelta(days=30), '200'),
    '6kk': (datetime.timedelta(days=6*30), '900'),
    '12kk': (datetime.timedelta(days=12*30), '1500'),
}

class GsmMessageHandler(object):
    """Common superclass for SMS and MMS handler, lord of all fevers & plague
    """

    def __init__(self, ctx):
        """Deal with sms context
        """

        self.ctx = ctx

        self.sms = self.ctx['sms']

        self.data = ctx['sms_form'].cleaned_data

        self.command = self.data['command'].lower()
        self.argument_list = self.data['argument'].split()

    def tanaan(self, user, tags, tag_id, FormClass):
        """Parse and return content
        Would be nice if the method could be called "tänään" :P
        """

        ## Prep data
        # Don't bounce texts because they're badly formed
        content = self.sms.content
        if not content.lower().endswith('prkl'):
            if content[-1] == '.' or content[-1] == '!':
                if not content[-5:-1].lower() == 'prkl':
                    content = '%s prkl' % content
            else:
                content = '%s prkl' % content

        # Sort of like a fake request.POST.copy()
        data = {
            'content': content,
            'user': user,
            'tags': (tag_id,),
        }

        # Apparently this does have to be this ugly
        submit_prkl_form = FormClass(data)

        # ..sigh
        submit_prkl_form.fields['tags'].choices = tags

        new_prkl = None
        if submit_prkl_form.is_valid():
            new_prkl = submit_prkl_form.save()
            new_prkl.sms = self.sms

            new_prkl.save()

        else:
            err = submit_prkl_form.errors.get('content', None)
            if err is not None:
                raise self.PrklError(u'%s (viestistä ei veloitettu)' % err)
            else:
                raise self.PrklSevereError(u'Prkleen lisäämisessä ongelma')

        return new_prkl


class SmsHandler(GsmMessageHandler):
    """Handle incoming sms with some resemblance of grace
    """

    class SmsHandlerException(Exception):
        """Basemost class
        """

        pass


    class InvalidVipWord(SmsHandlerException):
        """When the second word a vip purchase is unrecognized
        """

        pass


    class InvalidUserId(SmsHandlerException):
        """Almost like an alias for User.DoesNotExist
        """

        pass


    class PrklError(SmsHandlerException):
        """An error in the form, string MUST contain error
        """

        pass


    class PrklSevereError(SmsHandlerException):
        """An error so severe we don't know what it is
        """

        pass


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


class MmsHandler(GsmMessageHandler):
    """Deal with mms
    """

    class MmsHandlerException(Exception):
        """Basemost class
        """

        pass


    def tanaan(self, *args, **kwargs):
        """Deal with command tänään
        """

        new_prkl = GsmMessageHandler.tanaan(self, *args, **kwargs)

        mms = self.ctx['sms']

        # I am ashamed of myself
        smildata_lines = mms.smildata.splitlines()
        if smildata_lines[0].startswith('<?xml') and 'encoding' in smildata_lines[0]:
            smildata_lines = smildata_lines[1:]

        smildata = '\n'.join(smildata_lines)

        images_xml = mediator_utils.extract_images(smildata)
        images = mediator_utils.parse_images(images_xml)

        # Argh
        for image in images:
            db_image = models.PrklMms()
            db_image.prkl = new_prkl
            from django.core.files import uploadedfile
            pic = uploadedfile.SimpleUploadedFile(image.filename, image.read(), content_type=image.mimetype)

            db_image.image.save(pic.name, pic)
            db_image.save()

    def dump_xml(self):
        mms = self.ctx['sms']

        import time
        filename = '%s.xml' % time.time()
        f = open('/tmp/%s' % filename, 'wb')
        f.write(mms.smildata)
        f.close()


# EOF


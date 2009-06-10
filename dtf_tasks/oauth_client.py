# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import httplib
import time

from django.conf import settings

from oauth import oauth

SERVER = getattr(settings, 'OAUTH_SERVER', 'twitter.com')
PORT = getattr(settings, 'OAUTH_PORT', 443)

REQUEST_TOKEN_URL = getattr(settings, 'OAUTH_REQUEST_TOKEN_URL', 'https://%s/oauth/request_token' % SERVER)
ACCESS_TOKEN_URL = getattr(settings, 'OAUTH_ACCESS_TOKEN_URL', 'https://%s/oauth/access_token' % SERVER)
AUTHORIZATION_URL = getattr(settings, 'OAUTH_AUTHORIZATION_URL', 'http://%s/oauth/authorize' % SERVER)

CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', 'vwtr9NbrZPs6mjIpbfrZMA')
CONSUMER_SECRET = getattr(settings, 'CONSUMER_SECRET', 'RShpnfQeY0UpwurO7JAGvlNbWYPjflApAoUgcI5xZWc')

CALLBACK_URL = 'http://printer.example.com/request_token_ready'
RESOURCE_URL = 'http://photos.example.net/photos'

class TwitterOAuthClient(oauth.OAuthClient):
    """Taking heavily from http://www.djangosnippets.org/snippets/1353/
    """

    def __init__(self, server, port, request_token_url, access_token_url, authorization_url, signature_method):
        self.server = server
        self.port = port

        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url

        self.connection = httplib.HTTPSConnection('%s:%d' % (self.server, self.port))
        self.signature_method = signature_method

    def fetch_response(self, oauth_request):
        """Generic response getter
        """

        url = oauth_request.to_url()
        print url,
        self.connection.request(oauth_request.http_method, url)
        response = self.connection.getresponse()
        s = response.read()
        print response.status, '->',
        print s
        return s

    def get_unauthorised_request_token(self):
        """Unauth req token
        """

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, http_url=REQUEST_TOKEN_URL
        )
        oauth_request.sign_request(self.signature_method, consumer, None)
        resp = self.fetch_response(oauth_request)

        return oauth.OAuthToken.from_string(resp)


if __name__ == '__main__':
    # Only HMAC-SHA1 for twitter
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
    client = TwitterOAuthClient(SERVER, PORT, REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZATION_URL, signature_method)

    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)

    token = client.get_unauthorised_request_token()

    print token


# EOF


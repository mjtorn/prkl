# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import httplib
import time

from django.conf import settings

from oauth import oauth

def wrap_nonce(func):
    def wrap(*args, **kwargs):
        nonce = func(*args, **kwargs)

        return 'foo-%s-bar' % nonce

    return wrap

oauth.generate_nonce = wrap_nonce(oauth.generate_nonce)

SERVER = getattr(settings, 'OAUTH_SERVER', 'twitter.com')
PORT = getattr(settings, 'OAUTH_PORT', 443)

REQUEST_TOKEN_URL = getattr(settings, 'OAUTH_REQUEST_TOKEN_URL', 'https://%s/oauth/request_token' % SERVER)
ACCESS_TOKEN_URL = getattr(settings, 'OAUTH_ACCESS_TOKEN_URL', 'https://%s/oauth/access_token' % SERVER)
AUTHORIZATION_URL = getattr(settings, 'OAUTH_AUTHORIZATION_URL', 'http://%s/oauth/authorize' % SERVER)

CONSUMER_KEY = getattr(settings, 'CONSUMER_KEY', 'n9iEqITWW8wXDzTCLWkgg')
CONSUMER_SECRET = getattr(settings, 'CONSUMER_SECRET', 'ZjALA8Sx9MIcd2PVJwPEhXCqetQzJ5dBUgTAxZ96yM')

CALLBACK_URL = 'http://printer.example.com/request_token_ready'
RESOURCE_URL = 'http://photos.example.net/photos'

class OAuthRequestFail(Exception):
    pass

class TwitterOAuthClient(oauth.OAuthClient):
    """Taking heavily from http://www.djangosnippets.org/snippets/1353/
    """

    def __init__(self, server, port, request_token_url, access_token_url, authorization_url, signature_method, consumer):
        self.server = server
        self.port = port

        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url

        self.connection = httplib.HTTPSConnection('%s:%d' % (self.server, self.port))
        self.signature_method = signature_method
        self.consumer = consumer

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
        if response.status != 200:
            raise OAuthRequestFail('An error occurred: "%s"' % s)
        return s

    def get_unauthorised_request_token(self):
        """Unauth req token
        """

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, http_url=REQUEST_TOKEN_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, None)
        resp = self.fetch_response(oauth_request)

        return oauth.OAuthToken.from_string(resp)

    def exchange_request_token_for_access_token(self, request_token):
        """Send unauthorized token to oauth for access token
        """

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=request_token, http_url=ACCESS_TOKEN_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, request_token)
        resp = self.fetch_response(oauth_request)

        return oauth.OAuthToken.from_string(resp) 


if __name__ == '__main__':
    # Only HMAC-SHA1 for twitter
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
    oauth_consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)

    client = TwitterOAuthClient(SERVER, PORT, REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZATION_URL, signature_method, oauth_consumer)

    token = client.get_unauthorised_request_token()

    access_token = client.exchange_request_token_for_access_token(token)

    print access_token


# EOF


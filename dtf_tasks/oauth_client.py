# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import httplib
import time

from oauth import oauth

# What twitter gives
REQUEST_TOKEN_URL = 'https://twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'http://twitter.com/oauth/authorize'

CALLBACK_URL = 'http://printer.example.com/request_token_ready'
RESOURCE_URL = 'http://photos.example.net/photos'

CONSUMER_KEY = 'vwtr9NbrZPs6mjIpbfrZMA'
CONSUMER_SECRET = 'RShpnfQeY0UpwurO7JAGvlNbWYPjflApAoUgcI5xZWc'

SERVER = 'twitter.com'
PORT = 443

class TwitterOAuthClient(oauth.OAuthClient):
    def __init__(self, server, port, request_token_url, access_token_url, authorization_url):
        self.server = server
        self.port = port

        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.connection = httplib.HTTPSConnection('%s:%d' % (self.server, self.port))

    def fetch_request_token(self, oauth_request):
        print self.request_token_url, '<>', oauth_request.to_url()
        print oauth_request.to_header()
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) #, headers=oauth_request.to_header())
        response = self.connection.getresponse()
        print response.status, '===', 
#        print response.read()
        return oauth.OAuthToken.from_string(response.read())

if __name__ == '__main__':
    client = TwitterOAuthClient(SERVER, PORT, REQUEST_TOKEN_URL, ACCESS_TOKEN_URL, AUTHORIZATION_URL)
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)

    # Only HMAC-SHA1 for twitter
    signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()

    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_url=REQUEST_TOKEN_URL)
    oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)

    # Hack shit fuck
#    oauth_request.parameters['oauth_signature_method'] = 'hmac-sha1'
    print 'request parameters', oauth_request.parameters
    print 'request headers   ', oauth_request.to_header()

    token = client.fetch_request_token(oauth_request)

    print token


# EOF


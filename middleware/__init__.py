# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

class TrueIdMiddleware(object):
	def process_request(self, request):
		print 'request', id(request)

	def process_response(self, request, response):
		print 'response', id(response)

		return response

# EOF


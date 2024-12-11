class InitSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'loaded_ids' not in request.session:
            request.session['loaded_ids'] = []

        response = self.get_response(request)
        return response
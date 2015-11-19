
class VCRMiddleware:
    def process_request(self, request):
        import ipdb; ipdb.set_trace()
        print("Process Request")

    def process_view(self, request, view_func, view_args, view_kwargs):
        import ipdb; ipdb.set_trace()
        print("Process View")


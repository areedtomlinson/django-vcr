from django.conf import settings

class VCRMiddleware:
    class SharedInstance:
        def init_with_state(self, cassette, state):
            if not hasattr(settings, "VCR_CASSETTE_PATH"):
                raise Exception("You must specify a VCR_CASSETTE_PATH in settings")

            self.cassette_name = cassette
            self.state = state.lower()
            # Map VCR states to i/o operations:
            vcr_states = {
              'recording': 'w',
              'replaying': 'r',
              'stopped': None
            }
            if self.state not in vcr_states:
                raise Exception("state must be one of ", acceptable_states)
            
            if self.state == "stopped":
                return

            # Fetch and parse playbook.
            self.cassette_path = '/'.join([settings.VCR_CASSETTE_PATH, cassette]).replace('//', '/')

            try:
                self.cassette_file = open(self.cassette_path, vcr_states[self.state])
            except IOError as e:
                print("Could not open cassette. I/O Error({0}): {1}".format(e.errno, e.strerror))
            
            if self.state == "replaying":
                cassette_string = cassette_file.read()
                try:
                    self.cassette_json = json.loads(cassette_string)
                except ValueError as e:
                    raise Exception("Invalid JSON: ", e)

            elif self.state == "recording":
                self.cassette_json = json.loads("{}")

        def __init__(self):
            self.init_with_state("untitled_tape", "stopped")


    shared_instance = None

    def __init__(self):
        if not VCRMiddleware.shared_instance:
            VCRMiddleware.shared_instance = VCRMiddleware.SharedInstance()

    def save(self):
        # If we're recording, write cassette JSON to cassette file.
        # TODO: determine if we need ensure_ascii=False (to make file UTF-8)
        if self.shared_instance.state == "recording":
            if hasattr(self.shared_instance, "cassette_file"):
                json.dump(self.shared_instance.cassette_json, self.shared_instance.cassette_file)

    def process_request(self, request):
        # If we're recording, we'll add this request to the cassette JSON.
        import ipdb; ipdb.set_trace()
        print("Process Request")

    def process_response(self, request, response):
        # If we're recording, we'll add this response to the cassette JSON.
        import ipdb; ipdb.set_trace()
        print("Process View")


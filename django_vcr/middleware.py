import json

from django.http import HttpResponse
from django.conf import settings

from .utils import json_for_transaction, default_url_comparator, json_for_request, json_for_response


class VCRMiddleware:
    class SharedInstance:
        url_comparator = None

        def set_url_comparator(self, comparator):
            # Pass in a url_comparator function that accepts two URLs
            # and compares them for "equality"
            self.url_comparator = comparator

        def init_with_state(self, cassette, state):
            if not hasattr(settings, "VCR_CASSETTE_PATH"):
                raise Exception("You must specify a VCR_CASSETTE_PATH in settings")

            self.cassette_name = cassette
            self.state = state.lower()
            # Map VCR states to i/o operations:
            vcr_states = {
                'recording': 'w+',
                'replaying': 'r',
                'stopped': None
            }
            if self.state not in vcr_states:
                raise Exception("state must be one of ", vcr_states)

            if self.state == "stopped":
                return

            # Fetch and parse playbook.
            self.cassette_path = '/'.join([settings.VCR_CASSETTE_PATH, cassette]).replace('//', '/')

            try:
                self.cassette_file = open(self.cassette_path, vcr_states[self.state])
            except IOError as e:
                print("Could not open cassette. I/O Error({0}): {1}".format(e.errno, e.strerror))
                raise

            if self.state == "replaying":
                cassette_string = self.cassette_file.read()
                try:
                    self.cassette_json = json.loads(cassette_string)
                except ValueError as e:
                    raise Exception("Invalid JSON: ", e)

            elif self.state == "recording":
                self.cassette_json = json.loads("{}")

        def __init__(self):
            self.init_with_state("untitled_tape", "stopped")

    shared_instance = None
    transaction_json = {"request": None, "response": None}

    @classmethod
    def inst(cls):
        if not cls.shared_instance:
            cls.shared_instance = cls.SharedInstance()
            cls.shared_instance.set_url_comparator(default_url_comparator)
        return cls.shared_instance

    @classmethod
    def set_comparator(cls, comparator):
        cls.inst().set_url_comparator(comparator)

    @classmethod
    def start(cls, cassette, state):
        cls.inst().init_with_state(cassette, state)

    @classmethod
    def save(cls):
        # If we're recording, write cassette JSON to cassette file.
        # TODO: determine if we need ensure_ascii=False (to make file UTF-8)
        if cls.inst().state == "recording":
            if hasattr(cls.inst(), "cassette_file"):
                json.dump(cls.inst().cassette_json, cls.inst().cassette_file, indent=2)
                cls.inst().cassette_file.close()

    def process_request(self, request):
        # If we're recording, we'll add this request to the cassette JSON.
        # If we're replaying, we'll short-cut the networking and return an HTTPResponse.
        if self.inst().state == "recording":
            # Reset transaction JSON:
            self.transaction_json = {"request": None, "response": None}
            self.transaction_json['request'] = json_for_request(request)
            return None
        elif self.inst().state == "replaying":
            transaction_json = json_for_transaction(request.get_full_path(), "POST", self.cassette_json, self.url_comparator, pop_transaction=True)
            if transaction_json:
                body = transaction_json['response']['body']
                response = HttpResponse(body)
                for header in transaction_json['response']['headers'].items():
                    response[header[0]] = header[1]
                return response
        return None

    def process_response(self, request, response):
        # If we're recording, we'll add this response to the cassette JSON.
        if self.inst().state == "recording":
            # Reset transaction JSON:
            self.transaction_json['response'] = json_for_response(response, request)
            json_for_transaction(request.get_full_path(), request.method, self.cassette_json, self.url_comparator, transaction_to_add=self.transaction_json)
        return response

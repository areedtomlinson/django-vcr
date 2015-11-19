import json
from django.http import HttpResponse
from django.conf import settings


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
              'recording': 'w',
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

        def json_for_transaction(self, url, method, pop_transaction=False):
            matching_urls = [url_key for url_key in self.cassette_json.keys() if self.url_comparator(url_key, url)]
            if len(matching_urls) > 0:
                url_key = matching_urls[0]
                transactions_for_url = self.cassette_json[url_key]
                method = method.upper()
                transactions = transactions_for_url.get(method, None)
                if len(transactions) > 0:
                    transaction = transactions.pop(0)
                    if pop_transaction:
                        # Push that change back to the JSON
                        self.cassette_json[url_key][method] = transactions
                    return transaction
            else:
                return None

        def __init__(self):
            self.init_with_state("untitled_tape", "stopped")

    def default_comparator(url1, url2):
        # This default comparator ignores:
        #     String case
        #     GET parameters
        #     Protocol (i.e. http/https)
        #     Base URL
        # If we start with:
        #    https://website.com/API/v1/endpoint?param=value
        #    http://staging.website.com/api/v1/endpoint?param=otherValue
        # we compare:
        #    api/v1/endpoint
        #    api/v1/endpoint
        # and return True, because they're "equal"

        # Remove case
        url1 = url1.lower()
        url2 = url2.lower()

        # Remove GET params
        url1 = url1.split("?")[0]
        url2 = url2.split("?")[0]

        # Remove protocol
        url1 = url1.split("//")[-1]
        url2 = url2.split("//")[-1]

        # Remove base URL (simple check: look for a '.' to see if this is a domain name)
        if '.' in url1.split('/')[0]:
            url1 = '/'.join(url1.split('/')[1:])
        if '.' in url2.split('/')[0]:
            url2 = '/'.join(url2.split('/')[1:])

        return url1.lstrip('/').rstrip('/') == url2.lstrip('/').rstrip('/')

    shared_instance = None

    @classmethod
    def inst(cls):
        if not cls.shared_instance:
            cls.shared_instance = cls.SharedInstance()
            cls.shared_instance.set_url_comparator(cls.default_comparator)
        return cls.shared_instance

    @classmethod
    def set_comparator(cls, comparator):
        cls.inst().set_url_comparator(comparator)

    @classmethod
    def start(cls, cassette, state):
        cls.inst().init_with_state(cassette, state)

    def save(self):
        # If we're recording, write cassette JSON to cassette file.
        # TODO: determine if we need ensure_ascii=False (to make file UTF-8)
        if self.shared_instance.state == "recording":
            if hasattr(self.shared_instance, "cassette_file"):
                json.dump(self.shared_instance.cassette_json, self.shared_instance.cassette_file)

    def process_request(self, request):
        # If we're recording, we'll add this request to the cassette JSON.
        # If we're replaying, we'll short-cut the networking and return an HTTPResponse.
        if self.inst().state == "recording":
            # TODO: serialize request and add to cassette JSON
            return None
        elif self.inst().state == "replaying":
            transaction_json = self.inst().json_for_transaction(request.get_full_path(), "POST", pop_transaction=True)
            if transaction_json:
                body = transaction_json['response']['body']
                response = HttpResponse(body)
                for header in transaction_json['response']['headers'].items():
                    response[header[0]] = header[1]
                return response
            return None
        print("Process Request")

    def process_response(self, request, response):
        # If we're recording, we'll add this response to the cassette JSON.
        print("Process View")
        return response

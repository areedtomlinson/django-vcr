import json

from django.test import TestCase


class PlaybookTestCase(TestCase):
    url_comparator = None

        def set_url_comparator(self, comparator):
            # Pass in a url_comparator function that accepts two URLs
            # and compares them for "equality"
            self.url_comparator = comparator

    def assertCassette(cassette):
        # Run through playbook and assert that given interactions lead
        # to given responses. Assumes the presence of a "transaction_list"
        # array in the JSON file.
        cassette_json = readCassetteJSON(cassette)
        transaction_list = cassette_json['transaction_list']
        self.assertCassette(cassette, transaction_list)


    def assertCassette(cassette, transaction_list):
        # Run through playbook, with transactions in the order given in 
        # array "transaction_list".
        cassette_json = readCassetteJSON(cassette)
        
        for transaction in transaction_list:
            
            matching_urls = [url_key for url_key in self.cassette_json.keys() if self.url_comparator(url_key, url)]
            if len(matching_urls) > 0:
                url_key = matching_urls[0]
                return url_key
            return None


    def readCassetteJSON(cassette):
        if not hasattr(settings, "VCR_CASSETTE_PATH"):
                raise Exception("You must specify a VCR_CASSETTE_PATH in settings")

        self.cassette_path = '/'.join([settings.VCR_CASSETTE_PATH, cassette]).replace('//', '/')

        try:
            self.cassette_file = open(self.cassette_path, vcr_states[self.state])
        except IOError as e:
            print("Could not open cassette. I/O Error({0}): {1}".format(e.errno, e.strerror))
            raise

        cassette_string = self.cassette_file.read()
        try:
            self.cassette_json = json.loads(cassette_string)
        except ValueError as e:
            raise Exception("Invalid JSON: ", e)

        return self.cassette_json        
    
    

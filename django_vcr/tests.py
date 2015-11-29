import json

from dateutil.parser import parse as dateparse
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .utils import json_for_transaction, default_url_comparator, ordered_json


class PlaybookTestCase(APITestCase):
    url_comparator = default_url_comparator

    def set_url_comparator(self, comparator):
        # Pass in a url_comparator function that accepts two URLs
        # and compares them for "equality"
        self.url_comparator = comparator

    def assert_cassette(self, cassette):
        # Run through playbook and assert that given interactions lead
        # to given responses. Assumes the presence of a "transaction_list"
        # array in the JSON file.
        cassette_json = self.read_cassette_json(cassette)
        transaction_list = cassette_json['transaction_list']
        self.assertCassette(cassette, transaction_list)

    def make_request_from_json(self, cassette_json, url, method, user_email):
        api_method = {
            'DELETE': self.client.delete,
            'GET': self.client.get,
            'HEAD': self.client.head,
            'OPTIONS': self.client.options,
            'PATCH': self.client.patch,
            'POST': self.client.post,
            'PUT': self.client.put,
        }

        # Get specified user, or None
        user = User.objects.filter(email=user_email).first()
        # If user is None, this resets authentication
        self.client.force_authenticate(user=user)

        body = json.loads(json.dumps(cassette_json['body']))
        headers = cassette_json['headers']

        response = api_method[method](
            url,
            body,
            # format='json',
            content_type='application/json',
            **headers
        )

        return response

    def assertCompatibleJSON(self, taped={}, returned={}):
        # Order JSON:
        taped = ordered_json(taped)
        returned = ordered_json(taped)

        self.recursive_compare_json(taped=taped, returned=returned)

    def recursive_compare_json(self, taped=[], returned=[]):
        taped_keys = [item[0] for item in taped]
        returned_keys = [item[0] for item in returned]
        for index in range(len(taped)):
            taped_key = taped[index][0]
            taped_value = taped[index][1]

            self.assertTrue(len(returned) > index, "Key '{key}' missing from returned response".format(key=taped_key))
            returned_key = returned[index][0]
            returned_value = returned[index][1]

            print("Comparing:\n\t{taped_key}: {taped_value}\n\t{returned_key}: {returned_value}".format(taped_key=taped_key, taped_value=taped_value, returned_key=returned_key, returned_value=returned_value))

            self.assertEqual(taped_key, returned_key, "Key '{key}' missing from returned response".format(key=taped_key))

            # If both values are None, skip:
            if taped_value is None:
                if returned_value is None:
                    continue
                else:
                    self.fail("Taped value is None, but returned value is not None")

            # We deal with lists in a particular manner:
            if isinstance(taped_value, list):
                self.assertTrue(isinstance(returned_value, list), "Type mismatch: taped value for {key} is a list, but returned value is not a list".format(key=taped_key))
                self.recursive_compare_json(taped=taped_value, returned=returned_value)
                continue

            # Checks for string only:
            if isinstance(taped_value, str):
                if not isinstance(returned_value, str):
                    self.fail("Taped value was a string, but returned value was not")
                # Try to parse as a date:
                try:
                    dateparse(taped_value)
                except (ValueError, AttributeError):
                    pass
                else:
                    try:
                        dateparse(returned_value)
                    except ValueError:
                        self.fail("Taped value is a date, but returned value is not")
                    else:
                        continue

                # Try to parse as a URL (simple check for scheme type):
                if bool(urlparse(taped_value).scheme):
                    if bool(urlparse(returned_value).scheme):
                        continue
                    else:
                        self.fail("Taped value is a URL, but returned value is not")

            # Value wasn't a list, date, or URL... compare values straight-up.
            self.assertEqual(taped_value, returned_value, "Value mismatch:\nTaped: {taped}\nReturned: {returned}".format(taped=taped_value, returned=returned_value))
        

    def assert_taped_response(self, response_json, response):
        # Status Code
        self.assertEqual(response_json['code'], response.status_code, "Status code mismatch")
        
        # Headers
        # For the time being, only compare the following headers:
        headers_to_compare = ['Content-Type', 'X-Frame-Options', 'Allow', 'Vary', 'Content-Language']
        for header in headers_to_compare:
            self.assertTrue(response.has_header(header), "Header {header} missing from response".format(header=header))
            self.assertTrue(header in response_json['headers'].keys(), "Header {header} missing from response".format(header=header))
            self.assertEqual(response[header], response_json['headers'][header], "Header {header} mismatch".format(header=header))
        
        # Body
        # Simple comparison:
        #self.assertTrue(ordered_json(json.loads(response.content.decode("utf-8"))) == ordered_json(json.loads(response_json['body'])))
        self.assertCompatibleJSON(taped=json.loads(response.content.decode("utf-8")), returned=json.loads(response_json['body']))

        # What we really want to check for is backwards compatability, i.e. we
        # want to make sure no keys have been removed that weren't explicitly marked
        # as being OK to remove.
        #.....

    def assert_cassette_with_transaction_list(self, cassette, transaction_list):
        # Run through playbook, with transactions in the order given in
        # array "transaction_list".
        cassette_json = self.read_cassette_json(cassette)

        for transaction in transaction_list:
            url = transaction['url']
            method = transaction['method']
            user_email = transaction['user_email']
            json = json_for_transaction(url, method, cassette_json, self.url_comparator, pop_transaction=True)

            """
        response = self.client.put(
            reverse(
                'api-order-list',
                kwargs={'version': 'v1_1'}
            ),
            {
                'number': order.number,
                'naive_reservation_start': start_time_string,
                'estimated_duration': 180,
            }
        )
        self.assertEqual(response.status_code, 200)
        order = Order.pending_objects.get(number=order.number)
        expected_non_naive_start_datetime = market.time_zone.localize(datetime(2015, 5, 7, 10, 00))
        self.assertEqual(order.localized_reservation_start, expected_non_naive_start_datetime)




        for key in response.keys():
            if response.get(key) is None or key == 'pricing' or key == 'ordernotes':
                pass
            else:
                self.assertEqual(response.get(key), self.order_data_v1.get(key), "Values in key {} don't match.".format(key))

            """
            response = self.make_request_from_json(json['request'], url, method, user_email)
            self.assert_taped_response(json['response'], response)

    def read_cassette_json(self, cassette):
        if not hasattr(settings, "VCR_CASSETTE_PATH"):
            raise Exception("You must specify a VCR_CASSETTE_PATH in settings")

        self.cassette_path = '/'.join([settings.VCR_CASSETTE_PATH, cassette]).replace('//', '/')

        try:
            self.cassette_file = open(self.cassette_path, 'r')
        except IOError as e:
            print("Could not open cassette. I/O Error({0}): {1}".format(e.errno, e.strerror))
            raise

        cassette_string = self.cassette_file.read()
        try:
            self.cassette_json = json.loads(cassette_string)
        except ValueError as e:
            raise Exception("Invalid JSON: ", e)

        return self.cassette_json


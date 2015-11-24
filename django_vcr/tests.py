import json

from django.conf import settings
from django.test import TestCase
from rest_framework.test import APIClient

from utils import json_for_transaction, default_url_comparator


class PlaybookTestCase(TestCase):
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

    def make_request_from_json(self, json, url, method, user):
        client = APIClient()

        api_method = {
            'DELETE': client.delete,
            'GET': client.get,
            'HEAD': client.head,
            'OPTIONS': client.options,
            'PATCH': client.patch,
            'POST': client.post,
            'PUT': client.put,
        }

        client.force_authenticate(user=user)
        body = json['body']
        headers = json['headers']

        response = api_method[method](
            url,
            body,
            format='json',
            content_type='application/json',
            **headers
        )

        return response

    def assert_cassette_with_transaction_list(self, cassette, transaction_list):
        # Run through playbook, with transactions in the order given in
        # array "transaction_list".
        cassette_json = self.read_cassette_json(cassette)

        for transaction in transaction_list:
            url = transaction['url']
            method = transaction['method']
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
            response = self.make_request_from_json(json['request'], url, method)
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

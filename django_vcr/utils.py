def matching_url_in_cassette(url, method, cassette_json, url_comparator):
    matching_urls = [url_key for url_key in cassette_json.keys() if url_comparator(url_key, url)]
    if len(matching_urls) > 0:
        url_key = matching_urls[0]
        return url_key
    return None


def json_for_transaction(url, method, cassette_json, url_comparator, pop_transaction=False, transaction_to_add=None):
    url_key = matching_url_in_cassette(url, method, cassette_json, url_comparator)
    if url_key:
        transactions_for_url = cassette_json[url_key]
        method = method.upper()
        transactions = transactions_for_url.get(method, None)
        if transaction_to_add is not None:
            transactions.append(transaction_to_add)
            cassette_json[url_key][method] = transactions
            return transaction_to_add
        else:
            if len(transactions) > 0:
                transaction = transactions.pop(0)
                if pop_transaction:
                    # Push that change back to the JSON
                    cassette_json[url_key][method] = transactions
                return transaction
    elif transaction_to_add is not None:
        cassette_json[url] = {method: [transaction_to_add]}
    else:
        return None


def json_for_request(self, request):
    # Serialize request into JSON.
    request_json = {}
    if request.method == "POST":
        body = dict(request.POST.items())
    elif request.method == "GET":
        body = dict(request.GET.items())
    else:
        body = request.body.decode("utf-8")

    headers = {}
    valid_headers = ['CONTENT_TYPE', 'HTTP_COOKIE', 'CONTENT_LENGTH', 'SERVER_PROTOCOL']
    for header in valid_headers:
        headers[header] = request.META[header]

    request_json['body'] = body
    request_json['method'] = request.method
    request_json['headers'] = headers
    request_json['url'] = request.get_full_path()
    return request_json


def json_for_response(self, response, request):
    # Serialize response into JSON
    url = request.get_full_path()

    response_json = {}
    response_json['code'] = response.status_code
    response_json['body'] = response.data
    response_json['headers'] = dict(response.items())
    response_json['url'] = url
    return response_json


def default_url_comparator(url1, url2):
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

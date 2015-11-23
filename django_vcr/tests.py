from django.test import TestCase

class PlaybookTestCase(TestCase):
    def assertPlaybook(playbook):
        # Run through playbook and assert that given interactions lead
        # to given responses. Assumes the presence of a "transaction_list"
        # array in the JSON file.
        
        
    def assertPlaybook(playbook, transaction_list):
        # Run through playbook, with transactions in the order given in 
        # array "transaction_list".
    
    

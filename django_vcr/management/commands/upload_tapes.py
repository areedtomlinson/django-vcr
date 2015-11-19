import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    args = 'connection_string'
    help = 'Upload VCR tapes to remote server'

    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--connection_string',
            dest='connection_string',
            default=None,
            help='Connection string for uploading VCR tapes.'
        ),
    )

    def handle(self, *args, **options):
        print("This command will upload VCR tapes to a remote server.")
        # TODO: compress/zip directory at VCR_CASSETTE_PATH
        # TODO: timestamp compressed file
        # TODO: use connection string to upload to remote location

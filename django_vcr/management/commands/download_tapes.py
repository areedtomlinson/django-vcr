import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    args = 'url'
    help = 'Download VCR tapes from remote server'

    option_list = BaseCommand.option_list + (
        make_option(
            '-u', '--url',
            dest='url',
            default=None,
            help='URL for zip/tar/gz file that contains all necessary tapes.'
        ),
    )

    # TODO: make an option to change overwrite behavior

    def handle(self, *args, **options):
        print("This command will download VCR tapes from a remote server.")
        # TODO: use urllib2 to fetch from URL
        # TODO: unzip/uncompress and move to VCR_CASSETTE_PATH

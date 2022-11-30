#!/usr/bin/env python3

"""
Implemented according to https://www.cups.org/doc/api-filter.html
"""

import os
import sys

from pdfrw import PdfReader
from typing import List
from mug import connections, utils, models


class FilterError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super(msg)


class CUPSFilter:
    """
    The scheduler runs one or more [filters] to print any given job. The
    first filter reads from the print file and writes to the standard output, while
    the remaining filters read from the standard input and write to the standard
    output. The backend is the last filter in the chain and writes to the device. [1]
    """

    def __init__(self, argv: List[str], cups_env: dict, print_data: bytes = None):

        # Mug initalization

        self.db_session = connections.get_db_session()

        # Cups initalization

        self.argv = argv

        if len(argv) < 6 or len(argv) > 7:
            self.return_usage()

        # These arguments could be set some other way than sys.argv but the
        # formatting is the same regardless

        # argv[1] The job ID
        # argv[2] The user printing the job
        # argv[3] The job name/title
        # argv[4] The number of copies to print
        # argv[5] The options that were provided when the job was submitted
        # argv[6] The file to print (first program only) [1]
        self.job_id = self.argv[1]
        self.job_user = self.argv[2]
        self.job_name = self.argv[3]
        self.copies_count = self.argv[4]
        self.job_options = self.argv[5]

        self.print_data = print_data
        if not self.print_data:
            self.print_data = self.get_print_data_from_env()

        self.env = cups_env
        if not self.env:
            self.env = self.get_job_info_from_env()

    def dispatch(self):
        if self.env["CONTENT_TYPE"] != "application/pdf":
            raise FilterError(
                "Filetype was not 'application/pdf'! (currently only PDF files can be accounted for)"
            )

        # Page counting

        self.count_pages()
        if self.page_count == 0:
            self.return_no_content()

        # Accounting work

        pages_allowed = self.get_pages_allowed(self.job_user)

        if self.page_count > pages_allowed:
            self.return_quota_exceeded()

        # Pass job on to backend, all checks passed!

        # Uh-oh: this would be for if we were a filter, but it seems like the
        # way cupspykota implemented this was by acting as a backend and then
        # manually invoking the next backend in the chain...
        #
        # with sys.stdout.buffer as stdout:
        #     stdout.write(self.print_data)

        self.send_to_backend()

        exit(0)

    """
    Accounting and job data processing
    """

    def count_pages(self) -> int:
        pdf = PdfReader(fdata=self.print_data)
        self.page_count = len(pdf.pages)
        return self.page_count

    def get_pages_allowed(self, username) -> int:
        """
        Returns a user's remaining number of pages allowed to be printed, taking into account
        the user's status (whether to use their own personal quota or a group policy)
        TODO: This needs to actually check if the user has a group quota policy set to be checked instead
        """

        account_obj = (
            self.db_session.query(models.Account).filter(username=self.job_user).first()
        )

        if not account_obj:
            self.return_no_user()

        return account_obj.quota - account_obj.pages_printed

    def send_to_backend(self):
        """
        Emulate the same procedures CUPS uses to invoke backends for printing
        """
        pass

    """
    Environment initialization and preparation
    """

    def get_print_data_from_env(self) -> bytes:
        """
        Determines whether to get job data from stdin or from the CUPS data directory
        See https://www.cups.org/doc/api-filter.html#OVERVIEW for more info
        """

        data = bytes()

        fs_file = None
        if len(sys.argv) == 7:
            fs_file = sys.argv[6]
        stdin_buffer = sys.stdin.buffer

        if fs_file:
            with open(fs_file, "rb") as f:
                data = f.read()
        elif stdin_buffer:
            with stdin_buffer as stdin:
                while buffer := stdin.read():
                    data += buffer
        else:
            raise FilterError(
                "Could not find print data from standard input or ARGV[6]"
            )

        return data

    def get_job_info_from_env(self) -> dict:
        """
        Retrieves job attributes from environment variables set by CUPS
        See https://www.cups.org/doc/api-filter.html#ENVIRONMENT for more info
        """

        job = {}

        job["APPLE_LANGUAGE"] = self.env["APPLE_LANGUAGE"]
        job["CHARSET"] = self.env["CHARSET"]
        job["CLASS"] = self.env["CLASS"]
        job["CONTENT_TYPE"] = self.env["CONTENT_TYPE"]
        job["CUPS_CACHEDIR"] = self.env["CUPS_CACHEDIR"]
        job["CUPS_DATADIR"] = self.env["CUPS_DATADIR"]
        job["CUPS_FILETYPE"] = self.env["CUPS_FILETYPE"]
        job["CUPS_SERVERROOT"] = self.env["CUPS_SERVERROOT"]
        job["DEVICE_URI"] = self.env["DEVICE_URI"]
        job["FINAL_CONTENT_TYPE"] = self.env["FINAL_CONTENT_TYPE"]
        job["LANG"] = self.env["LANG"]
        job["PPD"] = self.env["PPD"]
        job["PRINTER"] = self.env["PRINTER"]
        job["RIP_CACHE"] = self.env["RIP_CACHE"]
        job["TMPDIR"] = self.env["TMPDIR"]

        return job

    """
    Exit functions
    See https://www.cups.org/doc/api-filter.html#MESSAGES for more info
    TODO: Ensure messages have the most useful, least verbose information in them (e.g. usernames)
    """

    def return_no_content(self):
        utils.stderr("ERROR: job data has no content that can be printed")
        exit(1)

    def return_no_user(self):
        utils.stderr("ERROR: user requesting job does not exist")
        exit(1)

    def return_quota_exceeded(self):
        utils.stderr("ERROR: the job exceeds the users print quota")
        exit(1)

    def return_usage(self):
        utils.stderr(
            f"Usage: {self.argv[0]} job-id user job-title nr-copies options [file]"
        )
        exit(1)


if __name__ == "__main__":
    # Reads file from environment by default; design allows for mock data to be
    # injected
    CUPSFilter(argv=sys.argv, cups_env=dict(os.environ)).dispatch()
#!/usr/bin/env python3

"""
Implemented according to https://www.cups.org/doc/api-filter.html
"""

import os
import signal
import sys
import pwd
import time

from pdfrw import PdfReader
from typing import BinaryIO, List, Optional
from mug import connections, utils, models
from mug.models import Account


class BackendError(Exception):
    """Exceptions encountered during backend processing"""


class CUPSBackend:
    """
    The scheduler runs one or more [filters] to print any given job. The
    first filter reads from the print file and writes to the standard output, while
    the remaining filters read from the standard input and write to the standard
    output. The backend is the last filter in the chain and writes to the device. [1]
    """

    def __init__(
        self, argv: List[str], cups_env: dict, print_data: Optional[BinaryIO] = None
    ):

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

        self.print_data = print_data if print_data else self.get_print_data_from_env()
        self.env = cups_env if cups_env else self.get_job_info_from_env()

    def dispatch(self):
        if self.env["CONTENT_TYPE"] != "application/pdf":
            raise BackendError(
                "Filetype was not 'application/pdf'! (currently only PDF files can be accounted for)"
            )

        # Page counting

        self.count_pages()
        if self.page_count == 0:
            self.print_err("job data has no content that can be printed")
            exit(0)  # TODO: Failure or success here??

        # Accounting work

        pages_allowed = self.get_pages_allowed(self.job_user)

        if self.page_count > pages_allowed:
            self.print_err(f"the job exceeds the users print quota ({self.job_user} has {pages_allowed} pages left and job was {self.page_count} pages)")
            exit(0)  # TODO: Failure or success here??

        retcode = self.send_to_backend()

        if retcode == 0:
            print(f"INFO: adding {self.page_count} pages to accounting for user {self.job_user}")
            self.account_pages(self.job_user, self.page_count)
        else:
            print(f"ERROR: backend returned code {retcode} unexpectedly")

        exit(retcode)

    """
    Accounting and job data processing
    """

    def count_pages(self) -> int:
        if self.print_data is None:
            raise BackendError(
                "Cannot count number of pages because print data does not exist!"
            )
        pdf = PdfReader(fdata=self.get_pdf_from_cups())
        self.page_count = len(pdf.pages)
        return self.page_count

    def get_pages_allowed(self, username) -> int:
        """
        Returns a user's remaining number of pages allowed to be printed, taking into account
        the user's status (whether to use their own personal quota or a group policy)
        TODO: This needs to actually check if the user has a group quota policy set to be checked instead
        """

        account_obj = (
            self.db_session.query(models.Account)
            .filter(Account.username == self.job_user)
            .first()
        )

        if not account_obj:
            self.print_err("user requesting job does not exist")

        # HACK: account_obj.pages_printed has been changed to default 0
        #       but might still be null in old implememtations
        if account_obj.pages_printed is None:
            account_obj.pages_printed = 0

        return account_obj.quota - account_obj.pages_printed

    def account_pages(self, username, page_count):
        account_obj: Optional[models.Account] = (
            self.db_session.query(models.Account)
            .filter(Account.username == username)
            .first()
        )

        if not account_obj:
            raise BackendError("Tried to account for account that does not exist!")

        # TODO: Don't assume personal quota is whats being used
        account_obj.pages_printed += page_count
        print(f"INFO: {self.job_user} has now printed {account_obj.pages_printed} of their {account_obj.quota} allowed", file=sys.stderr)

        self.db_session.commit()

    def send_to_backend(self):
        """
        Emulate the same procedures CUPS uses to invoke backends for printing
        Derived from Pykota's CUPSBackend.runOriginalBackend
        """

        # socket://192.168.1.1:6000
        # mug://socket://192.168.1.1:6000
        # mug://cups-pdf:/
        # TODO: This needs to be done rigorously (proper URI parsing)
        backend_bin = os.environ["DEVICE_URI"].split(":")[1][2:]
        original_uri = os.environ["DEVICE_URI"][6:]  # TODO: Assuming prefix is mug://
        os.environ["DEVICE_URI"] = original_uri

        originalbackend = os.path.join(os.path.split(sys.argv[0])[0], backend_bin)
        if not os.environ["CUPS_FILETYPE"] == "job-sheet":
            arguments = [os.environ["DEVICE_URI"]] + sys.argv[1:]
        else:
            # For banners, we absolutely WANT
            # to remove any filename from the command line!
            arguments = [os.environ["DEVICE_URI"]] + sys.argv[1:6]
        arguments[2] = self.job_user  # in case it was overwritten by external script
        # TODO : do something about job-billing option, in case it was overwritten as well...
        # TODO : do something about the job title : if we are printing a banner and the backend
        # TODO : uses the job's title to name an output file (cups-pdf:// for example), we're stuck !

        self.become_root()

        pid = os.fork()

        # In the child of the fork
        if pid == 0:
            if self.print_data is not None:
                # Redirecting file handle to real backend's stdin
                os.dup2(self.print_data.fileno(), 0)
                pid = os.getpid()

            os.execve(originalbackend, arguments, os.environ)

        # In the parent of the fork

        self.drop_root()

        # Waiting for original backend to exit...
        killed = 0
        status = -1
        while status == -1:
            try:
                status = os.waitpid(pid, 0)[1]
                time.sleep(1)
            except OSError as e:
                # TODO: Once we have SIGTERM handling:
                #       `and self.gotSigTerm``
                if e.errno == 4:
                    os.kill(pid, signal.SIGTERM)
                    killed = 1

        if os.WIFEXITED(status):
            status = os.WEXITSTATUS(status)
            message = f"CUPS backend {originalbackend} returned {status}."
            self.print_info(message)
            if status:
                level = "error"
                self.Reason = message
            else:
                level = "info"
            return status
        elif not killed:
            self.Reason = f"CUPS backend {originalbackend} died abnormally."
            self.print_info(self.Reason)
            return -1
        else:
            self.Reason = f"CUPS backend {originalbackend} was killed."
            self.print_info(self.Reason)
            return 1

    """
    Environment initialization and preparation
    """

    # TODO: replace with https://wiki.debian.org/CUPSFilter to process stdin
    def get_pdf_from_cups(self) -> bytes:
        return open(f"/var/spool/cups/d{str(self.job_id).zfill(5)}-001", "rb").read()

    def get_print_data_from_env(self) -> BinaryIO:
        """
        Determines whether to get job data from stdin or from the CUPS data directory
        See https://www.cups.org/doc/api-filter.html#OVERVIEW for more info
        """

        fs_file = None
        if len(sys.argv) == 7:
            fs_file = sys.argv[6]

        stdin_buffer = sys.stdin.buffer

        if fs_file:
            return open(fs_file, "rb")

        elif stdin_buffer:
            return stdin_buffer

        else:
            raise BackendError(
                "Could not find print data from standard input or ARGV[6]"
            )

    def get_print_data(self) -> bytes:
        if self.print_data is None:
            raise BackendError("Cannot read print data because none exists!")
        data = self.print_data.read()
        # self.print_data.seek(0, 0)  # Doesnt work with stdin
        return data

    def get_job_info_from_env(self) -> dict:
        """
        Retrieves job attributes from environment variables set by CUPS
        See https://www.cups.org/doc/api-filter.html#ENVIRONMENT for more info
        """

        job = {}

        job["APPLE_LANGUAGE"] = os.environ.get("APPLE_LANGUAGE", None)
        job["CHARSET"] = os.environ.get("CHARSET", None)
        job["CLASS"] = os.environ.get("CLASS", None)
        job["CONTENT_TYPE"] = os.environ.get("CONTENT_TYPE", None)
        job["CUPS_CACHEDIR"] = os.environ.get("CUPS_CACHEDIR", None)
        job["CUPS_DATADIR"] = os.environ.get("CUPS_DATADIR", None)
        job["CUPS_FILETYPE"] = os.environ.get("CUPS_FILETYPE", None)
        job["CUPS_SERVERROOT"] = os.environ.get("CUPS_SERVERROOT", None)
        job["DEVICE_URI"] = os.environ.get("DEVICE_URI", None)
        job["FINAL_CONTENT_TYPE"] = os.environ.get("FINAL_CONTENT_TYPE", None)
        job["LANG"] = os.environ.get("LANG", None)
        job["PPD"] = os.environ.get("PPD", None)
        job["PRINTER"] = os.environ.get("PRINTER", None)
        job["RIP_CACHE"] = os.environ.get("RIP_CACHE", None)
        job["TMPDIR"] = os.environ.get("TMPDIR", None)

        return job

    @staticmethod
    def become_root():
        os.seteuid(0)
        os.setegid(0)

    @staticmethod
    def drop_root():
        uid = os.geteuid()
        original_user = pwd.getpwuid(uid)

        os.seteuid(original_user.pw_uid)
        os.setegid(original_user.pw_gid)

    """
    Message functions
    See https://www.cups.org/doc/api-filter.html#MESSAGES for more info
    TODO: Ensure messages have the most useful, least verbose information in them (e.g. usernames)
    """

    def print_info(self, msg):
        utils.stderr(f"INFO: {msg}")

    def print_err(self, msg):
        utils.stderr(f"ERROR: {msg}")

    def return_usage(self):
        utils.stderr(
            f"Usage: {self.argv[0]} job-id user job-title nr-copies options [file]"
        )
        exit(1)


if __name__ == "__main__":
    # Reads file from environment by default; design allows for mock data to be
    # injected
    CUPSBackend(argv=sys.argv, cups_env=dict(os.environ)).dispatch()

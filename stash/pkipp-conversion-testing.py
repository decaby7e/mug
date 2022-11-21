#!/usr/bin/env python3

# See http://www.pykota.com/software/pkipplib
# Used to test conversion of pkipplib from 2 to 3

from pkipplib import pkipplib


def parsing():
    # Read IPP datas from a CUPS job control file
    myfile = open("/var/spool/cups/c00155")
    ippdatas = myfile.read()
    myfile.close()

    # Parse these datas
    request = pkipplib.IPPRequest(ippdatas)
    request.parse()

    # Print the whole result as a string
    print(request)

    # Access one of the job's attributes directly
    print(request.job["job-name"])


def creating():
    # Create a CUPS_GET_DEFAULT request
    request = pkipplib.IPPRequest(operation_id=pkipplib.CUPS_GET_DEFAULT)
    request.operation["attributes-charset"] = ("charset", "utf-8")
    request.operation["attributes-natural-language"] = ("naturalLanguage", "en-us")

    # Get the request as binary datas
    ippdata = request.dump()

    # Parse these datas back
    newrequest = pkipplib.IPPRequest(ippdata)
    newrequest.parse()

    # Of course, the result of parsing matches what we created before.
    print(newrequest.operation["attributes-natural-language"])


def cups():
    # Create a CUPS client instance
    # cups = pkipplib.CUPS(url="http://server:631, \
    #                      username="john", \
    #                      password="5.%!oyu")
    cups = pkipplib.CUPS(
        url="http://localhost:631",
        username="lpadmin",
        password="qwerty123",
    )

    # High level API : retrieve info about job 3 :
    answer = cups.getJobAttributes(3)
    # print(answer.job["document-format"])
    # That's all folks !

    # Lower level API :
    request = cups.newRequest(pkipplib.IPP_GET_PRINTER_ATTRIBUTES)
    request.operation["printer-uri"] = (
        "uri",
        cups.identifierToURI("printers", "MyTestPrinter"),
    )
    for attribute in ("printer-uri-supported", "printer-type", "member-uris"):
        # IMPORTANT : here, despite the unusual syntax, we append to
        # the list of requested attributes :
        request.operation["requested-attributes"] = ("nameWithoutLanguage", attribute)

    # Sends this request to the CUPS server
    answer = cups.doRequest(request)

    # Print the answer as a string of text
    print(answer)


if __name__ == "__main__":
    # parsing()
    creating()
    cups()

# Mug

Print accounting software for CUPS (a replacement to Pykota)

## Features

Mug provides users with the ability to...

- Control the passage of print jobs to printers using a custom CUPS backend

- Manage user quotas through a comprehensive and self-documented CLI (--help
  arguments provide all context needed to use the CLI)

- Consolidate deployment and management of a print server through the use of
  secured containerization technologies (namely rootless podman and standardized
  OCI images).

## Getting Started

Makefile contains most quickstart steps necessary for getting a rudimentary CUPS
server with Mug installed working. Podman has been chosen as the container
runtime for this application and is able to run this application as an
unprivileged user, an important feature considering the requirements to run
certain CUPS components as `root`.

### Creating the CUPS + Mug Environment

`make build` will create the necessary OCI images that will be used to run the
CUPS server and Mug software. This comes without Mug installed by default.

`make start` will start the containers using the OCI images built from the `make
build` step. CUPS will begin listening on port 631.

`make install` will install the Mug software into the CUPS environment.

### Initializing the Mug Environment

Before moving forward with printing from the CUPS server, we need to

TODO: show how to create a db and add users to it

### Testing Things Out

After we have created our Mug database and initialized it with a user, we can start printing!

`make print` provides a test PDF that can

## Current Limitations

### PDF Only

Currently, Mug is limited to being able to print PDFs only. This will be
broadened in the future, making use of CUPS existing extensive filter framework.
Newer versions of CUPS will deprecate filters, backend, and PPDs in favor of
creating [printer
applications](https://openprinting.github.io/documentation/01-printer-application/),
which also have the limitation of preferring PDFS, though it seems that existing
filter workflows can be preserved by encapsulation in a printer application, as
demonstrated in [this blog
post](https://openprinting.github.io/current/#the-new-architecture-for-printing-and-scanning)
by OpenPrinting.

### No Group Policies

Currently, quotas are only enforced on a user-by-user basis. This means that the
`status` attribute of accounts in Mug are not currently utilized, nor are the
attributes associated with groups.

## CUPS Administration Notes

To manually set PPD for printer in the case that the web GUI doesn't like Mug's
`device-uri`:

```sh
lpadmin -P [PPDFilePath] -d [PrinterName]
```

Printers that have been paused (most likely due to a processing failure
regarding a print job) can be resumed like so:

```sh
cupsenable [PrinterName]
```

## TODO

- [x] Add build process for cups-pdf
- [x] Fix issue w/ cups-pdf not printing
- [x] Continue conversion of pkipplib (urllib2->3)
- [x] Determine page count by generating PDF and counting pages from PDF? (replacement for `pkpgcounter`)

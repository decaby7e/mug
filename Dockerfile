ARG BASE_USER
ARG MAINTAINER
# FROM debian:buster
FROM debian:bullseye

# Install Packages (basic tools, cups, basic drivers, HP drivers)
RUN apt-get update \
&& apt-get install -y \
  sudo \
  whois \
  usbutils \
  cups \
  cups-client \
  cups-bsd \
  cups-filters \
  foomatic-db-compressed-ppds \
  printer-driver-all \
  openprinting-ppds \
  hpijs-ppds \
  hp-ppd \
  hplip \
  smbclient \
  printer-driver-cups-pdf \
  python3-pip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# Pre-install Python packages
COPY requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt &&\
    rm /tmp/requirements.txt

# Add user and disable sudo password checking
RUN useradd \
  --groups=sudo,lp,lpadmin \
  --create-home \
  --home-dir=/home/print \
  --shell=/bin/bash \
  --password=$(mkpasswd print) \
  print \
&& sed -i '/%sudo[[:space:]]/ s/ALL[[:space:]]*$/NOPASSWD:ALL/' /etc/sudoers

# Initialize mug environment (TODO: add config)
RUN mkdir /var/lib/mug &&\
    chown print:print /var/lib/mug

# Default shell
CMD ["/usr/sbin/cupsd", "-f"]

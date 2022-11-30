build: .FORCE
	podman build -t local/mug .

run:
	#   --userns keep-id:uid=1000,gid=1000 \
	sudo sysctl -w net.ipv4.ip_unprivileged_port_start=631 1>/dev/null
	podman run \
	  -itd \
	  --name mug \
	  -p 631:631 \
	  -v ./data/cups:/etc/cups \
	  -v ./data/spool:/var/spool/cups \
	  -v ./data/spool-pdf:/var/spool/cups-pdf \
	  -v ./config.toml:/etc/mug.toml \
	  -v ./data/sqlite.db:/var/lib/mug/sqlite.db \
	  local/mug

rm:
	podman stop mug
	podman rm mug

attach:
	podman exec -it mug /bin/bash

logs:
	podman exec -it mug cat /var/log/cups/error_log

install: pybuild
	podman cp build mug:/tmp/
	podman exec -it mug bash -c 'pip3 install --ignore-installed /tmp/build/*.whl'
	podman exec -it mug ln -sf /usr/local/lib/python3.9/dist-packages/mug/backend.py /usr/lib/cups/backend/mug
	podman exec -it mug chmod +x /usr/lib/cups/backend/mug

install_backend:
	podman cp mug/backend.py mug:/usr/local/lib/python3.9/dist-packages/mug/backend.py
	podman exec -it mug chmod 0500 /usr/local/lib/python3.9/dist-packages/mug/backend.py

print:
	podman cp data/test-paper.pdf mug:/tmp/
	podman exec -it mug bash -c 'lp -d MugPDF -h localhost /tmp/test-paper.pdf'

resume:
	podman exec -it mug bash -c 'cupsenable MugPDF' 

pybuild:
	mkdir -p build
	rm -rf build/*
	python3 setup.py sdist -d build/ bdist_wheel -d build/
	rm -r *.egg-info

pyinstall:
	pip3 uninstall -y build/*.whl
	pip3 install --upgrade build/*.whl

.FORCE:
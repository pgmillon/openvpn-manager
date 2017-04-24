FROM python:2.7

WORKDIR /docker

ADD config.json.docker /opt/etc/openvpn-manager/config.json
ADD . /docker

RUN pip install -e /docker

CMD python /docker/openvpn_manager/api/app.py

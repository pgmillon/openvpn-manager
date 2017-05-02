===============
OpenVPN Manager
===============

Description
===========

**OpenVPN Manager** is a simple yet effective API-based manager for OpenVPN connections.
It's originally written for my Synology DS209 NAS that I use as VPN box to connect my local network to my cloud network.

Features
========

- Complete & accessible JSON-based API
- Polling service to check connection status & automatic reconnection
- Password with Certificates (TLS) authentication

Getting Started
===============

::

    $ git clone https://github.com/pgmillon/openvpn-manager.git
    $ cd openvpn-manager
    $ docker-compose up
    
This will make an api node running on port 8888 and a poller node. Both using `config.json.docker <config.json.docker>`_.

This container is obviously not made for running your VPN connections but rather testing the API locally.

Once you get how things work, you can use the provided `API startup script <openvpn_manager/docs/initd-api.sh>`_ and `Poller startup script <openvpn_manager/docs/initd-poller.sh`_ to run everything on your Synology box.

Usage
=====

Once you have the API running, you can create the first connection ::

    $ curl -X POST -H "Content-Type: application/json" -d '{
	    "name": "My First Connection"
    }' "http://localhost:5000/api/connections"
    
    {
      "active": false, 
      "configFile": null, 
      "configuration": {}, 
      "files": [], 
      "href": "/api/connections?instid=2", 
      "id": 2, 
      "name": "My First Connection", 
      "processes": [], 
      "workingDir": "c3ccbe49e15a129147d328e41fe65f17"
    }
    
Now you can send an OpenVPN configuration file for that connection::

    $ curl -X PUT -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -F "file=@/path/to/some/configuration.ovpn" "http://localhost:5000/api/connections/2/config_file"
  
    200 OK

You can also send additional files (like certificates)::

    $ curl -X POST -H "Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW" -F "file=@/path/to/some/certificate.p12" "http://localhost:5000/api/connections/2/files"
    
Note: you can GET the list of files on connections/2/files/ and GET or DELETE each on connections/2/files/<file_id>

Once you're good to go, you can activate your connection::

    $ curl -X POST "http://localhost:5000/api/connections/2/connect"
    
    200 OK
    
Check the output of the openvpn command in <WORKDIR>/<connection_id>/openvpn.out.

Once the connection is established, you can run the poller service to ensure your connection is running.

Authors
=======

OpenVPN Manager is written and maintained by `Pierre-Gildas MILLON <pg.millon@gmail.com>`_.

`See here for the full list of contributors <https://github.com/pgmillon/openvpn-manager/graphs/contributors>`_.

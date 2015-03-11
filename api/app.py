#!/usr/bin/env python

import hashlib
import zlib
import socket
import time
import os
import psutil
import subprocess

from flask import Flask, request, json
from flask.ext.restless.manager import APIManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.helpers import url_for, make_response, send_file
from flask.json import jsonify
from os import walk, path
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey, Column
from sqlalchemy.sql.sqltypes import Integer, String, BLOB, Boolean
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

app = Flask(__name__)

app.config.update(json.load(open('/etc/openvpn-manager/config.json')))

db = SQLAlchemy(app)


class Connection(db.Model):
    __tablename__ = 'connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    configFile = Column(String, name='config_path')
    config = Column(BLOB)
    active = Column(Boolean, default=False)
    processesList = relationship('Process', backref='parentConnection')

    def href(self):
        return url_for('connectionsapi0.connectionsapi', instid=self.id)

    def processes(self):
        return [url_for('processesapi0.processesapi', instid=processUrl.pid) for processUrl in self.processesList]

    def files(self):
        return [{'name': path.basename(filename[1]), 'href': url_for('getFile', connection_id=self.id, file_id=filename[0])} for filename in self.attachments()]

    def attachments(self):
        workDir = path.join(path.abspath(app.config['WORK_DIR']), self.workingDir())

        if not path.exists(workDir):
            os.mkdir(workDir)

        filenames = [filename for (_, _, filename) in walk(workDir)]
        if filenames:
            return [(hashlib.md5(filename).hexdigest(), path.join(workDir, filename)) for filename in filenames[0]]
        else:
            return []

    def disconnect(self):
        self.active = False

        db.session.add(self)
        db.session.commit()

        for process in [process for process in self.processesList if 1 == process.status()]:
            process.stop()

    def getFreePort(self):
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def connect(self):
        configFile = self.configFileAbsPath()
        socketPath = path.join(path.abspath(app.config['WORK_DIR']), self.workingDir(), "openvpn.sock")

        options = [
            "openvpn",
            "--management", socketPath, "unix",
            "--lport", str(self.getFreePort()),
            "--config", self.configFileAbsPath()
        ]

        if "passwd-tls" == self.configuration()["auth"]:
            options.append("--management-query-passwords")

        options.append("2>&1 > %s & echo $!" % path.join(path.abspath(app.config['WORK_DIR']), self.workingDir(), "openvpn.out"))
        management = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        processEntity = Process()

        # try:
        process = subprocess.Popen(" ".join(options),
                                   cwd=os.path.dirname(configFile),
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   bufsize=1)

        processEntity.pid = int(process.stdout.readline())
        processEntity.connectionId = self.id
        self.active = True

        db.session.add(self)
        db.session.add(processEntity)

        db.session.commit()

        connect_try = 1
        while 1 == processEntity.status() and connect_try < 5:
            try:
                ++connect_try

                management.connect(socketPath)

                if "passwd-tls" == self.configuration()["auth"]:
                    management.sendall("username 'Auth' '%s'\r\n" % self.configuration()["user"])
                    management.sendall("password 'Auth' '%s'\r\n" % self.configuration()["password"])

                management.sendall("quit\r\n")
                break
            except socket.error, e:
                if e.errno in [111]:
                    time.sleep(.5)
                else:
                    raise e

        return processEntity.pid

    def attachFile(self, uploadedFile):
        """
        :type uploadedFile: werkzeug.datastructures.FileStorage
        :rtype : str
        """
        workDir = path.join(path.abspath(app.config['WORK_DIR']), self.workingDir())

        if not path.exists(workDir):
            os.mkdir(workDir)

        finalPathname = path.join(workDir, secure_filename(uploadedFile.filename))
        uploadedFile.save(finalPathname)
        return finalPathname

    def workingDir(self):
        return hashlib.md5('%d-%s' % (self.id, self.name)).hexdigest()

    def configFileAbsPath(self):
        return path.join(path.abspath(app.config['WORK_DIR']), self.workingDir(), self.configFile)

    def configuration(self):
        if self.config is None:
            return {}
        else:
            return json.loads(zlib.decompress(self.config))


class Process(db.Model):
    __tablename__ = 'processes'

    pid = Column(Integer, primary_key=True)
    connectionId = Column(Integer, ForeignKey('connections.id'), name='connection_id')

    def href(self):
        return url_for('processesapi0.processesapi', instid=self.pid)

    def connection(self):
        return url_for('connectionsapi0.connectionsapi', instid=self.connectionId)

    def status(self):
        try:
            p = psutil.Process(self.pid)
            return 1 if 'openvpn' in p.exe() else 0
        except psutil.NoSuchProcess:
            return 0

    def stop(self):
        p = psutil.Process(self.pid)
        p.terminate()


def findConnection(id):
    """
    :type id: int
    :rtype: Connection
    """
    return Connection.query.get(id)


def getFilename(connection_id, file_id):
    """
    :type connection_id: int
    :type file_id: str
    :return: str
    """
    connection = findConnection(connection_id)
    return [fileName for (fileHash, fileName) in connection.attachments() if fileHash == file_id][0]


@app.route('/api/test')
def test():
    connection = findConnection(1)

    return app.config

@app.before_first_request
def beforeFirstRequest():
    if not path.exists(app.config["WORK_DIR"]):
        os.mkdir(app.config["WORK_DIR"])

@app.route('/api/connections/<int:connection_id>/config_file', methods=['PUT'])
def setConfigFile(connection_id):
    connection = findConnection(connection_id)

    if connection.configFile is not None:
        deleteFiles(connection_id, connection.configFile)

    filename = connection.attachFile(request.files['file'])
    connection.configFile = path.basename(filename)
    db.session.add(connection)
    db.session.commit()
    return Response(status=200)


@app.route('/api/connections/<int:connection_id>/config_file', methods=['GET'])
def getConfigFile(connection_id):
    connection = findConnection(connection_id)
    return send_file(connection.configFile, as_attachment=True)


@app.route('/api/connections/<int:connection_id>/config', methods=['PUT'])
def setConfig(connection_id):
    connection = findConnection(connection_id)

    connection.config = zlib.compress(request.data)
    db.session.add(connection)
    db.session.commit()
    return Response(status=200)


@app.route('/api/connections/<int:connection_id>/files', methods=['POST'])
def attachFile(connection_id):
    connection = findConnection(connection_id)
    filename = connection.attachFile(request.files['file'])
    return jsonify({'href': url_for('getFile', connection_id=connection_id, file_id=hashlib.md5(filename).hexdigest())})


@app.route('/api/connections/<int:connection_id>/files', methods=['GET'])
def listFiles(connection_id):
    connection = findConnection(connection_id)
    return jsonify({'files': connection.files()})


@app.route('/api/connections/<int:connection_id>/files/<string:file_id>', methods=['DELETE'])
def deleteFiles(connection_id, file_id):
    try:
        filename = getFilename(connection_id, file_id)
        os.remove(filename)
        return Response(status=200)
    except IndexError:
        return make_response('File not found', 404)


@app.route('/api/connections/<int:connection_id>/files/<string:file_id>', methods=['GET'])
def getFile(connection_id, file_id):
    try:
        filename = getFilename(connection_id, file_id)
        return send_file(filename, as_attachment=True)
    except IndexError:
        return make_response('File not found', 404)


@app.route('/api/connections/<int:connection_id>/connect', methods=['POST'])
def connect(connection_id):
    connection = findConnection(connection_id)
    return jsonify({'href': url_for('processesapi0.processesapi', instid=connection.connect())})


@app.route('/api/connections/<int:connection_id>/disconnect', methods=['POST'])
def disconnect(connection_id):
    connection = findConnection(connection_id)
    connection.disconnect()
    return jsonify({'href': url_for('connectionsapi0.connectionsapi', instid=connection_id)})

manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Connection,
                   methods=['GET', 'POST', 'PUT'],
                   exclude_columns=['processesList', 'config'],
                   include_methods=['href', 'processes', 'files', 'workingDir', 'configuration'])
manager.create_api(Process, methods=['GET', 'DELETE'], exclude_columns=['connectionId', 'parentConnection'],
                   include_methods=['href', 'connection', 'status'])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888)

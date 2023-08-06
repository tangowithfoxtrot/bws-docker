import json
import subprocess
from dataclasses import dataclass

from flask import Flask, request, jsonify

bws = Flask(__name__)


# noinspection PyCompatibility
@dataclass
class BitwardenSecret:
    object: str
    id: str
    organizationId: str
    projectId: str
    key: str
    value: str
    note: str
    creationDate: str
    revisionDate: str

    @staticmethod
    def from_dict(obj) -> 'BitwardenSecret':
        assert isinstance(obj, dict)
        return BitwardenSecret(**obj)


# noinspection PyCompatibility
@dataclass
class BitwardenProject:
    object: str
    id: str
    organizationId: str
    name: str
    creationDate: str
    revisionDate: str

    @staticmethod
    def from_dict(obj) -> 'BitwardenProject':
        assert isinstance(obj, dict)
        return BitwardenProject(**obj)


class OrderedJsonEncoder(json.JSONEncoder):
    def encode(self, obj):
        # Sort the keys based on their original order in the dictionary
        # This will maintain the order of keys in the final JSON output
        if isinstance(obj, dict):
            items = sorted(
                obj.items(),
                key=lambda x: list(
                    obj.keys()).index(
                    x[0]))
            obj = dict(items)
        # noinspection PyCompatibility
        return super().encode(obj)


class CommandBuilder:
    """
    This class constructs commands based on the endpoint it is being
    instantiated in, while also nullifying arguments that are not
    provided in the request headers.
    """

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.command = []

    def build(self, _request, operation):
        self.command.append("bws")
        self.command.append(self.endpoint)
        self.command.append(operation)
        if _request.headers.get('Authorization'):
            self.command.append("-t")
            self.command.append(_request.headers.get('Authorization'))
        else:
            return jsonify(
                {'status': 'error', 'message': 'Missing Authorization header'}), 400
        if _request.headers.get('BWS-Server'):
            self.command.append("--server-url")
            self.command.append(_request.headers.get('BWS-Server'))
        if _request.method == "GET":
            return self.command  # GET requests don't have a body
        if _request.json.get('name'):
            self.command.append(_request.json.get('name'))
        if _request.json.get('value'):
            self.command.append(_request.json.get('value'))
        if self.endpoint == "secret" and _request.json.get('projectId'):
            self.command.append(_request.json.get('projectId'))
        if self.endpoint == "secret" and _request.json.get('note'):
            self.command.append("--note")
            self.command.append(_request.json.get('note'))
        return self.command


@bws.route('/api/v1/secrets', methods=['GET'])
def get_secrets():
    cmd = CommandBuilder("secret").build(request, "list")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        BitwardenSecrets = []
        for secret in json.loads(result.stdout):
            BitwardenSecrets.append(BitwardenSecret.from_dict(secret))
        response = {'status': 'success', 'data': [
            e.__dict__ for e in BitwardenSecrets]}
        return json.dumps(response, cls=OrderedJsonEncoder), 201
    else:
        response = {'status': 'error', 'message': result.stderr}
        return jsonify(response), 400


@bws.route('/api/v1/secret/<secret_id>', methods=['GET'])
def get_secret(secret_id):
    cmd = CommandBuilder("secret").build(request, "get")
    cmd.append(secret_id)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return {'status': 'success', 'data': json.loads(result.stdout)}, 200
    else:
        response = {'status': 'error', 'message': result.stderr}
        return jsonify(response), 400


@bws.route('/api/v1/secret', methods=['POST'])
def create_secret():
    cmd = CommandBuilder("secret").build(request, "create")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        response = {'status': 'success', 'data': json.loads(result.stdout)}
        return json.dumps(response, cls=OrderedJsonEncoder), 201
    else:
        response = {'status': 'error', 'message': result.stderr}
        return jsonify(response), 400


@bws.route('/api/v1/projects', methods=['GET'])
def get_projects():
    cmd = CommandBuilder("project").build(request, "list")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        BitwardenProjects = []
        for project in json.loads(result.stdout):
            BitwardenProjects.append(BitwardenProject.from_dict(project))
        response = {'status': 'success', 'data': [
            e.__dict__ for e in BitwardenProjects]}
        return json.dumps(response, cls=OrderedJsonEncoder), 201
    else:
        response = {'status': 'error', 'message': result.stderr}
        return jsonify(response), 400


@bws.route('/api/v1/project/<project_id>', methods=['GET'])
def get_project(project_id):
    cmd = CommandBuilder("project").build(request, "get")
    cmd.append(project_id)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        response = {'status': 'success', 'data': json.loads(result.stdout)}
        return json.dumps(response, cls=OrderedJsonEncoder), 201
    else:
        response = {'status': 'error', 'message': result.stderr}
        return jsonify(response), 400


@bws.route('/api/v1/project', methods=['POST'])
def create_project():
    cmd = CommandBuilder("project").build(request, "create")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        response = {'status': 'success', 'data': json.loads(result.stdout)}
        return json.dumps(response, cls=OrderedJsonEncoder), 201
    else:
        response = {'status': 'error', 'message': result.stderr, 'cmd': cmd}
        return json.dumps(response, cls=OrderedJsonEncoder), 400


if __name__ == '__main__':
    bws.run(host='0.0.0.0', port=5000)

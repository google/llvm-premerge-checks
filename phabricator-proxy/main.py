import flask
import requests
import os
from urllib.parse import urlparse, parse_qs
import json

app = flask.Flask(__name__)
app.config["DEBUG"] = True # TODO: make production
buildkite_api_token = os.getenv("BUILDKITE_API_TOKEN", "")


@app.route('/', methods=['GET'])
def home():
    return "Hi LLVM!"


@app.route('/build', methods=['POST', 'GET'])
def build():
    app.logger.info('request: %s %s', flask.request, flask.request.url)
    app.logger.info('headers: %s', flask.request.headers)
    if flask.request.method == 'POST':
        app.logger.info('data: %s', flask.request.data)
        app.logger.info('form: %s', flask.request.form)
        url = urlparse(flask.request.url)
        params = parse_qs(url.query)
        metadata = {}
        build_env = {}
        for k, v in params.items():
            if len(v) == 1:
                metadata[k] = v[0]
                build_env['ph_' + k] = v[0]
            else:
                metadata[k] = v
        branch = 'master'
        if 'scripts_branch' in metadata:
            branch = metadata['scripts_branch']
        build_request = {
            'commit': 'HEAD',
            'branch':  branch,
            'meta_data': metadata,
            'env': build_env,
        }
        app.logger.info('buildkite request: %s', build_request)
        headers = {'Authorization': f'Bearer {buildkite_api_token}'}
        response = requests.post(
            'https://api.buildkite.com/v2/organizations/llvm-project'
            '/pipelines/diff-checks/builds',
            json=build_request,
            headers=headers)
        app.logger.info('buildkite response: %s %s', response.status_code, response.text)
        rjs = json.loads(response.text)
        return rjs['id']
    else:
        return "expected POST request"


if __name__ == '__main__':
    app.run(host='0.0.0.0:8080')

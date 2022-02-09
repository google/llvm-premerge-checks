from cmath import log
from flask.logging import default_handler
from urllib.parse import urlparse, parse_qs
import flask
import json
import logging
import logging.handlers
import os
import requests


buildkite_api_token = os.getenv("BUILDKITE_API_TOKEN", "")

app = flask.Flask(__name__)
app.config["DEBUG"] = False
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
errHandler = logging.FileHandler('error.log', encoding='utf-8',)
errHandler.setLevel(logging.ERROR)
errHandler.setFormatter(formatter)
app.logger.addHandler(errHandler)
rotatingHandler = logging.handlers.TimedRotatingFileHandler('info.log', when='D', encoding='utf-8', backupCount=8)
rotatingHandler.setFormatter(formatter)
app.logger.addHandler(rotatingHandler)
app.logger.setLevel(logging.INFO)
stdoutLog = logging.StreamHandler()
stdoutLog.setFormatter(formatter)
app.logger.addHandler(stdoutLog)
app.logger.removeHandler(default_handler)

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
        build_env = {}
        for k, v in params.items():
            if len(v) == 1:
                build_env['ph_' + k] = v[0]
        refspec = 'main'
        if 'ph_scripts_refspec' in build_env:
            refspec = build_env['ph_scripts_refspec']
        build_request = {
            'commit': 'HEAD',
            'branch':  refspec,
            'env': build_env,
            'message': f'D{build_env["ph_buildable_revision"]}',
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
        return rjs['web_url']
    else:
        return "expected POST request"


if __name__ == '__main__':
    app.run(host='0.0.0.0:8080')

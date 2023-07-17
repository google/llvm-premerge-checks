import os
import json
import argparse
import requests
import time

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run sample build on buildkite.')
  parser.add_argument('--dryrun', action='store_true')
  parser.add_argument('--commit')
  pipeline='upstream-bazel-test'
  args = parser.parse_args()
  time.sleep(2)
  d = json.dumps({
      'branch': 'main',
      'commit': args.commit,
      'env': {
          'ph_log_level': 'DEBUG',
          #'ph_skip_linux': 'skip',
          'ph_linux_agents': '{"queue": "linux-google-test"}',
          #'ph_linux_agents': '{"queue": "linux-test"}',
          # 'ph_linux_agents': '{"queue": "linux-clang15-test"}',
          'ph_skip_windows': 'skip',
          #'ph_windows_agents': f'{{"name": "win-dev", "queue": "windows-test"}}',
         # 'ph_windows_agents': '{"queue": "windows-test"}',
          # 'ph_scripts_refspec': 'windows-vscmd',
          # 'ph_projects': 'all',
          'ph_skip_generated': 'skip',
          # 'ph_windows_agents': f'{{"name": "", "queue": "{queue}"}}',
      }})
  print(d)
  if (args.dryrun):
    exit(0)
  token = os.getenv('BUILDKITE_API_TOKEN')
  if token is None:
    print("'BUILDKITE_API_TOKEN' environment variable is not set")
    exit(1)

  print(f"token {token}")
  re = requests.post(f'https://api.buildkite.com/v2/organizations/llvm-project/pipelines/{pipeline}/builds',
    data=d,
    headers={'Authorization': f'Bearer {token}'})
  print(re.status_code)
  j = re.json()
  print(j['web_url'])

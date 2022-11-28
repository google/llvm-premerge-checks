import os
import json
import argparse
import requests

#         print(json.loads(re.json()))

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Run sample build on buildkite.')    
  parser.add_argument('--dryrun', action='store_true')
  args = parser.parse_args()

  d = json.dumps({
      'branch': 'main',
      'commit': 'HEAD',
      'env': {
          #'ph_skip_linux': 'skip',
          'ph_skip_generated': 'skip',
          'ph_log_level': 'DEBUG',
          'ph_skip_windows': 'skip',
          'ph_linux_agents': '{"queue": "linux-test"}',
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
  re = requests.post('https://api.buildkite.com/v2/organizations/llvm-project/pipelines/llvm-main/builds',
    data=d,
    headers={'Authorization': f'Bearer {token}'})
  print(re.status_code)
  print(re)
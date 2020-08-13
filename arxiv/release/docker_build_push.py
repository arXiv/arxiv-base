"""Runs docker login, build and push commands.

For use in travis ci and command line.

```
$export DOCKERHUB_USERNAME=frank
$export DOCKERHUB_PASSWORD=1234
$export TRAVIS_TAG=1.2.3
python -m arxiv.release.docker_build_push ./ submission-agent
```
"""

import os
import sys
from subprocess import call

try:
    tag = os.environ['TRAVIS_TAG']
    user = 'arxiv'
    context = sys.argv[1]
    label = sys.argv[2]
except Exception:
    print('Example of use:')
    print('TRAVIS_TAG=1.2.3 DOCKERHUB_PASSWORD=1234 DOCKERHUB_USERNAME=frank python -m arxiv.release.docker_build_push ./fourohfour fourohfour')
    exit(1)

try:    
    labeltag = f"{user}/{label}:{tag}"
    login = f'docker login -u "$DOCKERHUB_USERNAME" -p "$DOCKERHUB_PASSWORD"'
    build = f"""docker build -t {labeltag} {context}"""
    push = f"""docker push {labeltag}"""
    logout = "docker logout"    
    cmds = ' ' + ' && '.join([login, build, push, logout])

    #Running all the commands in a single subshell to keep docker login
    retcode = call(cmds, shell=True)
    if retcode < 0:
        print("Child was terminated by signal", -retcode, file=sys.stderr)
        exit(1)
    else:
        print("Child returned", retcode, file=sys.stderr)
        exit(retcode)
except OSError as e:
    print("Execution failed:", e, file=sys.stderr)
    exit(1)

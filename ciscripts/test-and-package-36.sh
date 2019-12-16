#!/usr/bin/env bash -e

### this script expects to be run from a docker image andyg42/centos-python36-build
### it expects the environment variables ${UPLOAD_BUCKET} and ${CIRCLE_BUILD_NUM} to be set

virtualenv-3 ~/virtualenvs/gnmvidispine
source ~/virtualenvs/gnmvidispine/bin/activate
pip install -r requirements.txt
pip install boto

declare -x PYTHONPATH=${HOME}/virtualenvs/gnmvidispine/lib/python3.6/site-packages
nosetests-3.6 --with-xunit tests/

./setup_py3.py sdist
./setup_py3.py buildrpm
./setup_py3.py awsupload --bucket ${UPLOAD_BUCKET} --path gnmvidispine --region eu-west-1  --acl public-read
#!/usr/bin/env bash -e

### this script expects to be run from a docker image andyg42/centos-python36-build
### it expects the environment variables ${UPLOAD_BUCKET} and ${CIRCLE_BUILD_NUM} to be set

if [ ! -d  $HOME/virtualenvs/gnmvidispine ]; then
    virtualenv ~/virtualenvs/gnmvidispine
fi

source ~/virtualenvs/gnmvidispine/bin/activate
pip install -r requirements.txt
pip install boto

declare -x PYTHONPATH=${HOME}/virtualenvs/gnmvidispine/lib/python2.7/site-packages
nosetests --with-xunit tests/

./setup.py sdist
./setup.py buildrpm
./setup.py buildcantemorpm
./setup.py awsupload --bucket ${UPLOAD_BUCKET} --path gnmvidispine --region eu-west-1  --acl public-read
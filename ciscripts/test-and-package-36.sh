#!/bin/bash -e

### this script expects to be run from a docker image andyg42/centos-python36-build
### it expects the environment variables ${UPLOAD_BUCKET} and ${CIRCLE_BUILD_NUM} to be set

virtualenv-3 ~/virtualenvs/gnmvidispine
source ~/virtualenvs/gnmvidispine/bin/activate
pip install -r requirements.txt
pip install boto

declare -x PYTHONPATH=${HOME}/virtualenvs/gnmvidispine/lib/python3.6/site-packages
nosetests-3.6 tests/


## In Teamcity, the source directory is a bind-mount over to the main server storage which appears not to support
## hardlinking which is required for RPM build. So we copy into the container's filesystem here.
SOURCE_DIR=$PWD
echo Original source directory is ${SOURCE_DIR}
ENDPART=`basename ${SOURCE_DIR}`
mkdir -p /usr/src/${ENDPART}
cp -a ${SOURCE_DIR}/ /usr/src || /bin/true

cd /usr/src/${ENDPART}

python3 ./setup_py3.py sdist
python3 ./setup_py3.py buildrpm

if [ ! -d "${SOURCE_DIR}/dist" ]; then
    mkdir -p ${SOURCE_DIR}/dist
fi

cp -rv dist/* ${SOURCE_DIR}/dist
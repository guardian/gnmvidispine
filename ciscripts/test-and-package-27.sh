#!/usr/bin/env bash -e

### this script expects to be run from a docker image andyg42/centos-python36-build
### it expects the environment variables ${UPLOAD_BUCKET} and ${CIRCLE_BUILD_NUM} to be set

if [ ! -d  "$HOME/virtualenvs/gnmvidispine" ]; then
    virtualenv ~/virtualenvs/gnmvidispine
fi

source ~/virtualenvs/gnmvidispine/bin/activate
pip install -r requirements.txt
pip install boto

declare -x PYTHONPATH=${HOME}/virtualenvs/gnmvidispine/lib/python2.7/site-packages
nosetests tests/

## In Teamcity, the source directory is a bind-mount over to the main server storage which appears not to support
## hardlinking which is required for RPM build. So we copy into the container's filesystem here.
SOURCE_DIR=$PWD
echo Original source directory is ${SOURCE_DIR}
ENDPART=`basename ${SOURCE_DIR}`
mkdir -p ${HOME}/gnmvidispine
cp -a ${SOURCE_DIR}/ ${HOME} || /bin/true
cd ${HOME}/${ENDPART}

./setup.py sdist
./setup.py buildrpm
./setup.py buildcantemorpm

if [ ! -d "${SOURCE_DIR}/dist" ]; then
    mkdir -p ${SOURCE_DIR}/dist
fi

cp -rv dist/* ${SOURCE_DIR}/dist
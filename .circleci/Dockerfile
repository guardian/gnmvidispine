FROM centos:7.4.1708

COPY provisionrpm.sh /tmp
RUN sh /tmp/provisionrpm.sh

RUN pip install nose pep8 virtualenv unittest2

USER circleci

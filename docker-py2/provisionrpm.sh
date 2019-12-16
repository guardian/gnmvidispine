#!/usr/bin/env bash -e

useradd circleci

yum -y clean all
yum -y install epel-release
#other packages that were present on ubuntu: libsasl2-devel libldap2-devel libssl-devel
yum -y install git python python2-pip python-virtualenv doxygen rpm-build

mkdir -p /opt/cantemo/python/
chown -R circleci /opt/cantemo/python/
yum -y remove epel-release

yum -y clean all
rm -rf /var/cache/yum
#!/usr/bin/env bash -e

useradd circleci

yum -y clean all
yum -y install epel-release
yum -y install git doxygen rpm-build python36 python36-setuptools python36-pip python36-nose python36-mock python36-devel python36-virtualenv

yum -y remove epel-release

yum -y clean all
rm -rf /var/cache/yum
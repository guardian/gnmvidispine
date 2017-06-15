#!/usr/bin/env bash -e

mkdir -p ~/rpmbuild/SOURCES
cp dist/gnmvidispine-1.9.DEV.tar.gz ~/rpmbuild/SOURCES

#make the standard rpm
rpmbuild -bb gnmvidispine-py27.spec

#make the portal rpm. First set up a suitable virtualenv for python 3
sudo mkdir -p /opt/cantemo/python
sudo chown -R ubuntu /opt/cantemo/python
sudo virtualenv /opt/cantemo/python

cat gnmvidispine-py27.spec | sed -E 's/^python/\/opt\/cantemo\/python\/bin\/python/' > temp.spec
cat temp.spec | sed -E 's/^Requires:/Requires: Portal >= 3.0/' > temp2.spec
cat temp2.spec | sed -E 's/^%define name gnmvidispine-py27/%define name gnmvidispine-portal/' > temp3.spec
cat temp3.spec | sed -E 's:--prefix=/usr:--prefix=/opt/cantemo/python:' > gnmvidispine-portal.spec

rpmbuild -bb gnmvidispine-portal.spec
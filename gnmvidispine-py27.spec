%define name gnmvidispine-py27
%define version 1.9
%define unmangled_version 1.9
%define release 1
%define sourcebundle gnmvidispine-1.9.DEV.tar.gz

Summary: An object-oriented Python interface to the Vidispine Media Asset Management system (Python 2.7)
Name: %{name}
Version: %{version}
Release: %{release}
Source0: gnmvidispine-1.9.DEV.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Andy Gallagher <andy.gallagher@theguardian.com>
Url: https://github.com/fredex42/gnmvidispine
AutoReqProv: no
Requires: python >= 2.7

%description
An object-oriented Python interface to the Vidispine Media Asset Management system

%prep
#%setup -n %{name}-%{unmangled_version}
tar xvzf ../SOURCES/%{sourcebundle}

%build
cd gnmvidispine-1.9.DEV
python setup.py build
doxygen

%install
cd gnmvidispine-1.9.DEV
python setup.py install -O1 --root=$RPM_BUILD_ROOT --prefix=/usr --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/usr/share/doc/gnmvidispine
cp -a doc/html/* $RPM_BUILD_ROOT/usr/share/doc/gnmvidispine

%clean
rm -rf $RPM_BUILD_ROOT

%files -f gnmvidispine-1.9.DEV/INSTALLED_FILES
%defattr(-,root,root)
/usr/share/doc/gnmvidispine/*

%post
if [ ! -x /opt/cantemo/python/bin/python ]; then pip install future; fi
if [ -x /opt/cantemo/python/bin/python ]; then /opt/cantemo/python/bin/pip install future; fi
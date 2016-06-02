%define name portal-gnmvidispine
%define version 1.0
%define unmangled_version 1.0
%define release 1

Summary: GNM's object-based Portal interface for Vidispine, built for Portal
Name: %{name}
Version: %{version}
Release: %{release}
License: Internal GNM software
Source0: gnmvidispine.tar.gz
Group: Applications/Libraries
#BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRoot: %{_tmppath}/gnmvidispine
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Andy Gallagher <andy.gallagher@theguardian.com>
Requires: Portal

%description
Object-oriented Python interface to the Vidispine API, used by some plugins and utilities

%prep

%build

%install
mkdir -p $RPM_BUILD_ROOT/opt/cantemo/portal/portal/plugins/gnmplutostats
cp -a /opt/cantemo/portal/portal/plugins/gnmplutostats/* $RPM_BUILD_ROOT/opt/cantemo/portal/portal/plugins/gnmplutostats

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/opt/cantemo/portal/portal/plugins/gnmplutostats

%post
/opt/cantemo/portal/manage.py collectstatic --noinput

%preun

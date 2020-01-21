#!/usr/bin/env python3
from distutils.core import setup,Command
import os
import re
import shutil

if 'CIRCLE_TAG' in os.environ:
    version = os.environ['CIRCLE_TAG']
else:
    if 'CI' in os.environ:
        buildnum = os.environ['CIRCLE_BUILD_NUM']
    else:
        buildnum = "DEV"
    version = "1.9.{build}".format(build=buildnum)
    shortversion = "1.9"
    
class AwsUploadCommand(Command):
    description = "Upload to AWS bucket. Credentials are taken from the environment defaults of the boto library. Requires boto to work"
    user_options = [
        ("region=","r", "Set the AWS region to communicate with"),
        ("bucket=","b", "Set the bucket to upload to. Note that you need both HeadObject AND PutObject permissions, not just Put"),
        ("path=","p", "Upload to this path within the bucket.  Leading / are ignored."),
        ("acl=","a", "Canned ACL to apply (see http://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl). Default is private.")
    ]
    
    @staticmethod
    def upload_callback(bytes_transferred, bytes_total):
        percent = (float(bytes_transferred)/float(bytes_total))*100
        print("awsupload: uploading %02d%%" % int(percent))
        
    def initialize_options(self):
        self.region = "eu-west-1"
        self.bucket = "pythondist"
        self.path = ""
        self.acl="private"
        
    def finalize_options(self):
        self.path = os.path.join(re.sub(r'^/+','', self.path), buildnum)
        print("awsupload: uploading to region {0}, bucket {1}, path {2}".format(self.region, self.bucket, self.path))
        
    def do_upload_file(self, bucket, localpath, filename):
        import boto.s3 as s3
        destpath = os.path.join(self.path,filename)
        print("awsupload: uploading to s3://{0}/{1} with {2} permissions".format(self.bucket,destpath, self.acl))
        key = s3.key.Key(bucket=bucket, name=destpath)
        with open(os.path.join(localpath, filename),"r") as f:
            key.set_contents_from_file(f, replace=False, cb=self.upload_callback, policy=self.acl)
            
    def run(self):
        import boto.s3 as s3
        conn = s3.connect_to_region(self.region)
        
        bucket = s3.bucket.Bucket(connection=conn, name=self.bucket)
        
        filebase = self.distribution.get_name()
        
        for filepath in os.listdir('dist'):
            if os.path.isdir(filepath): continue
            if not filepath.startswith(filebase): continue
            
            self.do_upload_file(bucket, 'dist/', filepath)


class BuildRpms(Command):
    description = "Build the RPMs for this package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def modify_specfile(self, specfile, destfile, replacements):
        """
        Modifies an RPM specfile. Pass a dictionary of {'regex_string_to_match': 'replacement'}
        :param specfile: source file to read
        :param destfile: destination file to output
        :param replacements: dictionary of {'regex_string': 'replacement_string'}
        :return: new filename
        """
        import re
        compiled_replacements = dict([(re.compile(regexstring_replacement[0]), regexstring_replacement[1]) for regexstring_replacement in list(replacements.items())])

        with open(specfile,"r") as fread:
            with open(destfile,"w") as fwrite:
                for line in fread.readlines():
                    newstring = line
                    for regex, replacement in list(compiled_replacements.items()):
                        if regex.search(line):
                            newstring = regex.sub(replacement, newstring)
                    fwrite.write(newstring)

        return destfile

    def make_rpm(self,sourcefile,dest_spec,replacements):
        """
        updates a spec file and builds an rpm from it
        :param sourcefile: source tarball
        :param dest_spec: destination name of the specfile to write
        :param replacements: dictionary of {'regex': 'replacement'} pairs to apply to specfile
        :return:
        """
        source_dist = "dist/{0}".format(sourcefile)
        rpm_buildpath = "{0}/rpmbuild".format(os.environ['HOME'])

        if not os.path.exists(rpm_buildpath):
            os.mkdir(rpm_buildpath)
            for f in ['SOURCES', 'BUILD','RPMS']:
                os.mkdir(os.path.join(rpm_buildpath,f))

        if not os.path.exists(source_dist):
            print("Could not find {0}.  Try running setup.py sdist first.".format(source_dist))
            exit(1)
        print("Using source distribution {0}".format(source_dist))
        self.modify_specfile('gnmvidispine-py36.spec',dest_spec,replacements)
        print("RPM build path is {0}".format(rpm_buildpath))
        shutil.copy(source_dist,os.path.join(rpm_buildpath, "SOURCES", sourcefile))

        os.system("rpmbuild -bb {0}".format(dest_spec))

        for filename in os.listdir(os.path.join(rpm_buildpath, "RPMS", "noarch")):
            shutil.move(os.path.join(rpm_buildpath, "RPMS", "noarch", filename), os.path.join("dist", filename))

    def run(self):
        pass


class BuildRegularRpm(BuildRpms):
    def run(self):
        sourcefile = self.distribution.get_name() + "-" + self.distribution.get_version() + ".tar.gz"
        #build the standard RPM
        self.make_rpm(sourcefile,"gnmvidispine-build.spec",
        {
            r'^%define version.*$': '%define version {0}'.format(shortversion),
            r'^%define unmangled_version.*$': '%define unmangled_version {0}'.format(shortversion),
            r'^%define sourcebundle.*$': '%define sourcebundle {0}'.format(sourcefile),
            r'^%define release.*$': '%define release {0}'.format(os.environ['CIRCLE_BUILD_NUM']),
            r'^cd gnmvidispine-.*$': 'cd {0}-{1}'.format(self.distribution.get_name(), self.distribution.get_version()),
            r'gnmvidispine-.*/INSTALLED_FILES': '{0}-{1}/INSTALLED_FILES'.format(self.distribution.get_name(),
                                                                                 self.distribution.get_version())
        })


class BuildCantemoRpm(BuildRpms):
    def run(self):
        sourcefile = self.distribution.get_name() + "-" + self.distribution.get_version() + ".tar.gz"
        #build another RPM that targets Portal
        self.make_rpm(sourcefile,"gnmvidispine-portal.spec",
        {
            r'^%define version.*$': '%define version {0}'.format(shortversion),
            r'^%define unmangled_version.*$': '%define unmangled_version {0}'.format(shortversion),
            r'^%define sourcebundle.*$': '%define sourcebundle {0}'.format(sourcefile),
            r'^%define release.*$': '%define release {0}'.format(buildnum),
            r'^Requires:': 'Requires: Portal >= 3.0 ',
            r'^%define name gnmvidispine-py36': '%define name gnmvidispine-portal',
            r'--prefix=/usr':' --prefix=/opt/cantemo/python',
            r'^cd gnmvidispine-.*$': 'cd {0}-{1}'.format(self.distribution.get_name(), self.distribution.get_version()),
            r'gnmvidispine-.*/INSTALLED_FILES': '{0}-{1}/INSTALLED_FILES'.format(self.distribution.get_name(),
                                                                                 self.distribution.get_version()),
            r'cp -a doc/html/* $RPM_BUILD_ROOT/usr/share/doc/gnmvidispine': ''  #don't include documentation or it may conflict with regular package
        })


setup(
    cmdclass={
        'awsupload': AwsUploadCommand,
        'buildrpm': BuildRegularRpm,
        'buildcantemorpm': BuildCantemoRpm
    },
    name="gnmvidispine",
    version=version,
    description="An object-oriented Python interface to the Vidispine Media Asset Management system",
    author="Andy Gallagher",
    author_email="andy.gallagher@theguardian.com",
    url="https://github.com/fredex42/gnmvidispine",
    package_data={'': ['Doxyfile']},
    packages=['gnmvidispine']
)
#!/usr/bin/env python
from distutils.core import setup,Command
import os
import re

if 'CIRCLE_TAG' in os.environ:
    version = os.environ['CIRCLE_TAG']
else:
    if 'CI' in os.environ:
        buildnum = os.environ['CIRCLE_BUILD_NUM']
    else:
        buildnum = "DEV"
    version = "1.9.{build}".format(build=buildnum)
    
    
class AwsUploadCommand(Command):
    import boto.s3 as s3
    description = "Upload to AWS bucket. Credentials are taken from the environment defaults of the boto library. Requires boto to work"
    user_options = [
        ("region=","r", "Set the AWS region to communicate with"),
        ("bucket=","b", "Set the bucket to upload to"),
        ("path=","p", "Upload to this path within the bucket.  Leading / are ignored."),
        ("acl=","a", "Canned ACL to apply (see http://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl). Default is private.")
    ]
    
    @staticmethod
    def upload_callback(bytes_transferred, bytes_total):
        percent = (float(bytes_transferred)/float(bytes_total))*100
        print "awsupload: uploading {:02d}%".format(int(percent))
        
    def initialize_options(self):
        self.region = "eu-west-1"
        self.bucket = "pythondist"
        self.path = ""
        self.acl="private"
        
    def finalize_options(self):
        self.path = os.path.join(re.sub(r'^/+','', self.path), buildnum)
        print "awsupload: uploading to region {0}, bucket {1}, path {2}".format(self.region, self.bucket, self.path)
        
    def do_upload_file(self, bucket, localpath, filename):
        destpath = os.path.join(self.path,filename)
        print "awsupload: uploading to s3://{0}/{1} with {2} permissions".format(self.bucket,destpath, self.acl)
        key = self.s3.key.Key(bucket=bucket, name=destpath)
        with open(os.path.join(localpath, filename),"r") as f:
            key.set_contents_from_file(f, replace=False, cb=self.upload_callback, policy=self.acl)
            
    def run(self):
        conn = self.s3.connect_to_region(self.region)
        
        bucket = self.s3.bucket.Bucket(connection=conn, name=self.bucket)
        
        filebase = self.distribution.get_name() + "-" + self.distribution.get_version()
        
        for filepath in os.listdir('dist'):
            if os.path.isdir(filepath): continue
            if not filepath.startswith(filebase): continue
            
            self.do_upload_file(bucket, 'dist/', filepath)

setup(
    cmdclass={
        'awsupload': AwsUploadCommand,
    },
    name="gnmvidispine",
    version=version,
    description="An object-oriented Python interface to the Vidispine Media Asset Management system",
    author="Andy Gallagher",
    author_email="andy.gallagher@theguardian.com",
    url="https://github.com/fredex42/gnmvidispine",
    packages=['gnmvidispine']
)
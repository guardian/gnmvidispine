# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
import httplib
import base64
import logging
import tempfile
from os import urandom


class TestVSStorage(unittest2.TestCase):
    fake_host = 'localhost'
    fake_port = 8080
    fake_user = 'username'
    fake_passwd = 'password'
    
    file_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><FileDocument xmlns="http://xml.vidispine.com/schema/vidispine"><id>KP-31774258</id><path>Multimedia_News/Anywhere_but_Washington/tom_silverstone_ALL_FOOTAGE/WEST VIRGINIA/EXPORTS/INTRO_WITH IDENT.mov</path><uri>omms://32bd5db9-52ca-11e4-9515-877ef3241ca7:_VSENC__gM%2FYdAoCKA2QhYNVGGEujw6t2p+j0Ulj4Ub62Rhft7mRqTzTG8W26T2bqqQpiAjO@10.235.51.145/5ce37552-358f-998b-115b-9569b8f21a01/32aae714-52ca-11e4-9515-877ef3241ca7/Multimedia_News/Anywhere_but_Washington/tom_silverstone_ALL_FOOTAGE/WEST%20VIRGINIA/EXPORTS/INTRO_WITH%20IDENT.mov</uri><state>CLOSED</state><size>96531092</size><timestamp>2016-12-26T10:04:14.093Z</timestamp><refreshFlag>1</refreshFlag><storage>KP-2</storage><metadata><field><key>MXFS_ARCHDAY</key><value>23</value></field><field><key>MXFS_ARCHYEAR</key><value>2016</value></field><field><key>MXFS_PARENTOID</key><value/></field><field><key>mtime</key><value>1474419644000</value></field><field><key>MXFS_ARCHIVE_TIME</key><value>1482476605861</value></field><field><key>MXFS_CREATIONMONTH</key><value>12</value></field><field><key>MXFS_CREATIONYEAR</key><value>2016</value></field><field><key>MXFS_INTRASH</key><value>false</value></field><field><key>MXFS_MODIFICATION_TIME</key><value>1482476605887</value></field><field><key>MXFS_CREATION_TIME</key><value>1482476605861</value></field><field><key>MXFS_FILENAME_UPPER</key><value>MULTIMEDIA_NEWS/ANYWHERE_BUT_WASHINGTON/TOM_SILVERSTONE_ALL_FOOTAGE/WEST VIRGINIA/EXPORTS/INTRO_WITH IDENT.MOV</value></field><field><key>MXFS_CREATIONDAY</key><value>23</value></field><field><key>created</key><value>1474419644000</value></field><field><key>MXFS_ARCHMONTH</key><value>12</value></field><field><key>path</key><value>.</value></field><field><key>MXFS_FILENAME</key><value>Multimedia_News/Anywhere_but_Washington/tom_silverstone_ALL_FOOTAGE/WEST VIRGINIA/EXPORTS/INTRO_WITH IDENT.mov</value></field><field><key>uuid</key><value>0cffcddc-c8dc-11e6-a3bc-bc113b8044e7-22</value></field><field><key>MXFS_CATEGORY</key><value>2</value></field><field><key>MXFS_ACCESS_TIME</key><value>1482722095243</value></field></metadata></FileDocument>"""
 
    class MockedResponse(object):
        def __init__(self, status_code, content, reason=""):
            self.status = status_code
            self.body = content
            self.reason = reason
        
        def read(self):
            return self.body
    
    def test_download(self):
        from gnmvidispine.vs_storage import VSFile,VSStorage
        from xml.etree.cElementTree import fromstring
        
        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        f = VSFile(parent_storage=s,parsed_data=fromstring(self.file_doc))
        
        f.name = "VX-123"

        f.parent.sendAuthorized = MagicMock(return_value=self.MockedResponse(200, "test content"))
        
        f.download()
        f.parent.sendAuthorized.assert_called_with('GET', '/API/storage/file/VX-123/data', '', {'Accept': '*'})
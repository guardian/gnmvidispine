# -*- coding: UTF-8 -*-

import unittest2
from mock import MagicMock, patch, call


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

    test_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <FileListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <hits>10</hits>
        <file>
            <id>KP-1153319</id>
            <path>141010motoGP_h264_mezzanine.mp4</path>
            <state>LOST</state>
            <size>59144931</size>
            <timestamp>2014-10-29T15:07:01.749Z</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1414595104000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1414595154000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1414595154000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1153432</id>
            <path>141010motoGP_KP-760.mp4</path>
            <state>LOST</state>
            <size>106111904</size>
            <hash>ac5f219f47aa48cb6fe282bbe9d55ed57163ccd3</hash>
            <timestamp>2014-10-29T16:45:22.782Z</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1414601025000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1414600424000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1414600424000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1153448</id>
            <path>141010motoGP_KP-1153448.mp4</path>
            <state>LOST</state>
            <size>106111904</size>
            <timestamp>2014-10-29T16:55:24.912Z</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1414601372000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1414601332000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1414601332000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1172096</id>
            <path>141112nightmare_h264_mezzanine.mp4</path>
            <state>LOST</state>
            <size>29189894</size>
            <timestamp>2014-11-13T19:31:04.129Z</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1415906989000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1415903347000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1415903347000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1172730</id>
            <path>Multimedia_Culture_Sport/Ingest_from_Prelude_footage/richard_sprenger_Ingest_from_Prelude_footage/Untitled/BPAV/CLPR/001_1121_01/001_1121_01.SMI</path>
            <state>LOST</state>
            <size>370295672</size>
            <hash>5b40490fa49b7ab7e087d2235c3a84b28ecf4792</hash>
            <timestamp>2016-10-12T14:01:03.851+01:00</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1425840702000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1415906501000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1415906501000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1172865</id>
            <path>Multimedia_Culture_Sport/Ingest_from_Prelude_footage/richard_sprenger_Ingest_from_Prelude_footage/2014-10-13_14-32-07/Untitled/BPAV/CLPR/001_1133_01/001_1133_01R01.BIM</path>
            <state>LOST</state>
            <size>7549</size>
            <hash>2b5755b1d5470a0cfd7abdfc831a09622e9f815d</hash>
            <timestamp>2016-10-12T14:01:03.853+01:00</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1417005886000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1415906953000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1415906953000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-1187058</id>
            <path>141112nightmare_KP-12205.mp4</path>
            <state>LOST</state>
            <size>29189894</size>
            <timestamp>2014-11-17T11:23:00.470Z</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>atime</key>
                    <value>1416223286000</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1416223254000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1416223254000</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-26209356</id>
            <path>141121BohnerTEST.mxf</path>
            <uri>file:///srv/Multimedia2/DAM/Media%20Libraries/Guardian%20Masters/141121BohnerTEST.mxf</uri>
            <state>CLOSED</state>
            <size>432855808</size>
            <hash>878175941060eeb659c03a411ed17f4eafef1e5b</hash>
            <timestamp>2017-05-10T08:42:57.462+01:00</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>MXFS_PARENTOID</key>
                    <value></value>
                </field>
                <field>
                    <key>MXFS_CREATION_TIME</key>
                    <value>1416586976044</value>
                </field>
                <field>
                    <key>atime</key>
                    <value>1416586975000</value>
                </field>
                <field>
                    <key>MXFS_CREATIONDAY</key>
                    <value>21</value>
                </field>
                <field>
                    <key>MXFS_CATEGORY</key>
                    <value>2</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1494401821000</value>
                </field>
                <field>
                    <key>MXFS_ACCESS_TIME</key>
                    <value>1426625512952</value>
                </field>
                <field>
                    <key>MXFS_ARCHDAY</key>
                    <value>21</value>
                </field>
                <field>
                    <key>MXFS_INTRASH</key>
                    <value>false</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1494401821000</value>
                </field>
                <field>
                    <key>MXFS_ARCHYEAR</key>
                    <value>2014</value>
                </field>
                <field>
                    <key>uuid</key>
                    <value>b8e2a9a4-7197-11e4-ba5a-eadf79e8d4b9-4</value>
                </field>
                <field>
                    <key>path</key>
                    <value>.</value>
                </field>
                <field>
                    <key>MXFS_ARCHIVE_TIME</key>
                    <value>1416586976044</value>
                </field>
                <field>
                    <key>MXFS_MODIFICATION_TIME</key>
                    <value>1416586976074</value>
                </field>
                <field>
                    <key>MXFS_CREATIONYEAR</key>
                    <value>2014</value>
                </field>
                <field>
                    <key>MXFS_ARCHMONTH</key>
                    <value>11</value>
                </field>
                <field>
                    <key>MXFS_CREATIONMONTH</key>
                    <value>11</value>
                </field>
                <field>
                    <key>MXFS_FILENAME</key>
                    <value>141121BohnerTEST.mxf</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-26216834</id>
            <path>edvideo/15-05-29_09-16-02.21329/Pam Hutchinson.mov</path>
            <state>LOST</state>
            <size>376101508</size>
            <hash>ec637b1a15757529e5560008606764534f80ac55</hash>
            <timestamp>2016-10-12T14:01:03.851+01:00</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>MXFS_PARENTOID</key>
                    <value></value>
                </field>
                <field>
                    <key>MXFS_CREATION_TIME</key>
                    <value>1432892602735</value>
                </field>
                <field>
                    <key>MXFS_CREATIONDAY</key>
                    <value>29</value>
                </field>
                <field>
                    <key>MXFS_CATEGORY</key>
                    <value>2</value>
                </field>
                <field>
                    <key>created</key>
                    <value>1449832034000</value>
                </field>
                <field>
                    <key>MXFS_ACCESS_TIME</key>
                    <value>1432895462570</value>
                </field>
                <field>
                    <key>MXFS_ARCHDAY</key>
                    <value>29</value>
                </field>
                <field>
                    <key>MXFS_INTRASH</key>
                    <value>false</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1449832034000</value>
                </field>
                <field>
                    <key>MXFS_ARCHYEAR</key>
                    <value>2015</value>
                </field>
                <field>
                    <key>uuid</key>
                    <value>25626e4c-05e7-11e5-9c4a-a2a2f3b96577-0</value>
                </field>
                <field>
                    <key>path</key>
                    <value>.</value>
                </field>
                <field>
                    <key>MXFS_ARCHIVE_TIME</key>
                    <value>1432892602735</value>
                </field>
                <field>
                    <key>MXFS_MODIFICATION_TIME</key>
                    <value>1432892602837</value>
                </field>
                <field>
                    <key>MXFS_CREATIONYEAR</key>
                    <value>2015</value>
                </field>
                <field>
                    <key>MXFS_ARCHMONTH</key>
                    <value>5</value>
                </field>
                <field>
                    <key>MXFS_CREATIONMONTH</key>
                    <value>5</value>
                </field>
                <field>
                    <key>MXFS_FILENAME</key>
                    <value>edvideo/15-05-29_09-16-02.21329/Pam Hutchinson.mov</value>
                </field>
            </metadata>
        </file>
        <file>
            <id>KP-27610776</id>
            <path>160324Test665.mxf</path>
            <uri>file:///srv/Multimedia2/DAM/Media%20Libraries/Guardian%20Masters/160324Test665.mxf</uri>
            <state>CLOSED</state>
            <size>24381332</size>
            <hash>b6bbc44e3d7c4e910fa90f34c2528dffaab09693</hash>
            <timestamp>2017-05-10T08:42:25.427+01:00</timestamp>
            <refreshFlag>1</refreshFlag>
            <storage>KP-6</storage>
            <metadata>
                <field>
                    <key>created</key>
                    <value>1458846705000</value>
                </field>
                <field>
                    <key>mtime</key>
                    <value>1458846705000</value>
                </field>
            </metadata>
        </file>
    </FileListDocument>"""

    test_list_doc_end = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <FileListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <hits>10</hits>
    </FileListDocument>"""

    def test_files(self):
        from gnmvidispine.vs_storage import VSStorage

        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)

        s.sendAuthorized = MagicMock(side_effect=[self.MockedResponse(200, self.test_list_doc),
                                                  self.MockedResponse(200, self.test_list_doc_end)])

        files_list = [f for f in s.files()]
        self.assertEqual(len(files_list),10)
        s.sendAuthorized.assert_has_calls([
            call('GET', '/API/storage/INVALIDNAME/file;start=0;includeItem=True;number=100?path=%2F', None, {'Accept': 'application/xml'}, rawData=False),
            call('GET', '/API/storage/INVALIDNAME/file;start=10;includeItem=True;number=100?path=%2F', None, {'Accept': 'application/xml'}, rawData=False)
        ])

    def test_files_path(self):
        from gnmvidispine.vs_storage import VSStorage

        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)

        s.sendAuthorized = MagicMock(side_effect=[self.MockedResponse(200, self.test_list_doc),
                                                  self.MockedResponse(200, self.test_list_doc_end)])

        files_list = [f for f in s.files(path="/some/long/filepath")]
        self.assertEqual(len(files_list),10)
        s.sendAuthorized.assert_has_calls([
            call('GET', '/API/storage/INVALIDNAME/file;start=0;includeItem=True;number=100?path=%2Fsome%2Flong%2Ffilepath', None, {'Accept': 'application/xml'}, rawData=False),
            call('GET', '/API/storage/INVALIDNAME/file;start=10;includeItem=True;number=100?path=%2Fsome%2Flong%2Ffilepath', None, {'Accept': 'application/xml'}, rawData=False)
        ])

    def test_files_closed(self):
        from gnmvidispine.vs_storage import VSStorage

        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)

        s.sendAuthorized = MagicMock(side_effect=[self.MockedResponse(200, self.test_list_doc),
                                                  self.MockedResponse(200, self.test_list_doc_end)])

        files_list = [f for f in s.files(state='CLOSED')]
        self.assertEqual(len(files_list),10)
        s.sendAuthorized.assert_has_calls([
            call('GET', '/API/storage/INVALIDNAME/file;start=0;includeItem=True;number=100?path=%2F&state=CLOSED', None, {'Accept': 'application/xml'}, rawData=False),
             call('GET', '/API/storage/INVALIDNAME/file;start=10;includeItem=True;number=100?path=%2F&state=CLOSED', None, {'Accept': 'application/xml'}, rawData=False)
        ])

    def test_file_count(self):
        from gnmvidispine.vs_storage import VSStorage

        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)

        s.sendAuthorized = MagicMock(side_effect=[self.MockedResponse(200, self.test_list_doc),
                                                  self.MockedResponse(200, self.test_list_doc_end)])

        result = s.file_count()
        self.assertEqual(result,10)

        s.sendAuthorized.assert_has_calls([
            call('GET', '/API/storage/INVALIDNAME/file;start=0;includeItem=True;number=0?path=%2F', None, {'Accept': 'application/xml'}, rawData=False)
        ])

    def test_file_count_state(self):
        from gnmvidispine.vs_storage import VSStorage

        s = VSStorage(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)

        s.sendAuthorized = MagicMock(side_effect=[self.MockedResponse(200, self.test_list_doc),
                                                  self.MockedResponse(200, self.test_list_doc_end)])

        result = s.file_count(state="LOST")
        self.assertEqual(result,10)

        s.sendAuthorized.assert_has_calls([
            call('GET', '/API/storage/INVALIDNAME/file;start=0;includeItem=True;number=0?path=%2F&state=LOST', None, {'Accept': 'application/xml'}, rawData=False)
        ])
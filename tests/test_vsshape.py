# -*- coding: UTF-8 -*-

import unittest2
from mock import MagicMock, patch
import http.client
import base64
import logging
import tempfile
from os import urandom


class TestVSShape(unittest2.TestCase):
    fake_host = 'localhost'
    fake_port = 8080
    fake_user = 'username'
    fake_passwd = 'password'
    
    test_shapedoc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
  <id>KP-2409324</id>
  <essenceVersion>0</essenceVersion>
  <tag>original</tag>
  <mimeType>video/quicktime</mimeType>
  <containerComponent>
    <file>
      <id>KP-31774258</id>
      <path>EXPORTS/INTRO_WITH IDENT.mov</path>
      <uri>omms://34238423-r2323442:d487893895723879r/EXPORTS/INTRO_WITH%20IDENT.mov</uri>
      <state>CLOSED</state>
      <size>96531092</size>
      <timestamp>2016-12-26T10:04:14.093Z</timestamp>
      <refreshFlag>1</refreshFlag>
      <storage>KP-2</storage>
      <metadata>
        <field>
          <key>MXFS_ARCHDAY</key>
          <value>23</value>
        </field>
        <field>
          <key>MXFS_ARCHYEAR</key>
          <value>2016</value>
        </field>
        <field>
          <key>MXFS_PARENTOID</key>
          <value/>
        </field>
        <field>
          <key>mtime</key>
          <value>1474419644000</value>
        </field>
        <field>
          <key>MXFS_CREATIONMONTH</key>
          <value>12</value>
        </field>
        <field>
          <key>MXFS_ARCHIVE_TIME</key>
          <value>1482476605861</value>
        </field>
        <field>
          <key>MXFS_CREATIONYEAR</key>
          <value>2016</value>
        </field>
        <field>
          <key>MXFS_INTRASH</key>
          <value>false</value>
        </field>
        <field>
          <key>MXFS_MODIFICATION_TIME</key>
          <value>1482476605887</value>
        </field>
        <field>
          <key>MXFS_CREATION_TIME</key>
          <value>1482476605861</value>
        </field>
        <field>
          <key>MXFS_FILENAME_UPPER</key>
          <value>EXPORTS/INTRO_WITH IDENT.mov</value>
        </field>
        <field>
          <key>MXFS_CREATIONDAY</key>
          <value>23</value>
        </field>
        <field>
          <key>created</key>
          <value>1474419644000</value>
        </field>
        <field>
          <key>MXFS_ARCHMONTH</key>
          <value>12</value>
        </field>
        <field>
          <key>path</key>
          <value>.</value>
        </field>
        <field>
          <key>MXFS_FILENAME</key>
          <value>EXPORTS/INTRO_WITH IDENT.mov</value>
        </field>
        <field>
          <key>uuid</key>
          <value>0cffcddc-c8dc-11e6-a3bc-bc1a3b8044ec-22</value>
        </field>
        <field>
          <key>MXFS_CATEGORY</key>
          <value>2</value>
        </field>
        <field>
          <key>MXFS_ACCESS_TIME</key>
          <value>1482722095243</value>
        </field>
      </metadata>
    </file>
    <file>
      <id>KP-32349474</id>
      <path>EXPORTS/INTRO_WITH IDENT.mov</path>
      <uri>file:///storage/path/EXPORTS/INTRO_WITH%20IDENT.mov</uri>
      <state>CLOSED</state>
      <size>96531092</size>
      <timestamp>2017-02-03T18:00:33.571Z</timestamp>
      <refreshFlag>1</refreshFlag>
      <storage>KP-8</storage>
      <metadata>
        <field>
          <key>MXFS_ARCHDAY</key>
          <value>23</value>
        </field>
        <field>
          <key>MXFS_ARCHYEAR</key>
          <value>2016</value>
        </field>
        <field>
          <key>MXFS_PARENTOID</key>
          <value/>
        </field>
        <field>
          <key>mtime</key>
          <value>1486144654000</value>
        </field>
        <field>
          <key>MXFS_CREATIONMONTH</key>
          <value>12</value>
        </field>
        <field>
          <key>MXFS_ARCHIVE_TIME</key>
          <value>1482476605861</value>
        </field>
        <field>
          <key>MXFS_CREATIONYEAR</key>
          <value>2016</value>
        </field>
        <field>
          <key>MXFS_INTRASH</key>
          <value>false</value>
        </field>
        <field>
          <key>MXFS_MODIFICATION_TIME</key>
          <value>1482476605887</value>
        </field>
        <field>
          <key>MXFS_CREATION_TIME</key>
          <value>1482476605861</value>
        </field>
        <field>
          <key>MXFS_FILENAME_UPPER</key>
          <value>EXPORTS/INTRO_WITH IDENT.MOV</value>
        </field>
        <field>
          <key>MXFS_CREATIONDAY</key>
          <value>23</value>
        </field>
        <field>
          <key>created</key>
          <value>1486144654000</value>
        </field>
        <field>
          <key>MXFS_ARCHMONTH</key>
          <value>12</value>
        </field>
        <field>
          <key>path</key>
          <value>.</value>
        </field>
        <field>
          <key>MXFS_FILENAME</key>
          <value>EXPORTS/INTRO_WITH IDENT.mov</value>
        </field>
        <field>
          <key>uuid</key>
          <value>0cffcddc-c8dc-11e6-a3bc-bc113b8044e7-22</value>
        </field>
        <field>
          <key>MXFS_CATEGORY</key>
          <value>2</value>
        </field>
        <field>
          <key>MXFS_ACCESS_TIME</key>
          <value>1482722095243</value>
        </field>
      </metadata>
    </file>
    <id>KP-5708272</id>
    <metadata>
      <key>start_timecode</key>
      <value>0</value>
    </metadata>
    <metadata>
      <key>minor_version</key>
      <value>537199360</value>
    </metadata>
    <metadata>
      <key>creation_time</key>
      <value>2016-09-28 01:00:38</value>
    </metadata>
    <metadata>
      <key>drop_frame</key>
      <value>false</value>
    </metadata>
    <metadata>
      <key>rounded_time_base</key>
      <value>25</value>
    </metadata>
    <metadata>
      <key>compatible_brands</key>
      <value>qt  </value>
    </metadata>
    <metadata>
      <key>major_brand</key>
      <value>qt  </value>
    </metadata>
    <duration>
      <samples>4440000</samples>
      <timeBase>
        <numerator>1</numerator>
        <denominator>1000000</denominator>
      </timeBase>
    </duration>
    <format>mov,mp4,m4a,3gp,3g2,mj2</format>
    <firstSMPTETimecode>00:00:00:00</firstSMPTETimecode>
    <startTimecode>0</startTimecode>
    <startTimestamp>
      <samples>0</samples>
      <timeBase>
        <numerator>1</numerator>
        <denominator>25</denominator>
      </timeBase>
    </startTimestamp>
    <roundedTimeBase>25</roundedTimeBase>
    <dropFrame>false</dropFrame>
    <timeCodeTimeBase>
      <numerator>1</numerator>
      <denominator>25</denominator>
    </timeCodeTimeBase>
    <mediaInfo>
      <property>
        <key>Audio codecs</key>
        <value>PCM</value>
      </property>
      <property>
        <key>Audio_Format_List</key>
        <value>PCM</value>
      </property>
      <property>
        <key>Audio_Format_WithHint_List</key>
        <value>PCM</value>
      </property>
      <property>
        <key>Audio_Language_List</key>
        <value>English</value>
      </property>
      <property>
        <key>Codec</key>
        <value>MPEG-4</value>
      </property>
      <property>
        <key>Codec ID</key>
        <value>qt</value>
      </property>
      <property>
        <key>Codec ID/Url</key>
        <value>http://www.apple.com/quicktime/download/standalone.html</value>
      </property>
      <property>
        <key>Codec/Extensions usually used</key>
        <value>mp4 m4v m4a m4b m4p 3gpp 3gp 3gpp2 3g2 k3g jpm jpx mqv ismv isma f4v</value>
      </property>
      <property>
        <key>Codecs Video</key>
        <value>apch</value>
      </property>
      <property>
        <key>Commercial name</key>
        <value>MPEG-4</value>
      </property>
      <property>
        <key>Complete name</key>
        <value>/srv/Multimedia2/Media Production/Assets/Multimedia_News/Anywhere_but_Washington/tom_silverstone_ALL_FOOTAGE/WEST VIRGINIA/EXPORTS/INTRO_WITH IDENT.mov</value>
      </property>
      <property>
        <key>Count</key>
        <value>280</value>
      </property>
      <property>
        <key>Count of audio streams</key>
        <value>1</value>
      </property>
      <property>
        <key>Count of menu streams</key>
        <value>1</value>
      </property>
      <property>
        <key>Count of stream of this kind</key>
        <value>1</value>
      </property>
      <property>
        <key>Count of video streams</key>
        <value>1</value>
      </property>
      <property>
        <key>DataSize</key>
        <value>95482524</value>
      </property>
      <property>
        <key>Duration</key>
        <value>4440</value>
      </property>
      <property>
        <key>Encoded date</key>
        <value>UTC 2016-09-28 01:00:38</value>
      </property>
      <property>
        <key>File extension</key>
        <value>mov</value>
      </property>
      <property>
        <key>File last modification date</key>
        <value>UTC 2016-09-21 01:00:44</value>
      </property>
      <property>
        <key>File last modification date (local)</key>
        <value>2016-09-21 02:00:44</value>
      </property>
      <property>
        <key>File name</key>
        <value>INTRO_WITH IDENT</value>
      </property>
      <property>
        <key>File size</key>
        <value>96531092</value>
      </property>
      <property>
        <key>Folder name</key>
        <value>/path/to/EXPORTS</value>
      </property>
      <property>
        <key>FooterSize</key>
        <value>0</value>
      </property>
      <property>
        <key>Format</key>
        <value>MPEG-4</value>
      </property>
      <property>
        <key>Format profile</key>
        <value>QuickTime</value>
      </property>
      <property>
        <key>Format/Extensions usually used</key>
        <value>mp4 m4v m4a m4b m4p 3gpp 3gp 3gpp2 3g2 k3g jpm jpx mqv ismv isma f4v</value>
      </property>
      <property>
        <key>HeaderSize</key>
        <value>1048568</value>
      </property>
      <property>
        <key>Internet media type</key>
        <value>video/mp4</value>
      </property>
      <property>
        <key>IsStreamable</key>
        <value>Yes</value>
      </property>
      <property>
        <key>Kind of stream</key>
        <value>General</value>
      </property>
      <property>
        <key>Menu_Format_List</key>
        <value>TimeCode</value>
      </property>
      <property>
        <key>Menu_Format_WithHint_List</key>
        <value>TimeCode</value>
      </property>
      <property>
        <key>Menu_Language_List</key>
        <value>English</value>
      </property>
      <property>
        <key>Overall bit rate</key>
        <value>173929895</value>
      </property>
      <property>
        <key>Overall bit rate mode</key>
        <value>VBR</value>
      </property>
      <property>
        <key>Proportion of this stream</key>
        <value>0.01086</value>
      </property>
      <property>
        <key>Stream identifier</key>
        <value>0</value>
      </property>
      <property>
        <key>Stream size</key>
        <value>1048580</value>
      </property>
      <property>
        <key>Tagged date</key>
        <value>UTC 2016-09-21 01:00:44</value>
      </property>
      <property>
        <key>Video_Format_List</key>
        <value>ProRes</value>
      </property>
      <property>
        <key>Video_Format_WithHint_List</key>
        <value>ProRes</value>
      </property>
      <property>
        <key>Video_Language_List</key>
        <value>English</value>
      </property>
      <property>
        <key>Writing library</key>
        <value>aapl</value>
      </property>
      <property>
        <key>Writing library/Name</key>
        <value>aapl</value>
      </property>
      <property>
        <key>�TIM</key>
        <value>00:00:00:00 / 25 / 1</value>
      </property>
    </mediaInfo>
  </containerComponent>
</ShapeDocument>
"""
    
    test_storage_rule = """<StorageRuleDocument id="lowres" xmlns="http://xml.vidispine.com/schema/vidispine"> <storageCount>3</storageCount> <priority level="1">capacity</priority> <priority level="2">bandwidth</priority> <storage>VX-123</storage> </StorageRuleDocument>"""

    class MockedResponse(object):
        def __init__(self, status_code, content, reason=""):
            self.status = status_code
            self.body = content
            self.reason = reason
        
        def read(self):
            return self.body

    def test_download(self):
        from gnmvidispine.vs_shape import VSShape
        from xml.etree.cElementTree import fromstring
        
        s = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
        s.name = "VX-123"
        s.dataContent = fromstring(self.test_shapedoc)
        s.sendAuthorized = MagicMock(return_value=self.MockedResponse(200,"test content"))
        
        s.download()
        s.sendAuthorized.assert_called_with('GET','/API/storage/file/KP-31774258/data','',{'Accept': '*'})
        
    def test_add_storage_rule(self):
        from gnmvidispine.vs_shape import VSShape
        from gnmvidispine.vs_storage_rule import VSStorageRuleNew
        from xml.etree.cElementTree import fromstring, tostring
        
        parsed_xml_doc = fromstring(self.test_storage_rule)
        newrule = VSStorageRuleNew()
        newrule.populate_from_xml(parsed_xml_doc)

        s = VSShape(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        s.name = "VX-123"
        s.contentDict = {'tag': 'original'}
        s.itemid = "VX-456"
        s.sendAuthorized = MagicMock(return_value=self.MockedResponse(200,self.test_storage_rule))
        
        s.add_storage_rule(newrule)
        s.sendAuthorized.assert_called_with('PUT','/API/item/VX-456/storage-rule/original',
                                            tostring(parsed_xml_doc),
                                            {'Content-Type': 'application/xml', 'Accept': 'application/xml'}, rawData=False)

    def test_delete_storage_rule(self):
        from gnmvidispine.vs_shape import VSShape

        s = VSShape(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        s.name = "VX-123"
        s.contentDict = {'tag': 'original'}
        s.itemid = "VX-456"
        s.sendAuthorized = MagicMock(return_value=self.MockedResponse(200, self.test_storage_rule))

        s.delete_storage_rule()
        s.sendAuthorized.assert_called_with('DELETE', '/API/item/VX-456/storage-rule/original', None, {'Accept': 'application/xml'}, rawData=False)

    def test_mime_type(self):
        from xml.etree.cElementTree import fromstring
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            test_shape_object.populate('test', 'test')
            self.assertEqual(test_shape_object.mimeType(), 'video/quicktime')

    def test_file_uris(self):
        from xml.etree.cElementTree import fromstring
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            test_shape_object.populate('test', 'test')
            test_file_uris_object = test_shape_object.fileURIs()
            test_place = 1
            for uri in test_file_uris_object:
                if test_place is 1:
                    self.assertEqual('omms://34238423-r2323442:d487893895723879r/EXPORTS/INTRO_WITH%20IDENT.mov', uri)
                if test_place is 2:
                    self.assertEqual('file:///storage/path/EXPORTS/INTRO_WITH%20IDENT.mov', uri)
                test_place = test_place + 1

    def test_files(self):
        from xml.etree.cElementTree import fromstring
        file_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<FileDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-48077439</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://1fa3ad40-65e4-11e9-a3bc-bc113b8044e7:_VSENC__3uhd3tAWvFSU0WX0W8TkA1halNoyKnHuf9Q4KlqgRMFjh%2FtK%2FVxjUQ==@10.0.0.1/5ce37552-358f-998b-115b-9569b8f21a01/1d07a65a-65e4-11e9-a3bc-bc113b8044e7/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<timestamp>2019-11-12T12:50:00.603Z</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-76</storage>
<metadata>
<field>
<key>MXFS_PARENTOID</key>
<value />
 </field>
<field>
<key>MXFS_CREATION_TIME</key>
<value>1558041125848</value>
 </field>
<field>
<key>MXFS_CATEGORY</key>
<value>2</value>
 </field>
<field>
<key>MXFS_CREATIONDAY</key>
<value>16</value>
 </field>
<field>
<key>created</key>
<value>1442718812000</value>
 </field>
<field>
<key>MXFS_ACCESS_TIME</key>
<value>1558041125905</value>
 </field>
<field>
<key>MXFS_ARCHDAY</key>
<value>16</value>
 </field>
<field>
<key>MXFS_INTRASH</key>
<value>false</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
<field>
<key>MXFS_ARCHYEAR</key>
<value>2019</value>
 </field>
<field>
<key>uuid</key>
<value>7ab026e5-749e-11e9-af8e-8c4bda3562c7-2546</value>
 </field>
<field>
<key>path</key>
<value>.</value>
 </field>
<field>
<key>MXFS_ARCHIVE_TIME</key>
<value>1558041125848</value>
 </field>
<field>
<key>MXFS_MODIFICATION_TIME</key>
<value>1558041125905</value>
 </field>
<field>
<key>MXFS_ARCHMONTH</key>
<value>5</value>
 </field>
<field>
<key>MXFS_CREATIONYEAR</key>
<value>2019</value>
 </field>
<field>
<key>MXFS_FILENAME_UPPER</key>
<value>141019_9661710_LOWRES.MP4</value>
 </field>
<field>
<key>MXFS_CREATIONMONTH</key>
<value>5</value>
 </field>
<field>
<key>MXFS_FILENAME</key>
<value>141019_9661710_lowres.mp4</value>
 </field>
 </metadata>
 </FileDocument>"""
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc)]) as mock_request:
            with patch('gnmvidispine.vs_storage.VSStorage.request', side_effect=[fromstring(file_doc), fromstring(file_doc)]) as mock_request:
                from gnmvidispine.vs_shape import VSShape
                test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
                test_shape_object.populate('test', 'test')
                test_files_object = test_shape_object.files()
                test_place = 1
                for file in test_files_object:
                    if test_place is 1:
                        self.assertEqual('KP-31774258', file.name)
                        self.assertEqual('KP-2', file.storageName)
                        self.assertEqual('EXPORTS/INTRO_WITH IDENT.mov', file.path)
                        self.assertEqual('omms://34238423-r2323442:d487893895723879r/EXPORTS/INTRO_WITH%20IDENT.mov', file.uri)
                        self.assertEqual('CLOSED', file.state)
                        self.assertEqual('96531092', file.size)
                    if test_place is 2:
                        self.assertEqual('KP-32349474', file.name)
                        self.assertEqual('KP-8', file.storageName)
                        self.assertEqual('EXPORTS/INTRO_WITH IDENT.mov', file.path)
                        self.assertEqual('file:///storage/path/EXPORTS/INTRO_WITH%20IDENT.mov', file.uri)
                        self.assertEqual('CLOSED', file.state)
                        self.assertEqual('96531092', file.size)
                    test_place = test_place + 1

    def test_mime_type_two(self):
        from xml.etree.cElementTree import fromstring
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            with self.assertRaises(ValueError):
                test_shape_object.mime_type
            test_shape_object.populate('test', 'test')
            self.assertEqual(test_shape_object.mime_type, 'video/quicktime')

    def test_essence_version(self):
        from xml.etree.cElementTree import fromstring
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            with self.assertRaises(ValueError):
                test_shape_object.essence_version
            test_shape_object.populate('test', 'test')
            self.assertEqual(test_shape_object.essence_version, 0)

    def test_storage_rules(self):
        from xml.etree.cElementTree import fromstring, tostring
        storage_rule_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<StorageRulesDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<tag id="lowres">
<storageCount>1</storageCount>
<priority level="1">capacity</priority>
<group>Proxies</group>
<not>
<storage>VX-16</storage>
<group>Deep Archive</group>
<group>Project Files</group>
<group>Nearline</group>
<group>Newswires</group>
<group>Guardian Masters</group>
<group>Online</group>
 </not>
<appliesTo>
<id>lowres</id>
<type>GENERIC</type>
 </appliesTo>
<precedence>HIGHEST</precedence>
 </tag>
<tag id="original">
<storageCount>1</storageCount>
<priority level="1">capacity</priority>
<group>Proxies</group>
<not>
<storage>VX-16</storage>
<group>Deep Archive</group>
<group>Project Files</group>
<group>Nearline</group>
<group>Newswires</group>
<group>Guardian Masters</group>
<group>Online</group>
 </not>
<appliesTo>
<id>original</id>
<type>GENERIC</type>
 </appliesTo>
<precedence>HIGHEST</precedence>
 </tag>
</StorageRulesDocument>"""
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc), fromstring(storage_rule_doc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            test_shape_object.populate('test', 'test')
            test_storage_rules = test_shape_object.storage_rules()
            test_storage_rules_object = test_storage_rules.rules()
            test_place = 1
            for rule in test_storage_rules_object:
                if test_place is 1:
                    self.assertIn(b'<ns0:id>lowres</ns0:id>', tostring(rule.xmlDOM))
                    self.assertIn(b'<ns0:precedence>HIGHEST</ns0:precedence>', tostring(rule.xmlDOM))
                    self.assertIn(b'<ns0:priority level="1">capacity</ns0:priority>', tostring(rule.xmlDOM))
                if test_place is 2:
                    self.assertIn(b'<ns0:id>original</ns0:id>', tostring(rule.xmlDOM))
                    self.assertIn(b'<ns0:precedence>HIGHEST</ns0:precedence>', tostring(rule.xmlDOM))
                    self.assertIn(b'<ns0:priority level="1">capacity</ns0:priority>', tostring(rule.xmlDOM))
                test_place = test_place + 1

    def test_analyze_doc_fragment(self):
        from xml.etree.cElementTree import tostring, Element
        from gnmvidispine.vs_shape import VSShape
        test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
        analyze_doc_root = Element("AnalyzeJobDocument", {'xmlns': 'http://xml.vidispine.com/schema/vidispine'})
        analyze_output = test_shape_object._analyzeDocFragment(analyze_doc_root, "black", threshold=20, percentage=50)
        self.assertEqual(tostring(analyze_output), b'<black><threshold>20</threshold><percentage>50</percentage></black>')
        analyze_output = test_shape_object._analyzeDocFragment(analyze_doc_root, "freeze", threshold=30, time=4.0)
        self.assertEqual(tostring(analyze_output), b'<freeze><threshold>30</threshold><time>4.0</time></freeze>')

    def test_analyze(self):
        from xml.etree.cElementTree import fromstring
        job_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<jobId>VX-17403032</jobId>
<user>guest</user>
<started>2019-11-20T15:41:00.668Z</started>
<status>READY</status>
<type>ANALYZE</type>
<priority>MEDIUM</priority>
 </JobDocument>"""
        with patch('gnmvidispine.vs_shape.VSShape.request', side_effect=[fromstring(self.test_shapedoc), fromstring(job_doc), fromstring(job_doc)]) as mock_request:
            from gnmvidispine.vs_shape import VSShape
            test_shape_object = VSShape(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            test_shape_object.populate('VX-1', 'VX-2')
            test_job_object = test_shape_object.analyze()
            test_shape_object.request.assert_called_with('/item/VX-1/shape/VX-2/analyze', body=b'<?xml version=\'1.0\' encoding=\'utf8\'?>\n<AnalyzeJobDocument xmlns="http://xml.vidispine.com/schema/vidispine"><black><threshold>0.1</threshold><percentage>95</percentage></black><freeze><threshold>0.05</threshold><time>4.0</time></freeze><bars><threshold>0.05</threshold><percentage>10</percentage></bars></AnalyzeJobDocument>', method='POST', query={'priority': 'MEDIUM'})
            self.assertEqual(test_job_object.name, 'VX-17403032')
            self.assertEqual(test_job_object.contentDict['status'], 'READY')
            self.assertEqual(test_job_object.contentDict['type'], 'ANALYZE')
            test_job_object = test_shape_object.analyze(blackThreshold=0.2, blackPercentage=94, freezeThreshold=0.04, freezeTime=3.0, barsThreshold=0.04, barsPercentage=11, priority="HIGH")
            test_shape_object.request.assert_called_with('/item/VX-1/shape/VX-2/analyze', body=b'<?xml version=\'1.0\' encoding=\'utf8\'?>\n<AnalyzeJobDocument xmlns="http://xml.vidispine.com/schema/vidispine"><black><threshold>0.2</threshold><percentage>94</percentage></black><freeze><threshold>0.04</threshold><time>3.0</time></freeze><bars><threshold>0.04</threshold><percentage>11</percentage></bars></AnalyzeJobDocument>', method='POST', query={'priority': 'HIGH'})
            self.assertEqual(test_job_object.name, 'VX-17403032')
            self.assertEqual(test_job_object.contentDict['status'], 'READY')
            self.assertEqual(test_job_object.contentDict['type'], 'ANALYZE')

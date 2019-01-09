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

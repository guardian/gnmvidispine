# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
from urllib2 import quote
import xml.etree.cElementTree as ET
import re


class TestVSItem(unittest2.TestCase):
    maxDiff=None

    fake_host = 'localhost'
    fake_port = 8080
    fake_user = 'username'
    fake_passwd = 'password'
    
    import_job_doc = """
    <JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <jobId>VX-80</jobId>
    <status>READY</status>
    <type>PLACEHOLDER_IMPORT</type>
</JobDocument>"""

    testdoc = """<?xml version="1.0" encoding="UTF-8"?>
    <MetadataListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <item id="VX-1234">
    <metadata>
        <timespan start="-INF" end="+INF">
            <field>
                <name>sometestfield</name>
                <value>sometestvalue</value>
            </field>
            <field>
                <name>someotherfield</name>
                <value>valueone</value>
                <value>valuetwo</value>
            </field>
        </timespan>
        </metadata>
        </item>
    </MetadataListDocument>"""

    class MockedResponse(object):
        def __init__(self, status_code, content, reason=""):
            self.status = status_code
            self.body = content
            self.reason = reason
        
        def read(self):
            return self.body

    def test_import_base_no_args(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
        result = i.import_base()
        self.assertEqual({'essence': 'false','priority': 'MEDIUM','tag': 'original', 'thumbnails': 'true'}, result)

    def test_import_base_jobmeta(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
        result = i.import_base(jobMetadata={'keyone': 'valueone','keytwo': 'valuetwo'})
        self.assertEqual({'essence': 'false', 'jobmetadata': ['keyone=valueone', 'keytwo=valuetwo'],
                          'priority': 'MEDIUM','tag': 'original', 'thumbnails': 'true'},
                         result)


    def test_import_to_shape(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)

        i.name = "VX-123"
        i.sendAuthorized = MagicMock(return_value=self.MockedResponse(200,  self.import_job_doc))
        
        with self.assertRaises(ValueError):
            i.import_to_shape() #expect ValueError if neither uri nor file ref
        
        fake_uri="file:///path/to/newmedia.mxf"
        quoted_uri=quote(fake_uri,"")   #we are embedding a URI as a parameter with another URL so it must be double-encoded
        
        i.import_to_shape(uri=fake_uri,shape_tag="shapetagname",priority="HIGH")
        i.sendAuthorized.assert_called_with('POST',
                                            '/API/item/VX-123/shape?priority=HIGH&essence=false&tag=shapetagname&thumbnails=true&uri={0}'.format(quoted_uri)
                                            ,"",{'Accept':'application/xml'}, rawData=True)

        fake_uri = "file:///path/to/" + quote("media with spaces.mxf",safe="/")
        quoted_uri = quote(fake_uri,"")  # we are embedding a URI as a parameter with another URL so it must be double-encoded
        
        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        i.sendAuthorized.assert_called_with('POST',
                                            '/API/item/VX-123/shape?priority=HIGH&essence=false&tag=shapetagname&thumbnails=true&uri={0}'.format(
                                                quoted_uri)
                                            , "", {'Accept': 'application/xml'}, rawData=True)

        fake_uri = "file:///path/to/" + quote("media+with+plusses.mxf",safe="/+")
        quoted_uri = quote(fake_uri,"")  # we are embedding a URI as a parameter with another URL so it must be double-encoded
        
        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        i.sendAuthorized.assert_called_with('POST',
                                            '/API/item/VX-123/shape?priority=HIGH&essence=false&tag=shapetagname&thumbnails=true&uri={0}'.format(
                                                quoted_uri)
                                            , "", {'Accept': 'application/xml'}, rawData=True)

    def test_make_metadata_document(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)

        i.name = "VX-123"

        testdoc = i._make_metadata_document({"field1": "value1","field2": "value2"})

        self.assertEqual(testdoc,"""<?xml version='1.0' encoding='UTF-8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field1</name><value>value1</value></field></timespan></MetadataDocument>""")

        testdoc = i._make_metadata_document({"field1": ["value1","value2","value3"], "field2": "value2"})
        self.assertEqual(testdoc,"""<?xml version='1.0' encoding='UTF-8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field1</name><value>value1</value><value>value2</value><value>value3</value></field></timespan></MetadataDocument>""")

    def test_import_external_xml(self):
        with patch('gnmvidispine.vs_item.VSItem.raw_request') as mock_request:
            from gnmvidispine.vs_item import VSItem
            testdoc = """<?xml version="1.0" encoding="UTF-8"?>
            <external-metadata>
                <somefieldname>value</somefieldname>
            </external-metadata>
            """
            i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            i.name = "VX-345"
            i.import_external_xml(testdoc,projection_name="myprojection")

            mock_request.assert_called_once_with("/item/VX-345/metadata", method="PUT", matrix={'projection': 'myprojection'},body=testdoc)

    def test_import_external_xml_with_unicode(self):
        with patch('gnmvidispine.vs_item.VSItem.raw_request') as mock_request:
            from gnmvidispine.vs_item import VSItem
            testdoc = u"""<?xml version="1.0" encoding="UTF-8"?>
            <external-metadata>
                <somefieldname>Arséne Wenger est alleé en vacances</somefieldname>
                <someotherfield>This — is a silly long -, as in — not -</someotherfield>
            </external-metadata>
            """
            i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
            i.name = "VX-345"
            i.import_external_xml(testdoc,projection_name="myprojection")

            mock_request.assert_called_once_with("/item/VX-345/metadata", method="PUT", matrix={'projection': 'myprojection'},body=testdoc)

    def test_populate(self):
        with patch("gnmvidispine.vs_item.VSItem.request", return_value=ET.fromstring(self.testdoc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            i.populate("VX-1234")

            mock_request.assert_called_once_with("/item/VX-1234/metadata",method="GET")
            self.assertEqual(i.get("sometestfield"),"sometestvalue")
            self.assertEqual(i.get("someotherfield",allowArray=True),["valueone","valuetwo"])
            self.assertEqual(i.name,"VX-1234")

    def test_fromxml(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        i.fromXML(self.testdoc)

        self.assertEqual(i.get("sometestfield"),"sometestvalue")
        self.assertEqual(i.get("someotherfield", allowArray=True),["valueone","valuetwo"])

    def test_toxml(self):
        fix = re.compile(r'((?<=>)(\n[\t]*)(?=[^<\t]))|(?<=[^>\t])(\n[\t]*)(?=<)')

        #christ knows why it gets indented like this, but it does.
        output_testdoc = fix.sub("","""<?xml version='1.0' encoding='UTF-8'?>
<ns0:MetadataListDocument xmlns:ns0="http://xml.vidispine.com/schema/vidispine">
    <ns0:item id="VX-1234">
    <ns0:metadata>
        <ns0:timespan end="+INF" start="-INF">
            <ns0:field>
                <ns0:name>sometestfield</ns0:name>
                <ns0:value>sometestvalue</ns0:value>
            </ns0:field>
            <ns0:field>
                <ns0:name>someotherfield</ns0:name>
                <ns0:value>valueone</ns0:value>
                <ns0:value>valuetwo</ns0:value>
            </ns0:field>
        </ns0:timespan>
        </ns0:metadata>
        </ns0:item>
    </ns0:MetadataListDocument>""")

        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        i.fromXML(self.testdoc)

        self.assertEqual(fix.sub("",i.toXML()),output_testdoc)
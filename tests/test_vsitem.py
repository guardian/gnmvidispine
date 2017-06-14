# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
from urllib2 import quote


class TestVSItem(unittest2.TestCase):
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
    
    class MockedResponse(object):
        def __init__(self, status_code, content, reason=""):
            self.status = status_code
            self.body = content
            self.reason = reason
        
        def read(self):
            return self.body

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
                                            '/API/item/VX-123/shape?thumbnails=true&essence=false&tag=shapetagname&uri={0}&priority=HIGH&no-transcode=false'.format(quoted_uri)
                                            ,"",{'Accept':'application/xml'})

        fake_uri = "file:///path/to/" + quote("media with spaces.mxf",safe="/")
        quoted_uri = quote(fake_uri,"")  # we are embedding a URI as a parameter with another URL so it must be double-encoded
        
        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        i.sendAuthorized.assert_called_with('POST',
                                            '/API/item/VX-123/shape?thumbnails=true&essence=false&tag=shapetagname&uri={0}&priority=HIGH&no-transcode=false'.format(
                                                quoted_uri)
                                            , "", {'Accept': 'application/xml'})

        fake_uri = "file:///path/to/" + quote("media+with+plusses.mxf",safe="/+")
        quoted_uri = quote(fake_uri,"")  # we are embedding a URI as a parameter with another URL so it must be double-encoded
        
        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        i.sendAuthorized.assert_called_with('POST',
                                            '/API/item/VX-123/shape?thumbnails=true&essence=false&tag=shapetagname&uri={0}&priority=HIGH&no-transcode=false'.format(
                                                quoted_uri)
                                            , "", {'Accept': 'application/xml'})

    def test_make_metadata_document(self):
        from gnmvidispine.vs_item import VSItem
        from datetime import datetime
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)

        i.name = "VX-123"

        testdoc = i._make_metadata_document({"field1": "value1","field2": "value2"})

        self.assertEqual(testdoc,"""<?xml version='1.0' encoding='UTF-8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field1</name><value>value1</value></field></timespan></MetadataDocument>""")

        testdate = datetime.now()
        testdoc = i._make_metadata_document({"field1": testdate, "field2": "value2"})

        shouldreturndoc = """<?xml version='1.0' encoding='UTF-8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field1</name><value>{0}</value></field></timespan></MetadataDocument>""".format(
            testdate.isoformat("T")
        )
        self.assertEqual(testdoc, shouldreturndoc)

        testdoc = i._make_metadata_document({"field1": ["value1","value2","value3"], "field2": "value2"})
        self.assertEqual(testdoc,"""<?xml version='1.0' encoding='UTF-8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field1</name><value>value1</value><value>value2</value><value>value3</value></field></timespan></MetadataDocument>""")

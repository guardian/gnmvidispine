from __future__ import absolute_import
import unittest2
from mock import MagicMock
import httplib
import base64


class TestVSApi(unittest2.TestCase):
    fake_host='localhost'
    fake_port=8080
    fake_user='username'
    fake_passwd='password'
    
    class MockedResponse(object):
        def __init__(self, status_code, content, reason=""):
            self.status = status_code
            self.body = content
            self.reason = reason
            
        def read(self):
            return self.body
        
    def test_get(self):
        """
        test a simple HTTP get request
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi
        sample_returned_xml = """<?xml version="1.0"?>
        <root xmlns="http://xml.vidispine.com/schema/vidispine">
          <element>string</element>
        </root>"""
        
        conn = httplib.HTTPConnection(host='localhost',port=8080)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(200,sample_returned_xml))
        
        api = VSApi(user=self.fake_user,passwd=self.fake_passwd,conn=conn)
        parsed_xml = api.request("/path/to/endpoint",method="GET")
        
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user,self.fake_passwd))
        conn.request.assert_called_with('GET','/API/path/to/endpoint', None, {'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()
        
        teststring = parsed_xml.find('{0}element'.format("{http://xml.vidispine.com/schema/vidispine}"))
        self.assertEqual(teststring.text,"string")
        
    def test_404(self):
        from gnmvidispine.vidispine_api import VSApi, VSNotFound, HTTPError
        
        exception_response = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ExceptionDocument xmlns="http://xml.vidispine.com/schema/vidispine">
  <notFound>
    <type>Item</type>
    <id>SD-46362</id>
  </notFound>
</ExceptionDocument>"""
        
        conn = httplib.HTTPConnection(host='localhost', port=8080)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(404, exception_response, reason="Test 404 failure"))
    
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
        
        with self.assertRaises(VSNotFound) as ex:
            api.request("/item/SD-46362/metadata", method="GET")

        self.assertEqual("SD-46362",ex.exception.exceptionID)
        self.assertEqual("notFound",ex.exception.exceptionType)
        self.assertEqual("no explanation provided",ex.exception.exceptionWhat)
            
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('GET', '/API/item/SD-46362/metadata', None,
                                        {'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()
    
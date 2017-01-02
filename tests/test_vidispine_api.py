from __future__ import absolute_import
import unittest2
from mock import MagicMock
import httplib
import base64
import logging

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

    def test_put(self):
        """
        test a simple HTTP put request
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi
        sample_send_xml = """<?xml version="1.0"?>
        <root xmlns="http://xml.vidispine.com/schema/vidispine">
          <element>string</element>
        </root>"""
        
        sample_returned_xml = """<?xml version="1.0"?>
        <response xmlns="http://xml.vidispine.com/schema/vidispine">
          <returned-element>string</returned-element>
        </response>
        """
        conn = httplib.HTTPConnection(host=self.fake_host, port=self.fake_port)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(200, sample_returned_xml)) #simulate empty OK response
    
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
        parsed_xml = api.request("/path/to/endpoint", method="PUT", body=sample_send_xml)
    
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('PUT', '/API/path/to/endpoint', sample_send_xml,
                                        {'Content-Type': 'application/xml', 'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()

        teststring = parsed_xml.find('{0}returned-element'.format("{http://xml.vidispine.com/schema/vidispine}"))
        self.assertEqual(teststring.text, "string")
        
    def test_post(self):
        """
        test a simple HTTP post request
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi
        sample_send_xml = """<?xml version="1.0"?>
        <root xmlns="http://xml.vidispine.com/schema/vidispine">
          <element>string</element>
        </root>"""
    
        conn = httplib.HTTPConnection(host=self.fake_host, port=self.fake_port)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(201, ""))  # simulate empty OK response
    
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
        api.request("/path/to/endpoint", method="POST", body=sample_send_xml)
    
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('POST', '/API/path/to/endpoint', sample_send_xml,
                                        {'Content-Type': 'application/xml', 'Authorization': "Basic " + computed_auth,
                                         'Accept'      : 'application/xml'})
        conn.getresponse.assert_called_with()
        
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
        
    def test_400(self):
        """
        tests the VSBadRequest exception
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi, VSBadRequest
        request_body = """<MetadataDocument xmlns="http://xml.vidispine.com/">
  <field>
    <name>blah</name>
    <value>smith</value>
  </field>
</MetadataDocument>"""  #invalid namespace will raise bad request error
        exception_response = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><ExceptionDocument xmlns="http://xml.vidispine.com/schema/vidispine"><invalidInput><context>metadata</context><id>VX-3245</id><explanation>Couldn't transform the input according to the projection.</explanation></invalidInput></ExceptionDocument>"""

        conn = httplib.HTTPConnection(host='localhost', port=8080)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(400, exception_response, reason="Test 40- failure"))
    
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
    
        with self.assertRaises(VSBadRequest) as ex:
            api.request("/item/VX-3245/metadata", method="PUT", body=request_body)
    
        self.assertEqual("VX-3245", ex.exception.exceptionID)
        self.assertEqual("invalidInput", ex.exception.exceptionType)
        self.assertEqual("Couldn't transform the input according to the projection.", ex.exception.exceptionWhat)
    
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('PUT', '/API/item/VX-3245/metadata', request_body,
                                        {'Content-Type': 'application/xml', 'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        
    def test_503(self):
        """
        test the exponential backoff/retry if server not available
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi,HTTPError
        from time import time
        
        conn = httplib.HTTPConnection(host=self.fake_host, port=self.fake_port)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(503, "No server available"))

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("gnmvidispine.vidispine_api")
        logger.error = MagicMock()
        logger.warning = MagicMock()
        
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn, logger=logger)
        api.retry_delay=1
        api.retry_attempts=5
        
        start_time = time()
        with self.assertRaises(HTTPError) as cm:
            api.request("/path/to/endpoint", method="GET")

        end_time = time()
        
        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('GET', '/API/path/to/endpoint', None,
                                        {'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()

        self.assertEqual(cm.exception.code, 503)
        self.assertGreaterEqual(end_time - start_time, api.retry_delay * api.retry_attempts)
        
        logger.warning.assert_called_with('Server not available error when contacting Vidispine. Waiting 1s before retry.')
        self.assertEqual(logger.warning.call_count, 6)
        
        logger.error.assert_called_with('Did not work after 5 retries, giving up')
        
    def test_409(self):
        """
        tests the VSConflict exception
        :return:
        """
        pass
    
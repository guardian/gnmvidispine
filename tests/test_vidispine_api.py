from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
import httplib
import base64
import logging
import tempfile
from os import urandom
from httplib import CannotSendRequest

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
        test the VSBadRequest exception, including error parsing
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
    
    def test_chunked_upload(self):
        """
        test the chunked_upload_request functionality
        :return:
        """
        from gnmvidispine.vidispine_api import VSApi,HTTPError
        
        conn = httplib.HTTPConnection(host=self.fake_host, port=self.fake_port)
        conn.request = MagicMock()
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("gnmvidispine.vidispine_api")
        logger.error = MagicMock()
        logger.warning = MagicMock()
        logger.debug = MagicMock()
        
        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn, logger=logger)
        api.raw_request = MagicMock()

        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        
        #create a test file
        testfilesize = 100000
        testchunksize = 1000
        
        class FakeUuid4(object):
            """
            mock object to return a known id. used via mock.patch below.
            """
            def get_hex(self):
                return 'fa6032d61c7b4db19425c6404ea7b822'
            
        with tempfile.TemporaryFile() as f:
            filecontent = bytes(urandom(testfilesize))
            f.write(filecontent)
            with patch('uuid.uuid4', side_effect=lambda: FakeUuid4()):
                api.chunked_upload_request(f, testfilesize, testchunksize, '/API/fakeupload', transferPriority=100, throttle=False,
                                           method="POST", filename="fakefile.dat", extra_headers={'extra_header': 'true'})
                
                should_have_headers = {
                    'Authorization': "Basic " + computed_auth,
                    'Content-Type': 'application/octet-stream',
                    'Accept': 'application/xml'
                }
                
                for byteindex in range(0,testfilesize,testchunksize):
                    should_have_qparams = {
                        'transferId': 'fa6032d61c7b4db19425c6404ea7b822',
                        'transferPriority': 100,
                        'throttle': False,
                        'filename': 'fakefile.dat'
                    }
                    should_have_extra_headers = {
                        'index': byteindex,
                        'size': testchunksize,
                    }
                    api.raw_request.assert_any_call('/API/fakeupload', matrix=None, body=filecontent[byteindex:byteindex+testchunksize],
                                                       content_type='application/octet-stream', method="POST",
                                                       query=should_have_qparams, extra_headers=should_have_extra_headers)

    def test_reuse(self):
        from gnmvidispine.vidispine_api import VSApi
        conn = httplib.HTTPConnection(host='localhost',port=8080)
        conn.request = MagicMock(side_effect=CannotSendRequest())
        
        a = VSApi(host='localhost',user='testuser',passwd='testpasswd',conn=conn)
        a.reset_http = MagicMock()
        
        with patch('time.sleep') as sleepmock:  #mocking sleep() makes the test run faster
            with self.assertRaises(CannotSendRequest):
                a.sendAuthorized('GET','/fake_path',"",{})
        self.assertEqual(a.reset_http.call_count,11)
        self.assertEqual(sleepmock.call_count,11)
    
    def test_reset_http(self):
        from gnmvidispine.vidispine_api import VSApi
        conn = httplib.HTTPConnection(host='localhost', port=8080)
        conn.close = MagicMock()

        a = VSApi(host='localhost', user='testuser', passwd='testpasswd', conn=conn)
        a.reset_http()
        conn.close.assert_called_once()
        self.assertNotEqual(conn,a._conn) #we should get a different object

    def test_querydict(self):
        from gnmvidispine.vidispine_api import VSApi
        sample_returned_xml = """<?xml version="1.0"?>
        <root xmlns="http://xml.vidispine.com/schema/vidispine">
          <element>string</element>
        </root>"""

        conn = httplib.HTTPConnection(host='localhost', port=8080)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(200, sample_returned_xml))

        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
        queryparams={
            'query1': 'value1',
            'query2': 'value2',
            'query3': ['value3','value4','value5']
        }

        parsed_xml = api.request("/path/to/endpoint", query=queryparams, method="GET")

        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('GET', '/API/path/to/endpoint?query2=value2&query3=value3&query3=value4&query3=value5&query1=value1', None,
                                        {'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()

    def test_matrixdict(self):
        from gnmvidispine.vidispine_api import VSApi
        sample_returned_xml = """<?xml version="1.0"?>
        <root xmlns="http://xml.vidispine.com/schema/vidispine">
          <element>string</element>
        </root>"""

        conn = httplib.HTTPConnection(host='localhost', port=8080)
        conn.request = MagicMock()
        conn.getresponse = MagicMock(return_value=self.MockedResponse(200, sample_returned_xml))

        api = VSApi(user=self.fake_user, passwd=self.fake_passwd, conn=conn)
        mtxparams={
            'mtx1': 'value1',
            'mtx2': 'value2',
            'mtx3': ['value3','value4','value5']
        }

        parsed_xml = api.request("/path/to/endpoint", matrix=mtxparams, method="GET")

        computed_auth = base64.b64encode("{0}:{1}".format(self.fake_user, self.fake_passwd))
        conn.request.assert_called_with('GET', '/API/path/to/endpoint;mtx3=value3;mtx3=value4;mtx3=value5;mtx2=value2;mtx1=value1', None,
                                        {'Authorization': "Basic " + computed_auth, 'Accept': 'application/xml'})
        conn.getresponse.assert_called_with()
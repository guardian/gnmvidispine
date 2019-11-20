# -*- coding: UTF-8 -*-
from future.standard_library import install_aliases
install_aliases()
import unittest2
from mock import MagicMock, patch
from urllib.parse import quote
import xml.etree.cElementTree as ET
import re
from urllib.parse import urlparse
from urllib.parse import parse_qs


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

    testdoctwo = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
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
    </ItemDocument>"""

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

        i.import_to_shape(uri=fake_uri,shape_tag="shapetagname",priority="HIGH")
        arg1, arg2, arg3, arg4 = i.sendAuthorized.call_args[0]
        self.assertEqual(arg1, 'POST')
        self.assertEqual(arg3, '')
        self.assertEqual(arg4, {'Accept': 'application/xml'})
        parsed_url = urlparse(arg2)
        self.assertEqual(parsed_url.path, '/API/item/VX-123/shape')
        query_dict = parse_qs(parsed_url.query)
        self.assertEqual(query_dict['priority'], ['HIGH'])
        self.assertEqual(query_dict['essence'], ['false'])
        self.assertEqual(query_dict['tag'], ['shapetagname'])
        self.assertEqual(query_dict['thumbnails'], ['true'])
        self.assertEqual(query_dict['uri'], ['file:///path/to/newmedia.mxf'])

        fake_uri = "file:///path/to/" + quote("media with spaces.mxf",safe="/")

        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        arg1, arg2, arg3, arg4 = i.sendAuthorized.call_args[0]
        self.assertEqual(arg1, 'POST')
        self.assertEqual(arg3, '')
        self.assertEqual(arg4, {'Accept': 'application/xml'})
        parsed_url = urlparse(arg2)
        self.assertEqual(parsed_url.path, '/API/item/VX-123/shape')
        query_dict = parse_qs(parsed_url.query)
        self.assertEqual(query_dict['priority'], ['HIGH'])
        self.assertEqual(query_dict['essence'], ['false'])
        self.assertEqual(query_dict['tag'], ['shapetagname'])
        self.assertEqual(query_dict['thumbnails'], ['true'])
        self.assertEqual(query_dict['uri'], ['file:///path/to/media%20with%20spaces.mxf'])

        fake_uri = "file:///path/to/" + quote("media+with+plusses.mxf",safe="/+")

        i.import_to_shape(uri=fake_uri, shape_tag="shapetagname", priority="HIGH")
        arg1, arg2, arg3, arg4 = i.sendAuthorized.call_args[0]
        self.assertEqual(arg1, 'POST')
        self.assertEqual(arg3, '')
        self.assertEqual(arg4, {'Accept': 'application/xml'})
        parsed_url = urlparse(arg2)
        self.assertEqual(parsed_url.path, '/API/item/VX-123/shape')
        query_dict = parse_qs(parsed_url.query)
        self.assertEqual(query_dict['priority'], ['HIGH'])
        self.assertEqual(query_dict['essence'], ['false'])
        self.assertEqual(query_dict['tag'], ['shapetagname'])
        self.assertEqual(query_dict['thumbnails'], ['true'])
        self.assertEqual(query_dict['uri'], ['file:///path/to/media+with+plusses.mxf'])

    def test_make_metadata_document(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)

        i.name = "VX-123"

        testdoc = i._make_metadata_document({"field2": "value2", "field3": 3,"field1": "value1"})

        self.assertEqual(testdoc,b"""<?xml version='1.0' encoding='utf8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>field2</name><value>value2</value></field><field><name>field3</name><value>3</value></field><field><name>field1</name><value>value1</value></field></timespan></MetadataDocument>""")

        testdoc = i._make_metadata_document({"field2": "value2", "field1": ["value1","value2","value3"]})
        self.assertEqual(testdoc,b"""<?xml version='1.0' encoding='utf8'?>
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
            testdoc = """<?xml version="1.0" encoding="UTF-8"?>
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

    def test_fromxml_can_code_with_ItemDocument(self):
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        i.fromXML(self.testdoctwo)

        self.assertEqual(i.get("sometestfield"),"sometestvalue")
        self.assertEqual(i.get("someotherfield", allowArray=True),["valueone","valuetwo"])

    def test_toxml(self):
        fix = re.compile(b'((?<=>)(\n[\t]*)(?=[^<\t]))|(?<=[^>\t])(\n[\t]*)(?=<)')

        #christ knows why it gets indented like this, but it does.
        output_testdoc = fix.sub(b"",b"""<?xml version='1.0' encoding='utf8'?>
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

        self.assertEqual(fix.sub(b"",i.toXML()),output_testdoc)

    def test_get_metadata_attributes(self):
        fake_data = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <revision>KP-19029938,KP-19008430,KP-19008428,KP-19008429</revision>
    <timespan start="-INF" end="+INF">
        <field uuid="6062c7ee-b4fe-4bbb-b61e-5d3debb05713" user="richard_sprenger" timestamp="2017-06-02T17:46:59.926+01:00" change="KP-19029938">
            <name>gnm_commission_status</name>
            <value uuid="d44f4268-f7af-46aa-884f-905855026c74" user="richard_sprenger" timestamp="2017-06-02T17:46:59.926+01:00" change="KP-19029938">Completed</value>
        </field>
        <field uuid="9860f876-b9e8-4799-8e68-cb292818a9cd" user="richard_sprenger" timestamp="2017-06-02T11:26:41.478+01:00" change="KP-19008429">
            <name>gnm_commission_owner</name>
            <value uuid="19e2cfdd-dd4c-4dc6-b910-6ce55b0c9c93" user="richard_sprenger" timestamp="2017-06-02T11:26:41.478+01:00" change="KP-19008429">11</value>
            <value uuid="EF41268C-00B4-431D-A36E-6D3B4D59A06A" user="bob_smith" timestamp="2017-06-02T11:26:44.478+01:00" change="KP-19008430">14</value>
        </field>
    </timespan>
</MetadataDocument>"""

        from gnmvidispine.vs_collection import VSCollection
        i = VSCollection(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        i.collectionId="VX-1234"
        i.fromXML(fake_data, objectClass="collection")

        result = i.get_metadata_attributes("gnm_commission_status")
        self.assertEqual(result[0].uuid,"6062c7ee-b4fe-4bbb-b61e-5d3debb05713")
        self.assertEqual(str(result[0].values),'[VSMetadataValue("Completed")]')

        result2 = i.get_metadata_attributes("gnm_commission_owner")
        self.assertEqual(str(result2[0].values),'[VSMetadataValue("11"), VSMetadataValue("14")]')

        result3 = i.get_metadata_attributes("invalidfieldname")
        self.assertEqual(result3, None)

    def test_add_external_id(self):
        """
        add_external_id should call to VS to set an external ID
        :return:
        """
        with patch('gnmvidispine.vs_item.VSItem.request') as mock_request:
            from gnmvidispine.vs_item import VSItem
            i = VSItem(host="localhost",port=1234,user="me",passwd="secret")

            i.name="VX-1234"
            i.add_external_id("08473AFA-E7D5-4B92-9C4F-81035523A492")
            mock_request.assert_called_once_with("/item/VX-1234/external-id/08473AFA-E7D5-4B92-9C4F-81035523A492", method="PUT")

    def test_remove_external_id(self):
        """
        remove_external_id should call VS to delete external id
        :return:
        """
        with patch('gnmvidispine.vs_item.VSItem.request') as mock_request:
            from gnmvidispine.vs_item import VSItem
            i = VSItem(host="localhost",port=1234,user="me",passwd="secret")

            i.name="VX-1234"
            i.remove_external_id("08473AFA-E7D5-4B92-9C4F-81035523A492")
            mock_request.assert_called_once_with("/item/VX-1234/external-id/08473AFA-E7D5-4B92-9C4F-81035523A492", method="DELETE")

    def test_transcode_error(self):
        """
        tests the VSTranscodeError exception
        :return:
        """

        job_doc = """<JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
            <jobId>VX-80</jobId>
            <status>FAILED</status>
            <type>PLACEHOLDER_IMPORT</type>
        </JobDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(job_doc)) as mock_request:
            with patch('gnmvidispine.vs_item.VSJob.request', return_value=ET.fromstring(job_doc)) as mock_request_two:
                from gnmvidispine.vs_item import VSItem, VSTranscodeError
                i = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
                with self.assertRaises(VSTranscodeError) as ex:
                    i.transcode("VX-3245")

    def test_path(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>text</name>
                    <value>sometestvalue</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        from gnmvidispine.vs_item import VSItem
        i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        i.fromXML(ET.fromstring(test_item_doc))
        output_path = i.path()
        self.assertEqual(output_path, "/item/VX-1234")

    def test_create_placeholder(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>text</name>
                    <value>sometestvalue</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        job_doc = """<JobDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
            <jobId>VX-80</jobId>
            <status>FAILED</status>
            <type>PLACEHOLDER_IMPORT</type>
        </JobDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            i = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            i.fromXML(ET.fromstring(test_item_doc))
            test_placeholder = i.createPlaceholder()
            arg1, arg2 = i.request.call_args
            self.assertEqual(arg1, ('/import/placeholder',))
            test_dict = arg2
            self.assertEqual(test_dict['method'], 'POST')
            self.assertEqual(test_dict['query'], {'video': 1, 'container': 1})
            self.assertEqual(test_placeholder.name, "VX-1234")
            self.assertEqual(test_placeholder.type, "item")
            self.assertEqual(test_placeholder.contentDict, {'text': 'sometestvalue'})

    def test_create_placeholder_from_metadata(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value>1</value>
                </field>
                <field>
                    <name>anothertest</name>
                    <value>2</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_placeholder_two = test_item.createPlaceholder(metadata={'test': '1', 'anothertest': '2'})
            arg1, arg2 = test_item.request.call_args
            self.assertEqual(arg1, ('/import/placeholder',))
            test_dict = arg2
            self.assertEqual(test_dict['method'], 'POST')
            self.assertEqual(test_dict['query'], {'container': 1})
            self.assertIn(b'<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test</name><value>1</value></field><field><name>anothertest</name><value>2</value></field></timespan></MetadataDocument>', test_dict['body'])
            self.assertEqual(test_placeholder_two.name, "VX-1234")
            self.assertEqual(test_placeholder_two.type, "item")

    def test_delete(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value>1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.fromXML(ET.fromstring(test_item_doc))
            test_item.delete()
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234',))
            self.assertEqual(test_dict['method'], 'DELETE')
            self.assertEqual(test_dict['query'], {})

        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.fromXML(ET.fromstring(test_item_doc))
            test_item.delete(keepShapeTagMedia=['original', 'test', 'string'])
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234',))
            self.assertEqual(test_dict['method'], 'DELETE')
            self.assertEqual(test_dict['query'], {'keepShapeTagMedia': 'original,test,string'})

        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.fromXML(ET.fromstring(test_item_doc))
            test_item.delete(keepShapeTagStorage=['VX-1', 'VX-2', 'VX-3'])
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234',))
            self.assertEqual(test_dict['method'], 'DELETE')
            self.assertEqual(test_dict['query'], {'keepShapeTagStorage': 'VX-1,VX-2,VX-3'})

    def test_get_metadata_field(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value>value</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            returned_value = test_item.get('test')
            self.assertEqual(returned_value, 'value')

        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value>value</value>
                    <value>two</value>
                    <value>three</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            returned_value = test_item.get('test')
            self.assertEqual(returned_value, 'value|two|three')
            returned_value = test_item.get('test', allowArray=True)
            self.assertEqual(returned_value, ['value', 'two', 'three'])

    def test_copy_to_placeholder(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value>1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            new_item = test_item.copyToPlaceholder(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            self.assertEqual(new_item.name, 'VX-1234')
            self.assertEqual(new_item.type, 'item')

    def test_metadata_changesets(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""

        changes_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <MetadataChangeSetDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<changeSet>
<id>VX-4784396</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="3f5dfaf5-0a50-4882-91cb-7511aabfbe33" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">
<name>gnm_asset_filming_location</name>
<value uuid="7a78948e-0b9e-4074-8315-2c224894eac0" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">None</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784397</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="ab1de902-2c25-4a67-aeb5-98b1819639af" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">
<name>mediaType</name>
<value uuid="3b71e57c-0cbd-4aa7-b5f0-eee04a8f5dea" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">none</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784398</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="85f785a8-037e-472a-8cfd-3ef1c21b52d6" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784398">
<name>shapeTag</name>
<value uuid="e2350aed-9835-4c6e-9a5c-989a86f42def" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784398">original</value>
 </field>
</timespan>
 </metadata>
 </changeSet>
 </MetadataChangeSetDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(changes_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            output_changesets = test_item.metadata_changesets()

            test_place = 1

            for changeset in output_changesets:
                if test_place is 1:
                    self.assertIn(b'admin', ET.tostring(changeset.mdContent))
                if test_place is 2:
                    self.assertIn(b'ab1de902-2c25-4a67-aeb5-98b1819639af', ET.tostring(changeset.mdContent))
                if test_place is 3:
                    self.assertIn(b'e2350aed-9835-4c6e-9a5c-989a86f42def', ET.tostring(changeset.mdContent))
                test_place = test_place + 1

    def test_metadata_changeset_list(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""

        changes_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <MetadataChangeSetDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<changeSet>
<id>VX-4784396</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="3f5dfaf5-0a50-4882-91cb-7511aabfbe33" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">
<name>gnm_asset_filming_location</name>
<value uuid="7a78948e-0b9e-4074-8315-2c224894eac0" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">None</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784397</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="ab1de902-2c25-4a67-aeb5-98b1819639af" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">
<name>mediaType</name>
<value uuid="3b71e57c-0cbd-4aa7-b5f0-eee04a8f5dea" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">none</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784398</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="85f785a8-037e-472a-8cfd-3ef1c21b52d6" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784398">
<name>shapeTag</name>
<value uuid="e2350aed-9835-4c6e-9a5c-989a86f42def" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784398">original</value>
 </field>
</timespan>
 </metadata>
 </changeSet>
 </MetadataChangeSetDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(changes_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            output_changeset_list = test_item.metadata_changeset_list()
            self.assertIn(b'admin', ET.tostring(output_changeset_list[0].mdContent))
            self.assertIn(b'ab1de902-2c25-4a67-aeb5-98b1819639af', ET.tostring(output_changeset_list[1].mdContent))
            self.assertIn(b'e2350aed-9835-4c6e-9a5c-989a86f42def', ET.tostring(output_changeset_list[2].mdContent))

    def test_metadata_changesets_for_field(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""

        changes_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <MetadataChangeSetDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<changeSet>
<id>VX-4784396</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="3f5dfaf5-0a50-4882-91cb-7511aabfbe33" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">
<name>gnm_asset_filming_location</name>
<value uuid="7a78948e-0b9e-4074-8315-2c224894eac0" user="admin" timestamp="2015-09-06T06:29:23.463+01:00" change="VX-4784396">None</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784397</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="ab1de902-2c25-4a67-aeb5-98b1819639af" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">
<name>mediaType</name>
<value uuid="3b71e57c-0cbd-4aa7-b5f0-eee04a8f5dea" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784397">none</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
 <changeSet>
<id>VX-4784398</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="ab1de902-2c25-4a67-aeb4-98b1819639af" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784398">
<name>mediaType</name>
<value uuid="3b71e57c-0cbd-4aa7-b5f4-eee04a8f5dea" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784398">none</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
<changeSet>
<id>VX-4784399</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="85f785a8-037e-472a-8cfd-3ef1c21b52d6" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784399">
<name>shapeTag</name>
<value uuid="e2350aed-9835-4c6e-9a5c-989a86f42def" user="system" timestamp="2015-09-06T06:29:25.250+01:00" change="VX-4784399">original</value>
 </field>
</timespan>
 </metadata>
 </changeSet>
 <changeSet>
<id>VX-4784400</id>
<metadata>
<revision />
<timespan start="-INF" end="+INF">
<field uuid="ab1de902-2c23-4a67-aeb5-98b1819639af" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784400">
<name>mediaType</name>
<value uuid="3b71e57c-0cb3-4aa7-b5f0-eee04a8f5dea" user="system" timestamp="2015-09-06T06:29:24.375+01:00" change="VX-4784400">none</value>
 </field>
 </timespan>
 </metadata>
 </changeSet>
 </MetadataChangeSetDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(changes_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            output_changesets = test_item.metadata_changesets_for_field('mediaType')

            test_place = 1

            for changeset in output_changesets:
                if test_place is 1:
                    self.assertIn(b'ab1de902-2c25-4a67-aeb5-98b1819639af', ET.tostring(changeset.mdContent))
                if test_place is 2:
                    self.assertIn(b'3b71e57c-0cbd-4aa7-b5f4-eee04a8f5dea', ET.tostring(changeset.mdContent))
                if test_place is 3:
                    self.assertIn(b'ab1de902-2c23-4a67-aeb5-98b1819639af', ET.tostring(changeset.mdContent))
                test_place = test_place + 1

    def test_project(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        test_projection_doc = """<?xml version="1.0" encoding="UTF-8" ?>
<meta-data>
<meta-group type="movie meta">
<meta name="gnm_legacydata_fcs_metadata_set" value="pa_asset_guardian_masters" />
<--1-->
<meta name="xmp_xmpMM_OriginalDocumentID" value="xmp.did:afc6234c-1442-4e1b-aae2-14457d9e1bc7" />
 </meta-group>
<meta-movie-info>
<meta-audio-track tokens="channels bitspersample samplerate" />
 </meta-movie-info>
 </meta-data>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            with patch('gnmvidispine.vs_item.VSItem.raw_request', return_value=test_projection_doc) as mock_request:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                output_projection = test_item.project('inmeta_V5')
                test_item.raw_request.assert_called_with('/item/VX-1234/metadata', matrix={'projection': 'inmeta_V5'})
                self.assertIn('channels bitspersample samplerate', output_projection)
                self.assertIn('xmp.did:afc6234c-1442-4e1b-aae2-14457d9e1bc7', output_projection)
                self.assertIn('pa_asset_guardian_masters', output_projection)

    def test_set_metadata(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', return_value=ET.fromstring(test_item_doc)) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            test_item.set_metadata({'one': 'two', 'three': 'four'})
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234/metadata',))
            self.assertEqual(test_dict['method'], 'PUT')
            self.assertIn(b'<name>one</name>', test_dict['body'])
            self.assertIn(b'<value>two</value>', test_dict['body'])
            self.assertIn(b'<name>three</name>', test_dict['body'])
            self.assertIn(b'<value>four</value>', test_dict['body'])
            test_item.set_metadata({'one': 'two', 'three': 'four'}, group='Asset', entitytype='item', mode='add')
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234/metadata',))
            self.assertEqual(test_dict['method'], 'PUT')
            self.assertIn(b'<name>one</name>', test_dict['body'])
            self.assertIn(b'<value>two</value>', test_dict['body'])
            self.assertIn(b'<name>three</name>', test_dict['body'])
            self.assertIn(b'<value>four</value>', test_dict['body'])
            self.assertIn(b'<group>Asset</group>', test_dict['body'])

    def test_get_shape(self):
        from gnmvidispine.vidispine_api import VSNotFound
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        shape_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <uri>VX-901604</uri>
        </URIListDocument>"""
        shape_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901604</id>
<essenceVersion>0</essenceVersion>
<tag>lowres</tag>
<mimeType>video/mp4</mimeType>
<containerComponent>
<file>
<id>VX-48077439</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://1fa3ad40-65e4-11e9-a3bc-bc113b8044e7:_VSENC__3uhd3tAWvFSU0WX0W8TkA1halNoyKnHuf9Q4KlqgRMFjh%2FtK%2FVxjUQ==@10.235.51.145/5ce37552-358f-998b-115b-9569b8f21a01/1d07a65a-65e4-11e9-a3bc-bc113b8044e7/141019_9661710_lowres.mp4</uri>
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
<key>MXFS_CREATIONDAY</key>
<value>16</value>
 </field>
<field>
<key>MXFS_CATEGORY</key>
<value>2</value>
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
 </file>
 <file>
<id>VX-25493774</id>
<path>141019_9661710_lowres.mp4</path>
<uri>file:///srv/Proxies2/CantemoProxies/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2017-04-18T11:52:35.888+01:00</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-10</storage>
<metadata>
<field>
<key>created</key>
<value>1442718812000</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
 </metadata>
 </file>
<file>
<id>VX-48072947</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://c8aa3eed-65e4-11e9-be56-8fb572ba0596:_VSENC__qkSnrEsZToutNO8juCnCZlufKDPDzqno4BG1TunbwY%2FqOOVMKmQPgg==@10.236.51.145/38b7c064-a862-0fe2-44cd-7191ca6201c3/c5b7da33-65e4-11e9-be56-8fb572ba0596/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2019-11-14T17:01:27.118Z</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-77</storage>
<metadata>
<field>
<key>MXFS_PARENTOID</key>
<value />
 </field>
<field>
<key>MXFS_CREATION_TIME</key>
<value>1558041261817</value>
 </field>
<field>
<key>MXFS_CREATIONDAY</key>
<value>16</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
<field>
<key>uuid</key>
<value>8ef02c67-749e-11e9-89c7-cd904410bfea-2589</value>
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
 </file>
<id>VX-2313281</id>
<metadata>
<key>creation_time</key>
<value>2014-10-19 15:56:52</value>
 </metadata>
<metadata>
<key>major_brand</key>
<value>qt</value>
 </metadata>
<metadata>
<key>drop_frame</key>
<value>false</value>
 </metadata>
<metadata>
<key>compatible_brands</key>
<value>qt</value>
 </metadata>
<duration>
<samples>322120000</samples>
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
<denominator>2500</denominator>
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
<value>AAC LC</value>
 </property>
<property>
<key>Audio_Format_List</key>
<value>AAC</value>
 </property>
<property>
<key>Codecs Video</key>
<value>AVC</value>
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
<value>291297</value>
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
<key>Video_Language_List</key>
<value>English</value>
 </property>
<property>
<key>Writing library</key>
<value>Apple QuickTime</value>
 </property>
<property>
<key>Writing library/Name</key>
<value>Apple QuickTime</value>
 </property>
 </mediaInfo>
 </containerComponent>
<audioComponent>
<file>
<id>VX-48077439</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://1fa3ad40-65e4-11e9-a3bc-bc113b8044e7:_VSENC__3uhd3tAWvFSU0WX0W8TkA1halNoyKnHuf9Q4KlqgRMFjh%2FtK%2FVxjUQ==@10.235.51.145/5ce37552-358f-998b-115b-9569b8f21a01/1d07a65a-65e4-11e9-a3bc-bc113b8044e7/141019_9661710_lowres.mp4</uri>
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
<key>mtime</key>
<value>1442718812000</value>
 </field>
<field>
<key>MXFS_ARCHYEAR</key>
<value>2019</value>
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
<key>MXFS_CREATIONMONTH</key>
<value>5</value>
 </field>
 </metadata>
 </file>
<file>
<id>VX-25493774</id>
<path>141019_9661710_lowres.mp4</path>
<uri>file:///srv/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2017-04-18T11:52:35.888+01:00</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-10</storage>
<metadata>
<field>
<key>created</key>
<value>1442718812000</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
 </metadata>
 </file>
<file>
<id>VX-48072947</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://c8aa3eed-65e4-11e9-be56-8fb572ba0596:_VSENC__qkSnrEsZToutNO8juCnCZlufKDPDzqno4BG1TunbwY%2FqOOVMKmQPgg==@10.236.51.145/38b7c064-a862-0fe2-44cd-7191ca6201c3/c5b7da33-65e4-11e9-be56-8fb572ba0596/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2019-11-14T17:01:27.118Z</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-77</storage>
<metadata>
<field>
<key>MXFS_PARENTOID</key>
<value />
 </field>
<field>
<key>MXFS_CREATION_TIME</key>
<value>1558041261817</value>
 </field>
<field>
<key>MXFS_CREATIONDAY</key>
<value>16</value>
 </field>
<field>
<key>MXFS_FILENAME</key>
<value>141019_9661710_lowres.mp4</value>
 </field>
 </metadata>
 </file>
<id>VX-2313282</id>
<metadata>
<key>creation_time</key>
<value>2014-10-19 15:56:52</value>
 </metadata>
<metadata>
<key>handler_name</key>
<value>Apple Alias Data Handler</value>
 </metadata>
<metadata>
<key>language</key>
<value>eng</value>
 </metadata>
<codec>aac</codec>
<timeBase>
<numerator>1</numerator>
<denominator>48000</denominator>
 </timeBase>
<itemTrack>A1</itemTrack>
<essenceStreamId>1</essenceStreamId>
<bitrate>125551</bitrate>
<numberOfPackets>15100</numberOfPackets>
<extradata>1190</extradata>
<pid>2</pid>
<duration>
<samples>15462400</samples>
<timeBase>
<numerator>1</numerator>
<denominator>48000</denominator>
 </timeBase>
 </duration>
<edl>
<timeScale>
<numerator>1</numerator>
<denominator>2500</denominator>
 </timeScale>
<entry start="0" length="805300" mediaRate="65536" />
 </edl>
<startTimestamp>
<samples>0</samples>
<timeBase>
<numerator>1</numerator>
<denominator>48000</denominator>
 </timeBase>
 </startTimestamp>
<channelCount>2</channelCount>
<channelLayout>3</channelLayout>
<sampleFormat>AV_SAMPLE_FMT_S16</sampleFormat>
<frameSize>1024</frameSize>
<mediaInfo>
<Bit_rate_mode>CBR</Bit_rate_mode>
<property>
<key>Bit rate</key>
<value>128000</value>
 </property>
<property>
<key>Bit rate mode</key>
<value>CBR</value>
 </property>
<property>
<key>Channel positions</key>
<value>2/0/0</value>
 </property>
<property>
<key>Channel(s)</key>
<value>2</value>
 </property>
<property>
<key>ChannelLayout</key>
<value>L R</value>
 </property>
<property>
<key>Source frame count</key>
<value>15100</value>
 </property>
<property>
<key>Source stream size</key>
<value>5055528</value>
 </property>
<property>
<key>Source_StreamSize_Proportion</key>
<value>0.15400</value>
 </property>
<property>
<key>Stream identifier</key>
<value>0</value>
 </property>
<property>
<key>Stream size</key>
<value>5055522</value>
 </property>
<property>
<key>StreamOrder</key>
<value>1</value>
 </property>
<property>
<key>Tagged date</key>
<value>UTC 2014-10-19 15:56:54</value>
 </property>
<property>
<key>Video0 delay</key>
<value>0</value>
 </property>
 </mediaInfo>
 </audioComponent>
<videoComponent>
<file>
<id>VX-48077439</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://1fa3ad40-65e4-11e9-a3bc-bc113b8044e7:_VSENC__3uhd3tAWvFSU0WX0W8TkA1halNoyKnHuf9Q4KlqgRMFjh%2FtK%2FVxjUQ==@10.235.51.145/5ce37552-358f-998b-115b-9569b8f21a01/1d07a65a-65e4-11e9-a3bc-bc113b8044e7/141019_9661710_lowres.mp4</uri>
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
<key>MXFS_CREATIONDAY</key>
<value>16</value>
 </field>
<field>
<key>MXFS_CATEGORY</key>
<value>2</value>
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
<key>MXFS_CREATIONMONTH</key>
<value>5</value>
 </field>
<field>
<key>MXFS_FILENAME</key>
<value>141019_9661710_lowres.mp4</value>
 </field>
 </metadata>
 </file>
<file>
<id>VX-25493774</id>
<path>141019_9661710_lowres.mp4</path>
<uri>file:///srv/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2017-04-18T11:52:35.888+01:00</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-10</storage>
<metadata>
<field>
<key>created</key>
<value>1442718812000</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
 </metadata>
 </file>
<file>
<id>VX-48072947</id>
<path>141019_9661710_lowres.mp4</path>
<uri>omms://c8aa3eed-65e4-11e9-be56-8fb572ba0596:_VSENC__qkSnrEsZToutNO8juCnCZlufKDPDzqno4BG1TunbwY%2FqOOVMKmQPgg==@10.236.51.145/38b7c064-a862-0fe2-44cd-7191ca6201c3/c5b7da33-65e4-11e9-be56-8fb572ba0596/141019_9661710_lowres.mp4</uri>
<state>CLOSED</state>
<size>32827409</size>
<hash>a918e28ac3c9142c88ad8bfacd8c34926e955f1f</hash>
<timestamp>2019-11-14T17:01:27.118Z</timestamp>
<refreshFlag>1</refreshFlag>
<storage>VX-77</storage>
<metadata>
<field>
<key>MXFS_PARENTOID</key>
<value />
 </field>
<field>
<key>MXFS_CREATION_TIME</key>
<value>1558041261817</value>
 </field>
<field>
<key>mtime</key>
<value>1442718812000</value>
 </field>
 </metadata>
 </file>
<id>VX-2313283</id>
<metadata>
<key>creation_time</key>
<value>2014-10-19 15:56:52</value>
 </metadata>
<metadata>
<key>handler_name</key>
<value>Apple Alias Data Handler</value>
 </metadata>
<metadata>
<key>language</key>
<value>eng</value>
 </metadata>
<codec>h264</codec>
<timeBase>
<numerator>1</numerator>
<denominator>2500</denominator>
 </timeBase>
<itemTrack>V1</itemTrack>
<essenceStreamId>0</essenceStreamId>
<bitrate>682492</bitrate>
<numberOfPackets>8053</numberOfPackets>
<extradata>014D400DFF010014274D400DA918303AF2E00D418041ADB0AD7BDF0101000428DE0988</extradata>
<pid>1</pid>
<duration>
<samples>805300</samples>
<timeBase>
<numerator>1</numerator>
<denominator>2500</denominator>
 </timeBase>
 </duration>
<profile>77</profile>
<level>13</level>
<edl>
<timeScale>
<numerator>1</numerator>
<denominator>2500</denominator>
 </timeScale>
<entry start="0" length="805300" mediaRate="65536" />
 </edl>
<startTimestamp>
<samples>0</samples>
<timeBase>
<numerator>1</numerator>
<denominator>2500</denominator>
 </timeBase>
 </startTimestamp>
<resolution>
<width>384</width>
<height>216</height>
 </resolution>
<pixelFormat>yuv420p</pixelFormat>
<maxBFrames>1</maxBFrames>
<pixelAspectRatio>
<horizontal>1</horizontal>
<vertical>1</vertical>
 </pixelAspectRatio>
<fieldOrder>progressive</fieldOrder>
<codecTimeBase>
<numerator>1</numerator>
<denominator>5000</denominator>
 </codecTimeBase>
<averageFrameRate>
<numerator>25</numerator>
<denominator>1</denominator>
 </averageFrameRate>
<realBaseFrameRate>
<numerator>25</numerator>
<denominator>1</denominator>
 </realBaseFrameRate>
<displayWidth>
<numerator>384</numerator>
<denominator>1</denominator>
 </displayWidth>
<displayHeight>
<numerator>216</numerator>
<denominator>1</denominator>
 </displayHeight>
<colr_primaries>6</colr_primaries>
<colr_transfer_function>1</colr_transfer_function>
<colr_matrix>6</colr_matrix>
<max_packet_size>27422</max_packet_size>
<ticks_per_frame>2</ticks_per_frame>
<bitDepth>8</bitDepth>
<bitsPerPixel>12</bitsPerPixel>
<colorPrimaries>SMPTE170M</colorPrimaries>
<mediaInfo>
<property>
<key>Bit depth</key>
<value>8</value>
 </property>
<property>
<key>Bit rate</key>
<value>682492</value>
 </property>
<property>
<key>Display aspect ratio</key>
<value>16:9</value>
 </property>
<property>
<key>Duration</key>
<value>322120</value>
 </property>
<property>
<key>Encoded date</key>
<value>UTC 2014-10-19 15:55:08</value>
 </property>
<property>
<key>Format</key>
<value>AVC</value>
 </property>
<property>
<key>Format profile</key>
<value>Main@L1.3</value>
 </property>
<property>
<key>Format settings</key>
<value>2 Ref Frames</value>
 </property>
<property>
<key>Format settings, CABAC</key>
<value>No</value>
 </property>
<property>
<key>Format settings, ReFrames</key>
<value>2</value>
 </property>
<property>
<key>Format/Info</key>
<value>Advanced Video Codec</value>
 </property>
<property>
<key>StreamOrder</key>
<value>0</value>
 </property>
<property>
<key>Tagged date</key>
<value>UTC 2014-10-19 15:56:54</value>
 </property>
<property>
<key>Transfer characteristics</key>
<value>BT.709</value>
 </property>
<property>
<key>Width</key>
<value>384</value>
 </property>
 </mediaInfo>
 </videoComponent>
<metadata>
<field>
<key>originalFilename</key>
<value>141019_9661710_lowres.mp4</value>
 </field>
</metadata>
 </ShapeDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(shape_list_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSShape.request', return_value=ET.fromstring(shape_doc)) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_shape = test_item.get_shape('lowres')
                test_item.request.assert_called_with('/item/VX-1234/shape')
                self.assertEqual(test_shape.name, 'VX-901604')
                self.assertEqual(test_shape.itemid, 'VX-1234')
                self.assertIn(b'lowres', ET.tostring(test_shape.dataContent))
                self.assertIn(b'141019_9661710_lowres.mp4', ET.tostring(test_shape.dataContent))
                self.assertIn(b'014D400DFF010014274D400DA918303AF2E00D418041ADB0AD7BDF0101000428DE0988', ET.tostring(test_shape.dataContent))
                self.assertIn(b'a918e28ac3c9142c88ad8bfacd8c34926e955f1f', ET.tostring(test_shape.dataContent))
                self.assertIn(b'1558041125848', ET.tostring(test_shape.dataContent))
                self.assertIn(b'32827409', ET.tostring(test_shape.dataContent))
                with self.assertRaises(VSNotFound):
                    test_item.get_shape('original')

    def test_shapes(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        shape_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <uri>VX-901604</uri>
        <uri>VX-901605</uri>
        <uri>VX-901606</uri>
        </URIListDocument>"""
        shape_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901604</id>
<essenceVersion>0</essenceVersion>
<tag>lowres</tag>
<mimeType>video/mp4</mimeType>
 </ShapeDocument>"""
        shape_doc_two = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901605</id>
<essenceVersion>0</essenceVersion>
<tag>original</tag>
<mimeType>video/mp4</mimeType>
 </ShapeDocument>"""
        shape_doc_three = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901606</id>
<essenceVersion>0</essenceVersion>
<tag>highres</tag>
<mimeType>video/mp4</mimeType>
 </ShapeDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(shape_list_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSShape.request', side_effect=[ET.fromstring(shape_doc), ET.fromstring(shape_doc_two), ET.fromstring(shape_doc_three)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_shapes = test_item.shapes()
                test_place = 1
                for shape in test_shapes:
                    if test_place is 1:
                        self.assertIn(b'lowres', ET.tostring(shape.dataContent))
                        self.assertIn(b'VX-901604', ET.tostring(shape.dataContent))
                    if test_place is 2:
                        self.assertIn(b'original', ET.tostring(shape.dataContent))
                        self.assertIn(b'VX-901605', ET.tostring(shape.dataContent))
                    if test_place is 3:
                        self.assertIn(b'highres', ET.tostring(shape.dataContent))
                        self.assertIn(b'VX-901606', ET.tostring(shape.dataContent))
                    test_place = test_place + 1

    def test_transcode(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        job_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
            <jobId>VX-80</jobId>
            <status>FINISHED</status>
            <type>PLACEHOLDER_IMPORT</type>
        </JobDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(job_doc), ET.fromstring(job_doc), ET.fromstring(job_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSJob.request', return_value=ET.fromstring(job_doc)) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_job_id = test_item.transcode("lowres", wait=False)
                self.assertEqual(test_job_id, 'VX-80')
                test_job = test_item.transcode("lowres", wait=False, allow_object=True)
                self.assertEqual(test_job.name, 'VX-80')
                self.assertIn(b'PLACEHOLDER_IMPORT', ET.tostring(test_job.dataContent))
                test_output = test_item.transcode("lowres")
                self.assertEqual(test_output, None)

    def test_export(self):
        from gnmvidispine.vs_job import VSJobFailed
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>originalFilename</name>
                    <value change="VX-15930">test.mp4</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        job_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
            <jobId>VX-80</jobId>
            <status>FINISHED</status>
            <type>PLACEHOLDER_IMPORT</type>
        </JobDocument>"""
        job_doc_two = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <JobDocument xmlns="http://xml.vidispine.com/schema/vidispine">
            <jobId>VX-80</jobId>
            <status>FAILED</status>
            <type>PLACEHOLDER_IMPORT</type>
        </JobDocument>"""

        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(job_doc), ET.fromstring(job_doc_two), ET.fromstring(job_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSJob.request', side_effect=[ET.fromstring(job_doc), ET.fromstring(job_doc_two), ET.fromstring(job_doc)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_export = test_item.export("lowres", '/test/path')
                self.assertEqual(test_export, None)
                with self.assertRaises(VSJobFailed):
                    test_item.export('original', '/test/path')
                test_export = test_item.export("lowres", '/test/path', metadata_projection='inmeta_V5', use_media_filename=False)
                self.assertEqual(test_export, None)

    def test_storage_rule(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        shape_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <uri>VX-901604</uri>
        </URIListDocument>"""
        shape_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901604</id>
<essenceVersion>0</essenceVersion>
<tag>lowres</tag>
<mimeType>video/mp4</mimeType>
 </ShapeDocument>"""
        rule_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
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
</StorageRulesDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(shape_list_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSShape.request', side_effect=[ET.fromstring(shape_doc), ET.fromstring(rule_doc)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_rule = test_item.storageRule(shapeTag='lowres')
                self.assertEqual(test_rule.content['lowres']['priority'], 'capacity')
                self.assertEqual(test_rule.content['lowres']['precedence'], 'HIGHEST')

    def test_apply_storage_rule(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        shape_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <uri>VX-901604</uri>
        </URIListDocument>"""
        shape_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ShapeDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<id>VX-901604</id>
<essenceVersion>0</essenceVersion>
<tag>lowres</tag>
<mimeType>video/mp4</mimeType>
 </ShapeDocument>"""
        rule_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
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
</StorageRulesDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(shape_list_doc), 'test', 'test']) as mock_request:
            with patch('gnmvidispine.vs_item.VSShape.request', side_effect=[ET.fromstring(shape_doc), ET.fromstring(rule_doc)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_rule = test_item.storageRule(shapeTag='lowres')
                self.assertEqual(test_rule.content['lowres']['priority'], 'capacity')
                self.assertEqual(test_rule.content['lowres']['precedence'], 'HIGHEST')
                with self.assertRaises(TypeError):
                    test_item.applyStorageRule('test')
                test_item.applyStorageRule(test_rule)
                arg1, test_dict = test_item.request.call_args
                self.assertEqual(arg1, ('/item/VX-1234/storage-rule/original',))
                self.assertEqual(test_dict['method'], 'POST')
                self.assertIn(b'<ns0:precedence>HIGHEST</ns0:precedence>', test_dict['body'])
                self.assertIn(b'<ns0:priority level="1">capacity</ns0:priority>', test_dict['body'])
                test_item.applyStorageRule(test_rule, shapeTag='lowres')
                arg1, test_dict = test_item.request.call_args
                self.assertEqual(arg1, ('/item/VX-1234/storage-rule/lowres',))
                self.assertEqual(test_dict['method'], 'POST')
                self.assertIn(b'<ns0:precedence>HIGHEST</ns0:precedence>', test_dict['body'])
                self.assertIn(b'<ns0:priority level="1">capacity</ns0:priority>', test_dict['body'])

    def test_apply_storage_rule_xml(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        shape_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
        <URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
        <uri>VX-901604</uri>
        </URIListDocument>"""
        rule_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
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
</StorageRulesDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), ET.fromstring(shape_list_doc), 'test', 'test']) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            test_item.applyStorageRuleXML(rule_doc)
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234/storage-rule/original',))
            self.assertEqual(test_dict['method'], 'PUT')
            self.assertIn('<precedence>HIGHEST</precedence>', test_dict['body'])
            self.assertIn('<priority level="1">capacity</priority>', test_dict['body'])
            test_item.applyStorageRuleXML(rule_doc, shapeTag='lowres')
            arg1, test_dict = test_item.request.call_args
            self.assertEqual(arg1, ('/item/VX-1234/storage-rule/lowres',))
            self.assertEqual(test_dict['method'], 'PUT')
            self.assertIn('<precedence>HIGHEST</precedence>', test_dict['body'])
            self.assertIn('<priority level="1">capacity</priority>', test_dict['body'])

    def test_get_acl(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        access_control_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<AccessControlListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<access id="VX-1205576">
<loc>http://vidispine:8080/API/item/VX-1234/access/VX-1205576</loc>
<recursive>true</recursive>
<permission>WRITE</permission>
<group>_transcoder</group>
 </access>
<access id="VX-1205575">
<loc>http://vidispine:8080/API/item/VX-1234/access/VX-1205575</loc>
<recursive>true</recursive>
<permission>OWNER</permission>
<user>admin</user>
 </access>
 </AccessControlListDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc)]) as mock_request:
            with patch('gnmvidispine.vs_acl.VSAcl.request', side_effect=[ET.fromstring(access_control_list_doc)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_list_object = test_item.get_acl()
                self.assertEqual(test_list_object._entries[0].name, 'VX-1205576')
                self.assertIn(b'<ns0:permission>WRITE</ns0:permission>', ET.tostring(test_list_object._entries[0].dataContent))
                self.assertIn(b'<ns0:group>_transcoder</ns0:group>', ET.tostring(test_list_object._entries[0].dataContent))
                self.assertEqual(test_list_object._entries[1].name, 'VX-1205575')
                self.assertIn(b'<ns0:permission>OWNER</ns0:permission>', ET.tostring(test_list_object._entries[1].dataContent))
                self.assertIn(b'<ns0:loc>http://vidispine:8080/API/item/VX-1234/access/VX-1205575</ns0:loc>', ET.tostring(test_list_object._entries[1].dataContent))

    def test_add_placeholder_shape(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc), 'test', 'test']) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            test_item.add_placeholder_shape()
            test_item.request.assert_called_with('/item/VX-1234/shape/placeholder', accept='text/plain', body='<SimpleMetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"></SimpleMetadataDocument>', method='POST', query={'tag': 'original', 'container': 1})
            test_item.add_placeholder_shape(shape_tag='lowres')
            test_item.request.assert_called_with('/item/VX-1234/shape/placeholder', accept='text/plain', body='<SimpleMetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"></SimpleMetadataDocument>', method='POST', query={'tag': 'lowres', 'container': 1})

    def test_thumbnails(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        uri_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<uri>http://vidispine:8080/API/thumbnail/VX-5/VX-452999;version=0</uri>
</URIListDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc)]) as mock_request:
            with patch('gnmvidispine.vs_thumbnail.VSThumbnailCollection.request', side_effect=[ET.fromstring(uri_list_doc)]) as mock_request_two:
                from gnmvidispine.vs_item import VSItem
                test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
                test_item.populate()
                self.assertEqual(test_item.type, 'item')
                self.assertEqual(test_item.name, 'VX-1234')
                test_list_object = test_item.thumbnails()
                self.assertEqual(test_list_object.parent_item.name, 'VX-1234')
                self.assertEqual(test_list_object._resource_list, ['http://vidispine:8080/API/thumbnail/VX-5/VX-452999;version=0'])

    def test_parent_collection_number(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
                <field>
                    <name>__collection_size</name>
                    <value>854</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            self.assertEqual(test_item.parent_collection_number, 854)

    def test_parent_collections(self):
        uri_list_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<URIListDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<uri>VX-8546</uri>
<uri>VX-8547</uri>
<uri>VX-8548</uri>
<uri>VX-8549</uri>
</URIListDocument>"""
        collection_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<CollectionDocument xmlns="http://xml.vidispine.com/schema/vidispine">
<loc>http://vidispine:8080/API/collection/VX-8546/</loc>
<id>VX-8546</id>
<name>141020_video_087</name>
<content>
<id>VX-420411</id>
<uri>http://vidispine:8080/API/item/VX-420411</uri>
<type>item</type>
<metadata />
</content>
<content>
<id>VX-452999</id>
<uri>http://vidispine:8080/API/item/VX-452999</uri>
<type>item</type>
<metadata />
</content>
<content>
<id>VX-552502</id>
<uri>http://vidispine:8080/API/item/VX-552502</uri>
<type>item</type>
<metadata />
</content>
</CollectionDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(uri_list_doc), ET.fromstring(uri_list_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc), ET.fromstring(collection_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            output_collections = test_item.parent_collections()
            test_place = 1
            for collection in output_collections:
                if test_place is 1:
                    self.assertEqual('VX-8546', collection.name)
                if test_place is 2:
                    self.assertEqual('VX-8547', collection.name)
                if test_place is 3:
                    self.assertEqual('VX-8548', collection.name)
                if test_place is 4:
                    self.assertEqual('VX-8549', collection.name)
                test_place = test_place + 1
            output_collections = test_item.parent_collections(shouldPopulate=True)
            test_place = 1
            for collection in output_collections:
                if test_place is 1:
                    self.assertEqual('collection', collection.type)
                    self.assertIn(b'<ns0:id>VX-452999</ns0:id>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:uri>http://vidispine:8080/API/item/VX-552502</ns0:uri>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:name>141020_video_087</ns0:name>', ET.tostring(collection.dataContent))
                    self.assertEqual(3, collection.itemCount)
                if test_place is 2:
                    self.assertEqual('collection', collection.type)
                    self.assertIn(b'<ns0:id>VX-452999</ns0:id>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:uri>http://vidispine:8080/API/item/VX-552502</ns0:uri>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:name>141020_video_087</ns0:name>', ET.tostring(collection.dataContent))
                    self.assertEqual(3, collection.itemCount)
                if test_place is 3:
                    self.assertEqual('collection', collection.type)
                    self.assertIn(b'<ns0:id>VX-452999</ns0:id>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:uri>http://vidispine:8080/API/item/VX-552502</ns0:uri>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:name>141020_video_087</ns0:name>', ET.tostring(collection.dataContent))
                    self.assertEqual(3, collection.itemCount)
                if test_place is 4:
                    self.assertEqual('collection', collection.type)
                    self.assertIn(b'<ns0:id>VX-452999</ns0:id>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:uri>http://vidispine:8080/API/item/VX-552502</ns0:uri>', ET.tostring(collection.dataContent))
                    self.assertIn(b'<ns0:name>141020_video_087</ns0:name>', ET.tostring(collection.dataContent))
                    self.assertEqual(3, collection.itemCount)
                test_place = test_place + 1

    def test_to_cache(self):
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
                <field>
                    <name>__collection_size</name>
                    <value>854</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc)]) as mock_request:
            from gnmvidispine.vs_item import VSItem
            test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
            test_item.populate()
            self.assertEqual(test_item.type, 'item')
            self.assertEqual(test_item.name, 'VX-1234')
            test_dict = test_item.to_cache()
            self.assertEqual(test_dict['_vidispine_id'], 'VX-1234')
            self.assertIn(b'<ns0:value change="VX-15930">1</ns0:value>', ET.tostring(test_dict['data']))
            self.assertIn(b'<ns0:name>__collection_size</ns0:name>', ET.tostring(test_dict['data']))
            self.assertIn(b'<ns0:value>854</ns0:value>', ET.tostring(test_dict['data']))
            self.assertEqual(test_dict['content'], {'test': '1', '__collection_size': '854'})

    def test_from_cache(self):
        from gnmvidispine.vs_item import VSItem
        input_dict = {'_vidispine_id': 'VX-1234', 'content': {'test': '1', '__collection_size': '854'}, 'data': '<ns0:ItemDocument xmlns:ns0="http://xml.vidispine.com/schema/vidispine" id="VX-1234">\n        <ns0:metadata>\n            <ns0:timespan end="+INF" start="-INF">\n                <ns0:field>\n                    <ns0:name>test</ns0:name>\n                    <ns0:value change="VX-15930">1</ns0:value>\n                </ns0:field>\n                <ns0:field>\n                    <ns0:name>__collection_size</ns0:name>\n                    <ns0:value>854</ns0:value>\n                </ns0:field>\n            </ns0:timespan>\n            </ns0:metadata>\n        </ns0:ItemDocument>'}
        test_item = VSItem(host=self.fake_host, port=self.fake_port, user=self.fake_user, passwd=self.fake_passwd)
        test_item.from_cache(input_dict)
        self.assertEqual(test_item.type, 'item')
        self.assertEqual(test_item.name, 'VX-1234')
        self.assertEqual(test_item.contentDict, {'test': '1', '__collection_size': '854'})
        self.assertEqual(test_item.dataContent, '<ns0:ItemDocument xmlns:ns0="http://xml.vidispine.com/schema/vidispine" id="VX-1234">\n        <ns0:metadata>\n            <ns0:timespan end="+INF" start="-INF">\n                <ns0:field>\n                    <ns0:name>test</ns0:name>\n                    <ns0:value change="VX-15930">1</ns0:value>\n                </ns0:field>\n                <ns0:field>\n                    <ns0:name>__collection_size</ns0:name>\n                    <ns0:value>854</ns0:value>\n                </ns0:field>\n            </ns0:timespan>\n            </ns0:metadata>\n        </ns0:ItemDocument>')


class TestVsMetadataBuilder(unittest2.TestCase):
    maxDiff = None

    def test_builder_refs(self):
        """
        Builder should recognise VSMetadataReference objects
        :return:
        """
        from gnmvidispine.vs_metadata import VSMetadataReference
        from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
        mock_item = MagicMock(target=VSItem)

        ref = VSMetadataReference()
        ref.uuid = "ED047409-706B-43B7-9F35-0DDBC6F2689E"

        b = VSMetadataBuilder(mock_item)
        b.addMeta({'test_field': ref})

        self.assertEqual(b.as_xml("utf8"),b"""<?xml version='1.0' encoding='utf8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><reference>ED047409-706B-43B7-9F35-0DDBC6F2689E</reference></field></timespan></MetadataDocument>""")

    def test_serialize_float(self):
        """
        Builder should be able to serialize floats
        :return:
        """
        from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
        mock_item = MagicMock(target=VSItem)

        b = VSMetadataBuilder(mock_item)
        b.addMeta({'test_field': 1.234})
        self.assertEqual(b.as_xml("utf8"),b"""<?xml version='1.0' encoding='utf8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>1.234</value></field></timespan></MetadataDocument>""")

    def test_serialize_datetime(self):
        """
        Builder should be able to serialize datetimes
        :return:
        """
        from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
        from datetime import datetime
        import pytz

        mock_item = MagicMock(target=VSItem)

        b = VSMetadataBuilder(mock_item)
        b.addMeta({'test_field': datetime(2015,0o7,12,23,0o4,31,0,pytz.timezone("Europe/London"))})
        self.assertEqual(b.as_xml("utf8"),b"""<?xml version='1.0' encoding='utf8'?>
<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>2015-07-12T23:04:31-00:01</value></field></timespan></MetadataDocument>""")

    def test_serialize_unicode_extended(self):
        """
        builder should be able to handle extended unicode chars
        :return:
        """
        from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
        from datetime import datetime
        import pytz

        mock_item = MagicMock(target=VSItem)


        b = VSMetadataBuilder(mock_item)
        b.addMeta({'test_field': "£1 for a house: made in Stoke-on-Trent"})
        try:
            xml_to_test_with = """<?xml version='1.0' encoding='utf8'?>\n<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>£1 for a house: made in Stoke-on-Trent</value></field></timespan></MetadataDocument>""".encode(encoding='UTF-8')
        except:
            xml_to_test_with = """<?xml version='1.0' encoding='utf8'?>\n<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>£1 for a house: made in Stoke-on-Trent</value></field></timespan></MetadataDocument>"""
        self.assertEqual(b.as_xml("utf8"), xml_to_test_with)

        b = VSMetadataBuilder(mock_item)
        b.addMeta({'test_field': "Fire at Trump Tower – video "})
        try:
            xml_to_test_with = """<?xml version='1.0' encoding='utf8'?>\n<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>Fire at Trump Tower – video </value></field></timespan></MetadataDocument>""".encode(encoding='UTF-8')
        except:
            xml_to_test_with = """<?xml version='1.0' encoding='utf8'?>\n<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF"><field><name>test_field</name><value>Fire at Trump Tower – video </value></field></timespan></MetadataDocument>"""
        self.assertEqual(b.as_xml("utf8"), xml_to_test_with)

    def test_add_group(self):
        from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
        mock_item = MagicMock(target=VSItem)
        test_metadata_builder = VSMetadataBuilder(mock_item)
        with self.assertRaises(TypeError):
            test_metadata_builder.addGroup('test', 'test')
        test_metadata_builder.addGroup('test', {'test': '1', '__collection_size': '854'})
        self.assertIn(b'<group><name>test</name>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>test</name><value>1</value></field>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>__collection_size</name><value>854</value></field>', ET.tostring(test_metadata_builder.rootNode))
        test_metadata_builder = VSMetadataBuilder(mock_item)
        test_metadata_builder.addGroup('test', {'test': '1', '__collection_size': '854'}, mode='add')
        self.assertIn(b'<group mode="add"><name>test</name>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>test</name><value>1</value></field>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>__collection_size</name><value>854</value></field>', ET.tostring(test_metadata_builder.rootNode))
        test_metadata_builder = VSMetadataBuilder(mock_item)
        test_metadata_builder.addGroup('test', {'test': {'test': '1', '__collection_size': '854'}, '__collection_size': '854'}, subgroupmode='add')
        self.assertIn(b'<group><name>test</name><group mode="add"><name>test</name>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>test</name><value>1</value></field>', ET.tostring(test_metadata_builder.rootNode))
        self.assertIn(b'<field><name>__collection_size</name><value>854</value></field>', ET.tostring(test_metadata_builder.rootNode))

    def test_commit(self):
        from gnmvidispine.vidispine_api import VSBadRequest
        test_item_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <ItemDocument id="VX-1234" xmlns="http://xml.vidispine.com/schema/vidispine">
        <metadata>
            <timespan start="-INF" end="+INF">
                <field>
                    <name>test</name>
                    <value change="VX-15930">1</value>
                </field>
            </timespan>
            </metadata>
        </ItemDocument>"""
        with patch('gnmvidispine.vs_item.VSItem.request', side_effect=[ET.fromstring(test_item_doc)]) as mock_request:
            with patch('gnmvidispine.vs_item.VSMetadataBuilder.request', side_effect=[VSBadRequest, 'test']) as mock_request_two:
                from gnmvidispine.vs_item import VSMetadataBuilder, VSItem
                test_item = VSItem(host='test', port=8080, user='test', passwd='test')
                test_item.populate()
                test_metadata_builder = VSMetadataBuilder(test_item)
                with self.assertRaises(VSBadRequest):
                    test_metadata_builder.commit()
                test_metadata_builder.commit()
                test_metadata_builder.request.assert_called_with('/item/VX-1234/metadata', body='<?xml version=\'1.0\' encoding=\'utf8\'?>\n<MetadataDocument xmlns="http://xml.vidispine.com/schema/vidispine"><timespan end="+INF" start="-INF" /></MetadataDocument>', method='PUT')
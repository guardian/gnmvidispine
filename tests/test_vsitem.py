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
                    self.assertIn(b'e2350aed-9835-4c6e-9a5c-989a86f42de', ET.tostring(changeset.mdContent))
                test_place = test_place + 1


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

# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
from urllib2 import quote
import xml.etree.cElementTree as ET
import re
from datetime import datetime
from dateutil.tz import tzoffset


class TestVSMetadataValue(unittest2.TestCase):
    maxDiff=None

    fake_host = 'localhost'
    fake_port = 8080
    fake_user = 'username'
    fake_passwd = 'password'

    def test_loads(self):
        """
        VSMetadataValue should load in data from a valid value entry
        :return:
        """
        from gnmvidispine.vs_metadata import VSMetadataValue
        testdata = ET.fromstring("""<value uuid="19e2cfdd-dd4c-4dc6-b910-6ce55b0c9c93" user="richard_sprenger" timestamp="2017-06-02T11:26:41.478+01:00" change="KP-19008429">11</value>""")

        value = VSMetadataValue(testdata)

        self.assertEqual(value.value,"11")
        self.assertEqual(value.uuid,"19e2cfdd-dd4c-4dc6-b910-6ce55b0c9c93")
        self.assertEqual(value.user,"richard_sprenger")
        self.assertEqual(value.timestamp,datetime(2017, 6, 2, 11, 26, 41, 478000, tzinfo=tzoffset(None, 3600)))


class TestVSMetadataAttribute(unittest2.TestCase):
    maxDiff=None

    fake_host = 'localhost'
    fake_port = 8080
    fake_user = 'username'
    fake_passwd = 'password'

    def test_loads(self):
        """
        VSMetadataAttribute should load in data from a valid field entry
        :return:
        """
        from gnmvidispine.vs_metadata import VSMetadataAttribute
        testdata = ET.fromstring("""<ns0:field xmlns:ns0="http://xml.vidispine.com/schema/vidispine" uuid="9860f876-b9e8-4799-8e68-cb292818a9cd" user="richard_sprenger" timestamp="2017-06-02T11:26:41.478+01:00" change="KP-19008429">
            <ns0:name>gnm_commission_owner</ns0:name>
            <ns0:value uuid="19e2cfdd-dd4c-4dc6-b910-6ce55b0c9c93" user="richard_sprenger" timestamp="2017-06-02T11:26:41.478+01:00" change="KP-19008429">11</ns0:value>
            <ns0:value uuid="EF41268C-00B4-431D-A36E-6D3B4D59A06A" user="bob_smith" timestamp="2017-06-02T11:26:44.478+01:00" change="KP-19008430">14</ns0:value>
        </ns0:field>""")
        field = VSMetadataAttribute(testdata)

        self.assertEqual(field.uuid,"9860f876-b9e8-4799-8e68-cb292818a9cd")
        self.assertEqual(field.user,"richard_sprenger")
        self.assertEqual(field.change,"KP-19008429")
        self.assertEqual(field.name,"gnm_commission_owner")
        #test using repr() that it actually works. assume that VSMetadataValue does its thang based on the unit test for it.
        self.assertEqual(str(field.values),"[VSMetadataValue(\"11\"), VSMetadataValue(\"14\")]")

    def test_references(self):
        """
        VSMetadataAttribute should load in external references from a valid field entry
        :return:
        """
        from gnmvidispine.vs_metadata import VSMetadataAttribute
        testdata = ET.fromstring("""<field xmlns="http://xml.vidispine.com/schema/vidispine" uuid="982ae13e-ee13-4b75-9ba6-8defa584efb7" user="adam_sich" timestamp="2017-11-14T11:33:30.631Z" change="KP-22501063">
            <name>gnm_commission_title</name>
            <referenced id="KP-23891" uuid="a8765513-8872-48f2-8549-ac1468405e8a" type="collection"/>
            <value uuid="97fe0bc2-291a-4fa8-a327-0a79f57b563e" user="adam_sich" timestamp="2017-02-16T16:36:21.066Z" change="KP-16051833">Owen Jones 2017</value>
        </field>""")

        field = VSMetadataAttribute(testdata)
        self.assertEqual(field.uuid,"982ae13e-ee13-4b75-9ba6-8defa584efb7")
        self.assertEqual(field.user,"adam_sich")
        self.assertEqual(field.change,"KP-22501063")
        self.assertEqual(field.name,"gnm_commission_title")
        self.assertEqual(str(field.references),"[VSMetadataReference a8765513-8872-48f2-8549-ac1468405e8a to collection KP-23891]")
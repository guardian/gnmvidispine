# -*- coding: UTF-8 -*-
from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch, call
import xml.etree.cElementTree as ET


class TestExternalIdNamespace(unittest2.TestCase):
    sample_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ExternalIdentifierNamespaceDocument xmlns="http://xml.vidispine.com/schema/vidispine">
    <name>uuid</name>
    <pattern>[A-Fa-f0-9]{8}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{12}</pattern>
    <priority>0</priority>
</ExternalIdentifierNamespaceDocument>"""

    def test_does_populate(self):
        """
        ExternalIdNamespace should populate from an XML document provided by the server
        :return:
        """
        with patch("gnmvidispine.vs_external_id.ExternalIdNamespace.request", return_value=ET.fromstring(self.sample_doc)) as mock_request:
            from gnmvidispine.vs_external_id import ExternalIdNamespace
            n = ExternalIdNamespace(host="localhost",port=1234,user="me",passwd="secret")
            n.populate("uuid")
            self.assertEqual(n.regex, "[A-Fa-f0-9]{8}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{4}\-[A-Fa-f0-9]{12}")
            self.assertEqual(n.priority, 0)
            self.assertEqual(n.name, "uuid")

    def test_create(self):
        """
        ExternalIdNamespace.create should build an XML document and PUT it to the server
        :return:
        """
        expected_doc = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<ExternalIdentifierNamespaceListDocument xmlns="http://xml.vidispine.com/schema/vidispine"><name>test</name><pattern>aaaa</pattern><priority>4</priority></ExternalIdentifierNamespaceListDocument>'
        with patch("gnmvidispine.vs_external_id.ExternalIdNamespace.request", return_value=ET.fromstring(expected_doc)) as mock_request:
            from gnmvidispine.vs_external_id import ExternalIdNamespace
            n = ExternalIdNamespace(host="localhost", port=1234, user="me", passwd="secret")
            n.create("test","aaaa",priority=4)

            mock_request.assert_called_once_with("/external-id/test", method="PUT", body=expected_doc)
            self.assertEqual(n.regex, "aaaa")
            self.assertEqual(n.priority, 4)
            self.assertEqual(n.name, "test")

    def test_setters(self):
        """
        attribute setters should update internal DOM representation
        :return:
        """
        with patch("gnmvidispine.vs_external_id.ExternalIdNamespace.request", return_value=ET.fromstring(self.sample_doc)) as mock_request:
            from gnmvidispine.vs_external_id import ExternalIdNamespace
            n = ExternalIdNamespace(host="localhost",port=1234,user="me",passwd="secret")
            n.populate("uuid")
            n.regex = "updated regex"
            self.assertEqual(n.regex, "updated regex")
            n.priority = 12
            self.assertEqual(n.priority, 12)
            n.name = "updated name"
            self.assertEqual(n.name, "updated name")

    def test_save(self):
        expected_doc = '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<ns0:ExternalIdentifierNamespaceDocument xmlns:ns0="http://xml.vidispine.com/schema/vidispine">\n    <ns0:name>uuid</ns0:name>\n    <ns0:pattern>aaaa</ns0:pattern>\n    <ns0:priority>4</ns0:priority>\n</ns0:ExternalIdentifierNamespaceDocument>'
        with patch("gnmvidispine.vs_external_id.ExternalIdNamespace.request", return_value=ET.fromstring(expected_doc)) as mock_request:
            from gnmvidispine.vs_external_id import ExternalIdNamespace
            n = ExternalIdNamespace(host="localhost", port=1234, user="me", passwd="secret")
            n._xmldoc = ET.fromstring(self.sample_doc)

            n.regex = "aaaa"
            n.priority = 4
            n.name = "test"

            n.save()
            mock_request.assert_called_once_with("/external-id/test", method="PUT", body=expected_doc)
            self.assertEqual(n.regex, "aaaa")
            self.assertEqual(n.priority, 4)
            self.assertEqual(n.name, "test")

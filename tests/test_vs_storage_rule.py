from __future__ import absolute_import
import unittest2
from mock import MagicMock, patch
import httplib
import base64
import logging
import tempfile
from os import urandom


class TestVSStorageRule(unittest2.TestCase):
    fake_host='localhost'
    fake_port=8080
    fake_user='username'
    fake_passwd='password'
    
    test_storagerule_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><StorageRulesDocument xmlns="http://xml.vidispine.com/schema/vidispine"><tag id="original"><storageCount>3</storageCount><priority level="1">bandwidth</priority><storage>KP-3</storage><storage>KP-2</storage><storage>KP-6</storage><not><group>Media Portal</group><group>Project Files</group><group>Online</group><group>Newswires</group><group>Data Migration</group><group>Proxies</group></not><appliesTo><id>KP*37474</id><type>LIBRARY</type></appliesTo><precedence>MEDIUM</precedence></tag></StorageRulesDocument>"""
    
    def test_storage_rule_colection(self):
        """
        test the storage rule collection iterator, fix for "can't set attribute" bug
        :return:
        """
        from gnmvidispine.vs_storage_rule import VSStorageRuleCollection
        from xml.etree.cElementTree import fromstring
        collection = VSStorageRuleCollection(host=self.fake_host,port=self.fake_port,user=self.fake_user,passwd=self.fake_passwd)
        
        collection.populate_from_xml(fromstring(self.test_storagerule_doc))
        
        rules = map(lambda x: x, collection.rules())
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].storage_count, 3)
        self.assertEqual(rules[0].precedence, "MEDIUM")
        self.assertEqual(rules[0].storages(), ["KP-3","KP-2","KP-6"])
        self.assertEqual(rules[0].groups(inverted=True), [
            "Media Portal", "Project Files", "Online", "Newswires", "Data Migration", "Proxies"
        ])
        self.assertEqual(rules[0].applies_to, ("LIBRARY", "KP*37474"))
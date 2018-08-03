from vidispine_api import VSApi
import xml.etree.cElementTree as ET


class ExternalIdNamespace(VSApi):
    def __init__(self, *args, **kwargs):
        super(ExternalIdNamespace, self).__init__(*args, **kwargs)
        self._xmldoc = None

    def populate(self, name):
        """
        Loads in information about the given namespace name or raises VSNotFound if not found
        :param name:
        :return:
        """
        self.name = name

        path = "/external-id/{0}".format(name)
        self._xmldoc = self.request(path, method="GET")
        return self

    def create(self, name, regex, priority=0):
        """
        Creates a new external ID namespace with the given name and regex, and populates the properties with the result
        :param name: name for the external ID namespace
        :param regex: regex against which any given names must match
        :param priority: priority with which the regex will be applied
        :return: self, or raises VSException
        """
        root = ET.Element("ExternalIdentifierNamespaceListDocument", {'xmlns': self.xmlns.lstrip('{').rstrip('}')})
        name_el = ET.SubElement(root, "name")
        name_el.text = name
        regex_el = ET.SubElement(root, "pattern")
        regex_el.text = regex
        prio_el = ET.SubElement(root, "priority")
        prio_el.text = str(priority)

        path = "/external-id/{0}".format(name)
        self.name = name
        self._xmldoc = self.request(path, method="PUT", body=ET.tostring(root, "UTF-8"))
        return self

    def save(self):
        """
        Updates the current state of the server to our state
        :return: self, or raises VSException
        """
        path = "/external-id/{0}".format(self.name)
        self.request(path,method="PUT",body=ET.tostring(self._xmldoc,encoding="UTF-8"))
        return self

    def safe_get(self, xpath, default=None):
        if self._xmldoc is None:
            raise ValueError("you must populate an ExternalIdNamespace before retrieving data")
        node = self._xmldoc.find(xpath)
        if node is not None:
            return node.text
        else:
            return default

    @property
    def regex(self):
        return self.safe_get("{0}pattern".format(self.xmlns))

    @regex.setter
    def regex(self, new_regex):
        node = self._xmldoc.find("{0}pattern".format(self.xmlns))
        node.text = new_regex

    @property
    def pattern(self):
        return self.regex

    @pattern.setter
    def pattern(self, new_regex):
        self.regex = new_regex

    @property
    def priority(self):
        return int(self.safe_get("{0}priority".format(self.xmlns), default=0))

    @priority.setter
    def priority(self, new_prio):
        if not isinstance(new_prio, int):
            raise TypeError("New priority must be an integer")
        node = self._xmldoc.find("{0}priority".format(self.xmlns))
        node.text = str(new_prio)


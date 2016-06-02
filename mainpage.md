!\mainpage
This is the GNM Python Vidispine interface
==========================================

This set of classes form a Python module that can be used to interact with the Vidispine media asset management system
in a fairly Pythonic, object-oriented way.

First Steps
-----------

The first step when using the module is to import the relevant objects to your source code, for example:
```python
from vidispine.vs_item import VSItem
```

Now, you need to initialise an object with the login credentials for your vidispine server. _Remember_, it's very bad
practise to include plaintext authentication credentials in your source code! Much better to do something like this:
```python
from optparse import OptionParser
parser = OptionParser()
parser.add_option("--host", dest="vshost", help="server to access Vidispine on", default="localhost")
parser.add_option("-u", "--vsuser", dest="vsuser", help="user to access Vidispine as", default="admin")
parser.add_option("-w","--vspasswd", dest="vspasswd", help="password for Vidispine user")

#(having already imported VSItem above)
s = VSItem(options.vshost,user=options.vsuser,passwd=options.vspasswd)
```

This registers your credentials with the object, but we haven't actually talked to Vidispine yet.  Next you need to set
the object up - usually by calling ```populate()```

```python
#this will contact Vidispine to get data about item VX-1234
s.populate('VX-1234')
```

You can now get hold of metadata for the item:

```python
print "Item title is {0}".format(s.get('title'))
```

Or set metadata:

```python
s.set({'title': 'New Title'})
```

You can investigate the shapes on the item:

```python
for shape in s.shapes():
  print u"Got shape {0} with id {1} on item {2}".format(unicode(shape),shape.name,s.name)
```

For more things you can do with the returned shape object, see the VSShape class documentation

You can investigate or modify the ACL:

```python
acl = s.get_acl()
for entry in acl.entries():
  print "Got ACL entry {0} on {1}".format(str(entry),s.name)
```

For more about ACLs, see the VSAcl and VSAccess class documentation (a VSAcl contains a bunch of VSAccess entries)

And so on.  There's lots more in the VSItem class documentation.

Exceptions
----------

If this command fails for some reason, a VSExeception will be raised.  The VSExceptions you're most likely to see are
VSNotFound and VSBadRequest (what these mean should be fairly obvious).

The VSException code tries to give you as much information as possible if you simply convert it to a string:
```python
try:
  s.populate('invalid_id')
except VSException as e:
  print u"{0}".format(unicode(e))
  print traceback.format_exc()
```

The VSException base class has several properties that will be of interest when debugging programs, including request_url,
request_body and request_method.  Consult the documentation in the vidispine_api class of the vidispine module for more information

Other exceptions include HttpError (a generic HTTP error that is not a Vidispine exception), InvalidData (the interface
has determined that the data you're trying to send is incorrect, before trying to pass it to Vidispine) and operation-specific
ones such as VSTranscodeError.

Searching
---------

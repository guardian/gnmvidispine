__author__ = 'Andy Gallagher <andy.gallagher@theguardian.com>'

from .vidispine_api import VSApi,VSException
import re
import datetime
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class VSJobFailed(VSException):
    def __init__(self,failedJob,**kwargs):
        super(VSJobFailed, self).__init__(kwargs)
        self.failedJob=failedJob

    def message(self):
        return "Job {id} of type {type} failed".format(id=self.failedJob.name,
                                                       type=self.failedJob.contentDict['type'])

    def __str__(self):
        return self.message()

    def failedJob(self):
        return self.failedJob

from pprint import pprint


def VSFindJobs(status=None,jobtype=None,connection=None,sort=None,metadata=False,onlyuser=False):
    """
    Generator that searches Vidispine for jobs matching the given spec and returns them as initialised VSJob instances.
     If no specification is given, then will return all jobs.
    Can raise AssertionError if parameters are not correct, or VSException subclasses if there is an error returned
    by the server

    :param status: Only search for jobs with this status - STARTED, ABORTED, RUNNING, FINISHED, etc. Consult Vidispine
    documentation for the full list of supported values. Ignored if set to None or not present
    :param jobtype: Only search for this type of job - THUMBNAIL, IMPORT, ESSENCE_VERSION, etc.  Consult Vidispine
     documentation for the full list of supported values.  Ignored if set to None or not present
    :param connection: Initialised VSApi object (or any other Vidispine base object) that contains connection details
    to communicate with Vidispine
    :param sort: Sort by this fieldname.  Ignored if set to None or not present
    :param metadata: Find jobs with metadata matching this specification, provided as a dict.  Consult Vidispine
    documentation for more information on this function.  Ignored if set to None or not present
    :param onlyuser: Only return jobs for the logged in user identified in connection. True/false parameter.
    :return: Generator of VSJob objects.
    """
    if not isinstance(connection,VSApi):
        raise AssertionError("Connection parameter must be a Vidispine API class")

    urlstring = "/job"
    if status is not None:
        urlstring += ";state={0}".format(status)
    if jobtype is not None:
        urlstring += ";type={0}".format(jobtype)
    if sort is not None:
        urlstring += ";sort={0}".format(sort)
    if not onlyuser:
        urlstring += ";user=false"  #by default, user=true => only return jobs by current user.

    #if metadata:
    #    urlstring += "?metadata=true"

    logger.debug("URL is {0}".format(urlstring))
    n = 0
    hits = 100
    while n<hits:
        request = urlstring + ";first={0}".format(n)
        response = connection.request(request, method="GET")
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        hits = int(response.find('{0}hits'.format(ns)).text)
        logger.debug("Got {0} hits".format(hits))

        for jobnode in response.findall('{0}job'.format(ns)):
            #pprint(jobnode.__dict__)
            idnode = jobnode.find('{0}jobId'.format(ns))
            if idnode is not None:
                #pprint(idnode.__dict__)
                #print "VSFindJobs: got job ID %s" % idnode.text
                logger.debug("got job ID {0}".format(idnode.text))
                jobinfo = VSJob(host=connection.host,port=connection.port,user=connection.user,passwd=connection.passwd)
                jobinfo.populate(idnode.text,metadata=metadata)
                yield jobinfo
            else:
                logger.error("Did not get a <jobId> node")
            n += 1


class VSJob(VSApi):
    def __init__(self, *args,**kwargs):
        super(VSJob, self).__init__(*args,**kwargs)
        self.dataContent = None
        self.name = "INVALIDNAME"
        self.contentDict = {}

    def fromResponse(self,responsedoc):
        self.dataContent=responsedoc
        ns = "{http://xml.vidispine.com/schema/vidispine}"

        self.name=self.dataContent.find('{0}jobId'.format(ns)).text


        self._populateInternal()

    def update(self,noraise=True):
        self.dataContent = self.request("/job/%s" % self.name)
        self._populateInternal()

        if not noraise:
            if self.didFail():
                raise VSJobFailed(self)

    def didFail(self):
        if 'status' in self.contentDict:
            if self.contentDict['status'].startswith("FAILED"):
                return True
            if self.contentDict['status'].startswith("ABORTED"):
                return True
        return False

    def didAbort(self): #i.e., was cancelled by user
        if 'status' in self.contentDict:
            if self.contentDict['status'].startswith("ABORTED"):
                return True
        return False

    def populate(self,id,metadata=False):
        self.name = id
        if metadata:
            self.dataContent = self.request("/job/%s?metadata=true" % id)

        else:
            self.dataContent = self.request("/job/%s" % id)

        self._populateInternal()

    def _populateInternal(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        #ET.dump(self.dataContent)

        for key in ['jobId','user','status','type','priority']:
            nodename = "{0}%s" % key
            try:
                self.contentDict[key] = self.dataContent.find(nodename.format(ns)).text
            except:
                pass

        for node in self.dataContent.findall("{0}data".format(ns)):
            try:
                key = node.find("{0}key".format(ns)).text
                value = node.find("{0}value".format(ns)).text
                if isinstance(value,datetime.datetime):
                    self.contentDict[key] = value

                try:
                    self.contentDict[key] = int(value)
                except:
                    try:
                        self.contentDict[key] = float(value)
                    except:
                        self.contentDict[key] = value

            except:
                pass

        startTimeNode = self.dataContent.find("{0}started".format(ns))
        if startTimeNode is not None:
            try:
                #remove microseconds from the time string. Ugly but it should work.
                timeString=re.sub('\.\d+','',startTimeNode.text)
                self.contentDict['started'] = datetime.datetime.strptime(timeString,"%Y-%m-%dT%H:%M:%SZ")
            except ValueError as e: #if the date doesn't parse
                print("WARNING: %s" % e.message)
                pass

    @property
    def errorMessage(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        if not self.dataContent:
            raise ValueError("Job object not initialised yet")

        for node in self.dataContent.findall("{0}data".format(ns)):
            keynode = node.find("{0}key".format(ns))
            if keynode.text is not None and keynode.text == "errorMessage":
                valnode = node.find("{0}value".format(ns))
                return valnode.text

        return "No error"

    @property
    def type(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        if self.dataContent is None:
            raise ValueError("Job object not initialised yet")

        try:
            return self.dataContent.find('{0}type'.format(ns)).text
        except AttributeError:
            return None

    @property
    def priority(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        if self.dataContent is None:
            raise ValueError("Job object not initialised yet")

        try:
            return self.dataContent.find('{0}priority'.format(ns)).text
        except AttributeError:
            return None

    @property
    def total_steps(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        if self.dataContent is None:
            raise ValueError("Job object not initialised yet")

        try:
            return self.dataContent.find('{0}totalSteps'.format(ns)).text
        except AttributeError:
            return None

    @property
    def current_step(self):
        ns = "{http://xml.vidispine.com/schema/vidispine}"
        if self.dataContent is None:
            raise ValueError("Job object not initialised yet")

        node = self.dataContent.find('{0}currentStep'.format(ns))
        if node is not None:
            return VSJobStep(node)
        else:
            return None

    @property
    def log(self):
        for subnode in self.dataContent.find('{0}log'.format(self.xmlns)):
            yield VSJobTask(subnode)

    def status(self):
        if 'status' in self.contentDict:
            return self.contentDict['status']
        else:
            return None

    def started(self):
        if 'started' in self.contentDict:
            return self.contentDict['started']
        else:
            return None

    def finished(self,noraise=True):
        if 'status' in self.contentDict:
            if self.contentDict['status'].startswith("FINISHED"):
                return True
            if self.didFail():
                if noraise:
                    return True
                else:
                    raise VSJobFailed(self)
            return False
        raise Exception("Job definition did not have a status!")

    def hasWarning(self):
        if 'status' in self.contentDict:
            if re.match('_WARNING',self.contentDict['status']):
                return True
            return False
        return True

    def abort(self):
        self.request("/job/{0}".format(self.name),method="DELETE")


class XMLPropMixin(object):
    ns = "{http://xml.vidispine.com/schema/vidispine}"

    def __init__(self):
        self.dataContent = None

    def _find_prop(self, propname):

        if self.dataContent is None:
            raise ValueError("Job object not initialised yet")

        try:
            return self.dataContent.find('{0}{1}'.format(self.ns, propname)).text
        except AttributeError:
            return None


class VSJobStep(XMLPropMixin):
    def __init__(self, xml_frag):
        super(VSJobStep,self).__init__()
        self.dataContent = xml_frag

    @property
    def description(self):
        return self._find_prop('description')

    @property
    def number(self):
        try:
            return int(self._find_prop('number'))
        except ValueError:
            return None

    @property
    def timestamp(self):
        from dateutil.parser import parse as parse_date

        ts_string = self._find_prop('timestamp')
        if ts_string is None:
            return None
        return parse_date(ts_string)

    @property
    def status(self):
        return self._find_prop('status')

    def __unicode__(self):
        return "Step {n}: {d} {s}".format(n=self.number, d=self.description, s=self.status)

    def __str__(self):
        return self.__unicode__().encode('ascii')


class VSJobTask(XMLPropMixin):
    def __init__(self, xml_frag):
        super(VSJobTask,self).__init__()
        self.dataContent = xml_frag

    @property
    def task_id(self):
        try:
            return int(self.dataContent.attrib['id'])
        except ValueError: #it's not an integer
            return None
        except KeyError: #the key did not exist
            return None

    @property
    def step(self):
        try:
            return int(self._find_prop('step'))
        except ValueError:
            return None

    @property
    def attempts(self):
        try:
            return int(self._find_prop('attempts'))
        except ValueError:
            return None

    @property
    def status(self):
        return self._find_prop('status')

    @property
    def timestamp(self):
        from dateutil.parser import parse as parse_date

        ts_string = self._find_prop('timestamp')
        if ts_string is None:
            return None
        return parse_date(ts_string)

    @property
    def description(self):
        return self._find_prop('description')

    @property
    def sub_steps(self):
        for node in self.dataContent.findall('{0}subStep'.format(self.ns)):
            yield VSJobStep(node)

    def __unicode__(self):
        return "Task {id}: {desc} {status} attempt {att} at {time}".format(
            id=self.task_id,
            desc=self.description,
            status=self.status,
            att=self.attempts,
            time=str(self.timestamp),
        )

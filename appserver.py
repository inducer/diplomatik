import re
import sys
import StringIO
import BaseHTTPServer
import datetime
import random
import traceback
import socket
import urlparse

from tools import expandHTMLTemplate
import tools



class tNotFoundError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.Value = value
    def __str__(self):
        return str(self.Value)




class tField:
    def __init__(self, name, description, shown_in_overview = True):
        self.Name = name
        self.Description = description
        self.ShownInOverview = shown_in_overview
        
    def name(self):
        return self.Name

    def description(self):
        return self.Description

    def isMandatory(self):
        return False

    def isShownInOverview(self):
        return self.ShownInOverview

    def getValue(self, object):
        return getattr(object, self.Name)

    def isSortable(self):
        return True

    def getDisplayHTML(self, object):
        raise NotImplementedError

    def getWidgetHTML(self, key, object):
        raise NotImplementedError

    def getWidgetHTMLFromInput(self, key, object, form_input):
        raise NotImplementedError

    def isValid(self, form_input):
        raise NotImplementedError

    def setValue(self, key, form_input, object):
        raise NotImplementedError
        




class tDisplayField(tField):
    def __init__(self, name, description, 
                 shown_in_overview = True):
        tField.__init__(self, name, description,
                        shown_in_overview)
        
    def isValid(self, form_input):
        return True

    def setValue(self, key, form_input, object):
        pass
        




class tStringField(tField):
    def __init__(self, name, description, 
                 shown_in_overview = True,
                 validation_re = None):
        tField.__init__(self, name, description,
                        shown_in_overview)
        self.ValidationRE = validation_re

    def isMandatory(self):
        return self.ValidationRE is not None and \
               self.ValidationRE.match("") is None

    def getDisplayHTML(self, object):
        return tools.escapeHTML(self.getValue(object))

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        if value is None:
            value = ""
        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % \
               (self.Name, tools.escapeHTML(value))

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % (
            self.Name, tools.escapeHTML(form_input[self.Name]))

    def isValid(self, form_input):
        if self.ValidationRE is not None:
            return self.ValidationRE.match(form_input[self.Name])
        else:
            return True

    def setValue(self, key, form_input, object):
        setattr(object, self.Name, form_input[self.Name])




class tDateField(tField):
    def __init__(self, name, description, 
                 shown_in_overview = True, 
                 none_ok = False):
        tField.__init__(self, name, description,
                        shown_in_overview)
        self.NoneOK = none_ok

    def isMandatory(self):
        return not self.NoneOK

    def isSortable(self):
        return not self.NoneOK

    def getDisplayHTML(self, object):
        date = self.getValue(object)
        if date is None:
            return "-/-"
        else:
            return tools.formatDate(date)

    def _getHTML(self, is_none, y, m, d):
        return expandHTMLTemplate("widget-date.html",
                                  {"name": self.Name,
                                   "y": y,
                                   "m": m,
                                   "d": d,
                                   "none_ok": self.NoneOK,
                                   "is_none": is_none,
                                   "dayrange": range(1,32),
                                   "monthrange": range(1,13),
                                   })

    def getWidgetHTML(self, key, object):
        date = self.getValue(object)
        is_none = date is None
        if date is None:
            date = datetime.date.today()
        return self._getHTML(is_none,
                             str(date.year),
                             date.month,
                             date.day)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        today = datetime.date.today()
        y = today.year
        m = today.month
        d = today.day

        try:
            y = int(form_input["%s_y" % self.Name])
        except ValueError:
            pass
        try:
            m = int(form_input["%s_m" % self.Name])
        except ValueError:
            pass
        try:
            d = int(form_input["%s_d" % self.Name])
        except ValueError:
            pass
        is_none = self.NoneOK and form_input["%s_null" % self.Name] == "1"

        return self._getHTML(is_none, str(y), m, d)

    def isValid(self, form_input):
        try:
            y = int(form_input["%s_y" % self.Name])
            m = int(form_input["%s_m" % self.Name])
            d = int(form_input["%s_d" % self.Name])
            datetime.date(y, m, d)
            return True
        except ValueError:
            return False

    def setValue(self, key, form_input, object):
        if self.NoneOK and form_input["%s_null" % self.Name] == "1":
            date = None
        else:
            y = int(form_input["%s_y" % self.Name])
            m = int(form_input["%s_m" % self.Name])
            d = int(form_input["%s_d" % self.Name])
            date = datetime.date(y, m, d)
        setattr(object, self.Name, date)




class tChoiceField(tField):
    def __init__(self, name, description, 
                 shown_in_overview, choices, none_ok = False):
        tField.__init__(self, name, description, 
                        shown_in_overview)
        self.Choices = choices
        self.NoneOK = none_ok

    def isMandatory(self):
        return not self.NoneOK

    def isValid(self, input):
        return True

    def _getValueFromInput(self, form_input):
        v = form_input[self.Name]
        if self.NoneOK:
            if v[0] == "-":
                supposed_value = v[1:]
            else:
                supposed_value = None
        else:
            supposed_value = v
        
        if supposed_value is not None:
            try:
                self.Choices[supposed_value]
                return supposed_value
            except KeyError:
                raise ValueError, "Invalid input in choice field"
        else:
            return supposed_value


    def getDisplayHTML(self, object):
        value = self.getValue(object)
        if value is None:
            return "-/-"
        else:
            return tools.escapeHTML(self.Choices[value])

    def _getHTML(self, choice):
        values = self.Choices.keys()
        descriptions = self.Choices.values()

        if self.NoneOK:
            values.insert(0, "None")
            values = ["-"+value for value in values]
            if choice is None:
                sel_index = 0
            else:
                sel_index = tools.find(values, "-"+choice)
        else:
            if choice is None:
                sel_index = 0
            else:
                sel_index = tools.find(values, choice)

        return expandHTMLTemplate(
            "widget-choice.html",
            {"name": self.Name,
             "indices": range(len(values)),
             "values": values,
             "descriptions": descriptions,
             "sel_index": sel_index })

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        return self._getHTML(value)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        value = self._getValueFromInput(form_input)
        return self._getHTML(value)


    def setValue(self, key, form_input, object):
        value = self._getValueFromInput(form_input)
        setattr(object, self.Name, value)




class tFloatField(tField):
    def __init__(self, name, description, 
                 shown_in_overview = True, 
                 min = None, max = None, none_ok = False):
        tField.__init__(self, name, description,
                        shown_in_overview)
        self.Minimum = min
        self.Maximum = max
        self.NoneOK = none_ok

    def isMandatory(self):
        return not self.NoneOK

    def isValid(self, input):
        try:
            self._getValueFromInput(input)
            return True
        except ValueError:
            return False

    def _getValueFromInput(self, form_input):
        v = form_input[self.Name]
        v = v.replace(",", ".")
        print "V!!", v
        if v == "":
            if self.NoneOK:
                return None
            else:
                raise ValueError, "None not allowed for this field"
        else:
            fv = float(v)
            if self.Minimum is not None and fv < self.Minimum:
                raise ValueError, "Value below allowed minimum"
            if self.Maximum is not None and fv > self.Maximum:
                raise ValueError, "Value above allowed maximum"
            return fv

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        if value is None:
            return "-/-"
        else:
            return str(value)

    def _getWidget(self, value):
        if value is None:
            svalue = ""
        else:
            svalue = str(value)

        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % (
            self.Name, svalue)

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        return self._getWidget(value)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % (
            self.Name, form_input[self.Name])

    def setValue(self, key, form_input, object):
        value = self._getValueFromInput(form_input)
        setattr(object, self.Name, value)




class tCheckField(tField):
    def __init__(self, name, description, 
                 shown_in_overview = True):
        tField.__init__(self, name, description,
                        shown_in_overview)

    def isMandatory(self):
        return True

    def isValid(self, input):
        return True

    def _getValueFromInput(self, form_input):
        try:
            form_input[self.Name]
            return True
        except KeyError:
            return False
            

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        if value:
            return "X"
        else:
            return "-"

    def _getWidget(self, value):
        if value:
            svalue = " checked=\"checked\""
        else:
            svalue = ""

        return "<input type=\"checkbox\" name=\"%s\" value=\"%s\"%s/>" % (
            self.Name, "1", svalue)

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        return self._getWidget(value)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self._getWidget(self._getValueFromInput(form_input))

    def setValue(self, key, form_input, object):
        value = self._getValueFromInput(form_input)
        setattr(object, self.Name, value)




class tChangeOnCreateAdapter(tField):
    def __init__(self, slave):
        tField.__init__(self, 
                        slave.Name,
                        slave.Description,
                        slave.ShownInOverview)
        self.Slave = slave

    def isMandatory(self):
        return self.Slave.isMandatory()

    def getValue(self, object):
        return self.Slave.getValue(object)

    def isSortable(self):
        return self.Slave.isSortable()

    def getDisplayHTML(self, object):
        return self.Slave.getDisplayHTML(object)

    def getWidgetHTML(self, key, object):
        if key is None:
            return self.Slave.getWidgetHTML(key, object)
        else:
            return self.Slave.getDisplayHTML(object)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        if key is None:
            return self.Slave.getWidgetHTML(key, object)
        else:
            return self.Slave.getDisplayHTML(object)

    def isValid(self, form_input):
        return self.Slave.isValid(form_input)

    def setValue(self, key, form_input, object):
        if key is None:
            self.Slave.setValue(key, form_input, object)




class tDatabaseHandler:
    def __init__(self, database, fields):
        self.Database = database
        self.Fields = fields

    def createNewObject(self):
        raise NotImplementedError

    def getObjectKey(self, key):
        return None

    def writeHook(self, key):
        pass

    def inPlaceWriteHook(self, key):
        pass

    def deleteHook(self, key):
        pass

    def defaultSortField(self):
        return None

    def getCustomization(self, element, situation, db_key):
        return ""

    def getFilterList(self):
        return [("none", "-")]

    def enumerateFilteredKeys(self, filter_name):
        if filter_name == "none":
            return self.Database.keys()
        else:
            raise RuntimeError, "unknown filter: %s" % filter_name

    def handleOverviewPage(self, request):
        try:
            current_filter = request.Query["filter"]
            keys = self.enumerateFilteredKeys(
                current_filter)
        except KeyError:
            current_filter = "none"
            keys = self.Database.keys()

        try:
            sort_by = request.Query["sortby"]
        except KeyError:
            sort_by = self.defaultSortField()

        if sort_by is not None:
            sort_fields = [f for f in self.Fields
                           if f.name() == sort_by]
            if len(sort_fields) != 1:
                raise tNotFoundError, \
                      "Cannot sort by unknown field %s" % sort_by
            sort_field = sort_fields[0]
            if not sort_field.isSortable():
                raise tNotFoundError, \
                      "Cannot sort by unordered field %s" % sort_by

            def cmp_func(a, b):
                return cmp(
                    sort_field.getValue(self.Database[a]),
                    sort_field.getValue(self.Database[b]))

            keys.sort(cmp_func)

        return tHTTPResponse(
            expandHTMLTemplate("db-overview.html",
                               {"database": self.Database,
                                "keys": keys,
                                "handler": self,
                                "fields": self.Fields,
                                "previous_query": request.Query,
                                "filters": self.getFilterList(),
                                "current_filter": current_filter}
                               ))

    def generateEditPage(self, request, key, obj):
        if request.Method == "POST":
            if not "save" in request.FormInput:
                return tHTTPResponse("", 302, {"Location": "../overview"})

            valid = True
            for field in self.Fields:
                if not field.isValid(request.FormInput):
                    valid = False
                    break
            if valid:
                for field in self.Fields:
                    field.setValue(key, request.FormInput, obj)

                new_key = self.getObjectKey(obj)
                if key is None:
                    if new_key is None:
                        # generate a new unique key
                        try:
                            while True:
                                new_key = str(random.randint(0,10000000))
                                self.Database[new_key]
                        except KeyError:
                            # found an unused key
                            pass
                    else:
                        if new_key in self.Database:
                            raise tools.tSubjectError(
                                "Object key %s already in use" % new_key)
                    self.Database[new_key] = obj
                else:
                    if new_key is None:
                        pass
                    elif key != new_key:
                        if new_key in self.Database:
                            raise tools.tSubjectError(
                                "Object key %s already in use" % new_key)

                        del self.Database[key]
                        self.Database[new_key] = obj
                    else:
                        self.inPlaceWriteHook(new_key)
                self.writeHook(new_key)

                return tHTTPResponse("", 302, {"Location": "../overview"})
            else:
                return tHTTPResponse(
                    expandHTMLTemplate("db-edit-validate.html",
                                       {"obj": obj,
                                        "key": key,
                                        "input": request.FormInput,
                                        "fields": self.Fields,
                                        "handler": self}
                                       ))
        else:
            return tHTTPResponse(
                expandHTMLTemplate("db-edit.html",
                                   {"obj": obj,
                                    "key": key,
                                    "fields": self.Fields,
                                    "handler": self}
                                   ))

    def handleNewPage(self, request):
        return self.generateEditPage(request, 
                                     None,
                                     self.createNewObject())
    
    def handleEditPage(self, request, key):
        try:
            obj = self.Database[key]
        except KeyError:
            raise tNotFoundError, "Edit request for non-existent key %s" % key

        return self.generateEditPage(request, key, obj)

    def handleDeletePage(self, request, key):
        if len(request.FormInput) == 0:
            try:
                return tHTTPResponse(
                    expandHTMLTemplate("db-delete-ask.html",
                                       {"obj": self.Database[key],
                                        "key": key,
                                        "fields": self.Fields,
                                        "handler": self}
                                       ))
            except KeyError:
                raise tNotFoundError, "Delete request for non-existent key %s" % key
        else:
            if "delete" in request.FormInput:
                del self.Database[key]
                self.deleteHook(key)
            return tHTTPResponse("", 302, {"Location": "../overview"})

    def getPage(self, request):
        edit_re = re.compile("^edit/([a-zA-Z0-9]+)$")
        edit_match = edit_re.search(request.Path)
        delete_re = re.compile("^delete/([a-zA-Z0-9]+)$")
        delete_match = delete_re.search(request.Path)

        if request.Path == "":
            return tHTTPResponse("", 302, 
                                 {"Location": "overview"})
        if request.Path == "overview":
            return self.handleOverviewPage(request)
        elif request.Path == "new/create":
            return self.handleNewPage(request)
        elif edit_match:
            return self.handleEditPage(request, 
                                       edit_match.group(1))
        elif delete_match:
            return self.handleDeletePage(request, 
                                         delete_match.group(1))
        else:
            raise tNotFoundError, "Invalid database handler request URI"




class tHTTPRequest:
    def __init__(self, method, headers, form_input, query,
                 full_path, path = None):
        self.Method = method
        self.Headers = headers
        self.FormInput = form_input
        self.Query = query
        self.FullPath = full_path
        if path is None:
            self.Path = full_path
        else:
            self.Path = path

    def changePath(self, path):
        return tHTTPRequest(
            self.Method,
            self.Headers,
            self.FormInput,
            self.Query,
            self.FullPath,
            path)




class tHTTPResponse:
    def __init__(self, content, response_code = 200, headers = None):
        self.Content = content
        self.ResponseCode = response_code
        if headers is None:
            if isinstance(self.Content, unicode):
                self.Headers = {"Content-type": "text/html; charset=utf-8"}
                self.Content = self.Content.encode("utf-8")
            else:
                self.Headers = {"Content-type": "text/html"}
        else:
            self.Headers = headers




class tAppServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def pageHandlers(self):
        raise NotImplementedError

    def do_GET(self):
        scheme, host, path, param, query, fragment = urlparse.urlparse(self.path)
        request = tHTTPRequest(
            "GET",
            self.headers,
            {},
            tools.parseQuery(query),
            path)
        self.handlePage(request)

    def do_POST(self):
        clength = int(self.headers["Content-Length"])
        post_data = self.rfile.read(clength)
        scheme, host, path, param, query, fragment = urlparse.urlparse(self.path)

        request = tHTTPRequest(
            "POST",
            self.headers,
            tools.parseQuery(post_data),
            tools.parseQuery(query),
            self.path)
        self.handlePage(request)

    def isAllowed(self, socket):
        return True

    def handlePage(self, request):
        if not self.isAllowed(socket):
            self.send_error(403, "Access denied")
            return

        for path_re, handler in self.pageHandlers():
            path_match = re.compile(path_re).match(request.Path)
            if path_match:
                try:
                    response = handler(
                        request.changePath(
                        request.Path[path_match.end():]))
                    if not isinstance(response, tHTTPResponse):
                        raise TypeError, "Expected tHTTPResponse"
                    if not isinstance(response.Content, str):
                        raise TypeError, "Expected string-like content in response"
                except tNotFoundError, e:
                    self.send_error(404, str(e))
                    return
                except tools.tSubjectError, e:
                    outbuf = StringIO.StringIO()
                    traceback.print_exc(file = outbuf)

                    response = tHTTPResponse(
                        tools.expandHTMLTemplate(
                        "subject-error.html",
                        {"traceback": outbuf.getvalue(),
                         "error_text": unicode(e)}),
                        500)
                except:
                    self.send_response(500)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    outbuf = StringIO.StringIO()
                    traceback.print_exc(file = outbuf)
                    errtext = "<body><h1>Server Error</h1>" + \
                              "<p>Sorry, the server could not complete your " + \
                              "request. The following is an error dump that " + \
                              "you may print to help localize the problem.</p>" + \
                              "<pre>%s</pre></body>" \
                              % tools.escapeHTML(outbuf.getvalue())
                    self.wfile.write(errtext)
                    return

                self.send_response(response.ResponseCode)
                for header, value in response.Headers.iteritems():
                    self.send_header(header, value)
                self.send_header("Pragma", "no-cache")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(response.Content)
                return

        self.send_error(404, "Not Found")


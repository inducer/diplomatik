import re
import sys
import os
import StringIO
import urllib
import BaseHTTPServer
import codecs
import datetime
import random
import traceback

import em




class tNotFoundError(Exception):
    def __init__(self, value):
        self.Value = value
    def __str__(self):
        return str(self.Value)




def expandHTMLTemplate(filename, globals_dict):
    output = StringIO.StringIO(u"")
    interpreter = em.Interpreter(globals = globals_dict, 
                                 output = output)
    interpreter.file(codecs.open(os.path.join("html-templates",
                                              filename),
                                 "r", "utf-8"))
    interpreter.shutdown()
    return output.getvalue()




class tField:
    def __init__(self, name, description):
        self.Name = name
        self.Description = description
        
    def description(self):
        return self.Description

    def getDisplayHTML(self, object):
        raise NotImplementedError

    def getWidgetHTML(self, object):
        raise NotImplementedError

    def getWidgetHTMLFromInput(self, form_input):
        raise NotImplementedError

    def isValid(self, form_input):
        return True

    def setValue(self, form_input, object):
        raise NotImplementedError
        




class tStringField(tField):
    def __init__(self, name, description, validation_re = None):
        tField.__init__(self, name, description)
        self.ValidationRE = validation_re

    def getValue(self, object):
        return getattr(object, self.Name)

    def getDisplayHTML(self, object):
        return self.getValue(object)

    def getWidgetHTML(self, object):
        # FIXME quotes
        value = self.getValue(object)
        if value is None:
            value = ""
        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % (
            self.Name, value.replace('"', "&quot;"))

    def getWidgetHTMLFromInput(self, form_input):
        return "<input type=\"text\" name=\"%s\" value=\"%s\"/>" % (
            self.Name, form_input[self.Name].replace('"', "&quot;"))

    def isValid(self, form_input):
        if self.ValidationRE is not None:
            return self.ValidationRE.match(form_input[self.Name])
        else:
            return True

    def setValue(self, form_input, object):
        setattr(object, self.Name, form_input[self.Name])




class tDateField(tField):
    def __init__(self, name, description, none_ok = False):
        tField.__init__(self, name, description)
        self.NoneOK = none_ok

    def isValid(self, input):
        return True

    def description(self):
        return self.Description

    def getValue(self, object):
        return getattr(object, self.Name)

    def getDisplayHTML(self, object):
        date = self.getValue(object)
        if date is None:
            return "-/-"
        else:
            return date.isoformat()

    def _getHTML(self, is_none, y, m, d):
        return expandHTMLTemplate("date.html",
                                  {"name": self.Name,
                                   "y": y,
                                   "m": m,
                                   "d": d,
                                   "none_ok": self.NoneOK,
                                   "is_none": is_none})

    def getWidgetHTML(self, object):
        date = self.getValue(object)
        is_none = date is None
        if date is None:
            date = datetime.date.today()
        return self._getHTML(is_none,
                             date.year,
                             date.month,
                             date.day)

    def getWidgetHTMLFromInput(self, form_input):
        today = datetime.date.today()
        y = today.year
        m = today.month
        d = today.day

        try:
            y = int(form_input["%s-y" % self.Name])
        except ValueError:
            pass
        try:
            m = int(form_input["%s-m" % self.Name])
        except ValueError:
            pass
        try:
            d = int(form_input["%s-d" % self.Name])
        except ValueError:
            pass

        return self._getHTML(form_inputy, m, d)

    def isValid(self, form_input):
        try:
            y = int(form_input["%s-y" % self.Name])
            m = int(form_input["%s-m" % self.Name])
            d = int(form_input["%s-d" % self.Name])
            date = datetime.date(y, m, d)
            return True
        except ValueError, e:
            return False

    def setValue(self, form_input, object):
        if self.NoneOK and form_input["%s-null" % self.Name] == "1":
            date = None
        else:
            y = int(form_input["%s-y" % self.Name])
            m = int(form_input["%s-m" % self.Name])
            d = int(form_input["%s-d" % self.Name])
            date = datetime.date(y, m, d)
        setattr(object, self.Name, date)




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

    def handleOverviewPage(self, path, form_input):
        return tHTTPResponse(
            expandHTMLTemplate("db-overview.html",
                               {"database": self.Database,
                                "fields": self.Fields}
                               ))

    def generateEditPage(self, path, form_input, key, obj):
        if len(form_input):
            if not "save" in form_input:
                return tHTTPResponse("", 302, {"Location": ".."})

            valid = True
            for field in self.Fields:
                if not field.isValid(form_input):
                    valid = False
                    break
            if valid:
                for field in self.Fields:
                    field.setValue(form_input, obj)

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
                    self.Database[new_key] = obj
                else:
                    if new_key is None:
                        pass
                    elif key != new_key:
                        del self.Database[key]
                        self.Database[new_key] = obj
                    else:
                        self.inPlaceWriteHook(new_key)
                self.writeHook(new_key)

                return tHTTPResponse("", 302, {"Location": ".."})
            else:
                return tHTTPResponse(
                    expandHTMLTemplate("db-edit-validate.html",
                                       {"obj": obj,
                                        "input": form_input,
                                        "fields": self.Fields}
                                       ))
        else:
            return tHTTPResponse(
                expandHTMLTemplate("db-edit.html",
                                   {"obj": obj,
                                    "fields": self.Fields}
                                   ))

    def handleNewPage(self, path, form_input):
        return self.generateEditPage(path, form_input, 
                                     None,
                                     self.createNewObject())
    
    def handleEditPage(self, path, form_input, key):
        try:
            obj = self.Database[key]
        except KeyError:
            raise tNotFoundError, "Edit request for non-existent key %s" % key

        return self.generateEditPage(path, form_input, key, obj)

    def handleDeletePage(self, path, form_input, key):
        if len(form_input) == 0:
            try:
                return tHTTPResponse(
                    expandHTMLTemplate("db-delete-ask.html",
                                       {"obj": self.Database[key],
                                        "fields": self.Fields}
                                       ))
            except KeyError:
                raise tNotFoundError, "Delete request for non-existent key %s" % key
        else:
            if "delete" in form_input:
                del self.Database[key]
                self.deleteHook(key)
            return tHTTPResponse("", 302, {"Location": ".."})

    def getPage(self, path, form_input):
        edit_re = re.compile("^edit/([a-zA-Z0-9]+)$")
        edit_match = edit_re.search(path)
        delete_re = re.compile("^delete/([a-zA-Z0-9]+)$")
        delete_match = delete_re.search(path)

        if path == "":
            return self.handleOverviewPage(path, form_input)
        elif path == "new/":
            return self.handleNewPage(path, form_input)
        elif edit_match:
            return self.handleEditPage(path, form_input, 
                                       edit_match.group(1))
        elif delete_match:
            return self.handleDeletePage(path, form_input, 
                                         delete_match.group(1))
        else:
            raise tNotFoundError, "Invalid database handler request URI"




def parseQuery(query):
    result = {}
    for part in query.split("&"):
        key, value = part.split("=")
        value = value.replace("+", " ")
        result[key] = unicode(urllib.unquote(value), 
                              "utf-8")
    return result




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
        self.handlePage(self.path, {})

    def do_POST(self):
        clength = int(self.headers["Content-Length"])
        post_data = self.rfile.read(clength)
        self.handlePage(self.path, parseQuery(post_data))

    def handlePage(self, path, form_input):
        for path_re, handler in self.pageHandlers():
            path_match = re.compile(path_re).match(path)
            if path_match:
                try:
                    response = handler(path[path_match.end():], form_input)
                except tNotFoundError, e:
                    self.send_error(404, str(e))
                    return
                except:
                    self.send_response(500)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    outbuf = StringIO.StringIO()
                    traceback.print_exc(file=outbuf)
                    errtext = "<body><h1>Server Error</h1>" + \
                              "<p>Sorry, the server could not complete your " + \
                              "request. The following is an error dump that " + \
                              "you may print to help localize the problem.</p>" + \
                              "<pre>%s</pre></body>" \
                              % outbuf.getvalue()
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


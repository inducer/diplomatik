import BaseHTTPServer
import re
import sys

import degreeruleset
import datamodel
import appserver
import texpdf

degree_rule_sets = [
    degreeruleset.tDegreeRuleSet()
    ]
store = datamodel.tDataStore("example-data", 
                             degree_rule_sets)



class tDegreesField(appserver.tField):
    def __init__(self, name, description):
        appserver.tField.__init__(self, name, description)

    def getValue(self, object):
        return getattr(object, self.Name)

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        print >> sys.stderr, value
        return ", ".join([
            degree_rule_sets[deg.DegreeRuleSet].description()
            for deg_key, deg in value.iteritems()
            if not deg.DegreeRuleSet is None
            ])

    def getWidgetHTML(self, object):
        value = self.getValue(object)
        return appserver.expandHTMLTemplate("degrees-widget.html",
                                            {"student": object,
                                             "degrees": value,
                                             "rulesets": degree_rule_sets})

    def getWidgetHTMLFromInput(self, object, form_input):
        return self.getWidgetHTML(object)

    def isValid(self, form_input):
        return True

    def setValue(self, form_input, object):
        pass



class tStudentDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, store):
        appserver.tDatabaseHandler.__init__(self,
                                            store,
                                            [
            appserver.tStringField("ID", "Matrikelnummer", 
                         re.compile("^[a-zA-Z0-9]+$")),
            appserver.tStringField("FirstName", "Vorname"),
            appserver.tStringField("MiddleName", "Weitere Vornamen"),
            appserver.tStringField("LastName", "Nachname"),
            appserver.tDateField("DateOfBirth", "Geburtsdatum", none_ok = True),
            tDegreesField("Degrees", "Abschl&uuml;sse"),
            appserver.tStringField("Notes", "Notizen")
            ])

    def createNewObject(self):
        return datamodel.tStudent()

    def getObjectKey(self, object):
        return object.ID

    def inPlaceWriteHook(self, key):
        store.writeStudent(key)




class tDegreeDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student):
        self.Student = student
        appserver.tDatabaseHandler.__init__(self,
                                            student.Degrees,
                                            [
            appserver.tDateField("EnrolledDate", "Begonnen"),
            appserver.tDateField("FinishedDate", "Abgeschlossen", none_ok = True),
            appserver.tStringField("Remark", "Bemerkungen"),
            ])

    def createNewObject(self):
        return datamodel.tDegree()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)




class tMainAppServer(appserver.tAppServer):
    def pageHandlers(self):
        def handleStudents(path, form_input):
            return tStudentDatabaseHandler(
                store).getPage(path, form_input)
        
        def handleDegrees(path, form_input):
            stud_id_re = re.compile("^([a-zA-Z0-9]+)/")
            stud_id_match = stud_id_re.match(path)
            if not stud_id_match:
                raise appserver.tNotFoundError, \
                      "Invalid degrees request %s" % path
            stud_id = stud_id_match.group(1)
            try:
                student = store[stud_id]
            except KeyError:
                raise appserver.tNotFoundError, \
                      "Unknown student ID: %s" % stud_id
              
            return tDegreeDatabaseHandler(student)\
                   .getPage(path[stud_id_match.end():], form_input)
        
        def generatePDF(path, form_input):
            return appserver.tHTTPResponse(
                texpdf.runLatex(r"\documentclass{article}"+
                                r"\begin{document}Hallo $\pi$"+
                                r"\end{document}"),
                200,
                {"Content-type": "application/pdf"})

        def redirectToStart(path, form_input):
            return appserver.tHTTPResponse(
                "", 302, {"Location": "/students/"})

        return [
            ("^/students/", handleStudents),
            ("^/degrees/", handleDegrees),
            ("^/pdf$", generatePDF),
            ("^/students$", redirectToStart),
            ("^/$", redirectToStart)
            ]

httpd = BaseHTTPServer.HTTPServer(('', 8000), 
                                  tMainAppServer)
httpd.serve_forever()

me = datamodel.tStudent()
me.ID = "992330"
store.writeStudent(me)

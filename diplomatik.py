import BaseHTTPServer
import re
import sys

import degreeruleset
import datamodel
import appserver
import texpdf

from tools import expandHTMLTemplate

degree_rule_sets = [
    degreeruleset.tTemaVDAltDegreeRuleSet(),
    degreeruleset.tTemaHDAltDegreeRuleSet()
    ]

degree_rule_sets_map = {}
for drs in degree_rule_sets:
    degree_rule_sets_map[drs.id()] = drs

store = datamodel.tDataStore("example-data", 
                             degree_rule_sets)



class tDegreesField(appserver.tDisplayField):
    def __init__(self, name, description):
        appserver.tField.__init__(self, name, description)

    def getValue(self, object):
        return getattr(object, self.Name)

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        return ", ".join([
            degree_rule_sets_map[deg.DegreeRuleSet].description()
            for deg_key, deg in value.iteritems()
            ])

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        print value
        return appserver.expandHTMLTemplate("degrees-widget.html",
                                            {"student": object,
                                             "degrees": value.values(),
                                             "rulesets": degree_rule_sets_map})

    def getWidgetHTMLFromInput(self, object, form_input):
        return self.getWidgetHTML(key, object)




class tExamsField(appserver.tDisplayField):
    def __init__(self, name, description, student):
        appserver.tField.__init__(self, name, description)
        self.Student = student

    def getValue(self, object):
        return getattr(object, self.Name)

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        return ", ".join([
            ex.Description
            for ex in value.itervalues()
            ])

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        print value
        return appserver.expandHTMLTemplate("exams-widget.html",
                                            {"student": self.Student,
                                             "degree": object,
                                             "degree_id": key,
                                             "exams": value.values(),
                                             })

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self.getWidgetHTML(key, object)




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
            appserver.tStringField("Notes", "Notizen"),
            appserver.tStringField("Email", "Email-Adresse")
            ])

    def createNewObject(self):
        return datamodel.tStudent()

    def getObjectKey(self, object):
        return object.ID

    def inPlaceWriteHook(self, key):
        store.writeStudent(key)

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Studierendendatenbank"

        if element == "header":
            result = expandHTMLTemplate("main-header.html")
            if situation == "overview":
                result += expandHTMLTemplate("welcome.html")
            return result
        return ""




class tDegreeDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student):
        self.Student = student
        appserver.tDatabaseHandler.__init__(self,
                                            student.Degrees,
                                            [
            appserver.tChoiceField(
            "DegreeRuleSet", "Art des Abschlusses",
            [(drs.id(), drs.description()) for drs in degree_rule_sets]),
            appserver.tDateField("EnrolledDate", "Begonnen"),
            appserver.tDateField("FinishedDate", "Abgeschlossen", none_ok = True),
            tExamsField("Exams", "Pr&uuml;fungen", student),
            appserver.tStringField("Remark", "Bemerkungen"),
            ])

    def createNewObject(self):
        return datamodel.tDegree()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Abschl&uuml;sse f&uuml;r %s" % self.Student.ID

        if element == "header":
            return expandHTMLTemplate(
                "degrees-header.html",
                {"student": self.Student})
        return ""




class tExamsDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student, deg_id, degree):
        self.Student = student
        self.DegreeID = deg_id
        self.Degree = degree
        appserver.tDatabaseHandler.__init__(self,
                                            degree.Exams,
                                            [
            appserver.tDateField("Date", "Datum"),
            # FIXME semester
            appserver.tStringField("Description", "Beschreibung"),
            appserver.tChoiceField("DegreeComponent", 
                                   "Komponente",
                                   degree_rule_sets_map[degree.DegreeRuleSet].degreeComponents()),
            appserver.tStringField("Examiner", "Pr&uuml;fer"),
            #appserver.tFloatField("CountedResult", "Gez&auml;hltes Ergebnis", 1.0, 6.0, 1),
            appserver.tStringField("NativeResult", "Original-Ergebnis"),
            #appserver.tFloatField("Credits", "SWS", 0.0, None, 1),
            appserver.tStringField("CreditsPrintable", "SWS (ausf&uuml;hrlich)"),
            appserver.tStringField("Remarks", "Bemerkung"),
            ])

    def createNewObject(self):
        return datamodel.tExam()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Pr&uuml;fungen f&uuml;r %s" % self.Student.ID

        if element == "header":
            return expandHTMLTemplate(
                "exams-header.html",
                {"student": self.Student,
                 "degree_id": self.DegreeID,
                 "degree": self.Degree,
                 "rulesets": degree_rule_sets_map})
        return ""



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

        def handleExams(path, form_input):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/")
            id_match = id_re.match(path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid exams request %s" % path
            stud_id = id_match.group(1)
            degree_id = id_match.group(2)
            try:
                student = store[stud_id]
            except KeyError:
                raise appserver.tNotFoundError, \
                      "Unknown student ID: %s" % stud_id
            try:
                degree = student.Degrees[degree_id]
            except KeyError:
                raise appserver.tNotFoundError, \
                      "Unknown degree ID: %s" % stud_id
              
            return tExamsDatabaseHandler(student, degree_id, degree)\
                   .getPage(path[id_match.end():], 
                            form_input)
        
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
            ("^/exams/", handleExams),
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

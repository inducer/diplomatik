import BaseHTTPServer
import re
import sys

import tools
import semester
import degreeruleset
import datamodel
import appserver

from tools import expandHTMLTemplate

__VERSION__ = "0.90"
LISTEN_PORT = 8000




# Custom fields implementations ----------------------------
class tSemesterField(appserver.tField):
    def __init__(self, name, description,
                 shown_in_overview = True,
                 none_ok = False):
        appserver.tField.__init__(self, name, description,
                        shown_in_overview)
        self.NoneOK = none_ok

    def getDisplayHTML(self, object):
        sem = self.getValue(object)
        if sem is None:
            return "-/-"
        else:
            return str(sem)

    def _getHTML(self, is_none, term, year):
        return expandHTMLTemplate("widget-semester.html",
                                  {"name": self.Name,
                                   "term": term,
                                   "year": year,
                                   "none_ok": self.NoneOK,
                                   "is_none": is_none,
                                   })

    def getWidgetHTML(self, key, object):
        sem = self.getValue(object) 
        v = sem or semester.tSemester().now()
        return self._getHTML(sem is None, v.Term, v.Year)

    def _getInput(self, form_input):
        if self.NoneOK and form_input["%s-null" % self.Name] == "1":
            return None
        else:
            y = int(form_input["%s-y" % self.Name])
            t = form_input["%s-t" % self.Name]
            return semester.tSemester(t, y)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self._getHTML(
            self.NoneOK and form_input["%s-null" % self.Name] == "1",
            form_input["%s-t" % self.Name],
            form_input["%s-y" % self.Name]
            )

    def isValid(self, form_input):
        try:
            int(form_input["%s-y" % self.Name])
            form_input["%s-y" % self.Name] in ["s", "t"]
            return True
        except ValueError:
            return False

    def setValue(self, key, form_input, object):
        setattr(object, self.Name, 
                self._getInput(form_input))



class tDegreesField(appserver.tDisplayField):
    def __init__(self, name, description):
        appserver.tDisplayField.__init__(self, name, description)

    def isSortable(self):
        return False

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        return ", ".join([
            degree_rule_sets_map[deg.DegreeRuleSet].description()
            for deg_key, deg in value.iteritems()
            ])

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)
        return appserver.expandHTMLTemplate("widget-degrees.html",
                                            {"student": object,
                                             "degrees": value.values(),
                                             "rulesets": degree_rule_sets_map})

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self.getWidgetHTML(key, object)




class tExamsField(appserver.tDisplayField):
    def __init__(self, name, description, student):
        appserver.tDisplayField.__init__(self, name, description)
        self.Student = student

    def isSortable(self):
        return False

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        return ", ".join([
            ex.Description
            for ex in value.itervalues()
            ])

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)

        exams = value.values()
        def cmp_date_func(a, b):
            return cmp(a.Date, b.Date)
        exams.sort(cmp_date_func)

        if key is None:
            components = {}
        else:
            components = dict(degree_rule_sets_map[object.DegreeRuleSet].degreeComponents())

        return appserver.expandHTMLTemplate("widget-exams.html",
                                            {"student": self.Student,
                                             "degree": object,
                                             "degree_id": key,
                                             "exams": exams,
                                             "components": components
                                             })

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self.getWidgetHTML(key, object)




class tSpecialSemestersField(appserver.tDisplayField):
    def __init__(self, name, description):
        appserver.tDisplayField.__init__(self, name, description,
                                         shown_in_overview = False)

    def isSortable(self):
        return False

    def getDisplayHTML(self, object):
        value = self.getValue(object)
        return ", ".join([
            str(sem.Semester)
            for sem in value.itervalues()
            ])

    def getWidgetHTML(self, key, object):
        value = self.getValue(object)

        sems = value.values()
        def cmp_date_func(a, b):
            return cmp(a.Semester, b.Semester)
        sems.sort(cmp_date_func)

        return appserver.expandHTMLTemplate("widget-specsem.html",
                                            {"student": object,
                                             "sems": sems,
                                             })

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self.getWidgetHTML(key, object)




# Database handlers ----------------------------------------
class tStudentDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, store):
        appserver.tDatabaseHandler.__init__(self,
                                            store,
                                            [
            appserver.tStringField("ID", "Matrikelnummer", 
                                   shown_in_overview = True,
                                   validation_re = \
                                   re.compile("^[a-zA-Z0-9]+$")),
            appserver.tStringField("FirstName", "Vorname"),
            appserver.tStringField("MiddleName", "Weitere Vornamen",
                                   False),
            appserver.tStringField("LastName", "Nachname"),
            appserver.tDateField("DateOfBirth", "Geburtsdatum", 
                                 shown_in_overview = False,
                                 none_ok = True),
            appserver.tStringField("PlaceOfBirth", "Geburtsort",
                                   shown_in_overview = False),
            tDegreesField("Degrees", "Abschl&uuml;sse"),
            tSpecialSemestersField("SpecialSemesters", "Spezielle Semester"),
            appserver.tStringField("Notes", "Notizen",
                                   shown_in_overview = False),
            appserver.tStringField("Email", "Email-Adresse",
                                   shown_in_overview = False)
            ])

    def createNewObject(self):
        return datamodel.tStudent()

    def getObjectKey(self, object):
        return object.ID

    def inPlaceWriteHook(self, key):
        store.writeStudent(key)

    def defaultSortField(self):
        return "LastName";

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Studierendendatenbank"

        if element == "extra-commands":
            return '<a href="/quit">Diplomatik beenden</a>'

        if element == "header":
            result = expandHTMLTemplate("main-header.html")

            if situation == "overview":
                result += expandHTMLTemplate("welcome.html",
                                             {"version": __VERSION__})

            if situation == "edit" and db_key:
                result += expandHTMLTemplate(
                    "student-reports.html",
                    {"student": self.Database[db_key],
                     "reports": degreeruleset.perStudentReports()
                     })

            return result
        return ""




class tSpecialSemesterDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student):
        self.Student = student
        appserver.tDatabaseHandler.__init__(self,
                                            student.SpecialSemesters,
                                            [
            tSemesterField("Semester", "Semester"),
            appserver.tChoiceField("Type", "Art",
                                   True,
                                   [("urlaub", "Urlaubssemester")]),
            appserver.tStringField("Remark", "Bemerkungen",
                                   shown_in_overview = True),
            ])

    def createNewObject(self):
        return datamodel.tSpecialSemester()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)

    def defaultSortField(self):
        return "Semester";

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Spezielle Semester f&uuml;r %s" % self.Student.ID

        if element == "header":
            return expandHTMLTemplate(
                "special-sem-header.html",
                {"student": self.Student})

        return ""




class tDegreeDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student):
        self.Student = student
        appserver.tDatabaseHandler.__init__(self,
                                            student.Degrees,
                                            [
            appserver.tChangeOnCreateAdapter(
            appserver.tChoiceField(
            "DegreeRuleSet", "Art des Abschlusses",
            shown_in_overview = True,
            choices = [(drs.id(), drs.description()) 
                       for drs in degree_rule_sets])),
            appserver.tDateField("EnrolledDate", "Begonnen"),
            appserver.tDateField("FinishedDate", "Abgeschlossen", 
                                 none_ok = True),
            appserver.tStringField("MinorSubject", "1. Nebenfach",
                                   shown_in_overview = False),
            tExamsField("Exams", "Pr&uuml;fungen", student),
            appserver.tStringField("Remark", "Bemerkungen",
                                   shown_in_overview = False),
            ])

    def createNewObject(self):
        return datamodel.tDegree()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)

    def defaultSortField(self):
        return "EnrolledDate";

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Abschl&uuml;sse f&uuml;r %s" % self.Student.ID

        if element == "header":
            result = expandHTMLTemplate(
                "degrees-header.html",
                {"student": self.Student})

            if situation == "edit" and db_key:
                degree = self.Database[db_key]
                drs = degree_rule_sets_map[degree.DegreeRuleSet]
                result += expandHTMLTemplate(
                    "degree-reports.html",
                    {"student": self.Student,
                     "degree_id": db_key,
                     "reports": drs.perDegreeReports()
                     })
            return result

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
            appserver.tStringField("Description", "Beschreibung"),
            appserver.tChoiceField("DegreeComponent", 
                                   "Komponente",
                                   shown_in_overview = True,
                                   choices = degree_rule_sets_map[degree.DegreeRuleSet].degreeComponents()
                                   ),
            appserver.tChoiceField("Source", "Ursprung",
                                   shown_in_overview = True,
                                   choices = degree_rule_sets_map[degree.DegreeRuleSet].examSources()
                                   ),
            appserver.tStringField("SourceDescription", "Ursprung (ausf&uuml;hrlich)",
                                   shown_in_overview = False),
            appserver.tStringField("Examiner", "Pr&uuml;fer"),
            appserver.tCheckField("Counted", "Gewertet?"),
            appserver.tFloatField("CountedResult", "Gez&auml;hltes Ergebnis",
                                  shown_in_overview = True,
                                  min = 1.0, 
                                  max = 6.0, 
                                  none_ok = True),
            appserver.tStringField("NativeResult", "Original-Ergebnis",
                                   shown_in_overview = False),
            appserver.tFloatField("Credits", "SWS", 
                                  shown_in_overview = True,
                                  min = 0.0, 
                                  max = None, 
                                  none_ok = True),
            appserver.tStringField("CreditsPrintable", "SWS (ausf&uuml;hrlich)",
                                   shown_in_overview = False),
            appserver.tStringField("Remarks", "Bemerkung",
                                   shown_in_overview = False),
            ])

    def createNewObject(self):
        return datamodel.tExam()

    def writeHook(self, key):
        store.writeStudent(self.Student.ID)

    def deleteHook(self, key):
        store.writeStudent(self.Student.ID)

    def defaultSortField(self):
        return "Date";

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




# Request dispatcher ---------------------------------------
class tMainAppServer(appserver.tAppServer):
    def resolveStudent(self, stud_id):
        try:
            student = store[stud_id]
        except KeyError:
            raise appserver.tNotFoundError, \
                  "Unknown student ID: %s" % stud_id
        return student
    
    def resolveDegree(self, stud_id, degree_id):
        student = self.resolveStudent(stud_id)

        try:
            degree = student.Degrees[degree_id]
        except KeyError:
            raise appserver.tNotFoundError, \
                  "Unknown degree ID: %s" % degree_id
        
        return student, degree

    def pageHandlers(self):
        def handleStudentDatabase(path, form_input):
            return tStudentDatabaseHandler(
                store).getPage(path, form_input)
        
        def handleSpecialSemesterDatabase(path, form_input):
            stud_id_re = re.compile("^([a-zA-Z0-9]+)/")
            stud_id_match = stud_id_re.match(path)
            if not stud_id_match:
                raise appserver.tNotFoundError, \
                      "Invalid special semesters request %s" % path
            stud_id = stud_id_match.group(1)
              
            return tSpecialSemesterDatabaseHandler(
                self.resolveStudent(stud_id))\
                .getPage(path[stud_id_match.end():], 
                         form_input)

        def handleDegreeDatabase(path, form_input):
            stud_id_re = re.compile("^([a-zA-Z0-9]+)/")
            stud_id_match = stud_id_re.match(path)
            if not stud_id_match:
                raise appserver.tNotFoundError, \
                      "Invalid degrees request %s" % path
            stud_id = stud_id_match.group(1)
              
            return tDegreeDatabaseHandler(
                self.resolveStudent(stud_id))\
                .getPage(path[stud_id_match.end():], 
                         form_input)

        def handleExamDatabase(path, form_input):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/")
            id_match = id_re.match(path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid exams request %s" % path
            stud_id = id_match.group(1)
            degree_id = id_match.group(2)
            student, degree = self.resolveDegree(stud_id,
                                                 degree_id)
              
            return tExamsDatabaseHandler(
                student, degree_id, degree)\
                .getPage(path[id_match.end():], 
                         form_input)
        
        def handlePerDegreeReports(path, form_input):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)$")
            id_match = id_re.match(path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid per-degree report request %s" % path
            report_id = id_match.group(1)
            format_id = id_match.group(2)
            student_id = id_match.group(3)
            degree_id = id_match.group(4)

            if format_id != "pdf":
                return "Formats besides PDF currently unsupported"

            student, degree = self.resolveDegree(student_id, degree_id)
              
            drs = degree_rule_sets_map[degree.DegreeRuleSet]
            return appserver.tHTTPResponse(
                drs.doPerDegreeReport(report_id,
                                      student,
                                      degree),
                200,
                {"Content-type": "application/pdf"})

        def handlePerStudentReports(path, form_input):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)$")
            id_match = id_re.match(path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid per-student report request %s" % path
            report_id = id_match.group(1)
            format_id = id_match.group(2)
            student_id = id_match.group(3)

            if format_id != "pdf":
                return "Formats besides PDF currently unsupported"

            student = self.resolveStudent(student_id)
              
            return appserver.tHTTPResponse(
                degreeruleset.doPerStudentReport(report_id,
                                                 student,
                                                 degree_rule_sets_map),
                200,
                {"Content-type": "application/pdf"})

        def redirectToStart(path, form_input):
            return appserver.tHTTPResponse(
                "", 302, {"Location": "/students/"})

        def doQuit(path, form_input):
            quitflag.set(True)
            return appserver.tHTTPResponse(
                "OK, wird beendet.",
                200,
                {"Content-type": "text/plain"})


        return [
            ("^/students/", handleStudentDatabase),
            ("^/specsem/", handleSpecialSemesterDatabase),
            ("^/degrees/", handleDegreeDatabase),
            ("^/exams/", handleExamDatabase),
            ("^/report/perstudent/", handlePerStudentReports),
            ("^/report/perdegree/", handlePerDegreeReports),
            ("^/students$", redirectToStart),
            ("^/quit$", doQuit),
            ("^/$", redirectToStart)
            ]





# Main program ---------------------------------------------
degree_rule_sets = [
    degreeruleset.tTemaVDAltDegreeRuleSet(),
    degreeruleset.tTemaHDAltDegreeRuleSet()
    ]

degree_rule_sets_map = {}
for drs in degree_rule_sets:
    degree_rule_sets_map[drs.id()] = drs

print "Loading student data...",
sys.stdout.flush()
store = datamodel.tDataStore("example-data", 
                             degree_rule_sets)
print "done"
httpd = BaseHTTPServer.HTTPServer(('', LISTEN_PORT), 
                                  tMainAppServer)

print "Serving requests at http://localhost:%d." % LISTEN_PORT
quitflag = tools.tReference(False)
while not quitflag.get():
    httpd.handle_request()

print "Diplomatik wurde ordnungsgemaess beendet."

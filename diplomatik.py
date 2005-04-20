#! /usr/bin/env python
# -*- coding: utf-8 -*-

import BaseHTTPServer
import re
import sys
import os
import os.path
import getopt

import tools
import semester
import degreeruleset
import reports
import datamodel
import datastore
import appserver

from tools import expandHTMLTemplate

__VERSION__ = file("VERSION").read().strip()
LISTEN_PORT = 8000
ALLOW_NON_LOCAL = False
DO_START_BROWSER = False




# Custom fields implementations ----------------------------
class tSemesterField(appserver.tField):
    def __init__(self, name, description,
                 shown_in_overview = True,
                 none_ok = False):
        appserver.tField.__init__(self, name, description,
                        shown_in_overview)
        self.NoneOK = none_ok

    def isMandatory(self):
        return not self.NoneOK

    def getDisplayHTML(self, key, object):
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
        return self._getHTML(sem is None, str(v.Term), str(v.Year))

    def _getInput(self, form_input):
        if self.NoneOK and form_input["%s_null" % self.Name] == "1":
            return None
        else:
            y = int(form_input["%s_y" % self.Name])
            t = form_input["%s_t" % self.Name]
            return semester.tSemester(t, y)

    def getWidgetHTMLFromInput(self, key, object, form_input):
        return self._getHTML(
            self.NoneOK and form_input["%s-null" % self.Name] == "1",
            str(form_input["%s_t" % self.Name]),
            str(form_input["%s_y" % self.Name])
            )

    def isValid(self, form_input):
        try:
            int(form_input["%s_y" % self.Name])
            form_input["%s_y" % self.Name] in ["s", "t"]
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

    def getDisplayHTML(self, key, object):
        value = self.getValue(object)
        return ", ".join([
            '<a href="/degrees/%s/edit/%s">%s</a>' % (
            object.ID,
            deg_key,
            degree_rule_sets_map[deg.DegreeRuleSet].description(),
            )
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

    def getDisplayHTML(self, key, object):
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

    def getDisplayHTML(self, key, object):
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
            appserver.tStringField("ID", "Matrikelnr.", 
                                   shown_in_overview = True,
                                   validation_re = \
                                   re.compile("^[a-zA-Z0-9]+$")),
            appserver.tCheckField("Active", "Aktiv?",
                                  shown_in_overview = False),
            appserver.tStringField("FirstName", "Vorname"),
            appserver.tStringField("MiddleName", "Weitere Vornamen",
                                   False),
            appserver.tStringField("LastName", "Nachname"),
            appserver.tChoiceField("Gender", "Geschlecht",
                                   False,
                                   tools.tAssociativeList([("m", u"Männlich"),
                                                           ("w", "Weiblich")])),
            appserver.tDateField("DateOfBirth", "Geburtsdatum", 
                                 shown_in_overview = False,
                                 none_ok = True),
            appserver.tStringField("PlaceOfBirth", "Geburtsort",
                                   shown_in_overview = False),
            tDegreesField("Degrees", u"Abschlüsse"),
            tSpecialSemestersField("SpecialSemesters", "Spezielle Semester"),
            appserver.tStringField("Email", "Email-Adresse",
                                   shown_in_overview = False),
            appserver.tStringField("Notes", "Notizen",
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
            return '&middot; <a href="/quit">Diplomatik beenden</a> ' + \
                   '&middot; <a href="/export-all">Exporte aktualisieren</a>'

        if element == "header":
            result = expandHTMLTemplate("main-header.html")

            if situation == "overview":
                result += expandHTMLTemplate(
                    "welcome.html",
                    {"version": __VERSION__})

                report_handler = reports.tGlobalReportHandler(
                    store,
                    degree_rule_sets_map)
                
                result += expandHTMLTemplate(
                    "reports.html",
                    {"reports": report_handler.getList(),
                     "urlscheme": "global"})

            if situation == "edit" and db_key:
                rep_handler = reports.tPerStudentReportHandler(
                    self.Database[db_key],
                    degree_rule_sets_map)
                result += expandHTMLTemplate(
                    "reports.html",
                    {"reports": rep_handler.getList(),
                     "urlscheme": "perstudent/%s" % db_key,
                     })

            return result
        return ""

    def getFilterGroupList(self):
        lnf = [("lastname-"+value.LastName[0].lower(), 
                value.LastName[0])
                for key, value in self.Database.iteritems()
                if value.LastName]
        lnf.sort()
        lnf = tools.uniq(lnf)
        ayf = []
        for key, value in self.Database.iteritems():
            if datamodel.firstEnrollment(value) is None:
                continue
            ay = semester.getAcademicYear(datamodel.firstEnrollment(value))
            ayf.append(("ay-%d" % ay, "Ak.J. %d" % ay))
        ayf.sort()
        ayf = tools.uniq(ayf)

        return appserver.tDatabaseHandler.getFilterGroupList(self) + \
               [lnf, ayf, [("active", "Aktiv"), ("inactive", "Inaktiv")], 
                           [("done", "Fertig"), ("not-done", "Nicht fertig")]]

    def getDefaultFilters(self):
        return ["active"]

    def filterKeys(self, filter_name, keys):
        lastname_re = re.compile("^lastname-(.)$")
        lastname_match = lastname_re.match(filter_name)
        ay_re = re.compile("^ay-([0-9]+)$")
        ay_match = ay_re.match(filter_name)

        kv = [(key, self.Database[key]) for key in keys]
        if lastname_match:
            start_char = lastname_match.group(1).lower()
            return [key for key, value in kv
                    if value.LastName and value.LastName[0].lower() == start_char]
        elif ay_match:
            academic_year = int(ay_match.group(1))
            return [key 
                    for key, value in kv
                    if datamodel.firstEnrollment(value) is not None
                    if semester.getAcademicYear(datamodel.firstEnrollment(value)) == academic_year]
        elif filter_name == "active":
            return [key 
                    for key, value in kv
                    if value.Active]
        elif filter_name == "inactive":
            return [key 
                    for key, value in kv
                    if not value.Active]
        elif filter_name == "done":
            return [key 
                    for key, value in kv
                    if datamodel.isDone(value)]
        elif filter_name == "not-done":
            return [key 
                    for key, value in kv
                    if not datamodel.isDone(value)]
        else:
            return appserver.tDatabaseHandler.filterKeys(self, filter_name, keys)




class tSpecialSemesterDatabaseHandler(appserver.tDatabaseHandler):
    def __init__(self, student):
        self.Student = student
        appserver.tDatabaseHandler.__init__(self,
                                            student.SpecialSemesters,
                                            [
            tSemesterField("Semester", "Semester"),
            appserver.tChoiceField("Type", "Art",
                                   True,
                                   tools.tAssociativeList([("urlaub", "Urlaubssemester")])),
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
            choices = tools.tAssociativeList([(drs.id(), drs.description()) 
                                              for drs in degree_rule_sets]))),
            tSemesterField("EnrolledSemester", "Beginn Studienabschnitt"),
            appserver.tDateField("FinishedDate", "Abgeschlossen", 
                                 none_ok = True),
            appserver.tStringField("MinorSubject", "1. Nebenfach",
                                   shown_in_overview = False),
            tExamsField("Exams", u"Prüfungen", student),
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
        return "EnrolledSemester";

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
                report_handler = drs.getPerDegreeReportHandler(
                    self.Student, degree)
                result += expandHTMLTemplate(
                    "reports.html",
                    {"reports": report_handler.getList(),
                     "urlscheme": "perdegree/%s/%s" % \
                     (self.Student.ID, db_key)
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
            appserver.tChoiceField("Source", "Herkunft",
                                   shown_in_overview = True,
                                   choices = degree_rule_sets_map[degree.DegreeRuleSet].examSources()
                                   ),
            appserver.tChoiceField("DegreeComponent", 
                                   "Komponente",
                                   shown_in_overview = True,
                                   choices = degree_rule_sets_map[degree.DegreeRuleSet].degreeComponents()
                                   ),
            appserver.tFloatField("Credits", "SWS", 
                                  shown_in_overview = True,
                                  min = 0.0, 
                                  max = None, 
                                  none_ok = True),
            appserver.tStringField("CreditsPrintable", u"SWS (ausführlich)",
                                   shown_in_overview = False),
            appserver.tFloatField("CountedResult", "Note",
                                  shown_in_overview = True,
                                  min = 1.0, 
                                  max = 6.0, 
                                  none_ok = True),
            appserver.tStringField("NativeResult", "Original-Ergebnis (falls abweichend)",
                                   shown_in_overview = False),
            appserver.tStringField("Description", "Fach"),
            appserver.tStringField("SourceDescription", u"Herkunft (ausführlich)",
                                   shown_in_overview = False),
            appserver.tStringField("Examiner", u"Prüfer"),
            appserver.tCheckField("Counted", "Gewertet"),
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
        return "DegreeComponent";

    def getCustomization(self, element, situation, db_key):
        if element == "title":
            return "Pr&uuml;fungen f&uuml;r %s" % self.Student.ID

        if element == "header":
            result = expandHTMLTemplate(
                "exams-header.html",
                {"student": self.Student,
                 "degree_id": self.DegreeID,
                 "degree": self.Degree,
                 "rulesets": degree_rule_sets_map})

            if situation == "edit" and db_key:
                exam = self.Database[db_key]
                drs = degree_rule_sets_map[self.Degree.DegreeRuleSet]
                report_handler = drs.getPerExamReportHandler(
                    self.Student, self.Degree, exam)
                result += expandHTMLTemplate(
                    "reports.html",
                    {"reports": report_handler.getList(),
                     "urlscheme": "perexam/%s/%s/%s" % \
                     (self.Student.ID, self.DegreeID, db_key)})

            return result
        return ""




# Request dispatcher ---------------------------------------
class tMainAppServer(appserver.tAppServer):
    def isAllowed(self, socket):
        return ALLOW_NON_LOCAL \
               or self.client_address[0] == socket.gethostbyname("localhost")

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

    def resolveExam(self, stud_id, degree_id, exam_id):
        student, degree = self.resolveDegree(stud_id, degree_id)

        try:
            exam = degree.Exams[exam_id]
        except KeyError:
            raise appserver.tNotFoundError, \
                  "Unknown exam ID: %s" % exam_id
        
        return student, degree, exam

    def pageHandlers(self):
        def handleStudentDatabase(request):
            return tStudentDatabaseHandler(
                store).getPage(request)
        
        def handleSpecialSemesterDatabase(request):
            stud_id_re = re.compile("^([a-zA-Z0-9]+)/")
            stud_id_match = stud_id_re.match(request.Path)
            if not stud_id_match:
                raise appserver.tNotFoundError, \
                      "Invalid special semesters request %s" % request.Path
            stud_id = stud_id_match.group(1)
              
            return tSpecialSemesterDatabaseHandler(
                self.resolveStudent(stud_id))\
                .getPage(request.changePath(
                request.Path[stud_id_match.end():]))

        def handleDegreeDatabase(request):
            stud_id_re = re.compile("^([a-zA-Z0-9]+)/")
            stud_id_match = stud_id_re.match(request.Path)
            if not stud_id_match:
                raise appserver.tNotFoundError, \
                      "Invalid degrees request %s" % request.Path
            stud_id = stud_id_match.group(1)
              
            return tDegreeDatabaseHandler(
                self.resolveStudent(stud_id))\
                .getPage(request.changePath(
                request.Path[stud_id_match.end():]))

        def handleExamDatabase(request):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/")
            id_match = id_re.match(request.Path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid exams request %s" % request.Path
            stud_id = id_match.group(1)
            degree_id = id_match.group(2)
            student, degree = self.resolveDegree(stud_id,
                                                 degree_id)
              
            return tExamsDatabaseHandler(
                student, degree_id, degree)\
                .getPage(request.changePath(
                request.Path[id_match.end():]))
        
        def handleGlobalReports(request):
            return reports.tGlobalReportHandler(
                store, degree_rule_sets_map)\
                .handleRequest(request)

        def handlePerStudentReports(request):
            id_re = re.compile("^([a-zA-Z0-9]+)/")
            id_match = id_re.match(request.Path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid per-student report request %s" % request.Path
            student = self.resolveStudent(id_match.group(1))
              
            return reports.tPerStudentReportHandler(
                student, degree_rule_sets_map)\
                .handleRequest(request.changePath(
                request.Path[id_match.end():]))

        def handlePerDegreeReports(request):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/")
            id_match = id_re.match(request.Path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid per-degree report request %s" % request.Path
            
            student, degree = self.resolveDegree(
                id_match.group(1),
                id_match.group(2))
              
            drs = degree_rule_sets_map[degree.DegreeRuleSet]
            report_handler = drs.getPerDegreeReportHandler(
                student, degree)

            return report_handler.handleRequest(request.changePath(
                request.Path[id_match.end():]))

        def handlePerExamReports(request):
            id_re = re.compile("^([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)/")
            id_match = id_re.match(request.Path)
            if not id_match:
                raise appserver.tNotFoundError, \
                      "Invalid per-exam report request %s" % request.Path
            
            student, degree, exam = self.resolveExam(
                id_match.group(1),
                id_match.group(2),
                id_match.group(3))
              
            drs = degree_rule_sets_map[degree.DegreeRuleSet]
            report_handler = drs.getPerExamReportHandler(
                student, degree, exam)

            return report_handler.handleRequest(request.changePath(
                request.Path[id_match.end():]))

        def handleStaticContent(request):
            fn_re = re.compile(r"^[-_a-zA-Z0-9]+\.([-_a-zA-Z0-9]+)$")
            fn_match = fn_re.match(request.Path)
            if not fn_match:
                raise appserver.tNotFoundError, \
                      "Invalid static content request %s" % path

            complete_fn = os.path.join("static",
                                       request.Path)
            ext = fn_match.group(1)
            if ext == "css":
                mime_type = "text/css"
            elif ext == "png":
                mime_type = "image/png"
            elif ext == "html":
                mime_type = "text/html"
            else:
                mime_type = "application/octet-stream"
                
            try:
                inf = file(complete_fn, "rb")
                content = inf.read()
                inf.close()
                
                return appserver.tHTTPResponse(
                    content, 200,
                    {"Content-type": mime_type})
            except IOError:
                raise appserver.tNotFoundError, \
                      "Static content `%s' not found" % path

        def redirectToStart(request):
            return appserver.tHTTPResponse(
                "", 302, {"Location": "/students/"})

        def doQuit(request):
            quitflag.set(True)
            return appserver.tHTTPResponse(
                "OK, wird beendet.",
                200,
                {"Content-type": "text/plain"})

        def doExportAll(request):
            store.exportAll()
            return appserver.tHTTPResponse(
                "Alle Daten erfolgreich exportiert.",
                200,
                {"Content-type": "text/plain"})

        return [
            ("^/students/", handleStudentDatabase),
            ("^/specsem/", handleSpecialSemesterDatabase),
            ("^/degrees/", handleDegreeDatabase),
            ("^/exams/", handleExamDatabase),
            ("^/report/global/", handleGlobalReports),
            ("^/report/perstudent/", handlePerStudentReports),
            ("^/report/perdegree/", handlePerDegreeReports),
            ("^/report/perexam/", handlePerExamReports),
            ("^/static/", handleStaticContent),
            ("^/students$", redirectToStart),
            ("^/quit$", doQuit),
            ("^/export-all$", doExportAll),
            ("^/$", redirectToStart)
            ]





# Main program ---------------------------------------------
opts, args = getopt.getopt(sys.argv[1:], [], 
                           ["allow-non-local",
                            "start-browser",
                            "create",
                            "debug-tex"])
if len(args) != 1:
    print "Benutzung: %s [Optionen] <Verzeichnis mit Studentendaten>" % sys.argv[0]
    print
    print "Optionen:"
    print "  --allow-non-local"
    print "      Nichtlokalen Zugriff erlauben (gefaehrlich!)"
    print "  --start-browser"
    print "      Automatisch einen Webbrowser starten"
    print "  --create"
    print "      Im angegebenen Verzeichnis eine Datenumgebung erzeugen,"
    print "      falls nicht vorhanden"
    print "  --debug-tex"
    print "      TeX-Dateien nach Bearbeitung nicht loeschen"
    sys.exit(1)

ALLOW_CREATE = False

for opt, value in opts:
    if opt == "--allow-non-local":
        print "WARNUNG: Nichtlokaler Zugriff wird zugelassen"
        ALLOW_NON_LOCAL = True
    if opt == "--start-browser":
        DO_START_BROWSER = True
    if opt == "--create":
        ALLOW_CREATE = True
    if opt == "--debug-tex":
        tools.TEX_DEBUG_MODE.set(True)


degree_rule_sets = [
    degreeruleset.tTemaVDAltDegreeRuleSet(),
    degreeruleset.tTemaHDAltDegreeRuleSet()
    ]

degree_rule_sets_map = {}
for drs in degree_rule_sets:
    degree_rule_sets_map[drs.id()] = drs

print "Lade Studentendaten...",
sys.stdout.flush()
store = datastore.tDataStore(args[0], 
                             degree_rule_sets_map,
                             allow_create = ALLOW_CREATE)
print "erledigt"
httpd = BaseHTTPServer.HTTPServer(('', LISTEN_PORT), 
                                  tMainAppServer)

url = "http://localhost:%d." % LISTEN_PORT
print "Horche nach Anfragen auf", url

if DO_START_BROWSER:
    # FIXME race condition
    import webbrowser

    webbrowser.open(url)
    print "Webbrowser gestartet"

quitflag = tools.tReference(False)
while not quitflag.get():
    httpd.handle_request()

print "Diplomatik wurde ordnungsgemaess beendet."

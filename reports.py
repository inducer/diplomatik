# -*- coding: utf-8 -*-

import re
import datetime
import math

import datamodel
import degreeruleset
import semester
import appserver
import tools
import os.path

from tools import tSubjectError




UNIBRIEF_INCLUDES = [os.path.join("unibrief", name) for name in 
                     ["unibrief.cls", "dinbrief.cls", "headerdata.tex", "unilogo.pdf"]] \
                     + ["variables.tex"]





class tReportHandler:
    def getList(self):
        return tools.tAssociativeList()

    def handleRequest(self, http_request):
        report_re = re.compile("^([-a-zA-Z0-9]+)\.([a-zA-Z0-9]+)$")
        report_match = report_re.match(http_request.Path)
        if not report_match:
            raise appserver.tNotFoundError, \
                  "Invalid report request %s" % http_request.Path

        report_id = report_match.group(1)
        format_id = report_match.group(2)
        if format_id != "pdf":
            raise appserver.tNotFoundError, \
                  "Formats besides PDF currently unsupported"

        fields, print_parms = self.getForm(report_id)

        if len(fields) == 0:
            return appserver.tHTTPResponse(
                self.getPDF(report_id, None),
                200,
                {"Content-type": "application/pdf"})
        else:
            title = self.getList()[report_id]

            if http_request.Method == "POST":
                valid = True
                for field in fields:
                    if not field.isValid(http_request.FormInput):
                        valid = False
                        break

                if valid:
                    for field in fields:
                        field.setValue(None, http_request.FormInput,
                                       print_parms)

                    return appserver.tHTTPResponse(
                        self.getPDF(report_id, print_parms),
                        200,
                        {"Content-type": "application/pdf"})
                else:
                    return appserver.tHTTPResponse(
                        tools.expandHTMLTemplate(
                        "print-form-validate.html",
                        {"fields": fields,
                         "title": title,
                         "obj": print_parms,
                         "input": http_request.FormInput}))
            else:
                return appserver.tHTTPResponse(
                    tools.expandHTMLTemplate(
                    "print-form.html",
                    {"fields": fields,
                     "title": title,
                     "obj": print_parms}))

    def getForm(self, report_id):
        return [], None

    def getPDF(self, report_id, form_data):
        raise KeyError, report_id




class tGlobalReportHandler(tReportHandler):
    def __init__(self, student_db, drs_map):
        self.StudentDB = student_db
        self.DRSMap = drs_map

    def getList(self):
        return tReportHandler.getList(self) + \
               tools.tAssociativeList([
            ("abschluesse", u"Abschlüsse in Zeitraum"),
            ("statistik-tema-hd-1983", "Statistik TeMa 83er PO"),
            ("statistik-tema-hd-2003", "Statistik TeMa 03er PO"),
            ("what-became-of", "Was ist geworden aus...?"),
            ])

    def getForm(self, report_id):
        if report_id in ["abschluesse", "statistik-tema-hd-1983", "statistik-tema-hd-2003"]:
            ws = semester.tSemester.now()
            if ws.Term == "s":
                ws = ws.previous()
            ss = ws.next()
            
            return [
                appserver.tDateField("From", "Von (einschl.)"),
                appserver.tDateField("To", "Bis (einschl.)"),
                ], tools.makeObject(
                {"From": ws.startDate(),
                 "To": ss.endDate()})
        elif report_id == "what-became-of":
            ay = semester.getAcademicYear(semester.tSemester.now())
            
            return [
                appserver.tFloatField("Year", "Jahrgang"),
                ], tools.makeObject(
                {"Year": ay})
        else:
            return tReportHandler.getForm(self, report_id)

    def getPDF(self, report_id, form_data):
        if report_id == "abschluesse":
            stud_deg = []
            for student in self.StudentDB.values():
                for degree in student.Degrees.values():
                    if degree.FinishedDate and \
                       form_data.From <= degree.FinishedDate <= form_data.To:
                        stud_deg.append((student, degree))

            def cmp_func_by_date(a, b):
                return cmp(a[1].FinishedDate,
                           b[1].FinishedDate)
            stud_deg.sort(cmp_func_by_date)

            return tools.runLatexOnTemplate(
                "abschluesse.tex",
                {"stud_deg": stud_deg,
                 "form_data": form_data,
                 "drs_map": self.DRSMap},
                ["header.tex", "variables.tex"])
        elif report_id.startswith("statistik-tema-hd-"):
            prefix = report_id.replace("statistik-", "")
            drs = self.DRSMap[prefix.replace("1983", "alt")]

            stud_deg = []
            for student in self.StudentDB.values():
                for degree in student.Degrees.values():
                    if degree.FinishedDate \
                         and form_data.From <= degree.FinishedDate <= form_data.To\
                         and degree.DegreeRuleSet == drs.id():

                        da = drs.getDiplomarbeit(student, degree)
                        pz = degree.FinishedDate - da.Date
                        sem = semester.countSemesters(
                            drs.getVordiplom(student).EnrolledSemester,
                            semester.tSemester.fromDate(
                            degree.FinishedDate))

                        data = {"Student": student,
                             "Degree": degree,
                             "Diplomarbeit": da,
                             "Gesamt": drs.getOverallGrade(student, degree),
                             "Pruefungszeitraum": int(math.ceil(pz.days/30.)),
                             "Semesters": sem-len(student.SpecialSemesters),
                             "SpecialSemesters": len(student.SpecialSemesters),
                             "TechFachName": degree.MinorSubject[:2],
                             }
                        if isinstance(drs, degreeruleset.tTema2003HDDegreeRuleSet):
                            data["Mathematik"] = drs.getMathGrade(student, degree)
                            data["TechFach"] = drs.getComponentAverageGrade(student, degree, "techfach")
                            data["Informatik"] = drs.getComponentAverageGrade(student, degree, "info")

                        elif isinstance(drs, degreeruleset.tTema1983HDDegreeRuleSet):
                            rm = drs.getComponentAverageGrade(student, degree, "rein")
                            am = drs.getComponentAverageGrade(student, degree, "angewandt")
                            nf1 = drs.getComponentAverageGrade(student, degree, "ing")
                            nf2 = drs.getComponentAverageGrade(student, degree, "inf")
                            pn = tools.roundGrade((rm+am+nf1+nf2)/4.)
                        
                            data["Rein"] = rm
                            data["Angewandt"] = am
                            data["NF1"] = nf1
                            data["NF2"] = nf2
                            data["Mathematik"] = pn
                        else:
                            raise RuntimeError, "Wrong tDegreeRuleSet type for statistics"
                        stud_deg.append(tools.makeObject(data))


            def cmp_func(a, b):
                return cmp(a.Degree.FinishedDate,
                           b.Degree.FinishedDate)
            stud_deg.sort(cmp_func)

            def countExamSource(degree, source):
                return len([1 for exam in sd.Degree.Exams.values()
                            if exam.Source == source
                            if exam.Counted])

            m_w = tools.histogram(
                [sd.Student.Gender for sd in stud_deg],
                {"m": 0, "w": 0})

            gesamt_hist = tools.histogram(
                [tools.gradeToWords(sd.Gesamt)
                 for sd in stud_deg],
                {"mit Auszeichnung": 0, 
                 "sehr gut": 0,
                 "gut": 0,
                 "befriedigend": 0})

            da_hist = tools.histogram(
                [tools.unifyGrade(sd.Diplomarbeit.CountedResult)
                 for sd in stud_deg])

            pn_hist = tools.histogram(
                [tools.unifyGrade(sd.Mathematik)
                 for sd in stud_deg])

            nf_hist = tools.histogram(
                [sd.Degree.MinorSubject for sd in stud_deg])

            sb_hist = tools.histogram(
                [countExamSource(sd.Degree, "freischuss")
                 for sd in stud_deg])

            sem_median = tools.median(
                [sd.Semesters for sd in stud_deg])

            pz_median = tools.median(
                [sd.Pruefungszeitraum for sd in stud_deg])

            ausland_count = len(
                [1 
                 for sd in stud_deg
                 if countExamSource(sd.Degree, "ausland") != 0])

            return tools.runLatexOnTemplate(
                "%s-statistik.tex" % prefix,
                {"stud_deg": stud_deg,
                 "form_data": form_data,
                 "drs_map": self.DRSMap,
                 "m_w": m_w,
                 "gesamt_hist": gesamt_hist,
                 "da_hist": da_hist,
                 "pn_hist": pn_hist,
                 "nf_hist": nf_hist,
                 "sb_hist": sb_hist,
                 "sem_median": sem_median,
                 "pz_median": pz_median,
                 "ausland_count": ausland_count,
                 "drs": drs,
                 })
        elif report_id == "what-became-of":
            year = int(form_data.Year)
            students = tools.sortBy(
                [student
                 for student in self.StudentDB.values()
                 if datamodel.academicYearOfStart(student) == year],
                "LastName")

            begun = {}
            finished = {}

            for student in students:
                for degree in student.Degrees.values():
                    drs_id = degree.DegreeRuleSet
                    begun[drs_id] = begun.setdefault(drs_id, 0) + 1
                    if degree.FinishedDate:
                        finished[drs_id] = finished.setdefault(drs_id, 0) + 1

            return tools.runLatexOnTemplate(
                "what-became-of.tex",
                {"year": year,
                 "students": students,
                 "begun": begun,
                 "finished": finished,
                 "drs_map": self.DRSMap},
                ["header.tex", "variables.tex"])

        else:
            return tReportHandler.getPDF(self, report_id, form_data)





def getTranscriptForm():
    return [
        appserver.tCheckField("IncludeFailed", 
                              u"Nicht bestandene Prüfungen einbeziehen?"),
        appserver.tCheckField("IncludeNonCounted", 
                              u"Nicht gewertete Prüfungen einbeziehen?"),
        ], tools.makeObject(
        {"IncludeFailed": True,
         "IncludeNonCounted": True})

def getTranscriptData(form_data, student, degree=None, drs=None, drs_map=None):
    def filter_func(exams):
        result = exams
        if not form_data.IncludeNonCounted:
            result = [exam for exam in result
                      if exam.Counted]
        if not form_data.IncludeFailed:
            result = [exam for exam in result
                      if exam.CountedResult < 5]
        print "YO", result
        return result

    def sort_func(drs, exams):
        exams = exams[:]

        def cmpexams(a, b):
            return cmp(
                (drs.mapComponentToSortKey(a.DegreeComponent), a.Date),
                (drs.mapComponentToSortKey(b.DegreeComponent), b.Date))
        exams.sort(cmpexams)
        return exams

    result = {"student": student,
              "filter_func": filter_func,
              "sort_func": sort_func,
              "include_non_counted": form_data.IncludeNonCounted}

    if degree:
        assert drs is not None
        result["degree"] = degree
        result["drs"] = drs
    else:
        assert drs_map is not None
        result["drs_map"] = drs_map

    return result




class tPerStudentReportHandler(tReportHandler):
    def __init__(self, student, drs_map):
        self.Student = student
        self.DRSMap = drs_map

    def getList(self):
        return tReportHandler.getList(self) + \
               tools.tAssociativeList([
            ("transcript", "Notenauszug")
            ])

    def getForm(self, report_id):
        if report_id == "transcript":
            return getTranscriptForm()
        else:
            return tReportHandler.getForm(self, report_id)

    def getPDF(self, report_id, form_data):
        if report_id == "transcript":
            return tools.runLatexOnTemplate(
                "transcript-complete.tex", 
                getTranscriptData(form_data, self.Student, drs_map=self.DRSMap),
                included_files=UNIBRIEF_INCLUDES)
        else:
            return tReportHandler.getPDF(self, report_id, form_data)





class tPerDegreeReportHandler(tReportHandler):
    def __init__(self, student, degree, drs):
        self.Student = student
        self.Degree = degree
        self.DegreeRuleSet = drs

    def getList(self):
        return tReportHandler.getList(self) + \
               tools.tAssociativeList([
            ("transcript", "Notenauszug (teilweise)")
            ])

    def getForm(self, report_id):
        if report_id == "transcript":
            return getTranscriptForm()
        else:
            return tReportHandler.getForm(self, report_id)

    def getPDF(self, report_id, form_data):
        if report_id == "transcript":
            return tools.runLatexOnTemplate(
                "transcript-single.tex", 
                getTranscriptData(form_data,
                                  self.Student, degree=self.Degree, 
                                  drs=self.DegreeRuleSet),
                included_files=UNIBRIEF_INCLUDES)
        else:
            return tReportHandler.getPDF(self, report_id, form_data)




class tPerExamReportHandler(tReportHandler):
    def __init__(self, student, degree, drs, exam):
        self.Student = student
        self.Degree = degree
        self.DegreeRuleSet = drs
        self.Exam = exam




class tTemaHDPerDegreeReportHandler(tPerDegreeReportHandler):
    def prefix(self):
        return self.DegreeRuleSet.id()

    def getList(self):
        return tPerDegreeReportHandler.getList(self) + \
               tools.tAssociativeList([
            ("hdfinal", u"Ausfertigung für die Prüfungsabteilung..."),
            ("overview", u"Übersichtszettel"),
            ("zulassung-leer", u"Zulassung zur Prüfung (blanko)"),
            ])

    def getZeugnisTeXDefs(self):
        return tools.expandTeXTemplate(
                "%s-defs-zeugnis.tex" % self.prefix(),
                self.getZeugnisData())

    def getPDF(self, report_id, form_data):
        if report_id == "hdfinal":
            drs = self.DegreeRuleSet

            vordiplom = drs.getVordiplom(self.Student)
            if not vordiplom.FinishedDate:
                raise tSubjectError, "Vordiplom nicht abgeschlossen"

            studienbeginn = datamodel.firstEnrollment(self.Student)
            studienbeginn_sem = semester.tSemester.fromDate(
                studienbeginn)
            if not self.Degree.FinishedDate:
                raise tSubjectError, "Enddatum HD nicht eingetragen"
            studienende_sem = semester.tSemester.fromDate(
                self.Degree.FinishedDate)
            semzahl = semester.countSemesters(
                studienbeginn_sem,
                studienende_sem)

            urlaubssem = len([1 for specsem in self.Student.SpecialSemesters.values()
                              if specsem.Type == "urlaub"])
            fachsem = semzahl - urlaubssem

            return tools.runLatexOnTemplate(
                "tema-hd-defs.tex",
                {"student": self.Student,
                 "degree": self.Degree,
                 "drs": drs,
                 "vddat": vordiplom.FinishedDate,
                 "semzahl": semzahl,
                 "studienbeginn_sem": studienbeginn_sem,
                 "zeugnis_defs": self.getZeugnisTeXDefs(),
                 "form": "%s-noten.tex" % self.prefix(),
                 "urlaubssem": urlaubssem,
                 "fachsem": fachsem,
                 },
                ["%s-noten.tex" % self.prefix(), "header.tex", "variables.tex",
                 "tema-hd-noten-kopf.tex"])

        elif report_id == "zulassung-leer":
            return tools.runLatexOnTemplate(
                "%s-pruefung-leer.tex" % self.prefix(),
                {"student": self.Student,
                 "degree": self.Degree,
                 "drs": self.DegreeRuleSet,
                 "today": datetime.date.today(),
                 },
                ["header.tex", "variables.tex"])

        elif report_id == "overview":
            data = {}
            data.update(self.getZeugnisData())
            counted_exams = [ex
                             for ex in self.Degree.Exams.values()
                             if ex.Counted]
            data["exams"] = tools.sortBy(counted_exams, "Date")

            data["math_complete"] = data["rein"] and data["angewandt"] \
                                    and (data["rein"].Credits + data["angewandt"].Credits) >= 28 \
                                    and min(data["rein"].Credits, data["angewandt"].Credits) >= 12

            return tools.runLatexOnTemplate(
                "%s-overview.tex" % self.prefix(),
                data,
                ["header.tex", "variables.tex"])

        else:
            return tPerDegreeReportHandler.getPDF(self, report_id, form_data)

    def gatherComponentData(self, comp):
        drs = self.DegreeRuleSet

        def getExaminer(exam):
            if exam.Source == "ausland":
                return "*"
            else:
                return exam.Examiner

        def getRemark(exam):
            if exam.Source == "ausland":
                return u"""
                (*) Teile der Prüfung wurden 
                an der %s abgelegt.""" % exam.SourceDescription
            else:
                return None

        exams = [exam
                 for exam in self.Degree.Exams.values()
                 if exam.DegreeComponent == comp
                 if exam.Counted]

        def date_sort_func(a, b):
            return cmp(a.Date, b.Date)
        exams.sort(date_sort_func)

        examiners = tools.uniq(
            [getExaminer(exam) for exam in exams])
        star_in_examiners = "*" in examiners
        if star_in_examiners:
            examiners.remove("*")
        examiners.sort()
        if star_in_examiners:
            examiners.append("*")

        return tools.makeObject({
            "Exams": u", ".join([
            exam.Description
            for exam in exams]),

            "AvgGrade": drs.getComponentAverageGrade(
            self.Student, self.Degree, comp),

            "WeightedGradeSum": drs.getWeightedGradeSum(
            self.Student, self.Degree, comp),

            "Credits": drs.getCreditsSum(
            self.Student, self.Degree, comp),

            "Examiners": ", ".join(examiners),

            "EndDate": 
            max([exam.Date for exam in exams]), 

            "Remarks": [ 
            getRemark(exam)
            for exam in exams
            if getRemark(exam)]
            })





class tTema1983HDPerDegreeReportHandler(tTemaHDPerDegreeReportHandler):
    def prefix(self):
        return "tema-hd-1983"

    def getZeugnisData(self):
        drs = self.DegreeRuleSet

        all_remarks = []

        data = {}
        for component in ["rein", "angewandt", "ing", "inf", "zusatz"]:
            try:
                data[component] = comp_data = self.gatherComponentData(component)
                all_remarks += comp_data.Remarks
            except tSubjectError:
                data[component] = None

        remarks = u"\\\\".join(
            [tools.escapeTeX(s) for s in tools.uniq(all_remarks)])

        try:
            data["diplomarbeit"]= drs.getDiplomarbeit(self.Student, self.Degree)
        except tSubjectError:
            data["diplomarbeit"] = None

        try:
            data["overall_grade"] = drs.getOverallGrade(self.Student, self.Degree)
        except tSubjectError, e:
            data["overall_grade"] = None

        data.update({"student": self.Student,
                     "degree": self.Degree,
                     "remarks": remarks,
                     })
        return data




class tTema2003HDPerDegreeReportHandler(tTemaHDPerDegreeReportHandler):
    def getZeugnisData(self):

        drs = self.DegreeRuleSet

        all_remarks = []

        data = {}
        for component in ["alggeo", "analysis", "numerik", "stochastik",
                          "techfach", "info", "zusatz"]:
            try:
                data[component] = comp_data = self.gatherComponentData(component)
                all_remarks += comp_data.Remarks
            except tSubjectError:
                data[component] = None

        remarks = u"\\\\".join(
            [tools.escapeTeX(s) for s in tools.uniq(all_remarks)])

        try:
            data["diplomarbeit"]= drs.getDiplomarbeit(self.Student, self.Degree)
        except tSubjectError:
            data["diplomarbeit"] = None

        try:
            data["overall_grade"] = drs.getOverallGrade(self.Student, self.Degree)
        except tSubjectError, e:
            print "ERROR", unicode(e).encode("latin1")
            data["overall_grade"] = None

        data.update({"student": self.Student,
                     "degree": self.Degree,
                     "remarks": remarks,
                     })
        return data





class tTemaHDPerExamReportHandler(tPerExamReportHandler):
    def prefix(self):
        return self.DegreeRuleSet.id()

    def getList(self):
        return tPerExamReportHandler.getList(self) + \
               tools.tAssociativeList([
            ("zulassung", u"Zulassung zur Prüfung")
            ])

    def getPDF(self, report_id, form_data):
        if report_id == "zulassung":
            return tools.runLatexOnTemplate(
                "%s-pruefung.tex" % self.prefix(),
                {"student": self.Student,
                 "drs": self.DegreeRuleSet,
                 "degree": self.Degree,
                 "exam": self.Exam,
                 "today": datetime.date.today(),
                 },
                ["header.tex", "variables.tex"])
        else:
            return tPerExamReportHandler.getPDF(self, report_id, form_data)




class tTema1983HDPerExamReportHandler(tTemaHDPerExamReportHandler):
    def prefix(self):
        return "tema-hd-1983";



class tTema2003HDPerExamReportHandler(tTemaHDPerExamReportHandler):
    pass

# -*- coding: utf-8 -*-

import re
import datetime
import math

import semester
import appserver
import tools

from tools import tSubjectError




class tReportHandler:
    def getList(self):
        return []

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
            title = tools.alistLookup(self.getList(),
                                      report_id)

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
        return tReportHandler.getList(self) + [
            ("abschluesse", u"Abschlüsse in Zeitraum"),
            ("statistik-temahdalt", "Statistik TeMa alte PO"),
            ]

    def getForm(self, report_id):
        if report_id in ["abschluesse", "statistik-temahdalt"]:
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

            def cmp_func(a, b):
                return cmp(a[1].FinishedDate,
                           b[1].FinishedDate)
            stud_deg.sort(cmp_func)

            return tools.runLatexOnTemplate(
                "abschluesse.tex",
                {"stud_deg": stud_deg,
                 "form_data": form_data,
                 "drs_map": self.DRSMap},
                ["header.tex"])
        elif report_id == "statistik-temahdalt":
            stud_deg = []
            for student in self.StudentDB.values():
                for degree in student.Degrees.values():
                    if degree.FinishedDate \
                         and form_data.From <= degree.FinishedDate <= form_data.To\
                         and degree.DegreeRuleSet == "tema-hd-alt":

                        drs = self.DRSMap[degree.DegreeRuleSet]
                        da = drs.getDiplomarbeit(student, degree)
                        rm = drs.getComponentAverageGrade(student, degree, "rein")
                        am = drs.getComponentAverageGrade(student, degree, "angewandt")
                        nf1 = drs.getComponentAverageGrade(student, degree, "1nf")
                        nf2 = drs.getComponentAverageGrade(student, degree, "2nf")
                        pn = (rm+am+nf1+nf2)/4.
                        gesamt = drs.getOverallGrade(student, degree)

                        sem = semester.countSemesters(
                            semester.tSemester.fromDate(
                            drs.getVordiplom(student).EnrolledDate),
                            semester.tSemester.fromDate(
                            degree.FinishedDate))

                        pz = degree.FinishedDate - da.Date

                        stud_deg.append(tools.makeObject(
                            {"Student": student,
                             "Degree": degree,
                             "Diplomarbeit": da,
                             "DRS": drs,
                             "Rein": rm,
                             "Angewandt": am,
                             "NF1": nf1,
                             "NF1Name": degree.MinorSubject[:2],
                             "NF2": nf2,
                             "Pruefungsnoten": pn,
                             "Gesamt": gesamt,
                             "Pruefungszeitraum": int(math.ceil(pz.days/30.)),
                             "Semesters": sem-len(student.SpecialSemesters),
                             "SpecialSemesters": len(student.SpecialSemesters),
                             }))


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
                [tools.gradeToWords(sd.Gesamt,
                                    use_distinction = True)
                 for sd in stud_deg],
                {"mit Auszeichnung": 0, 
                 "sehr gut": 0,
                 "gut": 0,
                 "befriedigend": 0})

            da_hist = tools.histogram(
                [tools.unifyGrade(sd.Diplomarbeit.CountedResult)
                 for sd in stud_deg])

            pn_hist = tools.histogram(
                [tools.unifyGrade(sd.Pruefungsnoten)
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
                "statistik-temahdalt.tex",
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
                 })
        else:
            return tReportHandler.getPDF(self, report_id, form_data)





class tPerStudentReportHandler(tReportHandler):
    def __init__(self, student, drs_map):
        self.Student = student
        self.DRSMap = drs_map

    def getList(self):
        return tReportHandler.getList(self) + [
            ("transcript", "Notenauszug")
            ]

    def getPDF(self, report_id, form_data):
        if report_id == "transcript":
            return tools.runLatexOnTemplate(
                "complete-transcript.tex",
                {"student": self.Student,
                 "drs_map": self.DRSMap})
        else:
            return tReportHandler.getPDF(self, report_id, form_data)





class tPerDegreeReportHandler(tReportHandler):
    def __init__(self, student, degree, drs):
        self.Student = student
        self.Degree = degree
        self.DegreeRuleSet = drs

    def getList(self):
        return tReportHandler.getList(self) + [
            ("transcript", "Notenauszug (teilweise)")
            ]

    def getPDF(self, report_id, form_data):
        if report_id == "transcript":
            return tools.runLatexOnTemplate(
                "degree-transcript.tex",
                {"student": self.Student,
                 "degree": self.Degree,
                 "drs": self.DegreeRuleSet})
        else:
            return tReportHandler.getPDF(self, report_id)




class tPerExamReportHandler(tReportHandler):
    def __init__(self, student, degree, drs, exam):
        self.Student = student
        self.Degree = degree
        self.DegreeRuleSet = drs
        self.Exam = exam




class tTeMaHDAltPerDegreeReportHandler(tPerDegreeReportHandler):
    def getList(self):
        return tPerDegreeReportHandler.getList(self) + [
            ("hdfinal", u"Ausfertigung für die Prüfungsabteilung...")
            ]

    def getPDF(self, report_id, form_data):
        if report_id == "hdfinal":
            def gatherComponent(comp):
                def getExaminer(exam):
                    if exam.Source == "ausland":
                        return exam.Examiner+"*"
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

                return tools.makeObject({
                    "Exams": u", ".join([
                    exam.Description
                    for exam in exams]),

                    "AvgGrade": drs.getComponentAverageGrade(
                    self.Student, self.Degree, comp),

                    "Examiners": u", ".join(tools.uniq(
                    [getExaminer(exam) for exam in exams])), 

                    "EndDate": 
                    max([exam.Date for exam in exams]), 

                    "Remarks": [ 
                    getRemark(exam)
                    for exam in exams
                    if getRemark(exam)]
                    })

            drs = self.DegreeRuleSet

            vordiplom = drs.getVordiplom(self.Student)
            if not vordiplom.FinishedDate:
                raise tSubjectError, "Vordiplom nicht abgeschlossen"

            studienbeginn = start = min([
                deg.EnrolledDate
                for deg in self.Student.Degrees.values()])
            studienbeginn_sem = semester.tSemester.fromDate(
                studienbeginn)
            if not self.Degree.FinishedDate:
                raise tSubjectError, "Enddatum HD nicht eingetragen"
            studienende_sem = semester.tSemester.fromDate(
                self.Degree.FinishedDate)
            semzahl = semester.countSemesters(
                studienbeginn_sem,
                studienende_sem)

            rein = gatherComponent("rein")
            angewandt = gatherComponent("angewandt")
            nf1 = gatherComponent("1nf")
            nf2 = gatherComponent("2nf")

            all_remarks = rein.Remarks + \
                          angewandt.Remarks + \
                          nf1.Remarks + \
                          nf2.Remarks
            try:
                zusatz = gatherComponent("zusatz")
                all_remarks += zusatz.Remarks
            except tSubjectError:
                zusatz = False

            remarks = u"\\\\".join(tools.uniq(all_remarks))

            da = drs.getDiplomarbeit(
                self.Student, self.Degree)
            overall_grade = drs.getOverallGrade(
                self.Student, self.Degree)
            
            return tools.runLatexOnTemplate(
                "hddefs.tex",
                {"student": self.Student,
                 "degree": self.Degree,
                 "podatum": "03.06.1983",
                 "popara": "\S 10 (2)",
                 "vddat": vordiplom.FinishedDate,
                 "semzahl": semzahl,
                 "studienbeginn_sem": studienbeginn_sem,
                 "rein": rein,
                 "angewandt": angewandt,
                 "nf1": nf1,
                 "nf2": nf2,
                 "zusatz": zusatz,
                 "da": da,
                 "remarks": remarks,
                 "overall_grade": overall_grade,
                 
                 "form": "noten-hd.tex",
                 },
                ["noten-hd.tex", "header.tex"])
            return tools.runLatexOnTemplate(
                "complete-transcript.tex",
                {"student": self.Student,
                 "drs_map": self.DRSMap})
        else:
            return tPerDegreeReportHandler.getPDF(self, report_id, form_data)





class tTeMaHDAltPerExamReportHandler(tPerExamReportHandler):
    def getList(self):
        return tPerExamReportHandler.getList(self) + [
            ("zulassung", u"Zulassung zur Prüfung")
            ]

    def getPDF(self, report_id, form_data):
        if report_id == "zulassung":
            return tools.runLatexOnTemplate(
                "temahdalt-pruefung.tex",
                {"student": self.Student,
                 "drs": self.DegreeRuleSet,
                 "degree": self.Degree,
                 "exam": self.Exam,
                 "today": datetime.date.today(),
                 "podatum": "03.06.1983",
                 "popara": "\S 10 (2)",
                 },
                ["header.tex"])
        else:
            return tPerExamReportHandler.getPDF(self, report_id, form_data)


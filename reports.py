# -*- coding: utf-8 -*-

import re

import semester
import appserver
import tools




class tReportHandler:
    def getList(self):
        return []

    def handleRequest(self, http_request):
        report_re = re.compile("^([a-zA-Z0-9]+)\.([a-zA-Z0-9]+)$")
        report_match = report_re.match(http_request.Path)
        if not report_match:
            raise appserver.tNotFoundError, \
                  "Invalid report request %s" % request.Path

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
            ("freischuesse", u"Studienbegleitende Prüfungen"),
            #("statistik", "Statistik"),
            ]

    def getForm(self, report_id):
        if report_id in ["abschluesse", "freischuesse"]:
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




class tTeMaHDAltReportHandler(tPerDegreeReportHandler):
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

                if len(exams) == 0:
                    return None
                       
                return tools.makeObject({
                    "Exams": u", ".join([
                    exam.Description
                    for exam in exams]),

                    "AvgGrade": sum([
                    tools.unifyGrade(exam.CountedResult) 
                    * exam.Credits
                    for exam in exams 
                    if exam.CountedResult and exam.Credits])\
                    / sum([ 
                    exam.Credits 
                    for exam in exams 
                    if exam.CountedResult and exam.Credits]), 

                    "Examiners": u", ".join(tools.uniq(
                    [getExaminer(exam) for exam in exams])), 

                    "EndDate": 
                    max([exam.Date for exam in exams]), 

                    "Remarks": [ 
                    getRemark(exam)
                    for exam in exams
                    if getRemark(exam)]
                    })

            vordiplome = [deg
                          for deg in self.Student.Degrees.values()
                          if deg.DegreeRuleSet == "tema-vd-alt"]
            if len(vordiplome) != 1:
                raise RuntimeError, "Anzahl Vordiplome ist ungleich eins"
            vordiplom = vordiplome[0]
            if not vordiplom.FinishedDate:
                raise RuntimeError, "Vordiplom nicht abgeschlossen"

            studienbeginn = start = min([
                deg.EnrolledDate
                for deg in self.Student.Degrees.values()])
            studienbeginn_sem = semester.tSemester.fromDate(
                studienbeginn)
            if not self.Degree.FinishedDate:
                raise RuntimeError, "Enddatum HD nicht eingetragen"
            studienende_sem = semester.tSemester.fromDate(
                self.Degree.FinishedDate)
            semzahl = semester.countSemesters(
                studienbeginn_sem,
                studienende_sem)

            rein = gatherComponent("rein")
            angewandt = gatherComponent("angewandt")
            nf1 = gatherComponent("1nf")
            nf2 = gatherComponent("2nf")
            zusatz = gatherComponent("zusatz")

            if not (rein and angewandt and nf1 and nf2):
                raise RuntimeError, "In einem der Pruefungsfaecher wurde " + \
                      "keine Pruefung absolviert."

            all_remarks = rein.Remarks + \
                          angewandt.Remarks + \
                          nf1.Remarks + \
                          nf2.Remarks
            if zusatz:
                all_remarks += zusatz.Remarks
            remarks = u"\\\\".join(tools.uniq(all_remarks))

            diplomarbeiten = [exam
                              for exam in self.Degree.Exams.values()
                              if exam.DegreeComponent == "diplomarbeit"]
            if len(diplomarbeiten) != 1:
                raise RuntimeError, "Anzahl Diplomarbeiten ist ungleich eins"
            da = diplomarbeiten[0]
            
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
                 
                 "form": "noten-hd.tex",
                 },
                ["noten-hd.tex", "header.tex"])
            return tools.runLatexOnTemplate(
                "complete-transcript.tex",
                {"student": self.Student,
                 "drs_map": self.DRSMap})
        else:
            return tPerDegreeReportHandler.getPDF(self, report_id, form_data)


# -*- coding: utf-8 -*-
import tools
import semester



class tReportHelper:
    def formatDate(self, date):
        return date.strftime("%d.%m.%Y")

    def formatNumber(self, format, number):
        return format % number

    def escapeTeX(self, value):
        return tools.escapeTeX(value)

    def gradeToWords(self, grade):
        if grade < 1.5:
            return "sehr gut"
        elif grade < 2.5:
            return "gut"
        elif grade < 3.5:
            return "befriedigend"
        elif grade <= 4:
            return "ausreichend"
        else:
            return "mangelhaft"

    def round(self, value, decimals):
        return round(value, decimals)





class tDegreeRuleSet:
    def __init__(self):
        pass

    def id(self):
        return "base"

    def description(self):
        return "base"
        
    def degreeComponents(self):
        return {} # [(id(str), description(str))]

    def examSources(self):
        return {} # [(id(str), description(str))]

    def isComplete(self, student):
        raise NotImplemented

    def perExamReports(self):
        return [] # [(id:str, description:str)]

    def doPerExamReport(self, id, student, degree, exam):
        raise KeyError, id

    def perDegreeReports(self):
        return [] # [(id:str, description:str)]

    def doPerDegreeReport(self, id, student, degree):
        raise KeyError, id

   



class tTemaVDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-vd-alt"

    def description(self):
        return "TeMa VD alt"
        
    def degreeComponents(self):
        return [
            ("ana", "Analysis"),
            ("la", "Lineare Algebra"),
            ("stoch", "Stochastik"),
            ("num", "Numerik"),
            ("scheine", "Scheine"),
            ]

    def examSources(self):
        return [
            ("uni", "Uni KA, regul&auml;r"),
            ("ausland", "Ausland"),
            ("andere", "Andere dt. Hochschule"),
            ]

    def isComplete(self, student):
        return False




class tTemaHDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-hd-alt"

    def description(self):
        return "TeMa HD alt"
        
    def degreeComponents(self):
        return [
            ("rein", "Reine Mathematik"),
            ("angewandt", "Angewandte Mathematik"),
            ("1nf", "Erstes Nebenfach"),
            ("2nf", "Angewandte Informatik"),
            ("diplomarbeit", "Diplomarbeit"),
            ("ueb-rein", "&Uuml;bungsschein reine Mathematik"),
            ("ueb-angewandt", "&Uuml;bungsschein angewandte Mathematik"),
            ("seminar", "Seminarschein"),
            ("zusatz", "Zusatzfach"),
            ]

    def examSources(self):
        return [
            ("uni", "Uni KA, regul&auml;r"),
            ("freischuss", "Uni KA, studienbegleitend"),
            ("ausland", "Ausland"),
            ("industrie", "Industrie"),
            ("andere", "Andere dt. Hochschule"),
            ]

    def isComplete(self, student):
        return False

    def perDegreeReports(self):
        return [
            ("hdfinal", "Ausfertigung f&uuml;r die Pr&uuml;fungsabteilung...")
            ]

    def doPerDegreeReport(self, id, student, degree):
        if id == "hdfinal":
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
                         for exam in degree.Exams.values()
                         if exam.DegreeComponent == comp]

                def date_sort_func(a, b):
                    return cmp(a.Date, b.Date)
                exams.sort(date_sort_func)

                if len(exams) == 0:
                    return None
                       
                return tools.makeObject({
                    "Exams": u", ".join([
                    exam.Description
                    for exam in exams
                    if exam.Counted]),

                    "AvgGrade": sum([
                    tools.unifyGrade(exam.CountedResult) 
                    * exam.Credits
                    for exam in exams 
                    if exam.CountedResult and exam.Credits])\
                    / sum([ 
                    exam.Credits 
                    for exam in exams 
                    if exam.CountedResult and exam.Credits]), 

                    "Examiners": u", ".join(
                    tools.uniq([ 
                    getExaminer(exam)
                    for exam in exams 
                    if exam.Counted])), 

                    "EndDate": max([ 
                    exam.Date 
                    for exam in exams 
                    if exam.Counted]), 

                    "Remarks": [ 
                    getRemark(exam)
                    for exam in exams
                    if exam.Counted
                    if getRemark(exam)]
                    })

            vordiplome = [deg
                          for deg in student.Degrees.values()
                          if deg.DegreeRuleSet == "tema-vd-alt"]
            if len(vordiplome) != 1:
                raise RuntimeError, "Anzahl Vordiplome ist ungleich eins"
            vordiplom = vordiplome[0]
            if not vordiplom.FinishedDate:
                raise RuntimeError, "Vordiplom nicht abgeschlossen"

            studienbeginn = start = min([
                deg.EnrolledDate
                for deg in student.Degrees.values()])
            studienbeginn_sem = semester.tSemester.fromDate(
                studienbeginn)
            if not degree.FinishedDate:
                raise RuntimeError, "Enddatum HD nicht eingetragen"
            studienende_sem = semester.tSemester.fromDate(
                degree.FinishedDate)
            semzahl = semester.countSemesters(
                studienbeginn_sem,
                studienende_sem)

            rein = gatherComponent("rein")
            angewandt = gatherComponent("angewandt")
            nf1 = gatherComponent("1nf")
            nf2 = gatherComponent("2nf")
            zusatz = gatherComponent("zusatz")

            all_remarks = rein.Remarks + \
                          angewandt.Remarks + \
                          nf1.Remarks + \
                          nf2.Remarks
            if zusatz:
                all_remarks += zusatz.Remarks
            remarks = u"\\\\".join(tools.uniq(all_remarks))

            diplomarbeiten = [exam
                              for exam in degree.Exams.values()
                              if exam.DegreeComponent == "diplomarbeit"]
            if len(diplomarbeiten) != 1:
                raise RuntimeError, "Anzahl Diplomarbeiten ist ungleich eins"
            da = diplomarbeiten[0]
            
            return tools.runLatexOnTemplate("hddefs.tex",
                                            {"student": student,
                                             "degree": degree,
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
                                             "h": tReportHelper(),
                                             },
                                            ["noten-hd.tex", "header.tex"])
        else:
            raise KeyError, id

# -*- coding: utf-8 -*-
import tools
import semester



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

    def perExamReports(self):
        return [] # [(id:str, description:str)]

    def doPerExamReport(self, id, student, degree, exam):
        raise KeyError, id

    def perDegreeReports(self):
        return [
            ("transcript", "Notenauszug (teilweise)")
            ] # [(id:str, description:str)]

    def doPerDegreeReport(self, id, student, degree):
        if id == "transcript":
            return tools.runLatexOnTemplate(
                "degree-transcript.tex",
                {"student": student,
                 "degree": degree,
                 "drs": self})
        else:
            raise KeyError, id

   



class tTemaVDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-vd-alt"

    def description(self):
        return "Technomathematik Vordiplom/PO vom 03.06.1983"
        
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
            ("uni", "Uni Karlsruhe"),
            ("ausland", "Ausland"),
            ("andere", "Andere dt. Hochschule"),
            ]




class tTemaHDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-hd-alt"

    def description(self):
        return "Technomathematik Hauptdiplom/PO vom 03.06.1983"
        
    def degreeComponents(self):
        return [
            ("rein", "Reine Mathematik"),
            ("angewandt", "Angewandte Mathematik"),
            ("1nf", "Erstes Nebenfach"),
            ("2nf", "Angewandte Informatik"),
            ("diplomarbeit", "Diplomarbeit"),
            ("ueb-rein", u"Übung Reine Mathematik"),
            ("ueb-angewandt", u"Übung Angewandte Mathematik"),
            ("seminar", "Seminar"),
            ("zusatz", "Zusatzfach"),
            ]

    def examSources(self):
        return [
            ("uni", "Uni Karlsruhe"),
            ("freischuss", "Uni Karlsruhe, studienbegleitend"),
            ("ausland", "Ausland"),
            ("industrie", "Industrie"),
            ("andere", "Andere dt. Hochschule"),
            ]

    def perDegreeReports(self):
        return tDegreeRuleSet.perDegreeReports(self)+ [
            ("hdfinal", u"Ausfertigung für die Prüfungsabteilung...")
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
                              for exam in degree.Exams.values()
                              if exam.DegreeComponent == "diplomarbeit"]
            if len(diplomarbeiten) != 1:
                raise RuntimeError, "Anzahl Diplomarbeiten ist ungleich eins"
            da = diplomarbeiten[0]
            
            return tools.runLatexOnTemplate(
                "hddefs.tex",
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
                 },
                ["noten-hd.tex", "header.tex"])
        else:
            return tDegreeRuleSet.doPerDegreeReport(
                self, id, student, degree)




def perStudentReports():
    return [
        ("transcript", "Notenauszug")
        ]




def doPerStudentReport(id, student, drs_map):
    if id == "transcript":
        return tools.runLatexOnTemplate("complete-transcript.tex",
                                        {"student": student,
                                         "drs_map": drs_map})
    else:
        return KeyError, id




def globalReports():
    return [
        ("abschluesse", "Abschlüsse in Zeitraum"),
        ("freischuesse", "Studienbegleitende Prüfungen"),
        ("statistik", "Statistik"),
        ]


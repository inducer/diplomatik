import tools
import semester




class tReportHelper:
    def formatDate(self, date):
        return date.strftime("%d.%m.%Y")




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
            
            return tools.runLatexOnTemplate("hddefs.tex",
                                            {"student": student,
                                             "degree": degree,
                                             "podatum": "03.06.1983",
                                             "popara": "\S 10 (2)",
                                             "vddat": vordiplom.FinishedDate,
                                             "semzahl": semzahl,
                                             "studienbeginn_sem": studienbeginn_sem,

                                             "form": "noten-hd.tex",
                                             "helper": tReportHelper(),
                                             },
                                            ["noten-hd.tex", "header.tex"])
        else:
            raise KeyError, id

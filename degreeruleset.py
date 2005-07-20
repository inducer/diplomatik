# -*- coding: utf-8 -*-

import tools
import reports
import datetime

from tools import tSubjectError




class tDegreeRuleSet(object):
    def __init__(self):
        pass

    def id(self):
        return "base"

    def description(self):
        return "base"
        
    def TeXtitle(self):
        return tools.escapeTeX(self.description())

    def minorSubjectDescription(self):
        return "Nebenfach"
        
    def creditsUnitDescription(self):
        """Returns a triple of
        - symbolic identifier (only lowercase letters, no spaces or numbers),
        - short description, and
        - long description
        of the used credit point system.  The symbolic identifier is only used
        to identify the system and not print the corresponding explaining footnote
        twice or more often.
        """
        return ("none", "CP", "Credit Points")
        
    def degreeComponents(self):
        """Returns an associative list that enumerates the types of
        exams that count towards this degree.

        An example:
        tools.tAssoicativeList(
        [("applied", "Applied Mathematics"),
         ("pure", "Pure Mathematics"),
         ])
        
        Note that the identifiers must be usable as TeX
        control sequence names and may thus only
        consist of upper and lower case letters.
        """
        return tools.tAssociativeList()

    def mapComponentToSortKey(self, comp_id):
        """Get a value that can serve as a sensible sort key for
        the degree components.

        Sorry---This method had to be added as an afterthought, since
        some component IDs that were already in deployment were not
        alphabetized to ensure correct sort order.

        Of course, you don't need to reimplement this if your component
        IDs already have the right order.
        """
        return comp_id

    def examSources(self):
        # id:str -> description:str
        return tools.tAssociativeList 

    def expectedExamCount(self, component):
        raise NotImplementedError

    def getExportData(self, student, degree):
        return ""

    def getCreditsSum(self, student, degree, component):
        exams = [exam
                 for exam in degree.Exams.values()
                 if exam.DegreeComponent == component
                 if exam.Counted
                 if exam.CountedResult and exam.Credits]

        return sum([exam.Credits for exam in exams])

    def getWeightedGradeSum(self, student, degree, component):
        exams = [exam
                 for exam in degree.Exams.values()
                 if exam.DegreeComponent == component
                 if exam.Counted
                 if exam.CountedResult and exam.Credits]
        return sum([exam.CountedResult
                    * exam.Credits
                    for exam in exams])

    def getComponentAverageGrade(self, student, degree, component):
        grade_sum = self.getWeightedGradeSum(student, degree, component)
        credits = self.getCreditsSum(student, degree, component)

        if credits == 0:
            raise tSubjectError, \
                  "Student %s hat in Komponente %s keine Pruefungen abgelegt" \
                  % (student.LastName, component)

        return tools.roundGrade(grade_sum / credits)

    def getOverallGrade(self, student, degree):
        raise NotImplementedError

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tPerExamReportHandler(
            student, degree, self, exam)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tPerDegreeReportHandler(
            student, degree, self)

   



class tTema1983VDDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-vd-alt"

    def description(self):
        return "Technomathematik Vordiplom/PO vom 03.06.1983"

    def TeXtitle(self):
        return "Technomathematik Vordiplom\\footnote{Pr\\\"ufungsordnung vom 03.06.1983}"
        
    def minorSubjectDescription(self):
        return "Technisches Nebenfach"
        
    def creditsUnitDescription(self):
        return ("sws", "SWS", "Semesterwochenstunden")
        
    def degreeComponents(self):
        return tools.tAssociativeList([
            ("ana", "Analysis"),
            ("la", "Lineare Algebra"),
            ("stoch", "Stochastik"),
            ("num", "Numerik"),
            ("techfach", "Technisches Fach"),
            ("info", "Angewandte Informatik"),
            ("scheine", "Scheine"),
            ])

    def examSources(self):
        return tools.tAssociativeList([
            ("uni", "Uni Karlsruhe"),
            ("ausland", "Ausland"),
            ("andere", "Andere dt. Hochschule"),
            ])

    def expectedExamCount(self, component):
        if component == "scheine":
            return 2
        else:
            return 1




class tTema2003VDDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-vd-2003"

    def description(self):
        return "Technomathematik Vordiplom/PO vom 10.09.2003"

    def TeXtitle(self):
        return "Technomathematik Vordiplom\\footnote{Neue Pr\\\"ufungsordnung vom 10.09.2003}"
        
    def minorSubjectDescription(self):
        return "Technisches Nebenfach"
        
    def creditsUnitDescription(self):
        return ("sws", "SWS", "Semesterwochenstunden")
        
    def degreeComponents(self):
        return tools.tAssociativeList([
            ("ana", "Analysis"),
            ("la", "Lineare Algebra"),
            ("stoch", "Stochastik"),
            ("num", "Numerik"),
            ("techfach", "Technisches Fach"),
            ("info", "Angewandte Informatik"),
            ("scheine", "Scheine"),
            ])

    def examSources(self):
        return tools.tAssociativeList([
            ("uni", "Uni Karlsruhe"),
            ("ausland", "Ausland"),
            ("andere", "Andere dt. Hochschule"),
            ])

    def expectedExamCount(self, component):
        if component == "scheine":
            return 2
        elif component == "techfach":
            return 4
        else:
            return 1




class tTemaHDDegreeRuleSet(tDegreeRuleSet):
    def creditsUnitDescription(self):
        return ("sws", "SWS", "Semesterwochenstunden")
        
    def examSources(self):
        return tools.tAssociativeList([
            ("uni", "Uni Karlsruhe"),
            ("freischuss", "Uni Karlsruhe, studienbegleitend"),
            ("ausland", "Ausland"),
            ("industrie", "Industrie"),
            ("andere", "Andere dt. Hochschule"),
            ])

    def getExportData(self, student, degree):
        rephand = self.getPerDegreeReportHandler(student, degree)
        try:
            return rephand.getZeugnisTeXDefs()
        except tSubjectError:
            return "% degree-specific export failed"

    def getVordiplom(self, student):
        vd_drs_id = self.id().replace("hd", "vd")
        vds = [degree
               for degree in student.Degrees.values()
               if degree.DegreeRuleSet == vd_drs_id
               if degree.FinishedDate]
        
        if len(vds) != 1:
            raise tSubjectError, \
                  "Student %s: Anzahl beendeter TeMa-Vordiplome ist ungleich eins" \
                  % student.LastName

        return vds[0]

    def getDiplomarbeit(self, student, degree):
        assert degree.DegreeRuleSet == self.id()

        diplomarbeiten = [exam
                          for exam in degree.Exams.values()
                          if exam.DegreeComponent == "diplomarbeit"
                          if exam.Counted and exam.CountedResult]
        if len(diplomarbeiten) != 1:
            raise tSubjectError, \
                  "Student %s: Anzahl benoteter, gewerteter Diplomarbeiten " \
                  "ist ungleich eins" \
                  % student.LastName
        return diplomarbeiten[0]





class tTema1983HDDegreeRuleSet(tTemaHDDegreeRuleSet):
    def id(self):
        return "tema-hd-alt"

    def description(self):
        return "Technomathematik Hauptdiplom/PO vom 03.06.1983"
        
    def TeXtitle(self):
        return "Technomathematik Hauptdiplom\\footnote{Pr\\\"ufungsordnung vom 03.06.1983}"

    def minorSubjectDescription(self):
        return "Technisches Nebenfach"

    def degreeComponents(self):
        return tools.tAssociativeList([
            ("rein", "Reine Mathematik"),
            ("angewandt", "Angewandte Mathematik"),
            ("ing", "Technisches Nebenfach"),
            ("inf", "Angewandte Informatik"),
            ("diplomarbeit", "Diplomarbeit"),
            ("uebrein", u"Übung Reine Mathematik"),
            ("uebangewandt", u"Übung Angewandte Mathematik"),
            ("seminar", "Seminar"),
            ("mrp", "Programmierpraktikum"),
            ("zusatz", "Zusatzfach"),
            ])

    def mapComponentToSortKey(self, comp_id):
        return {
            "diplomarbeit": 0,
            "rein": 10,
            "uebrein":15,
            "angewandt": 20,
            "uebangewandt":25,
            "ing": 30,
            "inf": 40,
            "seminar": 50,
            "mrp": 60,
            "zusatz": 70}[comp_id]

    def expectedExamCount(self, component):
        if component in ["rein",
                         "angewandt",
                         "ing",
                         "inf"]:
            return 5
        else:
            return 1

    def getOverallGrade(self, student, degree):
        assert degree.DegreeRuleSet == self.id()

        rm = self.getComponentAverageGrade(student, degree, "rein")
        am = self.getComponentAverageGrade(student, degree, "angewandt")
        nf1 = self.getComponentAverageGrade(student, degree, "ing")
        nf2 = self.getComponentAverageGrade(student, degree, "inf")
        da = self.getDiplomarbeit(student, degree)
        return tools.roundGrade((rm+am+nf1+nf2+2.*da.CountedResult)/6.,1)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tTema1983HDPerDegreeReportHandler(
            student, degree, self)

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tTema1983HDPerExamReportHandler(
            student, degree, self, exam)




class tTema2003HDDegreeRuleSet(tTemaHDDegreeRuleSet):
    def id(self):
        return "tema-hd-2003"

    def description(self):
        return "Technomathematik Hauptdiplom/PO vom 10.09.2003"
        
    def TeXtitle(self):
        return "Technomathematik Hauptdiplom\\footnote{Neue Pr\\\"ufungsordnung vom 10.09.2003}"

    def minorSubjectDescription(self):
        return "Technisches Nebenfach"
        
    def degreeComponents(self):
        return tools.tAssociativeList([
            ("alggeo", "Algebra/Geometrie"),
            ("analysis", "Analysis"),
            ("numerik", "Numerik/Wiss. Rechnen"),
            ("stochastik", "Stochastik"),
            ("techfach", "Technisches Nebenfach"),
            ("info", "Angewandte Informatik"),
            ("diplomarbeit", "Diplomarbeit"),
            ("seminar", "Seminar"),
            ("uebung", u"Übungsschein"),
            ("progpraktikum", "Programmierpraktikum"),
            ("zusatz", "Zusatzfach"),
            ])

    def mapComponentToSortKey(self, comp_id):
        return {
            "diplomarbeit": 0,
            "alggeo": 10,
            "analysis":20,
            "numerik": 30,
            "stochastik": 40,
            "uebung": 50,
            "seminar": 60,
            "techfach": 70,
            "info": 80,
            "progpraktikum": 90,
            "zusatz": 100}[comp_id]

    def expectedExamCount(self, component):
        if component in ["alggeo",
                         "ana",
                         "num",
                         "stoch"]:
            return 3
        else:
            return 1

    def getMathPool(self, student, degree):
        assert degree.DegreeRuleSet == self.id()

        math_pool = []
        for comp in ["alggeo", "analysis", "numerik", "stochastik"]:
            try:
                math_pool.append(self.getComponentAverageGrade(student, degree, comp))
            except tSubjectError:
                pass

        if len(math_pool) != 3:
            raise tSubjectError, u"Student %s: Anzhal mathematischer Fächer ungleich drei" \
                  % student.LastName
        return math_pool

    def getMathGrade(self, student, degree):
        math_pool = self.getMathPool(student, degree)
        return tools.roundGrade((sum(math_pool))/3.,1)

    def getOverallGrade(self, student, degree):
        math_pool = self.getMathPool(student, degree)

        techfach = self.getComponentAverageGrade(student, degree, "techfach")
        info = self.getComponentAverageGrade(student, degree, "info")
        da = self.getDiplomarbeit(student, degree)
        return tools.roundGrade((sum(math_pool)+techfach+info+2.*da.CountedResult)/7.,1)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tTema2003HDPerDegreeReportHandler(
            student, degree, self)

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tTema2003HDPerExamReportHandler(
            student, degree, self, exam)

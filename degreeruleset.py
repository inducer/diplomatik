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

    def examSources(self):
        # id:str -> description:str
        return tools.tAssociativeList 

    def expectedExamCount(self, component):
        raise NotImplementedError

    def getExportData(self, student, degree):
        return ""

    def getComponentAverageGrade(self, student, degree, component):
        exams = [exam
                 for exam in degree.Exams.values()
                 if exam.DegreeComponent == component
                 if exam.Counted
                 if exam.CountedResult and exam.Credits]

        credits = sum([exam.Credits for exam in exams])
        if credits == 0:
            raise tSubjectError, \
                  "Student %s hat in Komponente %s keine Pruefungen abgelegt" \
                  % (student.LastName, component)
        grade_sum = sum([
                    tools.unifyGrade(exam.CountedResult) 
                    * exam.Credits
                    for exam in exams])

        return tools.roundGrade(grade_sum / credits)

    def getOverallGrade(self, student, degree):
        raise NotImplementedError

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tPerExamReportHandler(
            student, degree, self, exam)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tPerDegreeReportHandler(
            student, degree, self)

    def ruleSetDate(self):
        raise NotImplementedError



   



class tTemaVDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-vd-alt"

    def description(self):
        return "Technomathematik Vordiplom/PO vom 03.06.1983"
        
    def degreeComponents(self):
        return tools.tAssociativeList([
            ("ana", "Analysis"),
            ("la", "Lineare Algebra"),
            ("stoch", "Stochastik"),
            ("num", "Numerik"),
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

    def ruleSetDate(self):
        return datetime.date(1983, 6, 3)



class tTemaHDAltDegreeRuleSet(tDegreeRuleSet):
    def __init__(self):
        tDegreeRuleSet.__init__(self)

    def id(self):
        return "tema-hd-alt"

    def description(self):
        return "Technomathematik Hauptdiplom/PO vom 03.06.1983"
        
    def degreeComponents(self):
        return tools.tAssociativeList([
            ("rein", "Reine Mathematik"),
            ("angewandt", "Angewandte Mathematik"),
            ("ing", "Erstes Nebenfach"),
            ("inf", "Angewandte Informatik"),
            ("diplomarbeit", "Diplomarbeit"),
            ("uebrein", u"Übung Reine Mathematik"),
            ("uebangewandt", u"Übung Angewandte Mathematik"),
            ("seminar", "Seminar"),
            ("mrp", "Mikrorechnerpraktikum"),
            ("zusatz", "Zusatzfach"),
            ])

    def examSources(self):
        return tools.tAssociativeList([
            ("uni", "Uni Karlsruhe"),
            ("freischuss", "Uni Karlsruhe, studienbegleitend"),
            ("ausland", "Ausland"),
            ("industrie", "Industrie"),
            ("andere", "Andere dt. Hochschule"),
            ])

    def expectedExamCount(self, component):
        if component in ["rein",
                         "angewandt",
                         "ing",
                         "inf"]:
            return 5
        else:
            return 1

    def getExportData(self, student, degree):
        rephand = self.getPerDegreeReportHandler(
            student, degree)
        try:
            return rephand.getZeugnisTeXDefs()
        except tSubjectError:
            return "% degree-specific export failed"

    def getVordiplom(self, student):
        vds = [degree
               for degree in student.Degrees.values()
               if degree.DegreeRuleSet == "tema-vd-alt"
               if degree.FinishedDate]
        
        for degree in student.Degrees.values():
            print student.ID, degree.DegreeRuleSet

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
                  "Student %s: Anzahl benoteter Diplomarbeiten ist ungleich eins" \
                  % student.LastName
        return diplomarbeiten[0]

    def getOverallGrade(self, student, degree):
        assert degree.DegreeRuleSet == self.id()

        rm = self.getComponentAverageGrade(student, degree, "rein")
        am = self.getComponentAverageGrade(student, degree, "angewandt")
        nf1 = self.getComponentAverageGrade(student, degree, "ing")
        nf2 = self.getComponentAverageGrade(student, degree, "inf")
        da = self.getDiplomarbeit(student, degree)
        return round((rm+am+nf1+nf2+2.*da.CountedResult)/6.,1)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tTeMaHDAltPerDegreeReportHandler(
            student, degree, self)

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tTeMaHDAltPerExamReportHandler(
            student, degree, self, exam)

    def ruleSetDate(self):
        return datetime.date(1983, 6, 3)


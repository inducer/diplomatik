# -*- coding: utf-8 -*-

import tools
import semester
import reports

from tools import tSubjectError




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

        return grade_sum / credits

    def getOverallGrade(self, student, degree):
        raise NotImplementedError

    def getPerExamReportHandler(self, student, degree, exam):
        return reports.tPerDegreeReportHandler(
            student, degree, self, exam)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tPerDegreeReportHandler(
            student, degree, self)


   



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

    def getVordiplom(self, student):
        vds = [degree
               for degree in student.Degrees.values()
               if degree.DegreeRuleSet == "tema-vd-alt"
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
                  "Student %s: Anzahl benotete Diplomarbeiten ist ungleich eins" \
                  % student.LastName
        return diplomarbeiten[0]

    def getOverallGrade(self, student, degree):
        assert degree.DegreeRuleSet == self.id()

        rm = self.getComponentAverageGrade(student, degree, "rein")
        am = self.getComponentAverageGrade(student, degree, "angewandt")
        nf1 = self.getComponentAverageGrade(student, degree, "1nf")
        nf2 = self.getComponentAverageGrade(student, degree, "2nf")
        da = self.getDiplomarbeit(student, degree)
        return round((rm+am+nf1+nf2+2.*da.CountedResult)/6.,1)

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tTeMaHDAltReportHandler(
            student, degree, self)


# -*- coding: utf-8 -*-

import tools
import semester
import reports



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

    def getPerDegreeReportHandler(self, student, degree):
        return reports.tTeMaHDAltReportHandler(
            student, degree, self)


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

    def doPerExamReport(self, id, student, exam):
        pass

    def perStudentReports(self):
        return [] # [(id:str, description:str)]

    def doPerStudentReport(self, id, student):
        pass

    def globalReports(self):
        return [] # [(id:str, description:str)]
    
    def doGlobalReport(self, name):
        pass




class tTemaVDAltDegreeRuleSet:
    def __init__(self):
        pass

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

    def perExamReports(self):
        return []

    def doPerExamReport(self, id, student, exam):
        pass

    def perStudentReports(self):
        return []

    def doPerStudentReport(self, id, student):
        pass

    def globalReports(self):
        return []
    
    def doGlobalReport(self, name):
        pass




class tTemaHDAltDegreeRuleSet:
    def __init__(self):
        pass

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

    def perExamReports(self):
        return []

    def doPerExamReport(self, id, student, exam):
        pass

    def perStudentReports(self):
        return []

    def doPerStudentReport(self, id, student):
        pass

    def globalReports(self):
        return []
    
    def doGlobalReport(self, name):
        pass

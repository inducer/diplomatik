class tDegreeRuleSet:
    def __init__(self):
        pass

    def id(self):
        return "base"

    def description(self):
        return "base"
        
    def degreeComponents(self):
        return {} # {id(str): description(str)}

    def isDegreeComplete(self, student):
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




import yaml
import os
import os.path
import stat
import codecs
import datetime



def dateToYaml(date):
    if date is None:
        return None
    else:
        return {"year": date.year,
                "month": date.month,
                "day": date.day}

def dateFromYaml(date):
    if date is None:
        return None
    else:
        return datetime.date(date["year"], 
                             date["month"], 
                             date["day"])

    

class tExam:
    def __init__(self):
        self.Date = None # timestamp
        self.Semester = None
        self.Description = "" # str
        self.DegreeComponent = None # str
        self.Examiner = "" # str
        self.NativeResult = None # str
        self.CountedResult = None # float
        self.Credits = None # float, like SWS
        self.CreditsPrintable = None # str, like "3+1"
        self.Remarks = "" # str

    def to_yaml(self):
        result = self.__dict__.copy()
        result["Date"] = dateToYaml(self.Date)
        return (result, "!!datamodel.tExam")

    def from_yaml(self, new_dict):
        self.__dict__.update(new_dict)
        self.Date = dateFromYaml(self.Date)
        return self



class tDegree:
    def __init__(self):
        self.EnrolledDate = None 
        self.FinishedDate = None
        self.Exams = {}
        self.DegreeRuleSet = None # str
        self.Remark = "" # str

    def degreeComponents(self):
        result = []
        for exam in self.Exams:
            if exam.DegreeRuleSet not in result:
                result.append(exam.DegreeRuleSet)
        return result

    def to_yaml(self):
        result = self.__dict__.copy()
        result["EnrolledDate"] = dateToYaml(self.EnrolledDate)
        result["FinishedDate"] = dateToYaml(self.FinishedDate)
        return (result, "!!datamodel.tDegree")

    def from_yaml(self, new_dict):
        self.__dict__.update(new_dict)
        self.EnrolledDate = dateFromYaml(self.EnrolledDate)
        self.FinishedDate = dateFromYaml(self.FinishedDate)
        return self



class tStudent:
    def __init__(self):
        self.ID = None # str
        self.FirstName = ""
        self.MiddleName = ""
        self.LastName = ""
        self.VacationSemesters = [] # list of semesters
        self.DateOfBirth = None
        self.Degrees = {}
        self.Notes = "" # str
        self.Email = "" # str

    def to_yaml(self):
        result = self.__dict__.copy()
        result["DateOfBirth"] = dateToYaml(self.DateOfBirth)
        return (result, "!!datamodel.tStudent")

    def from_yaml(self, new_dict):
        if "Notes" not in new_dict:
            self.Notes = ""
        if "Email" not in new_dict:
            self.Email = ""
        self.__dict__.update(new_dict)
        self.DateOfBirth = dateFromYaml(self.DateOfBirth)
        return self



class tDataStore:
    def __init__(self, directory, degree_rule_sets):
        self.Directory = directory
        self.Students = {}
        for fn in os.listdir(directory):
            complete_fn = os.path.join(directory, fn)
            if stat.S_ISREG(os.stat(complete_fn).st_mode):
                student = yaml.loadFile(complete_fn).next() 
                self.Students[student.ID] = student
           
    def keys(self):
        return self.Students.keys()

    def __getitem__(self, key):
        return self.Students[key]

    def __setitem__(self, key, student):
        self.Students[student.ID] = student
        self.writeStudent(key)

    def __delitem__(self, key):
        del self.Students[key]
        filename = os.path.join(self.Directory, key)
        os.unlink(filename)

    def writeStudent(self, key):
        student = self.Students[key]
        assert key == student.ID
        
        filename = os.path.join(self.Directory, student.ID)
        yaml.dumpToFile(file(filename, "wb"), 
                        student)

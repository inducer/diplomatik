import yaml
import os
import os.path
import stat
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
        self.Description = "" # str
        self.DegreeComponent = None # str
        self.Examiner = "" # str
        self.Counted = True # bool
        self.Source = None # str-key
        self.SourceDescription = "" # str
        self.NativeResult = None # str
        self.CountedResult = None # float or None
        self.Credits = None # float or None, like SWS
        self.CreditsPrintable = None # str, like "3+1"
        self.Remarks = "" # str

    def to_yaml(self):
        result = self.__dict__.copy()
        result["Date"] = dateToYaml(self.Date)
        return (result, "!!datamodel.tExam")

    def from_yaml(self, new_dict):
        if "Counted" not in new_dict:
            self.Counted = True
        if "Source" not in new_dict:
            self.Source = None
        if "SourceDescription" not in new_dict:
            self.SourceDescription = ""
        self.__dict__.update(new_dict)
        self.Date = dateFromYaml(self.Date)
        return self



class tDegree:
    def __init__(self):
        self.EnrolledDate = None 
        self.FinishedDate = None
        self.MinorSubject = ""
        self.Exams = {}
        self.DegreeRuleSet = None # str-key
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
        if "MinorSubject" not in new_dict:
            self.MinorSubject = ""

        self.__dict__.update(new_dict)
        self.EnrolledDate = dateFromYaml(self.EnrolledDate)
        self.FinishedDate = dateFromYaml(self.FinishedDate)
        return self



class tSpecialSemester:
    def __init__(self):
        self.Semester = None
        self.Type = None # str ("urlaub")
        self.Remark = "" # str




class tStudent:
    def __init__(self):
        self.ID = None # str
        self.FirstName = ""
        self.MiddleName = ""
        self.LastName = ""
        self.Gender = None # "m" / "w"
        self.SpecialSemesters = {} # list of semesters
        self.DateOfBirth = None
        self.PlaceOfBirth = ""
        self.Degrees = {}
        self.Notes = "" # str
        self.Email = "" # str

    def anrede(self):
        if self.Gender == "m":
            return "Herr"
        else:
            return "Frau"

    def to_yaml(self):
        result = self.__dict__.copy()
        result["DateOfBirth"] = dateToYaml(self.DateOfBirth)
        return (result, "!!datamodel.tStudent")

    def from_yaml(self, new_dict):
        if "Gender" not in new_dict:
            self.Gender = None
        if "SpecialSemesters" not in new_dict:
            self.SpecialSemesters = {}
        if "Notes" not in new_dict:
            self.Notes = ""
        if "Email" not in new_dict:
            self.Email = ""
        if "PlaceOfBirth" not in new_dict:
            self.PlaceOfBirth = ""
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

    def values(self):
        return self.Students.values()

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
        outf = file(filename, "wb")
        yaml.dumpToFile(outf, student)
        outf.close()

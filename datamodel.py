import datetime

import tools
import semester



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
        self.EnrolledSemester = None # semester
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
        result["FinishedDate"] = dateToYaml(self.FinishedDate)
        return (result, "!!datamodel.tDegree")

    def from_yaml(self, new_dict):
        if "MinorSubject" not in new_dict:
            self.MinorSubject = ""

        if "EnrolledDate" in new_dict:
            # compatibility: convert date to semester
            edate = dateFromYaml(new_dict["EnrolledDate"])
            del new_dict["EnrolledDate"]
            self.EnrolledSemester = semester.tSemester.fromDate(edate)

        self.__dict__.update(new_dict)
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




def firstEnrollment(student):
    enrollment_dates = [deg.EnrolledSemester.startDate()
                        for deg in student.Degrees.values()]
    if len(enrollment_dates) == 0:
        return None
    else:
        return min(enrollment_dates)

def firstEnrollmentSemester(student):
    enrollment_dates = [deg.EnrolledSemester
                        for deg in student.Degrees.values()]
    if len(enrollment_dates) == 0:
        return None
    else:
        return min(enrollment_dates)

def lastEnrollment(student):
    enrollment_dates = [deg.FinishedDate
                        for deg in student.Degrees.values()]
    if None in enrollment_dates:
        return datetime.date.today()
    elif len(enrollment_dates) == 0:
        return None
    else:
        return max(enrollment_dates)

def academicYearOfStart(student):
    fe = firstEnrollment(student) 
    if fe is None:
        return None
    else:
        return semester.getAcademicYear(fe)

def countStudySemesters(student):
    le = lastEnrollment(student)

    fe_sem = firstEnrollmentSemester(student)
    le_sem = le and semester.tSemester.fromDate(le)

    if not (fe_sem and le_sem):
        return 0

    return semester.countSemesters(fe_sem, le_sem)

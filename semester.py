class tSemester:
    def __init__(self):
        self.Term = None # "w"/"s"
        self.Year = None

    def __str__(self):
        if self.Term == "w":
            return "Winter %d/%02d" % (self.Year, (self.Year+1)%100)
        elif self.Term == "s":
            return "Sommer %d" % self.Year
        else:
            raise RuntimeError, "Invalid term in semester: %s" % self.Term

    def loadCurrent(self):
        raise NotImplemented
    
    def loadFromDate(self, date):
        raise NotImplemented

    def dumpStructure(self):
        return { "term": self.Term, "year", self.Year }

    def loadStructure(self, structure):
        self.Term = structure["term"]
        self.Year = structure["year"]
        return self




def countSemesters(from, to):
    pass




import datetime




class tSemester:
    def __init__(self):
        self.Term = None # "w"/"s"
        self.Year = None

    def __str__(self):
        if self.Term == "w":
            return "WS %d/%02d" % (self.Year, (self.Year+1)%100)
        elif self.Term == "s":
            return "SS %d" % self.Year
        else:
            raise RuntimeError, "Invalid term in semester: %s" % self.Term

    def now(cls):
        cls.loadFromDate(datetime.date.today())
    now = classmethod(now)
    
    def fromDate(cls, date):
        result = cls()
        result.Year = date.year
        if 4 <= date.month < 10:
            result.Term = "s"
        else:
            result.Term = "w"
            if date.month < 4:
                result.Year -= 1
        return result
    fromDate = classmethod(fromDate)




def countSemesters(start, stop):
    if start.Term == stop.Term:
        return (stop.Year - start.Year) * 2 + 1
    elif start.Term == "w":
        return (stop.Year - start.Year - 1) * 2
    elif start.Term == "s":
        return (stop.Year - start.Year + 1) * 2




import datetime




class tSemester:
    def __init__(self, term = None, year = None):
        self.Term = term # "w"/"s"
        self.Year = year

    def __str__(self):
        if self.Term == "w":
            return "WS %d/%02d" % (self.Year, (self.Year+1)%100)
        elif self.Term == "s":
            return "SS %d" % self.Year
        else:
            raise RuntimeError, "Invalid term in semester: %s" % self.Term

    def __cmp__(self, other):
        # mind the hack: "s" < "w", alphabetically
        return cmp(self.Year, other.Year) or \
               cmp(self.Term, other.Term)

    def now(cls):
        return cls.fromDate(datetime.date.today())
    now = classmethod(now)
    
    def fromDate(cls, date):
        y = date.year
        if 4 <= date.month < 10:
            t = "s"
        else:
            t = "w"
            if date.month < 4:
                y -= 1
        return cls(t, y)
    fromDate = classmethod(fromDate)




def countSemesters(start, stop):
    if start.Term == stop.Term:
        return (stop.Year - start.Year) * 2 + 1
    elif start.Term == "w":
        return (stop.Year - start.Year - 1) * 2
    elif start.Term == "s":
        return (stop.Year - start.Year + 1) * 2




from __future__ import division

import codecs
import stat
import os
import sets
import urllib
import math

import airspeed



def stringifySensibly(s):
    if not isinstance(s, basestring):
        return str(s)
    else:
        return s




class tSubjectError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.Value = value
    def __str__(self):
        return str(self.Value)
    def __unicode__(self):
        return unicode(self.Value)




class tReference:
    def __init__(self, value):
        self.Value = value

    def set(self, value):
        self.Value = value

    def get(self):
        return self.Value




def escapeTeX(value):
    value = value.replace("\\", "--BS-ESCAPE--")
    value = value.replace("&", "\\&")
    value = value.replace("~", "\\~")
    value = value.replace("$", "\\$")
    value = value.replace("--BS-ESCAPE--", "$\\backslash$")
    return value




def escapeHTML(value):
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    value = value.replace("\"", "&quot;")
    return value




def roundGrade(grade, places = 1):
    factor = 10**places
    return math.floor(float(grade*factor))/factor




def sortBy(list, field):
    def cmp_func(a, b):
        return cmp(getattr(a, field), getattr(b, field))
    
    result = list[:]
    result.sort(cmp_func)
    return result




def uniq(list):
    seen_keys = sets.Set()
    result = []
    for i in list:
        if not i in seen_keys:
            result.append(i)
            seen_keys.add(i)
    return result




def unifyGrade(grade):
    base_grade = round(grade)
    diff = grade - base_grade
    if diff < -1./6:
        return base_grade - 1./3
    elif diff < 1./6:
        return base_grade
    else:
        return base_grade + 1./3




def makeObject(dict):
    class tInnocentContainer:
        pass

    result = tInnocentContainer()
    for key, value in dict.iteritems():
        setattr(result, key, value)
    return result




def find(haystack, needle):
    for i, v in enumerate(haystack):
        if needle == v:
            return i
    raise KeyError, "needle not in haystack"




class tAssociativeList(object):
    """The main difference between a dictionary and this
    class is that the insertion order of keys is maintained 
    at all times.
    """
    def __init__(self, list = []):
        self.Value = list[:]

    def keys(self):
        return [key for key, value in self.Value]

    def values(self):
        return [value for key, value in self.Value]

    def iteritems(self):
        return self.Value
    
    def __getitem__(self, sought_key):
        for key, value in self.Value:
            if sought_key == key:
                return value
        raise KeyError, sought_key

    def __add__(self, other):
        return tAssociativeList(self.Value + other.Value)

    def __iadd__(self, other):
        self.Value += other.Value
        return self




def median(list):
    if len(list) == 0:
        raise ValueError, "median() of empty list"

    print len(list)
    list.sort()
    l = len(list)
    l_2 = int(l / 2)
    if l % 2 == 0:
        print "l_2:", l_2
        return (list[l_2-1] + list[l_2]) / 2
    else:
        return list[l_2]




def histogram(values, start = {}):
    result = start.copy()
    for v in values:
        result[v] = 1 + result.setdefault(v, 0)
    return result




def gradeToWords(grade):
    if grade < 1:
        return "?"
    elif grade < 1.5:
        return "sehr gut"
    elif grade < 2.5:
        return "gut"
    elif grade < 3.5:
        return "befriedigend"
    elif grade <= 4:
        return "ausreichend"
    else:
        return "?"




def formatDate(date):
    return date.strftime("%d.%m.%Y")




def _expandTemplate(dir, filename, globals_dict):
    class _tTemplateHelper:
        """This class provides a namespace for helpers in
        Airspeed templating code.
        """

        def formatDate(self, date):
            return formatDate(date)

        def formatNumber(self, format, number):
            return format % number

        def formatBool(self, value):
            if value:
                return "1"
            else:
                return "0"

        def escapeTeX(self, value):
            return escapeTeX(value)

        def escapeHTML(self, value):
            return escapeHTML(value)

        def dump(self, value):
            print "*** DEBUG DUMP", repr(value)
            return ""

        def add(self, value, value2):
            return value + value2

        def sort(self, list):
            result = list[:]
            result.sort()
            return result

        def sortBy(self, list, field):
            return sortBy(list, field)

        def filterBy(self, list, field, value):
            return [v for v in list if getattr(v, field) == value]

        def len(self, value):
            return len(value)

        def gradeToWords(self, grade):
            return gradeToWords(grade)

        def round(self, value, decimals):
            return round(value, decimals)

        def composeQuery(self, key, value, previous):
            return composeQuery({key: value}, previous)

        def eletterate(self, list, element_count, blank):
            return [makeObject(
                {"Letter": chr(97+i),
                 "Data": v,
                 "Active": True})
                    for i, v in enumerate(list)] \
                    + \
                    [makeObject(
                {"Letter": chr(97+i),
                 "Data": blank,
                 "Active": False})
                    for i in range(len(list), element_count)]


    my_dict = globals_dict.copy()
    my_dict["h"] = _tTemplateHelper()
    my_dict["none"] = None
    my_dict["emptylist"] = []
    template = codecs.open(os.path.join(dir, filename),
                           "r", "utf-8").read()
    loader = airspeed.CachingFileLoader(dir)
    return airspeed.Template(template).merge(my_dict,
                                             loader)




def expandHTMLTemplate(filename, globals_dict = {}):
    my_dict = globals_dict.copy()
    my_dict["doctype"] = \
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'+ \
    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'

    return _expandTemplate("html-templates", filename, 
                           my_dict)




def expandTeXTemplate(filename, globals_dict):
    my_dict = globals_dict.copy()
    my_dict["none"] = None
    return _expandTemplate("tex-templates",
                           filename,
                           my_dict)




def runLatexOnTemplate(filename, globals_dict, 
                       included_files = []):
    return runLatex(expandTeXTemplate(filename,
                                      globals_dict),
                    included_files)




def copyFile(dest, src):
    """Copy the single file named `src' to `dest'.

    Don't use this with big files."""

    inf = file(src, "rb")
    fcont = inf.read()
    inf.close()

    outf = file(dest, "wb")
    outf.write(fcont)
    outf.close()




def removeDirRecursively(dir):
    for name in os.listdir(dir):
        fullname = os.path.join(dir, name)
        statbuf = os.stat(fullname)
        if stat.S_ISDIR(statbuf.st_mode):
            removeDirRecursively(fullname)
        else:
            os.unlink(fullname)
    os.rmdir(dir)




TEX_DEBUG_MODE = tReference(False)




def runLatex(text, included_files):
    temp_dir_name = os.tempnam(None, "diplomatik")
    print "*** PROCESSING TeX JOB under", temp_dir_name
    previous_wd = os.getcwd()
    os.mkdir(temp_dir_name)

    for i in included_files:
        copyFile(os.path.join(temp_dir_name, i),
                 os.path.join("tex-templates", i))

    os.chdir(temp_dir_name)
    try:
        outf = codecs.open("output.tex", "wb", "latin1")
        outf.write(text)
        outf.close()

        # three times so that the .aux can settle
        if os.system("pdflatex output") != 0:
            raise RuntimeError, "LaTeX run failed"
        if os.system("pdflatex output") != 0:
            raise RuntimeError, "LaTeX run failed"
        if os.system("pdflatex output") != 0:
            raise RuntimeError, "LaTeX run failed"

        pdff = file("output.pdf", "rb")
        pdf_string = pdff.read()
        pdff.close()

        return pdf_string
    finally:
        os.chdir(previous_wd)
        if not TEX_DEBUG_MODE.get():
            removeDirRecursively(temp_dir_name)




def parseQuery(query):
    result = {}
    if query == "":
        return result
    for part in query.split("&"):
        kvlist = part.split("=")
        if len(kvlist) == 1:
            key = kvlist[0]
            value = None
        else:
            key = kvlist[0].replace("+", " ")
            value = unicode(urllib.unquote_plus(kvlist[1]),
                "utf-8")
        result[key] = value
    return result




def composeQuery(items, previous_query = {}):
    query_items = previous_query.copy()
    query_items.update(items)
    if query_items:
        str_items = ["%s=%s" % (key,
                                urllib.quote_plus(value.encode("utf-8")))
                     for key, value in query_items.iteritems()]
        return "?"+ "&".join(str_items)
    else:
        return ""
    



def doesDirExist(directory):
    try:
        statbuf = os.stat(directory)
        return stat.S_ISDIR(statbuf.st_mode)
    except OSError:
        return False

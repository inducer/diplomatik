import codecs
import os
import sets

import airspeed




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




def alistLookup(alist, sought_key):
    for key, value in alist:
        if sought_key == key:
            return value
    raise KeyError, sought_key





def _expandTemplate(dir, filename, globals_dict):
    template = codecs.open(os.path.join(dir, filename),
                           "r", "utf-8").read()
    loader = airspeed.CachingFileLoader(dir)
    return airspeed.Template(template).merge(globals_dict,
                                             loader)




def expandHTMLTemplate(filename, globals_dict = {}):
    my_dict = globals_dict.copy()
    my_dict["none"] = None
    my_dict["doctype"] = \
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'+ \
    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'


    template = codecs.open(os.path.join("html-templates",
                                        filename),
                           "r", "utf-8").read()
    
    return _expandTemplate("html-templates", filename, 
                           my_dict)




def runLatexOnTemplate(filename, globals_dict, 
                       included_files = []):
    my_dict = globals_dict.copy()
    my_dict["none"] = None
    return runLatex(_expandTemplate("tex-templates",
                                    filename,
                                    my_dict),
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

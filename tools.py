import codecs
import os
import airspeed




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





def expandHTMLTemplate(filename, globals_dict = {}):
    my_dict = globals_dict.copy()
    my_dict["none"] = None
    my_dict["doctype"] = \
    '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"'+ \
    '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'

    template = codecs.open(os.path.join("html-templates",
                                        filename),
                           "r", "utf-8").read()
    
    return airspeed.Template(template).merge(my_dict)





def runLatexOnTemplate(filename, globals_dict, 
                       included_files = []):
    my_dict = globals_dict.copy()
    my_dict["none"] = None
    template = codecs.open(os.path.join("tex-templates",
                                        filename),
                           "r", "utf-8").read()
    return runLatex(airspeed.Template(template).merge(my_dict),
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
    temp_dir_name = os.tempnam()
    print "*** PROCESSING TeX JOB under", temp_dir_name
    previous_wd = os.getcwd()
    os.mkdir(temp_dir_name)

    for i in included_files:
        copyFile(os.path.join(temp_dir_name, i),
                 os.path.join("tex-templates", i))

    os.chdir(temp_dir_name)
    
    outf = codecs.open("output.tex", "wb", "latin1")
    outf.write(text)
    outf.close()

    os.system("pdflatex output")

    pdff = file("output.pdf", "rb")
    pdf_string = pdff.read()
    pdff.close()

    os.chdir(previous_wd)
    return pdf_string

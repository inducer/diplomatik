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





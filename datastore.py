import os
import stat
import codecs
import tools
import yaml
import os.path
import datamodel
import semester




class tDataStore:
    TAG = "Diplomatik data store v1\n"

    def __init__(self, directory, degree_rule_sets_map, allow_create = False):
        tag_fn = os.path.join(directory, "version-tag")
        self.DataDir = os.path.join(directory, "data")
        self.ExportDir = os.path.join(directory, "export")
        self.DRSMap = degree_rule_sets_map

        # check for data store tag
        try:
            tag_f = file(tag_fn, "rb")
            tag = tag_f.read()
            tag_f.close()

            valid_archive = tag == self.TAG
        except IOError:
            valid_archive = False

        if not valid_archive:
            if allow_create:
                os.mkdir(directory)

                tag_f = file(tag_fn, "wb")
                tag_f.write(self.TAG)
                tag_f.close()

                os.mkdir(self.DataDir)
                os.mkdir(self.ExportDir)
            else:
                raise RuntimeError, "No valid archive found at %s -- Did WinZip mess up your line endings?" \
                      % directory

        self.Directory = directory
        self.Students = {}
        for fn in os.listdir(self.DataDir):
            complete_fn = os.path.join(self.DataDir, fn)
            if stat.S_ISREG(os.stat(complete_fn).st_mode):
                student = yaml.loadFile(complete_fn).next() 
                self.Students[student.ID] = student

        self.ExportFilenames = {}
        for key, student in self.Students.iteritems():
            self.ExportFilenames[key] = self.getExportFilename(student)

    def getExportDir(self, student):
        ay = datamodel.academicYearOfStart(student)
        if ay is None:
            return os.path.join(
                self.ExportDir,
                "kein-aj")
        else:
            return os.path.join(
                self.ExportDir,
                "aj-%d" % ay)
           
    def getExportFilename(self, student):
        return str(os.path.join(
            self.getExportDir(student),
            "%s.tex" % student.ID))
    
    def keys(self):
        return self.Students.keys()

    def values(self):
        return self.Students.values()

    def iteritems(self):
        return self.Students.iteritems()

    def __getitem__(self, key):
        return self.Students[key]

    def __setitem__(self, key, student):
        self.Students[student.ID] = student
        self.writeStudent(key)

    def __delitem__(self, key):
        del self.Students[key]
        filename = os.path.join(self.DataDir, key)
        os.unlink(filename)

    def getExportData(self, student):
        studbeg = datamodel.firstEnrollment(student)
        if studbeg:
            studbeg_sem = semester.tSemester.fromDate(studbeg)
        else:
            studbeg_sem = None

        return tools.expandTeXTemplate(
            "export.tex",
            {"student": student,
             "drs_map": self.DRSMap,
             "urlaubssem": len([1 for specsem in student.SpecialSemesters.values()
                                if specsem.Type == "urlaub"]),
             "semesters": datamodel.countStudySemesters(student),
             "beginn": studbeg_sem
            }).encode("utf-8")

    def exportAll(self):
        for key in self.keys():
            self.writeStudent(key)

    def writeStudent(self, key):
        student = self.Students[key]
        assert key == student.ID
        
        data_filename = os.path.join(self.DataDir, student.ID)
        outf = file(data_filename, "wb")
        yaml.dumpToFile(outf, student)
        outf.close()

        # maintain exported data
        export_data = self.getExportData(student)

        new_export_filename = self.getExportFilename(student)
        new_export_dir = self.getExportDir(student)

        try:
            prev_export_filename = self.ExportFilenames[key]
            if prev_export_filename != new_export_filename:
                try:
                    os.unlink(prev_export_filename)
                except OSError:
                    pass
        except KeyError:
            # we do not have a previous filename for new keys,
            # that's ok.
            pass

        if not tools.doesDirExist(new_export_dir):
            os.mkdir(new_export_dir)

        exportf = file(new_export_filename, "wb")
        exportf.write(export_data)
        exportf.close()


import os




def runLatexWithPreprocessor(file, globals):
    output = StringIO.StringIO()
    interpreter = em.Interpreter(globals = globals_dict, 
                                 output = output)
    interpreter.file(file(os.path.join("tex-templates",
                                       filename),
                          "r"))
    interpreter.shutdown()
    return runLatex(output.getvalue())




def runLatex(text):
    name = os.tempnam()
    previous_wd = os.getcwd()
    os.mkdir(name)
    os.chdir(name)
    
    outf = file("output.tex", "w+b")
    outf.write(text)
    outf.close()

    os.system("pdflatex output")

    pdff = file("output.pdf", "r+b")
    pdf_string = pdff.read()

    os.chdir(previous_wd)
    return pdf_string

   


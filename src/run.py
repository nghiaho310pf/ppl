import glob
import sys,os,traceback
sys.path.append('./test/')
import subprocess
import unittest
from antlr4 import *

#Make sure that ANTLR_JAR is set to antlr-4.9.2-complete.jar
ANTLR_JAR = os.environ.get('ANTLR_JAR')
TARGET = '../target/main/minigo/parser' if os.name == 'posix' else os.path.normpath('../target/')
JAVA_EXE_PATH = os.environ.get('JAVA_EXE_PATH') or "java"
JAVAC_EXE_PATH = os.environ.get('JAVAC_EXE_PATH') or "javac"

locpath = ['./main/minigo/parser/','./main/minigo/astgen/','./main/minigo/utils/']
for p in locpath:
    if not p in sys.path:
        sys.path.append(p)

def main(argv):
    global ANTLR_JAR, TARGET
    if len(argv) < 1:
        printUsage()
    elif argv[0] == 'gen':
        subprocess.run([JAVA_EXE_PATH,"-jar",ANTLR_JAR,"-o","../target","-no-listener","-visitor","main/minigo/parser/MiniGo.g4"])
    elif argv[0] == 'clean':
        files = glob.glob(f'{TARGET}/MiniGo*')
        for f in files:
            os.remove(f)
    elif argv[0] == '-assign1':
        from TestUtils import TestLexer,TestParser
        lexstart = int(argv[1])
        lexend = int(argv[2]) + 1
        lextestdir = argv[3]
        lexsoldir = argv[4]
        recstart = int(argv[5])
        recend = int(argv[6]) + 1
        rectestdir = argv[7]
        recsoldir = argv[8]
        for i in range(lexstart,lexend):
            try: 
                TestLexer.test(lextestdir,lexsoldir,i)
            except:
                trace = traceback.format_exc()
                print ("Test " + str(i) + " catches unexpected error:" + trace + "\n")
        for i in range(recstart,recend):
            try:
                TestParser.test(rectestdir,recsoldir,i)
            except:
                trace = traceback.format_exc()
                print ("Test " + str(i) + " catches unexpected error:" + trace + "\n")
    elif argv[0] == 'test':
        if not './main/minigo/parser/' in sys.path:
            sys.path.append('./main/minigo/parser/')
        if os.path.isdir(TARGET) and not TARGET in sys.path:
            sys.path.append(TARGET)
        from LexerSuite import LexerSuite
        from ParserSuite import ParserSuite
        from ASTGenSuite import ASTGenSuite
        from CheckSuite import CheckSuite

        test(unittest.TestSuite([
            # unittest.TestLoader().loadTestsFromTestCase(LexerSuite),
            # unittest.TestLoader().loadTestsFromTestCase(ParserSuite),
            # unittest.TestLoader().loadTestsFromTestCase(ASTGenSuite),
            unittest.TestLoader().loadTestsFromTestCase(CheckSuite)
        ]))
    else:
        printUsage()

def test(suite):
    from io import StringIO
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    runner.run(suite)
    stream.seek(0)
    print(stream.read())

def printUsage():
    print("Usage:")
    print("  python3 run.py gen                            # Generate required files")
    print("  python3 run.py test LexerSuite [test_case]    # Run LexerSuite tests (test_case is optional)")
    print("  python3 run.py test ParserSuite [test_case]   # Run ParserSuite tests (test_case is optional)")
    print("  python3 run.py test ASTGenSuite [test_case]   # Run ASTGenSuite tests (test_case is optional)")
    print()
    print("Notes:")
    print("  - Replace [test_case] with the specific test you want to run, e.g., test_1.")
    print("  - If [test_case] is not provided, all tests in the suite will be executed.")

if __name__ == "__main__":
    main(sys.argv[1:])
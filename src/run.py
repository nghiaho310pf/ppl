import glob
import sys,os,traceback
sys.path.append('./test/')
sys.path.append('./main/minigo/parser/')
sys.path.append('./main/minigo/utils/')
sys.path.append('./main/minigo/astgen/')
sys.path.append('./main/minigo/checker/')
sys.path.append('./main/minigo/codegen/')
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
    elif argv[0] == 'test':
        if os.path.isdir(TARGET) and not TARGET in sys.path:
            sys.path.append(TARGET)
        from LexerSuite import LexerSuite
        from ParserSuite import ParserSuite
        from ASTGenSuite import ASTGenSuite
        from CheckSuite import CheckSuite
        from CodeGenSuite import CheckCodeGenSuite

        test(unittest.TestSuite([
            # unittest.TestLoader().loadTestsFromTestCase(LexerSuite),
            # unittest.TestLoader().loadTestsFromTestCase(ParserSuite),
            # unittest.TestLoader().loadTestsFromTestCase(ASTGenSuite),
            # unittest.TestLoader().loadTestsFromTestCase(CheckSuite),
            unittest.TestLoader().loadTestsFromTestCase(CheckCodeGenSuite),
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
    print("  python3 run.py gen     # Generate required files")
    print("  python3 run.py test    # Run tests")

if __name__ == "__main__":
    main(sys.argv[1:])
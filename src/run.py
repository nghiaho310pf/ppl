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
        if len(argv) < 2:
            printUsage()
        elif argv[1] == 'LexerSuite':
            from LexerSuite import LexerSuite
            suite = unittest.TestLoader().loadTestsFromTestCase(LexerSuite)
            test(argv, suite)
        elif argv[1] == 'ParserSuite':
            from ParserSuite import ParserSuite
            suite = unittest.TestLoader().loadTestsFromTestCase(ParserSuite)
            test(argv, suite)
        elif argv[1] == 'ASTGenSuite':
            from ASTGenSuite import ASTGenSuite
            suite = unittest.TestLoader().loadTestsFromTestCase(ASTGenSuite)
            test(argv, suite)
        else:
            printUsage()
    else:
        printUsage()

def getAndTest(argv, cls):
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(cls)
    test(argv, suite)

def getAndTestFucntion(argv, cls, nameFunction):
    suite = unittest.TestSuite()
    suite.addTest(cls(nameFunction))
    test(argv, suite)

def generate_repeating_sequence(size):
    base_sequence = "1234567890"
    repeated_sequence = (base_sequence * ((size // len(base_sequence)) + 1))[:size]
    return repeated_sequence

def printMiniGo(argv, stream, result):
    print("----------------------------------------------------------------------")
    print(f'Tests run: {result.testsRun}')

    stream.seek(0)
    expect = stream.readline()
    print(generate_repeating_sequence(len(expect) - 1))

    styled_expect = ''.join(
        f"{c}" if c == 'E' else
        f"{c}" if c == 'F' else
        f"{c}" if c == '.' else c
        for c in expect
    )
    print(styled_expect, end='')

    listErrors = []
    listFailures = []
    for i in range(1, len(expect)):
        if expect[i - 1] == 'E': listErrors.append(i)
        elif expect[i - 1] == 'F': listFailures.append(i)

    errors_str = ", ".join(map(str, listErrors))
    failures_str = ", ".join(map(str, listFailures))

    if len(listFailures) + len(listErrors):
        Pass = 100.0 * (1 - (len(listFailures) + len(listErrors)) / (len(expect) - 1))
        print(f"\nPass     : {Pass:.2f} %")
        print(f"Errors   : {errors_str}")
        print(f"Failures : {failures_str}")
    else:
        print(f"Pass full 10.")
    print("----------------------------------------------------------------------")

def test(argv, suite):
    from pprint import pprint
    from io import StringIO
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    result = runner.run(suite)
    stream.seek(0)
    print(stream.read())
    # printMiniGo(argv, stream, result)


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
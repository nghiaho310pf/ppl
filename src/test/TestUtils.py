import os
import subprocess
from io import StringIO

from antlr4 import *
from antlr4.error.ErrorListener import ConsoleErrorListener

from ASTGeneration import ASTGeneration
from CodeGenerator import CodeGenerator
from MiniGoLexer import MiniGoLexer
from MiniGoParser import MiniGoParser
from StaticCheck import StaticChecker
from StaticError import StaticError
from lexererr import *
from run import JAVA_EXE_PATH


class TestLexer:
    @staticmethod
    def checkLexeme(input, expect, num):
        input_stream = InputStream(input)
        dest = StringIO()
        lexer = MiniGoLexer(input_stream)
        try:
            TestLexer.printLexeme(dest, lexer)
        except (ErrorToken, UncloseString, IllegalEscape) as err:
            dest.write(err.message)
        except Exception as err:
            dest.write(str(err) + "\n")
        line = dest.getvalue()

        if line != expect:
            raise Exception(f"Expected {expect}\n"
                            f"              found {line}")

        # return line == expect
        return True

    @staticmethod
    def printLexeme(dest, lexer):
        tok = lexer.nextToken()
        if tok.type != Token.EOF:
            dest.write(tok.text + ",")
            TestLexer.printLexeme(dest, lexer)
        else:
            dest.write("<EOF>")


class NewErrorListener(ConsoleErrorListener):
    INSTANCE = None

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise SyntaxException("Error on line " + str(line) + " col " + str(column + 1) + ": " + offendingSymbol.text)


NewErrorListener.INSTANCE = NewErrorListener()


class SyntaxException(Exception):
    def __init__(self, msg):
        self.message = msg


class TestParser:
    @staticmethod
    def createErrorListener():
        return NewErrorListener.INSTANCE

    @staticmethod
    def checkParser(input, expect, num):
        input_stream = InputStream(input)
        dest = StringIO()
        lexer = MiniGoLexer(input_stream)
        listener = TestParser.createErrorListener()

        tokens = CommonTokenStream(lexer)

        parser = MiniGoParser(tokens)
        parser.removeErrorListeners()
        parser.addErrorListener(listener)
        try:
            parser.program()
            dest.write("successful")
        except SyntaxException as f:
            dest.write(f.message)
        except Exception as e:
            dest.write(str(e))
        line = dest.getvalue()

        if line != expect:
            raise Exception(f"Expected {expect}\n"
                            f"              found {line}")

        # return line == expect
        return True


class TestAST:
    @staticmethod
    def checkASTGen(input, expect, num):
        input_stream = InputStream(input)
        dest = StringIO()

        lexer = MiniGoLexer(input_stream)
        tokens = CommonTokenStream(lexer)

        listener = NewErrorListener()

        parser = MiniGoParser(tokens)
        parser.removeErrorListeners()
        parser.addErrorListener(listener)

        tree = parser.program()
        asttree = ASTGeneration().visit(tree)
        dest.write(str(asttree))

        line = dest.getvalue()

        if line != expect:
            raise Exception(f"Expected {expect}\n"
                            f"              found {line}")

        # return line == expect
        return True


class TestChecker:
    @staticmethod
    def test(input, expect, num):
        return TestChecker.checkStatic(input, expect, num)

    @staticmethod
    def checkStatic(input, expect, num):
        dest = StringIO()

        if type(input) is str:
            input_stream = InputStream(input)
            lexer = MiniGoLexer(input_stream)
            tokens = CommonTokenStream(lexer)
            parser = MiniGoParser(tokens)
            tree = parser.program()
            asttree = ASTGeneration().visit(tree)
        else:
            asttree = input

        checker = StaticChecker(asttree)
        rawdog_it = False
        if rawdog_it:
            res = checker.check()
        else:
            try:
                res = checker.check()
            except StaticError as e:
                dest.write(str(e) + '\n')

            line = dest.getvalue().strip()
            expect = expect.strip()

            if line != expect:
                # Just clean it up
                if expect.endswith("\n") and line.endswith("\n"):
                    expect = expect[:-1]
                    line = line[:-1]
                raise Exception(f"Expected {expect}\n"
                                f"              found {line}")

        # return line == expect
        return True


class TestCodeGen():
    @staticmethod
    def test(input, expect, num):
        return TestCodeGen.check(input, expect, num)

    @staticmethod
    def check(input, expect, num):
        if type(input) is str:
            input_stream = InputStream(input)
            lexer = MiniGoLexer(input_stream)
            tokens = CommonTokenStream(lexer)
            parser = MiniGoParser(tokens)
            tree = parser.program()
            asttree = ASTGeneration().visit(tree)
            checker = StaticChecker(asttree)
            checker.check()
        else:
            asttree = input

        jasmin_output_path = f"./test/solutions/{num}"
        os.makedirs(jasmin_output_path, exist_ok=True)

        output_path = os.path.join(jasmin_output_path, "out.txt")
        JASMIN_JAR = "../../../external/jasmin.jar"

        with open(output_path, "w") as dest:
            codeGen = CodeGenerator()
            try:
                codeGen.gen(asttree, jasmin_output_path)

                subprocess.call(
                    f"{JAVA_EXE_PATH} -jar {JASMIN_JAR} *.j",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    cwd=jasmin_output_path
                )

                subprocess.run(
                    f"{JAVA_EXE_PATH} -cp .{os.pathsep}../../../lib MiniGoClass",
                    shell=True,
                    stdout=dest,
                    timeout=10,
                    cwd=jasmin_output_path
                )

            except StaticError as e:
                dest.write(str(e))
            except subprocess.TimeoutExpired:
                dest.write("Time out\n")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"command '{e.cmd}' returned with error (code {e.returncode}): {e.output}")

        with open(output_path, "r") as dest:
            line = dest.read().strip()
            expect = expect.strip()

            if line != expect:
                if expect.endswith("\n") and line.endswith("\n"):
                    expect = expect[:-1]
                    line = line[:-1]
                raise Exception(f"Expected {expect}\n"
                                f"              found {line}")

            return line == expect

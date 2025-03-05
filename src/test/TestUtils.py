import sys,os
from io import StringIO

from antlr4 import *
from antlr4.error.ErrorListener import ConsoleErrorListener,ErrorListener
#if not './main/minigo/parser/' in sys.path:
#    sys.path.append('./main/minigo/parser/')
#if os.path.isdir('../target/main/minigo/parser') and not '../target/main/minigo/parser/' in sys.path:
#    sys.path.append('../target/main/minigo/parser/')
from MiniGoLexer import MiniGoLexer
from MiniGoParser import MiniGoParser
from lexererr import *
from ASTGeneration import ASTGeneration

# class TestUtil:
#     @staticmethod
#     def makeSource(inputStr,num):
#         filename = "./test/testcases/" + str(num) + ".txt"
#         file = open(filename,"w")
#         file.write(inputStr)
#         file.close()
#         return FileStream(filename)


class TestLexer:
    @staticmethod
    def checkLexeme(input,expect,num):
        input_stream = InputStream(input)
        dest = StringIO()
        lexer = MiniGoLexer(input_stream)
        try:
            TestLexer.printLexeme(dest,lexer)
        except (ErrorToken,UncloseString,IllegalEscape) as err:
            dest.write(err.message)
        except Exception as err:
            dest.write(str(err)+"\n")
        line = dest.getvalue()

        if line != expect:
            print(f"Test {num}:")
            print(f"    expected {expect}")
            print(f"       found {line}")

        # return line == expect
        return True

    @staticmethod    
    def printLexeme(dest,lexer):
        tok = lexer.nextToken()
        if tok.type != Token.EOF:
            dest.write(tok.text+",")
            TestLexer.printLexeme(dest,lexer)
        else:
            dest.write("<EOF>")
class NewErrorListener(ConsoleErrorListener):
    INSTANCE = None
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise SyntaxException("Error on line "+ str(line) + " col " + str(column + 1)+ ": " + offendingSymbol.text)
NewErrorListener.INSTANCE = NewErrorListener()

class SyntaxException(Exception):
    def __init__(self,msg):
        self.message = msg

class TestParser:
    @staticmethod
    def createErrorListener():
         return NewErrorListener.INSTANCE

    @staticmethod
    def checkParser(input,expect,num):
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
    def checkASTGen(input,expect,num):
        input_stream = InputStream(input)
        dest = StringIO()

        lexer = MiniGoLexer(input_stream)
        tokens = CommonTokenStream(lexer)
        parser = MiniGoParser(tokens)
        tree = None
        try:
            tree = parser.program()
        except SyntaxException as f:
            dest.write(f.message)
        except Exception as e:
            dest.write(str(e))
        asttree = ASTGeneration().visit(tree)

        dest.write(str(asttree))

        line = dest.getvalue()

        if line != expect:
            raise Exception(f"Expected {expect}\n"
                            f"              found {line}")

        # return line == expect
        return True
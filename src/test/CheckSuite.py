import unittest
from TestUtils import TestChecker
from AST import *

class CheckSuite(unittest.TestCase):
    # def test_redeclared(self):
    #     input = """var a int; var b int; var a int; """
    #     expect = "Redeclared Variable: a\n"
    #     self.assertTrue(TestChecker.test(input,expect,400))
    #
    # def test_type_mismatch(self):
    #     input = """var a int = 1.2;"""
    #     expect = "Type Mismatch: VarDecl(a,IntType,FloatLiteral(1.2))\n"
    #     self.assertTrue(TestChecker.test(input,expect,401))
    #
    # def test_undeclared_identifier(self):
    #     input = Program([VarDecl("a",IntType(),Id("b"))])
    #     expect = "Undeclared Identifier: b\n"
    #     self.assertTrue(TestChecker.test(input,expect,402))

    def test_1(self):
        input = """
            type Point struct {
                x float;
                y float;
            }

            func (p Point) Length() float {
                return 1.0;
            }

            func X() Point {
                var a = Point{};
                var x int = a.Length();
            }
        """
        expect = "Type Mismatch: VarDecl(x,IntType,MethodCall(Id(a),Length,[]))\n"
        self.assertTrue(TestChecker.test(input,expect,402))

    def test_2(self):
        input = """
            const q = 1 + 2

            func thing1() [q]int {
                return [3]int{0, 1, 2};
            }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 402))

    def test_3(self):
        input = """
            const q = 1 + 3

            func thing1() [q]int {
                return [3]int{0, 1, 2};
            }
        """
        expect = "Type Mismatch: Return(ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(0),IntLiteral(1),IntLiteral(2)]))\n"
        self.assertTrue(TestChecker.test(input, expect, 402))

    def test_4(self):
        input = """
            const q float = 1 + 3
        """
        expect = "Type Mismatch: Return(ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(0),IntLiteral(1),IntLiteral(2)]))\n"
        self.assertTrue(TestChecker.test(input, expect, 402))


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
            func sqrt(v float) float {
                return 1.0;
            }
        
            type Point struct {
                x float;
                y float;
            }
            
            func (p Point) Length() float {
                return sqrt(x * x + y * y);
            }
        
            func X() Point {
                var a = Point{};
                var x int = a.Length();
            }
        """
        expect = "Type Mismatch: VarDecl(x,IntType,MethodCall(Id(a),Length,[]))\n"
        self.assertTrue(TestChecker.test(input,expect,402))

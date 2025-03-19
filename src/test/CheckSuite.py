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

    # def test_1(self):
    #     input = """
    #         type Point struct {
    #             x float;
    #             y float;
    #         }
    #
    #         func (p Point) Length() float {
    #             return 1.0;
    #         }
    #
    #         func X() Point {
    #             var a = Point{};
    #             var x int = a.Length();
    #         }
    #     """
    #     expect = "Type Mismatch: VarDecl(x,IntType,MethodCall(Id(a),Length,[]))\n"
    #     self.assertTrue(TestChecker.test(input,expect,402))
    #
    # def test_2(self):
    #     input = """
    #         const q = 1 + 2
    #
    #         func thing1() [q]int {
    #             return [3]int{0, 1, 2};
    #         }
    #     """
    #     expect = ""
    #     self.assertTrue(TestChecker.test(input, expect, 402))
    #
    # def test_3(self):
    #     input = """
    #         const q = 1 + 3
    #
    #         func thing1() [q]int {
    #             return [3]int{0, 1, 2};
    #         }
    #     """
    #     expect = "Type Mismatch: Return(ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(0),IntLiteral(1),IntLiteral(2)]))\n"
    #     self.assertTrue(TestChecker.test(input, expect, 402))
    #
    # def test_4(self):
    #     input = """
    #         const q float = 1 + 3
    #     """
    #     expect = "Type Mismatch: ConstDecl(q,FloatType,BinaryOp(IntLiteral(1),+,IntLiteral(3)))\n"
    #     self.assertTrue(TestChecker.test(input, expect, 402))
    #
    # def test_5(self):
    #     input = """
    #         func main() {
    #             x := 3
    #         }
    #     """
    #     expect = ""
    #     self.assertTrue(TestChecker.test(input, expect, 402))
    #
    # def test_6(self):
    #     input = """
    #         func main() {
    #             x := 3
    #             x := 4.5
    #         }
    #     """
    #     expect = "Type Mismatch: Assign(Id(x),FloatLiteral(4.5))\n"
    #     self.assertTrue(TestChecker.test(input, expect, 402))
    #
    # def test_029(self):
    #     input = """
    #         func main() {
    #             var MOD = 1 + 1;
    #             var arr [MOD][5]int;
    #             var multi_arr [2][5]int;
    #             arr := multi_arr;
    #         }
    #     """
    #     expect = "Type Mismatch: Id(MOD)\n"
    #     self.assertTrue(TestChecker.test(input, expect, 429))
    #
    # def test_033(self):
    #     input = """
    #         type Calculator struct {
    #             value int;
    #         }
    #
    #         func (c Calculator) Add(x int) float {
    #             return c.value + x;
    #         }
    #
    #         func main() {
    #             var a Calculator;
    #             var MOD string = 1 + a.Add(1);
    #         }
    #     """
    #     expect = "Type Mismatch: VarDecl(MOD,StringType,BinaryOp(IntLiteral(1),+,MethodCall(Id(a),Add,[IntLiteral(1)])))\n"
    #     self.assertTrue(TestChecker.test(input, expect, 433))
    #
    # def test_032(self):
    #     input = """
    #         type Calculator struct {
    #             value int;
    #         }
    #
    #         func (c Calculator) Add(x int) int {
    #             return c.value + x;
    #         }
    #
    #         func main() {
    #             var a Calculator;
    #             const MOD = 1 + a.Add(1);
    #             var arr [MOD][5]int;
    #             var multi_arr [2][5]int;
    #             arr := multi_arr;
    #         }
    #     """
    #     expect = "Type Mismatch: Id(a)\n"
    #     self.assertTrue(TestChecker.test(input,expect,432))

    # def test_035(self):
    #     input = """
    #         type Point struct {
    #             x float;
    #             y float;
    #         }
    #
    #         func (p Point) Length() float {
    #             return p.x * p.x + p.y * p.y;
    #         }
    #
    #         func X() Point {
    #             var a = Point{x: 2.0, y: 4.0};
    #             var x float = a.Length();
    #             return a
    #         }
    #     """
    #     expect = ""
    #     self.assertTrue(TestChecker.test(input, expect, 402))

    # def test_037(self):
    #     input = """
    #         type I struct {
    #             i int;
    #         }
    #
    #         func X() {
    #             const a = I{i: 2};
    #             const b = a.i;
    #             var x = [b]int{2, 3};
    #         }
    #     """
    #     expect = ""
    #     self.assertTrue(TestChecker.test(input, expect, 402))

    def test_035(self):
        input = """
            func A() {
            }
            
            func B() {
                A
            }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 402))

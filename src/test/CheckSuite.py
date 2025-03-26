import unittest
from TestUtils import TestChecker
from AST import *
import inspect

test_increment = 0

def make_test_number():
    global test_increment
    v = test_increment
    test_increment += 1
    return v

class CheckSuite(unittest.TestCase):
    def test_orig_1(self):
        i = Program([VarDecl("a",IntType(),None),VarDecl("b",FloatType(),None),VarDecl("a",IntType(),None)])
        self.assertTrue(TestChecker.test(i, "Redeclared Variable: a\n", make_test_number()))

    def test_orig_2(self):
        i = Program([VarDecl("a",IntType(),FloatLiteral(1.2))])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(a,IntType,FloatLiteral(1.2))\n", make_test_number()))

    def test_orig_3(self):
        i = Program([VarDecl("a",IntType(),Id("b"))])
        self.assertTrue(TestChecker.test(i, "Undeclared Identifier: b\n", make_test_number()))

    def test_literal_1(self):
        i = Program([VarDecl("a",IntType(),IntLiteral(2))])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_literal_2(self):
        i = Program([VarDecl("a",FloatType(),FloatLiteral(2.5))])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_literal_3(self):
        i = Program([VarDecl("a",StringType(),StringLiteral("\"abc\""))])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_literal_4(self):
        i = Program([VarDecl("a", BoolType(), BooleanLiteral(False))])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_literal_5(self):
        i = Program([
            StructType("X", [("a", IntType())], []),
            VarDecl("a", Id("X"), StructLiteral("X", [("a", IntLiteral(2))]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_nil_cast_1(self):
        i = Program([
            StructType("X", [("a", IntType())], []),
            VarDecl("a", Id("X"), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_nil_cast_2(self):
        i = Program([
            InterfaceType("X", [Prototype("x", [], VoidType())]),
            VarDecl("a", Id("X"), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_nil_cast_3(self):
        i = Program([
            InterfaceType("X", [Prototype("x", [], VoidType())]),
            VarDecl("a", Id("X"), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))



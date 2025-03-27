"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=6hUH7RxU2yQ
"""

import unittest
from TestUtils import TestChecker
from AST import *

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

    def test_nil_cast_4(self):
        i = Program([
            VarDecl("a", IntType(), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(a,IntType,Nil)\n", make_test_number()))

    def test_nil_cast_5(self):
        i = Program([
            VarDecl("a", StringType(), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(a,StringType,Nil)\n", make_test_number()))

    def test_nil_cast_6(self):
        i = Program([
            VarDecl("a", FloatType(), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(a,FloatType,Nil)\n", make_test_number()))

    def test_nil_cast_7(self):
        i = Program([
            VarDecl("a", BoolType(), NilLiteral())
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(a,BoolType,Nil)\n", make_test_number()))

    def test_interface_cast_1(self):
        i = Program([
            StructType("X", [("i", IntType())], []),
            MethodDecl("x", Id("X"), FuncDecl("a", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            InterfaceType("Q", [Prototype("a", [IntType()], VoidType())]),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("x1", Id("X"), StructLiteral("X", [("i", IntLiteral(0))])),
                VarDecl("qx", Id("Q"), Id("x1")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_interface_cast_2(self):
        i = Program([
            StructType("X", [("i", IntType())], []),
            MethodDecl("x", Id("X"), FuncDecl("a", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            MethodDecl("x", Id("X"), FuncDecl("b", [ParamDecl("r", FloatType())], IntType(), Block([]))),
            InterfaceType("Q", [
                Prototype("a", [IntType()], VoidType()),
                Prototype("b", [FloatType()], IntType()),
            ]),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("x1", Id("X"), StructLiteral("X", [("i", IntLiteral(0))])),
                VarDecl("qx", Id("Q"), Id("x1")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_interface_cast_3(self):
        i = Program([
            StructType("X", [("i", IntType())], []),
            MethodDecl("x", Id("X"), FuncDecl("a", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            MethodDecl("x", Id("X"), FuncDecl("b", [ParamDecl("r", FloatType())], IntType(), Block([]))),
            InterfaceType("Q", [
                Prototype("a", [IntType()], VoidType()),
                Prototype("b", [FloatType()], VoidType()),
            ]),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("x1", Id("X"), StructLiteral("X", [("i", IntLiteral(0))])),
                VarDecl("qx", Id("Q"), Id("x1")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(qx,Id(Q),Id(x1))\n", make_test_number()))

    def test_interface_cast_4(self):
        i = Program([
            StructType("X", [("i", IntType())], []),
            MethodDecl("x", Id("X"), FuncDecl("a", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            MethodDecl("x", Id("X"), FuncDecl("b", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            InterfaceType("Q", [
                Prototype("a", [IntType()], VoidType()),
                Prototype("b", [FloatType()], VoidType()),
            ]),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("x1", Id("X"), StructLiteral("X", [("i", IntLiteral(0))])),
                VarDecl("qx", Id("Q"), Id("x1")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(qx,Id(Q),Id(x1))\n", make_test_number()))

    def test_interface_cast_5(self):
        i = Program([
            StructType("X", [("i", IntType())], []),
            MethodDecl("x", Id("X"), FuncDecl("a", [ParamDecl("r", IntType())], VoidType(), Block([]))),
            InterfaceType("Q", [
                Prototype("a", [IntType()], VoidType()),
                Prototype("b", [FloatType()], VoidType()),
            ]),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("x1", Id("X"), StructLiteral("X", [("i", IntLiteral(0))])),
                VarDecl("qx", Id("Q"), Id("x1")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: VarDecl(qx,Id(Q),Id(x1))\n", make_test_number()))

    def test_global_naming_1(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_global_naming_2(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            VarDecl("x2", None, IntLiteral(0))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_global_naming_3(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            VarDecl("x1", None, IntLiteral(0))
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Variable: x1\n", make_test_number()))

    def test_global_naming_4(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            ConstDecl("x1", IntType(), IntLiteral(0))
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: x1\n", make_test_number()))

    def test_global_naming_5(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            FuncDecl("x1", [], VoidType(), Block([]))
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Function: x1\n", make_test_number()))

    def test_global_naming_6(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            StructType("x1", [], [])
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Type: x1\n", make_test_number()))

    def test_global_naming_7(self):
        i = Program([
            VarDecl("x1", None, IntLiteral(0)),
            InterfaceType("x1", [])
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Type: x1\n", make_test_number()))

    def test_prelude_trampling_1(self):
        i = Program([
            ConstDecl("getInt", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: getInt\n", make_test_number()))

    def test_prelude_trampling_2(self):
        i = Program([
            ConstDecl("putInt", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putInt\n", make_test_number()))

    def test_prelude_trampling_3(self):
        i = Program([
            ConstDecl("putIntLn", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putIntLn\n", make_test_number()))

    def test_prelude_trampling_4(self):
        i = Program([
            ConstDecl("getFloat", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: getFloat\n", make_test_number()))

    def test_prelude_trampling_5(self):
        i = Program([
            ConstDecl("putFloat", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putFloat\n", make_test_number()))

    def test_prelude_trampling_6(self):
        i = Program([
            ConstDecl("putFloatLn", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putFloatLn\n", make_test_number()))

    def test_prelude_trampling_7(self):
        i = Program([
            ConstDecl("getBool", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: getBool\n", make_test_number()))

    def test_prelude_trampling_8(self):
        i = Program([
            ConstDecl("putBool", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putBool\n", make_test_number()))

    def test_prelude_trampling_9(self):
        i = Program([
            ConstDecl("putBoolLn", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putBoolLn\n", make_test_number()))

    def test_prelude_trampling_10(self):
        i = Program([
            ConstDecl("getString", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: getString\n", make_test_number()))

    def test_prelude_trampling_11(self):
        i = Program([
            ConstDecl("putString", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putString\n", make_test_number()))

    def test_prelude_trampling_12(self):
        i = Program([
            ConstDecl("putStringLn", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putStringLn\n", make_test_number()))

    def test_prelude_trampling_13(self):
        i = Program([
            ConstDecl("putLn", IntType(), IntLiteral(0)),
        ])
        self.assertTrue(TestChecker.test(i, "Redeclared Constant: putLn\n", make_test_number()))

    def test_name_shadowing_1(self):
        i = Program([
            FuncDecl("f", [ParamDecl("p1", IntType())], VoidType(), Block([
                VarDecl("p1", FloatType(), FloatLiteral(2.5))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_name_shadowing_2(self):
        i = Program([
            VarDecl("p1", IntType(), IntLiteral(2)),
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("p1", FloatType(), FloatLiteral(2.5)),
                Assign(Id("p1"), FloatLiteral(3.0))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_name_shadowing_3(self):
        i = Program([
            FuncDecl("f", [ParamDecl("p1", IntType())], VoidType(), Block([
                VarDecl("p1", FloatType(), FloatLiteral(2.5)),
                Assign(Id("p1"), FloatLiteral(3.0))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_name_shadowing_4(self):
        i = Program([
            VarDecl("p1", BoolType(), BooleanLiteral(False)),
            FuncDecl("f", [ParamDecl("p1", IntType())], VoidType(), Block([
                Assign(Id("p1"), IntLiteral(3)),
                VarDecl("p1", FloatType(), FloatLiteral(2.5)),
                Assign(Id("p1"), FloatLiteral(3.0))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_name_shadowing_5(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                ForStep(
                    Assign(Id("i"), IntLiteral(0)),
                    BinaryOp("<", Id("i"), IntLiteral(10)),
                    Assign(Id("i"), BinaryOp("+", Id("i"), IntLiteral(1))),
                    Block([
                        VarDecl("i", FloatType(), FloatLiteral(0.0))
                    ])
                )
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_name_shadowing_6(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                ForEach(
                    Id("i"),
                    Id("it"),
                    ArrayLiteral([IntLiteral(10)], IntType(), [IntLiteral(it) for it in range(0, 10)]),
                    Block([
                        VarDecl("i", FloatType(), FloatLiteral(0.0)),
                        VarDecl("it", FloatType(), FloatLiteral(0.0))
                    ])
                )
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_implicit_declaration_1(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                Assign(Id("i"), IntLiteral(0)),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_implicit_declaration_2(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                Assign(Id("i"), IntLiteral(0)),
                Assign(Id("i"), FloatLiteral(0)),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: Assign(Id(i),FloatLiteral(0))\n", make_test_number()))

    def test_implicit_declaration_3(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                Assign(Id("i"), Id("i")),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Undeclared Identifier: i\n", make_test_number()))

    def test_implicit_declaration_4(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                ForStep(
                    Assign(Id("i"), IntLiteral(0)),
                    BooleanLiteral(False),
                    Assign(Id("i"), Id("i")),
                    Block([])
                )
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_1(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), BinaryOp("+", IntLiteral(0), IntLiteral(0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_2(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), BinaryOp("-", IntLiteral(0), IntLiteral(0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_3(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), BinaryOp("*", IntLiteral(0), IntLiteral(0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_4(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), BinaryOp("/", IntLiteral(0), IntLiteral(1))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_5(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), BinaryOp("%", IntLiteral(0), IntLiteral(1))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_6(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("+", FloatLiteral(0.0), FloatLiteral(0.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_7(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("-", FloatLiteral(0.0), FloatLiteral(0.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_8(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("*", FloatLiteral(0.0), FloatLiteral(0.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_9(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("/", FloatLiteral(0.0), FloatLiteral(1.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_10(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("+", FloatLiteral(1.5), FloatLiteral(2.5))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_11(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("-", FloatLiteral(3.0), FloatLiteral(1.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_12(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("*", FloatLiteral(2.0), FloatLiteral(3.5))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_13(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), BinaryOp("/", FloatLiteral(10.0), FloatLiteral(2.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_14(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), UnaryOp("-", IntLiteral(2))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_arithmetic_operations_15(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", FloatType(), UnaryOp("-", FloatLiteral(2))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_1(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", BooleanLiteral(True), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_2(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", BooleanLiteral(False), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_3(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), UnaryOp("!", BooleanLiteral(False))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_4(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", UnaryOp("!", BooleanLiteral(True)), BooleanLiteral(False))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_5(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", UnaryOp("!", BooleanLiteral(False)), BooleanLiteral(False))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_6(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", BooleanLiteral(True), UnaryOp("!", BooleanLiteral(False)))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_7(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", BooleanLiteral(False), UnaryOp("!", BooleanLiteral(True)))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_8(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", BinaryOp("||", BooleanLiteral(True), BooleanLiteral(False)),
                                                  BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_9(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", BinaryOp("&&", BooleanLiteral(True), BooleanLiteral(False)),
                                                  BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_10(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), UnaryOp("!", BinaryOp("&&", BooleanLiteral(True), BooleanLiteral(False)))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_bool_operations_invalid_1(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", IntLiteral(1), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(IntLiteral(1),&&,BooleanLiteral(true))\n", make_test_number()))

    def test_bool_operations_invalid_2(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", FloatLiteral(1.0), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(FloatLiteral(1.0),||,BooleanLiteral(true))\n", make_test_number()))

    def test_bool_operations_invalid_3(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), UnaryOp("!", IntLiteral(1))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: UnaryOp(!,IntLiteral(1))\n", make_test_number()))

    def test_bool_operations_invalid_4(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", BooleanLiteral(True), IntLiteral(1))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(BooleanLiteral(true),&&,IntLiteral(1))\n", make_test_number()))

    def test_bool_operations_invalid_5(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", BooleanLiteral(True), FloatLiteral(1.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(BooleanLiteral(true),||,FloatLiteral(1.0))\n", make_test_number()))

    def test_bool_operations_invalid_6(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("&&", FloatLiteral(1.0), IntLiteral(1))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(FloatLiteral(1.0),&&,IntLiteral(1))\n", make_test_number()))

    def test_bool_operations_invalid_7(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), BinaryOp("||", IntLiteral(1), FloatLiteral(1.0))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(IntLiteral(1),||,FloatLiteral(1.0))\n", make_test_number()))

    def test_bool_operations_invalid_8(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(),
                        BinaryOp("&&", BinaryOp("||", BooleanLiteral(True), IntLiteral(1)), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(BooleanLiteral(true),||,IntLiteral(1))\n", make_test_number()))

    def test_bool_operations_invalid_9(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(),
                        BinaryOp("||", BinaryOp("&&", FloatLiteral(1.0), BooleanLiteral(False)), BooleanLiteral(True))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(FloatLiteral(1.0),&&,BooleanLiteral(false))\n", make_test_number()))

    def test_bool_operations_invalid_10(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("b", BoolType(), UnaryOp("!", BinaryOp("&&", BooleanLiteral(True), FloatLiteral(1.0)))),
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: BinaryOp(BooleanLiteral(true),&&,FloatLiteral(1.0))\n", make_test_number()))

    def test_if_1(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", BoolType(), BooleanLiteral(False)),
                If(Id("i"), Block([]), Block([]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_if_2(self):
        i = Program([
            FuncDecl("f", [], VoidType(), Block([
                VarDecl("i", IntType(), IntLiteral(2)),
                If(Id("i"), Block([]), Block([]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "Type Mismatch: If(Id(i),Block([]),Block([]))\n", make_test_number()))

    def test_func_call_1(self):
        i = Program([
            FuncDecl("foo", [ParamDecl("x", IntType())], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                FuncCall("foo", [IntLiteral(1)])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_2(self):
        i = Program([
            FuncDecl("bar", [ParamDecl("x", FloatType())], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                FuncCall("bar", [FloatLiteral(1.0)])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_3(self):
        i = Program([
            FuncDecl("baz", [ParamDecl("x", BoolType())], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                FuncCall("baz", [BooleanLiteral(True)])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_4(self):
        i = Program([
            FuncDecl("str_func", [ParamDecl("s", StringType())], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                FuncCall("str_func", [StringLiteral("hello")])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_5(self):
        i = Program([
            FuncDecl("arr_func", [ParamDecl("arr", ArrayType([IntLiteral(5)], IntType()))], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("my_arr", ArrayType([IntLiteral(5)], IntType()), ArrayLiteral([IntLiteral(5)], IntType(),
                                                                                      [IntLiteral(1), IntLiteral(2),
                                                                                       IntLiteral(3), IntLiteral(4),
                                                                                       IntLiteral(5)])),
                FuncCall("arr_func", [Id("my_arr")])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_6(self):
        i = Program([
            StructType("MyStruct", [("x", IntType())], []),
            FuncDecl("struct_func", [ParamDecl("s", Id("MyStruct"))], VoidType(), Block([])),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("my_struct", Id("MyStruct"), StructLiteral("MyStruct", [("x", IntLiteral(10))])),
                FuncCall("struct_func", [Id("my_struct")])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_func_call_7(self):
        i = Program([
            FuncDecl("multi_param",
                     [ParamDecl("a", IntType()), ParamDecl("b", FloatType()), ParamDecl("c", BoolType())], VoidType(),
                     Block([])),
            FuncDecl("main", [], VoidType(), Block([
                FuncCall("multi_param", [IntLiteral(1), FloatLiteral(2.0), BooleanLiteral(True)])
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_1(self):
        i = Program([
            ConstDecl("x", IntType(), BinaryOp("+", IntLiteral(2), IntLiteral(3))),
            ConstDecl("y", IntType(), BinaryOp("*", IntLiteral(1), IntLiteral(5))),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("x")], IntType()), ArrayLiteral([Id("x")], IntType(),
                                                                             [IntLiteral(1), IntLiteral(2),
                                                                              IntLiteral(3), IntLiteral(4),
                                                                              IntLiteral(5)])),
                Assign(Id("arr"), ArrayLiteral([Id("y")], IntType(),
                                               [IntLiteral(6), IntLiteral(7), IntLiteral(8), IntLiteral(9),
                                                IntLiteral(10)]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_2(self):
        i = Program([
            ConstDecl("size", IntType(), IntLiteral(10)),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("size")], IntType()),
                        ArrayLiteral([Id("size")], IntType(), [IntLiteral(i) for i in range(10)])),
                Assign(Id("arr"), ArrayLiteral([Id("size")], IntType(), [IntLiteral(i + 10) for i in range(10)]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_3(self):
        i = Program([
            ConstDecl("dim1", IntType(), IntLiteral(2)),
            ConstDecl("dim2", IntType(), IntLiteral(3)),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("dim1"), Id("dim2")], IntType()),
                        ArrayLiteral([Id("dim1"), Id("dim2")], IntType(),
                                     [[IntLiteral(1), IntLiteral(2), IntLiteral(3)],
                                      [IntLiteral(4), IntLiteral(5), IntLiteral(6)]])),
                Assign(Id("arr"), ArrayLiteral([Id("dim1"), Id("dim2")], IntType(),
                                               [[IntLiteral(7), IntLiteral(8), IntLiteral(9)],
                                                [IntLiteral(10), IntLiteral(11), IntLiteral(12)]]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_4(self):
        i = Program([
            ConstDecl("dim", IntType(), BinaryOp("/", IntLiteral(10), IntLiteral(2))),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("dim")], IntType()), ArrayLiteral([Id("dim")], IntType(),
                                                                               [IntLiteral(1), IntLiteral(2),
                                                                                IntLiteral(3), IntLiteral(4),
                                                                                IntLiteral(5)])),
                Assign(Id("arr"), ArrayLiteral([Id("dim")], IntType(),
                                               [IntLiteral(6), IntLiteral(7), IntLiteral(8), IntLiteral(9),
                                                IntLiteral(10)]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_5(self):
        i = Program([
            ConstDecl("dim1", IntType(), BinaryOp("%", IntLiteral(11), IntLiteral(3))),
            ConstDecl("dim2", IntType(), BinaryOp("-", IntLiteral(7), IntLiteral(4))),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("dim1"), Id("dim2")], IntType()),
                        ArrayLiteral([Id("dim1"), Id("dim2")], IntType(),
                                     [[IntLiteral(1), IntLiteral(2), IntLiteral(3)],
                                      [IntLiteral(4), IntLiteral(5), IntLiteral(6)]])),
                Assign(Id("arr"), ArrayLiteral([Id("dim1"), Id("dim2")], IntType(),
                                               [[IntLiteral(7), IntLiteral(8), IntLiteral(9)],
                                                [IntLiteral(10), IntLiteral(11), IntLiteral(12)]]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))

    def test_const_array_dim_6(self):
        i = Program([
            ConstDecl("dim", IntType(), UnaryOp("-", IntLiteral(-5))),
            FuncDecl("main", [], VoidType(), Block([
                VarDecl("arr", ArrayType([Id("dim")], IntType()), ArrayLiteral([Id("dim")], IntType(),
                                                                               [IntLiteral(1), IntLiteral(2),
                                                                                IntLiteral(3), IntLiteral(4),
                                                                                IntLiteral(5)])),
                Assign(Id("arr"), ArrayLiteral([Id("dim")], IntType(),
                                               [IntLiteral(6), IntLiteral(7), IntLiteral(8), IntLiteral(9),
                                                IntLiteral(10)]))
            ]))
        ])
        self.assertTrue(TestChecker.test(i, "", make_test_number()))
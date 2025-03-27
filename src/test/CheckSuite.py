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
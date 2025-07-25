"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=I5aT1fRa9Mc
 * @note https://www.youtube.com/watch?v=rCWrqSqhcJ8
"""
from abc import ABC
from functools import reduce
from typing import Optional, List, Union, Tuple

import AST
import StaticCheck
from Emitter import Emitter
from Frame import Frame
from Utils import Utils
from Visitor import BaseVisitor


class Val(ABC):
    pass

class Index(Val):
    def __init__(self, value):
        #value: Int

        self.value = value

class CName(Val):
    def __init__(self, value, isStatic=True):
        #value: String
        self.isStatic = isStatic
        self.value = value

###### For transforming & simplifying the AST to something closer to an in-memory IR ######

class BadCoverage(Exception):
    def __str__(self):
        return f"Either input AST has an error that would have been caught by StaticChecker, or Simplifier/CodeGeneration has a bug"

class CtxObject:
    def __init__(self):
        pass

# For name resolution.

class Sym(CtxObject):
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.name = name

class StructSym(Sym):
    original_ast: AST.StructType

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.StructType):
        super().__init__(name)
        self.original_ast = original_ast

        self.being_checked = False
        self.done_resolving = False

class InterfaceSym(Sym):
    original_ast: AST.InterfaceType

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.InterfaceType):
        super().__init__(name)
        self.original_ast = original_ast

        self.being_checked = False
        self.done_resolving = False

class FunctionSym(Sym):
    original_ast: Union[AST.FuncDecl, Tuple[str, List[AST.Type], AST.Type]]
    done_resolving: bool

    def __init__(self, name: str, original_ast: Union[AST.FuncDecl, Tuple[str, List[AST.Type], AST.Type]]):
        super().__init__(name)
        self.original_ast = original_ast
        self.done_resolving = False

class VarSym(Sym):
    original_ast: Union[AST.VarDecl, AST.Id]

    def __init__(self, name: str, original_ast: Union[AST.VarDecl, AST.Id]):
        super().__init__(name)
        self.original_ast = original_ast # VarDecl for usual vars, Id for loops

class ConstSym(Sym):
    original_ast: AST.ConstDecl
    global_symbol_index: Optional[int]

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.ConstDecl):
        super().__init__(name)
        self.original_ast = original_ast
        self.global_symbol_index = None

        self.being_checked = False
        self.done_resolving = False

class FnParamSym(Sym):
    parameter_type: AST.Type

    def __init__(self, name: str, parameter_type: AST.Type):
        super().__init__(name)
        self.parameter_type = parameter_type

# Cheap hack for resolving methods.

class SimplifierUnresolvedMethod(CtxObject):
    original_ast: AST.MethodDecl
    struct_symbol: Optional[StructSym]

    def __init__(self, original_ast: AST.MethodDecl):
        super().__init__()
        self.original_ast = original_ast
        self.struct_symbol = None

# Identifier resolution mode

class SimplifierIdResolutionMode(CtxObject):
    def __init__(self):
        super().__init__()

class SimplifierIsExpressionVisit(SimplifierIdResolutionMode):
    def __init__(self):
        super().__init__()

class SimplifierIsTypenameVisit(SimplifierIdResolutionMode):
    def __init__(self):
        super().__init__()

# For banning function/method calls and references to non-consts.

class SimplifierIsComptimeExpressionVisit(CtxObject):
    def __init__(self):
        super().__init__()

# Special nil type.

class SimplifierNilType:
    def __init__(self):
        pass

# Assistive casts

class ConvertIntToFloat(AST.Expr):
    original_int_expr: AST.Expr

    def __init__(self, original_int_expr: AST.Expr):
        self.original_int_expr = original_int_expr

    def __str__(self):
        return "ConvertIntToFloat(" + str(self.original_int_expr) + ")"

    def accept(self, v, param):
        return v.visitConvertIntToFloat(self, param)

# TODO: assistive exprs that cast:
#  - nils to structs
#  - nils to interfaces
#  - structs to interfaces
#  - int arrays to float arrays

# Assistive concrete expressions

class ConcreteStructLiteral(AST.Literal):
    struct: AST.StructType
    elements: List[Tuple[str,AST.Expr]] # [] if there is no elements

    def __init__(self, struct: AST.StructType, elements: List[Tuple[str,AST.Expr]]):
        self.struct = struct
        self.elements = elements

    def __str__(self):
        return "ConcreteStructLiteral(" + self.struct.name + ',[' + ','.join(("("+str(i)+","+str(j)+")") for i,j in self.elements) + "])"

    def accept(self, v, param):
        return v.visitConcreteStructLiteral(self, param)

class ConcreteFuncCall(AST.Expr, AST.Stmt):
    func: Union[AST.FuncDecl, Tuple[str, str, List[AST.Type], AST.Type]]
    args: List[AST.Expr] # [] if there is no arg

    def __init__(self, func: Union[AST.FuncDecl, Tuple[str, str, List[AST.Type], AST.Type]], args: List[AST.Expr]):
        self.func = func
        self.args = args

    def __str__(self):
        return "ConcreteFuncCall(" + str(self.func.name) + ",[" +  ','.join(str(i) for i in self.args) + "])"

    def accept(self, v, param):
        return v.visitConcreteFuncCall(self, param)

class Simplifier(BaseVisitor):
    global_declarations: List[CtxObject]
    root_ast: AST.Program

    def __init__(self, root_ast: AST.Program):
        self.global_declarations = self.create_prelude()
        self.root_ast = root_ast

    @staticmethod
    def hard_compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        if isinstance(a, AST.ArrayType) and isinstance(b, AST.ArrayType):
            return Simplifier.hard_compare_types(a.eleType, b.eleType) and len(a.dimens) == len(b.dimens) and all(
                isinstance(a, AST.IntLiteral) and isinstance(b, AST.IntLiteral) and a.value == b.value for a, b in
                zip(a.dimens, b.dimens))
        return type(a) == type(b)

    def maybe_wrap_cast_a_to_b(self, a_ty: AST.Type, b_ty: AST.Type, a_expr: AST.Expr):
        # TODO: nil-to-struct and nil-to-interface casts.

        # Allow going from ints to floats.
        if isinstance(a_ty, AST.IntType) and isinstance(b_ty, AST.FloatType):
            return ConvertIntToFloat(a_expr)

        if isinstance(a_ty, AST.StructType) and isinstance(b_ty, AST.StructType):
            # Type-check skipped
            return a_expr

        if isinstance(a_ty, AST.InterfaceType) and isinstance(b_ty, AST.InterfaceType):
            # Type-check skipped
            return a_expr

        # Allow structs to be cast to interfaces.
        if isinstance(a_ty, AST.StructType) and isinstance(b_ty, AST.InterfaceType):
            if b_ty not in a_ty.implements:
                a_ty.implements.append(b_ty)
            return a_expr

        if isinstance(a_ty, AST.ArrayType) and isinstance(b_ty, AST.ArrayType):
            return a_expr # TODO

        return a_expr

    def simplify_nested_list(self, original_ast: AST.ArrayLiteral, ast: AST.NestedList, ele_type: AST.Type, dimens: List[AST.IntLiteral], given_scope: List[CtxObject]):
        if len(dimens) > 1:
            return [self.simplify_nested_list(original_ast, sublist, ele_type, dimens[1:], given_scope) for sublist in ast]
        else:
            processed = []
            for ele in ast:
                this_ele_expr, this_ele_type = self.visit(ele, given_scope) # No need to append IsExpressionVisit.
                this_ele_expr = self.maybe_wrap_cast_a_to_b(this_ele_type, ele_type, this_ele_expr)
                processed.append(this_ele_expr)
            return processed

    @staticmethod
    def create_prelude():
        get_int = FunctionSym("getInt", ("io", [], AST.IntType()))
        get_int.parent_class = "io"
        get_int.done_resolving = True

        put_int = FunctionSym("putInt", ("io", [AST.IntType()], AST.VoidType()))
        put_int.done_resolving = True

        put_int_ln = FunctionSym("putIntLn", ("io", [AST.IntType()], AST.VoidType()))
        put_int_ln.done_resolving = True

        get_float = FunctionSym("getFloat", ("io", [], AST.FloatType()))
        get_float.done_resolving = True

        put_float = FunctionSym("putFloat", ("io", [AST.FloatType()], AST.VoidType()))
        put_float.done_resolving = True

        put_float_ln = FunctionSym("putFloatLn", ("io", [AST.FloatType()], AST.VoidType()))
        put_float_ln.done_resolving = True

        get_bool = FunctionSym("getBool", ("io", [], AST.BoolType()))
        get_bool.done_resolving = True

        put_bool = FunctionSym("putBool", ("io", [AST.BoolType()], AST.VoidType()))
        put_bool.done_resolving = True

        put_bool_ln = FunctionSym("putBoolLn", ("io", [AST.BoolType()], AST.VoidType()))
        put_bool_ln.done_resolving = True

        get_string = FunctionSym("getString", ("io", [], AST.StringType()))
        get_string.done_resolving = True

        put_string = FunctionSym("putString", ("io", [AST.StringType()], AST.VoidType()))
        put_string.done_resolving = True

        put_string_ln = FunctionSym("putStringLn", ("io", [AST.StringType()], AST.VoidType()))
        put_string_ln.done_resolving = True

        put_ln = FunctionSym("putLn", ("io", [], AST.VoidType()))
        put_ln.done_resolving = True

        return [
            get_int,
            put_int,
            put_int_ln,
            get_float,
            put_float,
            put_float_ln,
            get_bool,
            put_bool,
            put_bool_ln,
            get_string,
            put_string,
            put_string_ln,
            put_ln,
        ]

    # Unified from global_make_default_value and local_make_default_value.
    # For checking global objects:
    #   - pass an int as a global scope object index limit.
    # For checking local objects:
    #   - pass a List[ScopeObject] for local scoping.
    def make_default_value(self, typename: AST.Type, scoping: Union[int, List[CtxObject]], make_nested_list: bool = False):
        if isinstance(typename, AST.IntType):
            return AST.IntLiteral(0)
        elif isinstance(typename, AST.FloatType):
            return AST.FloatLiteral(0.0)
        elif isinstance(typename, AST.StringType):
            return AST.StringLiteral("\"\"")
        elif isinstance(typename, AST.BoolType):
            return AST.BooleanLiteral(False)
        elif isinstance(typename, AST.ArrayType):
            # Sanity check.
            d = typename.dimens[0]
            if not isinstance(d, AST.IntLiteral):
                raise BadCoverage()
            child_type = AST.ArrayType(typename.dimens[1:], typename.eleType) if len(typename.dimens) > 1 else typename.eleType
            vals: AST.NestedList = [self.make_default_value(child_type, scoping, True) for _ in range(d.value)]
            if make_nested_list:
                return vals
            return AST.ArrayLiteral(typename.dimens, typename.eleType, vals)
        elif isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Sym) and (sym.name == typename.name):
                    if isinstance(sym, StructSym):
                        return ConcreteStructLiteral(sym.original_ast, [])
                    elif isinstance(sym, InterfaceSym):
                        return AST.NilLiteral()
                    elif (isinstance(sym, ConstSym) or isinstance(sym, VarSym)) and (isinstance(scoping, List) or (i < scoping)):
                        raise BadCoverage()
            raise BadCoverage()
        elif isinstance(typename, AST.StructType):
            return ConcreteStructLiteral(typename, [])
        return AST.NilLiteral()

    def make_unreachable_value(self, typename: AST.Type):
        if isinstance(typename, AST.IntType):
            return AST.IntLiteral(0)
        elif isinstance(typename, AST.FloatType):
            return AST.FloatLiteral(0.0)
        elif isinstance(typename, AST.BoolType):
            return AST.BooleanLiteral(False)
        return AST.NilLiteral()

    # Unified from global_comptime_evaluate and local_comptime_evaluate.
    # For global consts:
    #   - pass an int as a global scope object index limit.
    # For local consts:
    #   - pass a List[ScopeObject] for local scoping.
    def comptime_evaluate(self, ast: AST.Expr, scoping: Union[int, List[CtxObject]]):
        if isinstance(ast, AST.Id):
            symbols = self.global_declarations if isinstance(scoping, int) else filter(lambda x: isinstance(x, Sym), reversed(scoping))
            for i, sym in enumerate(symbols):
                if isinstance(sym, Sym) and (sym.name == ast.name):
                    if isinstance(sym, ConstSym):
                        if isinstance(scoping, List) or i < scoping:
                            if isinstance(scoping, int):
                                # In midst of global comptime resolution! Need to resolve this const before using it.
                                self.global_resolve_constant(sym, scoping)
                            return sym.original_ast.iniExpr
                    else:
                        raise BadCoverage()
            raise BadCoverage()
        elif isinstance(ast, AST.FuncCall) or isinstance(ast, AST.MethCall):
            # Function calls are not allowed at compilation-time evaluation.
            raise BadCoverage()
        elif isinstance(ast, AST.ArrayCell):
            receiver = self.comptime_evaluate(ast.arr, scoping)
            if not isinstance(receiver, AST.ArrayLiteral):
                raise BadCoverage()

            inner: AST.NestedList = receiver.value
            resulting_dimens = receiver.dimens

            for it in ast.idx:
                if not isinstance(inner, list):
                    raise BadCoverage()
                e = self.comptime_evaluate(it, scoping)
                if not isinstance(e, AST.IntLiteral):
                    raise BadCoverage()
                if e.value < 0 or e.value >= len(inner):
                    raise BadCoverage()
                inner = inner[e.value]
                resulting_dimens = resulting_dimens[:-1]

            if isinstance(inner, list):
                return AST.ArrayLiteral(resulting_dimens, receiver.eleType, inner)
        elif isinstance(ast, AST.FieldAccess):
            receiver = self.comptime_evaluate(ast.receiver, scoping)
            field = ast.field
            if not isinstance(receiver, ConcreteStructLiteral):
                raise BadCoverage()

            q: Optional[Tuple[str, AST.Expr]] = next(filter(lambda t: t[0] == field, receiver.elements), None)
            if q is None:
                field_type = next(filter(lambda x: x[0] == field, receiver.struct.elements))[1]
                return self.make_default_value(field_type, scoping)
            return self.comptime_evaluate(q[1], scoping)

        elif isinstance(ast, AST.BinaryOp):
            lhs = self.comptime_evaluate(ast.left, scoping)
            rhs = self.comptime_evaluate(ast.right, scoping)
            if ast.op == "+":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value + rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) + float(rhs.value))
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.StringLiteral(f"\"{lhs.value[1:-1]}{rhs.value[1:-1]}\"")
                else:
                    raise BadCoverage()
            elif ast.op == "-":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value - rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) - float(rhs.value))
                else:
                    raise BadCoverage()
            elif ast.op == "*":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value * rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) * float(rhs.value))
                else:
                    raise BadCoverage()
            elif ast.op == "/":
                # TODO: Ask prof. Phung what to do when RHS is zero.
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(int(lhs.value / rhs.value))
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) / float(rhs.value))
                else:
                    raise BadCoverage()
            elif ast.op == "%":
                # TODO: Ask prof. Phung what to do when RHS is zero.
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value % rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == ">":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "<":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == ">=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "<=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "==":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "!=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "&&":
                if isinstance(lhs, AST.BooleanLiteral) and isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(lhs.value and rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "||":
                if isinstance(lhs, AST.BooleanLiteral) and isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(lhs.value or rhs.value)
                else:
                    raise BadCoverage()
            else:
                raise BadCoverage()
        elif isinstance(ast, AST.UnaryOp):
            rhs = self.comptime_evaluate(ast.body, scoping)
            if ast.op == "!":
                if isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(not rhs.value)
                else:
                    raise BadCoverage()
            elif ast.op == "-":
                if isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(-rhs.value)
                elif isinstance(rhs, AST.FloatLiteral):
                    return AST.FloatLiteral(-rhs.value)
                else:
                    raise BadCoverage()
            else:
                raise BadCoverage()
        elif isinstance(ast, AST.StructLiteral):
            symbols = self.global_declarations if isinstance(scoping, int) else filter(lambda x: isinstance(x, Sym), reversed(scoping))
            for i, sym in enumerate(symbols):
                if isinstance(sym, Sym) and (sym.name == ast.name):
                    if not isinstance(sym, StructSym):
                        raise BadCoverage()
                    self.global_resolve_struct_definition(sym, max(scoping, i) if isinstance(scoping, int) else scoping)
                    elements_ast: List[Tuple[str, AST.Expr]] = ast.elements
                    return ConcreteStructLiteral(sym.original_ast, [
                        (name, self.comptime_evaluate(val, scoping)) for name, val in elements_ast
                    ])
            raise BadCoverage()
        else:
            # Probably NilLiteral or ArrayLiteral.
            return ast

    @staticmethod
    def type_of_literal(ast: AST.Literal):
        if isinstance(ast, AST.IntLiteral):
            return AST.IntType()
        if isinstance(ast, AST.FloatLiteral):
            return AST.FloatType()
        if isinstance(ast, AST.StringLiteral):
            return AST.StringType()
        if isinstance(ast, AST.BooleanLiteral):
            return AST.BoolType()
        if isinstance(ast, AST.ArrayLiteral):
            return AST.ArrayType(ast.dimens, ast.eleType)
        if isinstance(ast, ConcreteStructLiteral):
            return ast.struct
        if isinstance(ast, AST.NilLiteral):
            return SimplifierNilType()
        raise BadCoverage()

    # Global things get their own set of functions because of complicated identifier dependencies.
    def global_resolve_struct_definition(self, sym: StructSym, index_limit: int):
        if sym.done_resolving:
            return sym.original_ast

        if sym.being_checked:
            # Allow structs to have fields pointing to themselves...?
            return sym.original_ast

        sym.being_checked = True
        sym.original_ast.elements = [(name, self.global_resolve_typename(typename, index_limit)) for name, typename in sym.original_ast.elements]
        sym.being_checked = False
        sym.done_resolving = True
        return sym.original_ast

    def global_resolve_interface_definition(self, sym: InterfaceSym, index_limit: int):
        if sym.done_resolving:
            return sym.original_ast

        if sym.being_checked:
            # Allow interfaces to have methods returning themselves.
            return sym.original_ast

        sym.being_checked = True
        for prototype in sym.original_ast.methods:
            prototype.params = [self.global_resolve_typename(it, index_limit) for it in prototype.params]
            prototype.retType = self.global_resolve_typename(prototype.retType, index_limit)
        sym.being_checked = False
        sym.done_resolving = True
        return sym.original_ast

    def global_resolve_function_definition(self, sym: FunctionSym, index_limit: int):
        if sym.done_resolving:
            return

        ast = sym.original_ast
        if not isinstance(ast, AST.FuncDecl):
            return # cheap hack
        ast.retType = self.global_resolve_typename(ast.retType, index_limit)
        ast.params = [AST.ParamDecl(it.parName, self.global_resolve_typename(it.parType, index_limit)) for it in ast.params]

        sym.done_resolving = True

    def global_resolve_method_definition(self, ast: AST.MethodDecl, index_limit: int):
        ast.recType = self.global_resolve_typename(ast.recType, index_limit)
        ast.fun.retType = self.global_resolve_typename(ast.fun.retType, index_limit)
        ast.fun.params = [AST.ParamDecl(it.parName, self.global_resolve_typename(it.parType, index_limit)) for it in ast.fun.params]

    def global_resolve_constant(self, sym: ConstSym, index_limit: int):
        if sym.done_resolving:
            return

        sym.being_checked = True
        simplified = self.comptime_evaluate(sym.original_ast.iniExpr, index_limit)
        sym.original_ast.iniExpr = simplified
        if sym.original_ast.conType is None:
            sym.original_ast.conType = self.type_of_literal(simplified)
        else:
            sym.original_ast.conType = self.global_resolve_typename(sym.original_ast.conType, index_limit)
        # Explicit type is ignored; we already went over it in static checking
        sym.being_checked = False
        sym.done_resolving = True

    def global_resolve_typename(self, typename: AST.Type, index_limit: int):
        if isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Sym) and (sym.name == typename.name):
                    if isinstance(sym, StructSym):
                        if sym.being_checked:
                            return sym.original_ast
                        return self.global_resolve_struct_definition(sym, index_limit)
                    elif isinstance(sym, InterfaceSym):
                        if sym.being_checked:
                            return sym.original_ast
                        return self.global_resolve_interface_definition(sym, index_limit)
                    elif (i < index_limit) and (isinstance(sym, ConstSym) or isinstance(sym, VarSym)):
                        raise BadCoverage()
            raise BadCoverage()
        elif isinstance(typename, AST.ArrayType):
            dimensions = [self.comptime_evaluate(it, index_limit) for it in typename.dimens]
            if not all(isinstance(dimension, AST.IntLiteral) for dimension in dimensions):
                raise BadCoverage()
            resolved_element_type = self.global_resolve_typename(typename.eleType, index_limit)
            return AST.ArrayType(dimensions, resolved_element_type)
        return typename

    def simplify(self):
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: List[CtxObject]):
        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                self.global_declarations.append(StructSym(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                self.global_declarations.append(InterfaceSym(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                self.global_declarations.append(FunctionSym(thing.name, thing))
            elif isinstance(thing, AST.MethodDecl):
                self.global_declarations.append(SimplifierUnresolvedMethod(thing))
            elif isinstance(thing, AST.ConstDecl):
                self.global_declarations.append(ConstSym(thing.conName, thing))
            elif isinstance(thing, AST.VarDecl):
                self.global_declarations.append(VarSym(thing.varName, thing))

        for i, sym in enumerate(self.global_declarations):
            if isinstance(sym, StructSym):
                self.global_resolve_struct_definition(sym, i)
            elif isinstance(sym, InterfaceSym):
                self.global_resolve_interface_definition(sym, i)
            elif isinstance(sym, FunctionSym):
                # Cheap hack to filter out the prelude.
                if isinstance(sym.original_ast, AST.FuncDecl):
                    self.global_resolve_function_definition(sym, i)
            elif isinstance(sym, SimplifierUnresolvedMethod):
                recv_ty: AST.Id = sym.original_ast.recType # NOTE: forced typing
                recv_name = recv_ty.name
                struct: Optional[StructSym] = next(filter(lambda x: isinstance(x, StructSym) and (x.name == recv_name), self.global_declarations))
                if struct is None:
                    raise BadCoverage()
                struct.original_ast.methods.append(sym.original_ast)
                sym.struct_symbol = struct
                self.global_resolve_method_definition(sym.original_ast, i)
            elif isinstance(sym, ConstSym):
                self.global_resolve_constant(sym, i)

        my_scope = given_scope.copy()

        for sym in self.global_declarations:
            if isinstance(sym, StructSym):
                my_scope.append(sym)
            elif isinstance(sym, InterfaceSym):
                my_scope.append(sym)
            elif isinstance(sym, FunctionSym):
                my_scope.append(sym)

        for sym in self.global_declarations:
            if isinstance(sym, StructSym):
                self.visit(sym.original_ast, my_scope)
            elif isinstance(sym, InterfaceSym):
                self.visit(sym.original_ast, my_scope)
            # Cheap hack to filter out the prelude.
            elif isinstance(sym, FunctionSym) and isinstance(sym.original_ast, AST.FuncDecl):
                self.visit(sym.original_ast, my_scope)
            elif isinstance(sym, SimplifierUnresolvedMethod):
                self.visit(sym.original_ast, my_scope + [sym])
            elif isinstance(sym, ConstSym):
                self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)
            elif isinstance(sym, VarSym):
                sym.resolved_type = self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)

        return AST.Program(list(filter(lambda x: not isinstance(x, AST.MethodDecl), ast.decl)))

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: List[CtxObject]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        if ast.varInit is None:
            resolved_type = self.visit(ast.varType, given_scope + [SimplifierIsTypenameVisit()])
            resolved_expr = self.make_default_value(resolved_type, given_scope)
            ast.varType = resolved_type
            ast.varInit = resolved_expr
        else:
            resolved_expr, resolved_type = self.visit(ast.varInit, given_scope + [SimplifierIsExpressionVisit()])
            if ast.varType is None:
                ast.varType = resolved_type
            else:
                ast.varType = self.visit(ast.varType, given_scope + [SimplifierIsTypenameVisit()])
            ast.varInit = self.maybe_wrap_cast_a_to_b(resolved_type, ast.varType, resolved_expr)

        return ast

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: List[CtxObject]):
        resolved_expr, resolved_type = self.visit(ast.iniExpr, given_scope + [SimplifierIsExpressionVisit()])
        if ast.conType is None:
            ast.conType = resolved_type
        else:
            ast.conType = self.visit(ast.conType, given_scope + [SimplifierIsTypenameVisit()])
        ast.iniExpr = self.maybe_wrap_cast_a_to_b(resolved_type, ast.conType, resolved_expr)

        return ast

    def visitFuncDecl(self, ast: AST.FuncDecl, given_scope: List[CtxObject]):
        my_scope = given_scope.copy()
        for i, param in enumerate(ast.params):
            my_scope.append(FnParamSym(param.parName, ast.params[i].parType))
        ast.body = self.visit(ast.body, my_scope)

    def visitMethodDecl(self, ast: AST.MethodDecl, given_scope: List[CtxObject]):
        my_scope = given_scope.copy()
        my_scope.append(FnParamSym(ast.receiver, ast.recType))
        for i, param in enumerate(ast.fun.params):
            my_scope.append(FnParamSym(param.parName, param.parType))
        if not isinstance(ast.fun.retType, AST.VoidType):
            ast.fun.body.member.append(AST.Return(self.make_unreachable_value(ast.fun.retType)))
        ast.fun.body = self.visit(ast.fun.body, my_scope)

    def visitPrototype(self, ast, param):
        return ast # ???

    def visitIntType(self, ast, param):
        return ast # Intentional.

    def visitFloatType(self, ast, param):
        return ast # Intentional.

    def visitBoolType(self, ast, param):
        return ast # Intentional.

    def visitStringType(self, ast, param):
        return ast # Intentional.

    def visitVoidType(self, ast, param):
        return ast # Intentional.

    def visitArrayType(self, ast: AST.ArrayType, given_scope: List[CtxObject]):
        return AST.ArrayType([self.comptime_evaluate(it, given_scope) for it in ast.dimens], self.visit(ast.eleType, given_scope))

    def visitStructType(self, ast: AST.StructType, given_scope: List[CtxObject]):
        return ast # Intentional.

    def visitInterfaceType(self, ast: AST.InterfaceType, given_scope: List[CtxObject]):
        return ast # Intentional.

    def visitBlock(self, ast: AST.Block, given_scope: List[CtxObject]):
        resulting_block = []

        my_scope = given_scope.copy()

        # Vars and consts within the same block cannot collide names. Inner blocks can shadow.
        for statement in ast.member:
            if isinstance(statement, AST.VarDecl):
                sym = VarSym(statement.varName, statement)
                sym.resolved_type = self.visit(statement, my_scope)
                my_scope.append(sym)
                resulting_block.append(statement)
            elif isinstance(statement, AST.ConstDecl):
                sym = ConstSym(statement.conName, statement)
                sym.resolved_type = self.visit(statement, my_scope)
                sym.resolved_value = self.comptime_evaluate(statement.iniExpr, my_scope) if (statement.iniExpr is not None) else None
                my_scope.append(sym)
                resulting_block.append(statement)
            elif isinstance(statement, AST.Expr):
                expr_simplified, expr_type = self.visit(statement, my_scope + [SimplifierIsExpressionVisit()])
                resulting_block.append(expr_simplified)
            elif isinstance(statement, AST.Assign) and isinstance(statement.lhs, AST.Id):
                lhs: AST.Id = statement.lhs
                # Is the name not declared? If so, turn it into a variable declaration.
                existing_maybe_variable = next(filter(lambda x: isinstance(x, Sym) and (x.name == lhs.name), reversed(my_scope)), None)
                if existing_maybe_variable is None or not (isinstance(existing_maybe_variable, VarSym) or isinstance(existing_maybe_variable, ConstSym) or isinstance(existing_maybe_variable, FnParamSym)):
                    simplified_expr, implicit_type = self.visit(statement.rhs, my_scope + [SimplifierIsExpressionVisit()])
                    fake_ast = AST.VarDecl(lhs.name, implicit_type, simplified_expr)
                    sym = VarSym(lhs.name, fake_ast)
                    my_scope.append(sym)
                    resulting_block.append(fake_ast)
                else:
                    resulting_block.append(self.visit(statement, my_scope))
            else:
                # This is probably a statement.
                resulting_block.append(self.visit(statement, my_scope))
        return AST.Block(resulting_block)

    def visitAssign(self, ast: AST.Assign, given_scope: List[CtxObject]):
        lhs_expr, lhs_type = self.visit(ast.lhs, given_scope + [SimplifierIsExpressionVisit()])
        rhs_expr, rhs_type = self.visit(ast.rhs, given_scope + [SimplifierIsExpressionVisit()])
        return AST.Assign(lhs_expr, self.maybe_wrap_cast_a_to_b(rhs_type, lhs_type, rhs_expr))

    def visitIf(self, ast: AST.If, given_scope: List[CtxObject]):
        simplified_condition, condition_type = self.visit(ast.expr, given_scope + [SimplifierIsExpressionVisit()])
        ast.expr = simplified_condition
        ast.thenStmt = self.visit(ast.thenStmt, given_scope)
        if ast.elseStmt is not None:
            ast.elseStmt = self.visit(ast.elseStmt, given_scope)
        return ast

    def visitForBasic(self, ast: AST.ForBasic, given_scope: List[CtxObject]):
        condition_expr, condition_type = self.visit(ast.cond, given_scope + [SimplifierIsExpressionVisit()])
        ast.cond = condition_expr
        ast.loop = self.visit(ast.loop, given_scope)
        return ast

    def visitForStep(self, ast: AST.ForStep, given_scope: List[CtxObject]):
        my_scope = given_scope.copy()

        if isinstance(ast.init, AST.VarDecl):
            sym = VarSym(ast.init.varName, ast.init)
            ast.init = self.visit(ast.init, my_scope)
            my_scope.append(sym)
        elif isinstance(ast.init, AST.Assign) and isinstance(ast.init.lhs, AST.Id):
            lhs: AST.Id = ast.init.lhs
            # Is the name not declared? If so, turn it into a variable declaration.
            existing_maybe_variable = next(filter(lambda x: isinstance(x, Sym) and (x.name == lhs.name), reversed(my_scope)), None)
            if existing_maybe_variable is None or not (isinstance(existing_maybe_variable, VarSym) or isinstance(existing_maybe_variable, ConstSym) or isinstance(existing_maybe_variable, FnParamSym)):
                simplified_expr, implicit_type = self.visit(ast.init.rhs, my_scope + [SimplifierIsExpressionVisit()])
                fake_ast = AST.VarDecl(lhs.name, implicit_type, simplified_expr)
                ast.init = fake_ast
                my_scope.append(VarSym(lhs.name, fake_ast))
            else:
                ast.init = self.visit(ast.init, my_scope)
        elif isinstance(ast.init, AST.Expr):
            init_expr, init_type = self.visit(ast.init, my_scope)
            ast.init = init_expr
        else:
            self.visit(ast.init, my_scope)

        condition_expr, condition_type = self.visit(ast.cond, my_scope + [SimplifierIsExpressionVisit()])
        ast.cond = condition_expr

        # This is just an assign.
        ast.upda = self.visit(ast.upda, my_scope)

        ast.loop = self.visit(ast.loop, my_scope)
        return ast

    def visitForEach(self, ast: AST.ForEach, given_scope: List[CtxObject]):
        my_scope = given_scope.copy()

        idx_sym = next(filter(lambda x: isinstance(x, Sym) and (x.name == ast.idx.name), reversed(my_scope)), None)
        if idx_sym is None or not (isinstance(idx_sym, VarSym) or isinstance(idx_sym, FnParamSym)):
            raise BadCoverage()

        value_sym = next(filter(lambda x: isinstance(x, Sym) and (x.name == ast.value.name), reversed(my_scope)), None)
        if value_sym is None or not (isinstance(value_sym, VarSym) or isinstance(value_sym, FnParamSym)):
            raise BadCoverage()

        iteration_target_expr, iteration_target_type = self.visit(ast.arr, my_scope + [SimplifierIsExpressionVisit()])
        ast.arr = iteration_target_expr

        ast.loop = self.visit(ast.loop, my_scope)
        return ast

    def visitContinue(self, ast: AST.Continue, given_scope: List[CtxObject]):
        return ast

    def visitBreak(self, ast: AST.Break, given_scope: List[CtxObject]):
        return ast

    def visitReturn(self, ast: AST.Return, given_scope: List[CtxObject]):
        if ast.expr is not None:
            expr, expr_type = self.visit(ast.expr, given_scope + [SimplifierIsExpressionVisit()])
            ast.expr = expr
        return ast

    def visitBinaryOp(self, ast: AST.BinaryOp, given_scope: List[CtxObject]):
        lhs_expr, lhs = self.visit(ast.left, given_scope)
        rhs_expr, rhs = self.visit(ast.right, given_scope)
        if ast.op == "+":
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.IntType()
            if isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, ConvertIntToFloat(rhs_expr)), AST.FloatType()
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.FloatType):
                return AST.BinaryOp(ast.op, ConvertIntToFloat(lhs_expr), rhs_expr), AST.FloatType()
            if isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.FloatType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.FloatType()
            if isinstance(lhs, AST.StringType) and isinstance(rhs, AST.StringType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.StringType()
        if ast.op in ["-", "*", "/"]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.IntType()
            if isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, ConvertIntToFloat(rhs_expr)), AST.FloatType()
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.FloatType):
                return AST.BinaryOp(ast.op, ConvertIntToFloat(lhs_expr), rhs_expr), AST.FloatType()
            if isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.FloatType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.FloatType()
        if ast.op == "%":
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.IntType()
        if ast.op in [">", "<", ">=", "<=", "==", "!="]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.BoolType()
            if isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.FloatType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.BoolType()
            if isinstance(lhs, AST.StringType) and isinstance(rhs, AST.StringType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.BoolType()
        if ast.op in ["&&", "||"]:
            if isinstance(lhs, AST.BoolType) and isinstance(rhs, AST.BoolType):
                return AST.BinaryOp(ast.op, lhs_expr, rhs_expr), AST.BoolType()
        raise BadCoverage()

    def visitUnaryOp(self, ast: AST.UnaryOp, given_scope: List[CtxObject]):
        rhs_expr, rhs = self.visit(ast.body, given_scope)
        if ast.op == "!":
            if isinstance(rhs, AST.BoolType):
                return AST.UnaryOp(ast.op, rhs_expr), AST.BoolType()
        if ast.op == "-":
            if isinstance(rhs, AST.IntType):
                return AST.UnaryOp(ast.op, rhs_expr), AST.IntType()
            if isinstance(rhs, AST.FloatType):
                return AST.UnaryOp(ast.op, rhs_expr), AST.FloatType()
        raise BadCoverage()

    def visitFuncCall(self, ast: AST.FuncCall, given_scope: List[CtxObject]):
        args: List[Tuple[AST.Expr, AST.Type]] = [self.visit(it, given_scope) for it in ast.args]
        for sym in filter(lambda x: isinstance(x, Sym), reversed(given_scope)):
            if sym.name == ast.funName:
                if isinstance(sym, FunctionSym):
                    if isinstance(sym.original_ast, AST.FuncDecl):
                        casted_args = [
                            self.maybe_wrap_cast_a_to_b(source_type, target_parameter.parType, source_expr)
                            for (source_expr, source_type), target_parameter in zip(args, sym.original_ast.params)
                        ]
                        return ConcreteFuncCall(sym.original_ast, casted_args), sym.original_ast.retType
                    parent_class, param_types, ret_type = sym.original_ast
                    casted_args = [
                        self.maybe_wrap_cast_a_to_b(source_type, target_type, source_expr)
                        for (source_expr, source_type), target_type in zip(args, param_types)
                    ]
                    return ConcreteFuncCall((ast.funName, parent_class, param_types, ret_type), casted_args), ret_type
                else:
                    raise BadCoverage()
        raise BadCoverage()

    def visitMethCall(self, ast: AST.MethCall, given_scope: List[CtxObject]):
        receiver_expr, receiver_type = self.visit(ast.receiver, given_scope) # No need to append IsExpressionVisit.
        ast.receiver = receiver_expr
        args: List[Tuple[AST.Expr, AST.Type]] = [self.visit(it, given_scope) for it in ast.args]
        if isinstance(receiver_type, AST.StructType):
            method: AST.MethodDecl = next(filter(lambda x: x.fun.name == ast.metName, receiver_type.methods))
            ast.args = [
                self.maybe_wrap_cast_a_to_b(source_type, target_parameter.parType, source_expr)
                for (source_expr, source_type), target_parameter in zip(args, method.fun.params)
            ]
            return ast, method.fun.retType
        if isinstance(receiver_type, AST.InterfaceType):
            method: AST.Prototype = next(filter(lambda x: x.name == ast.metName, receiver_type.methods))
            ast.args = [
                self.maybe_wrap_cast_a_to_b(source_type, target_type, source_expr)
                for (source_expr, source_type), target_type in zip(args, method.params)
            ]
            return ast, method.retType
        raise BadCoverage()

    def visitId(self, ast: AST.Id, given_scope: List[CtxObject]):
        id_mode: Union[SimplifierIsTypenameVisit, SimplifierIsExpressionVisit, None] = next(filter(lambda x: isinstance(x, SimplifierIsTypenameVisit) or isinstance(x, SimplifierIsExpressionVisit), reversed(given_scope)), None)
        for sym in filter(lambda x: isinstance(x, Sym), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSym) or isinstance(sym, InterfaceSym):
                    if isinstance(id_mode, SimplifierIsExpressionVisit):
                        raise BadCoverage()
                    return sym.original_ast
                elif isinstance(sym, ConstSym):
                    if isinstance(id_mode, SimplifierIsTypenameVisit):
                        raise BadCoverage()
                    return ast, sym.original_ast.conType
                elif isinstance(sym, VarSym):
                    if isinstance(id_mode, SimplifierIsTypenameVisit):
                        raise BadCoverage()
                    return ast, sym.original_ast.varType
                elif isinstance(sym, FnParamSym):
                    if isinstance(id_mode, SimplifierIsTypenameVisit):
                        raise BadCoverage()
                    return ast, sym.parameter_type
                else:
                    raise BadCoverage()
        raise BadCoverage()

    def visitArrayCell(self, ast: AST.ArrayCell, given_scope: List[CtxObject]):
        receiver_expr, receiver_type = self.visit(ast.arr, given_scope) # No need to append IsExpressionVisit.
        ast.arr = receiver_expr
        ast.idx = [self.visit(it, given_scope)[0] for it in ast.idx]
        if len(receiver_type.dimens) == len(ast.idx):
            return ast, receiver_type.eleType
        return ast, AST.ArrayType(receiver_type.dimens[len(ast.idx):], receiver_type.eleType)

    def visitFieldAccess(self, ast: AST.FieldAccess, given_scope: List[CtxObject]):
        receiver_expr, receiver_type = self.visit(ast.receiver, given_scope) # No need to append IsExpressionVisit.
        ast.receiver = receiver_expr
        f_name, f_type = next(filter(lambda x: x[0] == ast.field, receiver_type.elements))
        return ast, f_type

    def visitIntLiteral(self, ast, param):
        return ast, AST.IntType()

    def visitFloatLiteral(self, ast, param):
        return ast, AST.FloatType()

    def visitBooleanLiteral(self, ast, param):
        return ast, AST.BoolType()

    def visitStringLiteral(self, ast, param):
        return ast, AST.StringType()

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, given_scope: List[CtxObject]):
        dimensions = [self.comptime_evaluate(it, given_scope) for it in ast.dimens]
        ele_type = self.visit(ast.eleType, given_scope + [SimplifierIsTypenameVisit()])
        return AST.ArrayLiteral(dimensions, ele_type, self.simplify_nested_list(ast, ast.value, ele_type, dimensions, given_scope)), AST.ArrayType(dimensions, ele_type)

    def visitStructLiteral(self, ast: AST.StructLiteral, given_scope: List[CtxObject]):
        # Find the struct name.
        struct = self.visit(AST.Id(ast.name), given_scope + [SimplifierIsTypenameVisit()])
        if not isinstance(struct, AST.StructType):
            raise BadCoverage()

        new_elements = []
        for i, element in enumerate(ast.elements):
            field_name, field_value = element
            target_struct_field_type: AST.Type = next(filter(lambda x: x[0] == field_name, struct.elements))[1]
            simplified_initializer, field_initializer_type = self.visit(field_value, given_scope)
            simplified_initializer = self.maybe_wrap_cast_a_to_b(field_initializer_type, target_struct_field_type, simplified_initializer)
            new_elements.append((field_name, simplified_initializer))

        return ConcreteStructLiteral(struct, new_elements), struct

    def visitNilLiteral(self, ast, param):
        return ast, SimplifierNilType()

###### End of simplifier ######

class CodeGenerator(BaseVisitor, Utils):
    emit: Optional[Emitter]
    simplifier: Optional[Simplifier]

    # Copied from StaticCheck/Simplifier but without any scoping and type resolution logic since it's all smooth sailing from here thanks to Simplifier just getting rid of AST.Id-as-types
    def make_default_value_ast(self, typename: AST.Type, make_nested_list: bool = False):
        if isinstance(typename, AST.IntType):
            return AST.IntLiteral(0)
        elif isinstance(typename, AST.FloatType):
            return AST.FloatLiteral(0.0)
        elif isinstance(typename, AST.StringType):
            return AST.StringLiteral("\"\"")
        elif isinstance(typename, AST.BoolType):
            return AST.BooleanLiteral(False)
        elif isinstance(typename, AST.ArrayType):
            # Sanity check.
            d = typename.dimens[0]
            if not isinstance(d, AST.IntLiteral):
                raise BadCoverage()
            child_type = AST.ArrayType(typename.dimens[1:], typename.eleType) if len(typename.dimens) > 1 else typename.eleType
            vals: AST.NestedList = [self.make_default_value_ast(child_type, True) for _ in range(d.value)]
            if make_nested_list:
                return vals
            return AST.ArrayLiteral(typename.dimens, typename.eleType, vals)
        elif isinstance(typename, AST.Id):
            raise BadCoverage()
        elif isinstance(typename, AST.StructType):
            return ConcreteStructLiteral(typename, [])
        return AST.NilLiteral()

    def can_be_globally_directly_initialized(self, value: AST.Literal):
        if isinstance(value, AST.IntLiteral) or isinstance(value, AST.FloatLiteral):
            return True
        if isinstance(value, AST.BooleanLiteral):
            return True
        if isinstance(value, AST.StringLiteral):
            return True
        return False

    def make_default_static_field_value(self, value: AST.Literal):
        if isinstance(value, AST.IntLiteral) or isinstance(value, AST.FloatLiteral):
            return str(value.value)
        if isinstance(value, AST.BooleanLiteral):
            return str(1 if value.value else 0)
        if isinstance(value, AST.StringLiteral):
            return value.value
        return None

    def __init__(self):
        self.className = "MiniGoClass"
        self.astTree = None
        self.path = None
        self.emit = None
        self.simplifier = None

    def init(self):
        mem = [
            StaticCheck.Symbol("getInt", StaticCheck.MType([], AST.IntType()), CName("io", True)),
            StaticCheck.Symbol("putInt", StaticCheck.MType([AST.IntType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("putIntLn", StaticCheck.MType([AST.IntType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("getFloat", StaticCheck.MType([], AST.FloatType()), CName("io", True)),
            StaticCheck.Symbol("putFloat", StaticCheck.MType([AST.FloatType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("putFloatLn", StaticCheck.MType([AST.FloatType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("getBool", StaticCheck.MType([], AST.BoolType()), CName("io", True)),
            StaticCheck.Symbol("putBool", StaticCheck.MType([AST.BoolType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("putBoolLn", StaticCheck.MType([AST.BoolType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("getString", StaticCheck.MType([], AST.StringType()), CName("io", True)),
            StaticCheck.Symbol("putString", StaticCheck.MType([AST.StringType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("putStringLn", StaticCheck.MType([AST.StringType()], AST.VoidType()), CName("io", True)),
            StaticCheck.Symbol("putLn", StaticCheck.MType([], AST.VoidType()), CName("io", True))
        ]
        return mem

    def gen(self, ast, dir_):
        self.simplifier = Simplifier(ast)
        simplified = self.simplifier.simplify()
        gl = self.init()
        self.astTree = simplified
        self.path = dir_
        self.emit = Emitter(dir_ + "/" + self.className + ".j")
        self.visit(simplified, gl)

    def emit_init_clinit(self, className=None, global_vars_consts: Optional[List[Union[AST.VarDecl, AST.ConstDecl]]]=None, o=None):
        if className is None:
            className = self.className

        # Empty <init> that just calls java.lang.Object.<init>
        frame = Frame("<init>", AST.VoidType())
        self.emit.printout(self.emit.emitMETHOD("<init>", StaticCheck.MType([], AST.VoidType()), False, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "this", className, frame.getStartLabel(), frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        self.emit.printout(self.emit.emitREADVAR("this", className, 0, frame))
        self.emit.printout(self.emit.emitINVOKESPECIAL(frame))
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame) + "\n")

        # Where the cool stuff really happens (<clinit>)
        frame = Frame("<clinit>", AST.VoidType())
        self.emit.printout(self.emit.emitMETHOD("<clinit>", StaticCheck.MType([], AST.VoidType()), False, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        ## The good stuff
        if global_vars_consts is not None and o is not None:
            env = o.copy()
            env["frame"] = frame
            for z in global_vars_consts:
                if isinstance(z, AST.VarDecl):
                    if self.can_be_globally_directly_initialized(z.varInit):
                        continue
                    self.emit.printout(self.visit(z.varInit, env)[0])
                    self.emit.printout(self.emit.emitPUTSTATIC(f"{className}/{z.varName}", z.varType, frame))
                elif isinstance(z, AST.ConstDecl):
                    if self.can_be_globally_directly_initialized(z.iniExpr):
                        continue
                    self.emit.printout(self.visit(z.iniExpr, env)[0])
                    self.emit.printout(self.emit.emitPUTSTATIC(f"{className}/{z.conName}", z.conType, frame))
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame) + "\n")

        frame.exitScope()

    # Visitor methods

    def visitProgram(self, ast, c):
        env = {'env': [c]}
        self.emit.printout(self.emit.emitPROLOG(self.className, "java.lang.Object", False))
        env = reduce(lambda a,x: self.visit(x, a), filter(lambda x: isinstance(x, AST.VarDecl) or isinstance(x, AST.ConstDecl), ast.decl), env)
        env = reduce(lambda a,x: self.visit(x, a), filter(lambda x: not (isinstance(x, AST.StructType) or isinstance(x, AST.InterfaceType) or isinstance(x, AST.VarDecl) or isinstance(x, AST.ConstDecl)), ast.decl), env)
        self.emit_init_clinit(None, list(filter(lambda x: isinstance(x, AST.VarDecl) or isinstance(x, AST.ConstDecl), ast.decl)), env)
        env = reduce(lambda a,x: self.visit(x, a), filter(lambda x: isinstance(x, AST.StructType) or isinstance(x, AST.InterfaceType), ast.decl), env)
        self.emit.printout(self.emit.emitEPILOG())
        return env

    def visitVarDecl(self, ast: AST.VarDecl, o):
        if 'frame' not in o: # global var
            o['env'][0].append(StaticCheck.Symbol(ast.varName, ast.varType, CName(self.className)))
            v = self.make_default_static_field_value(ast.varInit) if self.can_be_globally_directly_initialized(ast.varInit) else None
            self.emit.printout(self.emit.emitATTRIBUTE(ast.varName, ast.varType, True, False, v))
        else:
            frame = o['frame']
            index = frame.getNewIndex()
            o['env'][0].append(StaticCheck.Symbol(ast.varName, ast.varType, Index(index)))
            self.emit.printout(self.emit.emitVAR(index, ast.varName, ast.varType, frame.getStartLabel(), frame.getEndLabel(), frame))
            if ast.varInit is not None:
                init_j, init_ty = self.visit(ast.varInit, o)
                self.emit.printout(init_j)
                self.emit.printout(self.emit.emitWRITEVAR(ast.varName, ast.varType, index, frame))
        return o

    def visitConstDecl(self, ast: AST.ConstDecl, o):
        if 'frame' not in o: # global const
            o['env'][0].append(StaticCheck.Symbol(ast.conName, ast.conType, CName(self.className)))
            v = self.make_default_static_field_value(ast.iniExpr) if self.can_be_globally_directly_initialized(ast.iniExpr) else None
            self.emit.printout(self.emit.emitATTRIBUTE(ast.conName, ast.conType, True, False, v))
        else:
            frame = o['frame']
            index = frame.getNewIndex()
            o['env'][0].append(StaticCheck.Symbol(ast.conName, ast.conType, Index(index)))
            self.emit.printout(self.emit.emitVAR(index, ast.conName, ast.conType, frame.getStartLabel(), frame.getEndLabel(), frame))
            if ast.iniExpr is not None:
                init_j, init_ty = self.visit(ast.iniExpr, o)
                self.emit.printout(init_j)
                self.emit.printout(self.emit.emitWRITEVAR(ast.conName, ast.conType, index, frame))
        return o

    def visitParamDecl(self, ast, o):
        # not needed anymore
        return o

    def visitFuncDecl(self, ast: AST.FuncDecl, o):
        frame = Frame(ast.name, ast.retType)
        is_main = ast.name == "main"
        if is_main:
            mtype = StaticCheck.MType([AST.ArrayType([None],AST.StringType())], AST.VoidType())
        else:
            param_types = [param.parType for param in ast.params]
            mtype = StaticCheck.MType(param_types, ast.retType)
        o['env'][0].append(StaticCheck.Symbol(ast.name, mtype, CName(self.className)))
        env = o.copy()
        env['frame'] = frame
        self.emit.printout(self.emit.emitMETHOD(ast.name, mtype, True, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        env['env'] = [[
            StaticCheck.Symbol(param.parName, param.parType, Index(frame.getNewIndex()))
            for param in ast.params
        ]] + env['env']
        if is_main:
            self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "args", AST.ArrayType([None],AST.StringType()), frame.getStartLabel(), frame.getEndLabel(), frame))
        else:
            env = reduce(lambda acc,e: self.visit(e,acc),ast.params,env)
        self.visit(ast.body,env)
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(ast.retType) is AST.VoidType:
            self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        else:
            self.emit.printout(self.emit.emitNOP(frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
        return o

    def visitMethodDecl(self, ast: AST.MethodDecl, o):
        frame = Frame(ast.fun.name, ast.fun.retType)
        recv_type: AST.StructType = ast.recType
        param_types = [param.parType for param in ast.fun.params]
        mtype = StaticCheck.MType(param_types, ast.fun.retType)
        o['env'][0].append(StaticCheck.Symbol(ast.fun.name, mtype, CName(recv_type.name)))
        env = o.copy()
        env['frame'] = frame
        self.emit.printout(self.emit.emitMETHOD(ast.fun.name, mtype, False, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        env['env'] = [[
            StaticCheck.Symbol(ast.receiver, recv_type, Index(frame.getNewIndex()))
                      ] + [
            StaticCheck.Symbol(param.parName, param.parType, Index(frame.getNewIndex()))
            for param in ast.fun.params
        ]] + env['env']
        env = reduce(lambda acc,e: self.visit(e,acc), ast.fun.params, env)
        self.visit(ast.fun.body,env)
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(ast.fun.retType) is AST.VoidType:
            self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        else:
            self.emit.printout(self.emit.emitNOP(frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
        return o

    def visitPrototype(self, ast: AST.Prototype, o):
        self.emit.printout(self.emit.emitMETHOD(f"abstract {ast.name}", StaticCheck.MType(ast.params, ast.retType), False, None))
        self.emit.printout(self.emit.jvm.emitENDMETHOD())

    def visitIntType(self, ast, param):
        return None

    def visitFloatType(self, ast, param):
        return None

    def visitBoolType(self, ast, param):
        return None

    def visitStringType(self, ast, param):
        return None

    def visitVoidType(self, ast, param):
        return None

    def visitArrayType(self, ast, param):
        return None

    def visitStructType(self, ast: AST.StructType, o):
        sub_emit = Emitter(self.path + "/" + ast.name + ".j")
        old_emit = self.emit
        self.emit = sub_emit

        # Class prologue
        sub_emit.printout(sub_emit.emitPROLOG(ast.name, "java.lang.Object", False))

        # Implements?
        for impl in ast.implements:
            sub_emit.printout(sub_emit.emitIMPLEMENTS(impl.name))

        # Make fields
        for field_name, field_type in ast.elements:
            sub_emit.printout(sub_emit.emitINSTANCEFIELD(f"public {field_name}", field_type, False, None))

        # Make <init> method
        frame = Frame("<init>", AST.VoidType())
        frame.enterScope(True)
        init_start_label = frame.getStartLabel()
        init_end_label = frame.getEndLabel()
        initializer_mtype = StaticCheck.MType([field_type for field_name, field_type in ast.elements], AST.VoidType())
        sub_emit.printout(sub_emit.emitMETHOD("<init>", initializer_mtype, False, frame))
        ## Emit this-var
        sub_emit.printout(sub_emit.emitVAR(frame.getNewIndex(), "this", ast, init_start_label, init_end_label, frame))
        ## Emit parameters-as-variables
        [sub_emit.printout(sub_emit.emitVAR(frame.getNewIndex(), field_name, field_type, init_start_label, init_end_label, frame)) for field_name, field_type in ast.elements]
        sub_emit.printout(sub_emit.emitLABEL(init_start_label, frame))
        ## Just have a `this` ready.
        sub_emit.printout(sub_emit.emitREADVAR("this", ast, 0, frame))
        ## Call <init> of base object (java.lang.Object)
        sub_emit.printout(sub_emit.emitDUP(frame))
        sub_emit.printout(sub_emit.emitINVOKESPECIAL(frame)) # pops the duplicated this
        ## Emit assignments from those variables to the fields they're meant for
        [
            sub_emit.printout(
                sub_emit.emitDUP(frame) +
                sub_emit.emitREADVAR("this", field_type, i + 1, frame) +
                sub_emit.emitPUTFIELD(f"{ast.name}/{field_name}", field_type, frame)
            )
            for i, (field_name, field_type) in enumerate(ast.elements)
        ]

        sub_emit.printout(sub_emit.emitLABEL(frame.getEndLabel(), frame))
        sub_emit.printout(sub_emit.emitRETURN(AST.VoidType(), frame))
        sub_emit.printout(sub_emit.emitENDMETHOD(frame))
        frame.exitScope()

        for method in ast.methods:
            self.visit(method, o)

        sub_emit.emitEPILOG()

        self.emit = old_emit

        return o

    def visitInterfaceType(self, ast: AST.InterfaceType, o):
        sub_emit = Emitter(self.path + "/" + ast.name + ".j")
        old_emit = self.emit
        self.emit = sub_emit

        sub_emit.printout(sub_emit.emitPROLOG(ast.name, "java.lang.Object", True))
        for method in ast.methods:
            self.visit(method, o)
        sub_emit.emitEPILOG()

        self.emit = old_emit

        return o

    def visitBlock(self, ast, o):
        env = o.copy()
        env['env'] = [[]] + env['env']
        env['frame'].enterScope(False)
        self.emit.printout(self.emit.emitLABEL(env['frame'].getStartLabel(), env['frame']))
        for e in ast.member:
            if isinstance(e, AST.Expr):
                j, ty = self.visit(e, env)
                self.emit.printout(j)
            else:
                old_env = env
                env = self.visit(e, env)
        self.emit.printout(self.emit.emitLABEL(env['frame'].getEndLabel(), env['frame']))
        env['frame'].exitScope()
        return o

    def visitAssign(self, ast: AST.Assign, o):
        lhs_ast: AST.LHS = ast.lhs
        frame: Frame = o["frame"]
        if isinstance(lhs_ast, AST.Id):
            prep_j = None
            prep_ty = None
        elif isinstance(lhs_ast, AST.FieldAccess):
            prep_j, prep_ty = self.visit(lhs_ast.receiver, o)
        elif isinstance(lhs_ast, AST.ArrayCell):
            prep_expr = AST.ArrayCell(lhs_ast.arr, lhs_ast.idx[:-1]) if len(lhs_ast.idx) > 1 else lhs_ast.arr
            prep_j, prep_ty = self.visit(prep_expr, o)
            last_indexing_j, last_indexing_ty = self.visit(lhs_ast.idx[-1], o)
            prep_j += last_indexing_j
        else:
            raise BadCoverage()

        rhs_j, rhs_ty = self.visit(ast.rhs, o)

        if isinstance(lhs_ast, AST.Id):
            name = lhs_ast.name
            sym: StaticCheck.Symbol = next(filter(lambda x: x.name == name, [j for i in o['env'] for j in i[::-1]]), None) # reverse the damn thing!
            val = sym.value
            lhs_j = self.emit.emitWRITEVAR(name, sym.mtype, val.value, frame) if isinstance(val, Index) else self.emit.emitPUTSTATIC(f"{self.className}/{sym.name}", sym.mtype, frame)
        elif isinstance(lhs_ast, AST.FieldAccess):
            if not isinstance(prep_ty, AST.StructType):
                raise BadCoverage()

            field_name = lhs_ast.field
            field_type = next(filter(lambda x: x[0] == field_name, prep_ty.elements))[1]
            lhs_j = self.emit.emitPUTFIELD(f"{prep_ty.name}/{lhs_ast.field}", field_type, frame)
        elif isinstance(lhs_ast, AST.ArrayCell):
            if not isinstance(prep_ty, AST.ArrayType):
                raise BadCoverage()
            prep_ty = AST.ArrayType(prep_ty.dimens[1:], prep_ty.eleType) if len(prep_ty.dimens) > 1 else prep_ty.eleType
            lhs_j = self.emit.emitASTORE(prep_ty, frame)
        else:
            raise BadCoverage()

        if prep_j is not None:
            self.emit.printout(prep_j)
        self.emit.printout(rhs_j)
        self.emit.printout(lhs_j)
        return o

    def visitIf(self, ast: AST.If, o):
        frame: Frame = o["frame"]

        if isinstance(ast.expr, AST.BinaryOp) and ast.expr.op in [">", ">=", "<", "<=", "!=", "=="]:
            l_j, l_ty = self.visit(ast.expr.left, o)
            r_j, r_ty = self.visit(ast.expr.right, o)

            self.emit.printout(l_j)
            self.emit.printout(r_j)

            l1 = frame.getNewLabel()
            self.emit.printout(self.emit.emitRELOP(ast.expr.op, l_ty, None, l1, frame))
            self.visit(ast.thenStmt, o)

            if ast.elseStmt is None:
                self.emit.printout(self.emit.emitLABEL(l1, frame))
            else:
                l2 = frame.getNewLabel()
                self.emit.printout(self.emit.emitGOTO(l2, frame))
                self.emit.printout(self.emit.emitLABEL(l1, frame))
                self.visit(ast.elseStmt, o)
                self.emit.printout(self.emit.emitLABEL(l2, frame))

            return o
        
        cond_j, cond_ty = self.visit(ast.expr, o)

        if ast.elseStmt is None:
            l1 = frame.getNewLabel()
            self.emit.printout(cond_j)
            self.emit.printout(self.emit.emitIFFALSE(l1, frame))
            self.visit(ast.thenStmt, o)
            self.emit.printout(self.emit.emitLABEL(l1, frame))
        else:
            l1 = frame.getNewLabel()
            l2 = frame.getNewLabel()

            self.emit.printout(cond_j)
            self.emit.printout(self.emit.emitIFFALSE(l1, frame))
            self.visit(ast.thenStmt, o)
            self.emit.printout(self.emit.emitGOTO(l2, frame))
            self.emit.printout(self.emit.emitLABEL(l1, frame))
            self.visit(ast.elseStmt, o)
            self.emit.printout(self.emit.emitLABEL(l2, frame))

        return o

    def visitForBasic(self, ast: AST.ForBasic, o):
        frame: Frame = o["frame"]
        
        frame.enterLoop()

        cond_j, cond_ty = self.visit(ast.cond, o)
        b = frame.getBreakLabel()
        c = frame.getContinueLabel()
        self.emit.printout(self.emit.emitLABEL(c, frame))
        self.emit.printout(cond_j)
        q = self.emit.emitIFFALSE(b, frame)
        self.emit.printout(q)
        self.visit(ast.loop, o)
        self.emit.printout(self.emit.emitGOTO(c, frame))
        self.emit.printout(self.emit.emitLABEL(b, frame))

        frame.exitLoop()
        return o

    def visitForStep(self, ast: AST.ForStep, o):
        env = o.copy()
        frame: Frame = env["frame"]

        # in addition to the new scope inside `ast.loop: Block` we need another one for the potential var decls
        env["env"] = [[]] + env["env"]

        frame.enterScope(False)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        if isinstance(ast.init, AST.Expr):
            init_j, init_ty = self.visit(ast.init, env)
            self.emit.printout(init_j)
        else:
            self.visit(ast.init, env)
        frame.enterLoop()
        actual_loop_start = frame.getNewLabel()
        self.emit.printout(self.emit.emitLABEL(actual_loop_start, frame))
        cond_j, cond_ty = self.visit(ast.cond, env)
        self.emit.printout(cond_j)
        self.emit.printout(self.emit.emitIFFALSE(frame.getBreakLabel(), frame))
        self.visit(ast.loop, env)
        self.emit.printout(self.emit.emitLABEL(frame.getContinueLabel(), frame))
        if isinstance(ast.init, AST.Expr):
            upda_j, upda_ty = self.visit(ast.upda, env)
            self.emit.printout(upda_j)
        else:
            self.visit(ast.upda, env)
        self.emit.printout(self.emit.emitGOTO(actual_loop_start, frame))
        self.emit.printout(self.emit.emitLABEL(frame.getBreakLabel(), frame))
        frame.exitLoop()
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        frame.exitScope()
        return o

    def visitForEach(self, ast, param):
        # Assignment 4 spec says these evil little constructs don't exist. :)
        raise BadCoverage()

    def visitContinue(self, ast: AST.Continue, o):
        frame: Frame = o["frame"]
        self.emit.printout(self.emit.emitGOTO(frame.getContinueLabel(), frame))
        return o

    def visitBreak(self, ast: AST.Break, o):
        frame: Frame = o["frame"]
        self.emit.printout(self.emit.emitGOTO(frame.getBreakLabel(), frame))
        return o

    def visitReturn(self, ast: AST.Return, o):
        frame: Frame = o["frame"]
        if ast.expr is None:
            j = self.emit.emitRETURN(AST.VoidType(), frame)
            self.emit.printout(j)
            return o

        r_j, r_ty = self.visit(ast.expr, o)
        self.emit.printout(r_j)
        self.emit.printout(self.emit.emitRETURN(r_ty, frame))

        return o

    def visitBinaryOp(self, ast, o):
        if "frame" not in o:
            l_j, l_ty = self.visit(ast.left, o)
            r_j, r_ty = self.visit(ast.right, o)
            return "", l_ty

        frame: Frame = o["frame"]

        l_j, l_ty = self.visit(ast.left, o)
        r_j, r_ty = self.visit(ast.right, o)

        if ast.op == "+" and isinstance(l_ty, AST.StringType):
            j = self.emit.emitSTRCONCAT(frame)
        elif ast.op in ["+", "-"]:
            j = self.emit.emitADDOP(ast.op, l_ty, frame)
        elif ast.op in ["*", "/"]:
            j = self.emit.emitMULOP(ast.op, l_ty, frame)
        elif ast.op == "&&":
            j = self.emit.emitANDOP(frame)
        elif ast.op == "||":
            j = self.emit.emitOROP(frame)
        elif ast.op == "%":
            j = self.emit.emitMOD(frame)
        else:
            j = self.emit.emitREOP(ast.op, l_ty, frame)

        return l_j + r_j + j, l_ty

    def visitUnaryOp(self, ast: AST.UnaryOp, o):
        if "frame" not in o:
            r_j, r_ty = self.visit(ast.body, o)
            return "", r_ty

        frame: Frame = o["frame"]

        o2 = o.copy()
        r_j, r_ty = self.visit(ast.body, o2)
        if ast.op == "-":
            j = self.emit.emitNEGOP(r_ty, frame)
        else:
            j = self.emit.emitPUSHICONST(1, frame) + self.emit.emitXOROP(frame)
        return r_j + j, r_ty

    def visitConvertIntToFloat(self, ast: ConvertIntToFloat, o):
        if "frame" not in o:
            e_j, e_ty = self.visit(ast.original_int_expr, o)
            return "", AST.IntType()

        frame: Frame = o["frame"]

        o2 = o.copy()
        e_j, e_ty = self.visit(ast.original_int_expr, o2)
        l_j = self.emit.emitI2F(frame)

        return e_j + l_j, AST.FloatType()

    def visitFuncCall(self, ast, o):
        raise BadCoverage()

    def visitConcreteFuncCall(self, ast: ConcreteFuncCall, o):
        env = o.copy()
        args = [self.visit(x, env)[0] for x in ast.args]
        if isinstance(ast.func, AST.FuncDecl):
            lx = f"{self.className}/{ast.func.name}"
            mtype = StaticCheck.MType([param.parType for param in ast.func.params], ast.func.retType)
        else:
            fun_name, parent_class, param_types, ret_type = ast.func
            lx = f"{parent_class}/{fun_name}"
            mtype = StaticCheck.MType(param_types, ret_type)
        j = self.emit.emitINVOKESTATIC(lx, mtype, o['frame'])
        return ''.join(args) + j, mtype.rettype

    def visitMethCall(self, ast: AST.MethCall, o):
        l_j, l_ty = self.visit(ast.receiver, o)

        frame: Frame = o["frame"]
        args = [self.visit(x, o)[0] for x in ast.args]
        if isinstance(l_ty, AST.StructType):
            method: AST.MethodDecl = next(filter(lambda x: x.fun.name == ast.metName, l_ty.methods))
            mtype = StaticCheck.MType([param.parType for param in method.fun.params], method.fun.retType)
            j = self.emit.emitINVOKEVIRTUAL(f"{l_ty.name}/{ast.metName}", mtype, frame)
            ret_type = method.fun.retType
        elif isinstance(l_ty, AST.InterfaceType):
            prototype: AST.Prototype = next(filter(lambda x: x.name == ast.metName, l_ty.methods))
            mtype = StaticCheck.MType(prototype.params, prototype.retType)
            j = self.emit.emitINVOKEINTERFACE(f"{l_ty.name}/{ast.metName}", mtype, frame)
            ret_type = prototype.retType
        else:
            raise BadCoverage()
        return l_j + ''.join(args) + j, ret_type

    def visitId(self, ast, o):
        sym: StaticCheck.Symbol = next(filter(lambda x: x.name == ast.name, [j for i in o['env'] for j in i[::-1]]), None) # reverse the damn thing!
        val = sym.value
        frame: Frame = o["frame"]
        j = self.emit.emitREADVAR(ast.name, sym.mtype, val.value, frame) if isinstance(val, Index) else self.emit.emitGETSTATIC(f"{self.className}/{sym.name}", sym.mtype, frame)
        return j, sym.mtype

    def visitArrayCell(self, ast: AST.ArrayCell, o):
        l_j, l_ty = self.visit(ast.arr, o)
        if not isinstance(l_ty, AST.ArrayType):
            raise BadCoverage()
        frame: Frame = o["frame"]
        q = [l_j]
        for idx in ast.idx:
            r_j, r_ty = self.visit(idx, o)
            l_ty = AST.ArrayType(l_ty.dimens[1:], l_ty.eleType) if len(l_ty.dimens) > 1 else l_ty.eleType
            q.append(r_j)
            q.append(self.emit.emitALOAD(l_ty, frame))
        return ''.join(q), l_ty

    def visitFieldAccess(self, ast: AST.FieldAccess, o):
        l_j, l_ty = self.visit(ast.receiver, o)
        if not isinstance(l_ty, AST.StructType):
            raise BadCoverage()
        field_type = next(filter(lambda x: x[0] == ast.field, l_ty.elements))[1]
        frame: Frame = o["frame"]
        j = self.emit.emitGETFIELD(f"{l_ty.name}/{ast.field}", field_type, frame)
        return l_j + j, field_type

    def visitIntLiteral(self, ast: AST.IntLiteral, o):
        if "frame" not in o:
            return "", AST.IntType()
        return self.emit.emitPUSHICONST(ast.value, o['frame']), AST.IntType()

    def visitFloatLiteral(self, ast: AST.FloatLiteral, o):
        if "frame" not in o:
            return "", AST.FloatType()
        frame: Frame = o["frame"]
        return self.emit.emitPUSHFCONST(ast.value, frame), AST.FloatType()

    def visitBooleanLiteral(self, ast: AST.BooleanLiteral, o):
        if "frame" not in o:
            return "", AST.BoolType()
        frame: Frame = o["frame"]
        return self.emit.emitPUSHICONST(1 if ast.value else 0, frame), AST.BoolType()

    def visitStringLiteral(self, ast, o):
        if "frame" not in o:
            return "", AST.StringType()
        frame: Frame = o["frame"]
        return self.emit.emitPUSHCONST(ast.value, AST.StringType(), frame), AST.StringType()

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, o):
        frame: Frame = o["frame"]
        q = ""
        dim = ast.dimens[0]
        if not isinstance(dim, AST.IntLiteral):
            raise BadCoverage()

        subtype = AST.ArrayType(ast.dimens[1:], ast.eleType) if len(ast.dimens) > 1 else ast.eleType
        q += self.emit.emitPUSHICONST(dim.value, frame) + self.emit.emitNEWARRAY(subtype, frame)
        for i, expr in enumerate(ast.value):
            dup_j = self.emit.emitDUP(frame)
            idx_j = self.emit.emitPUSHICONST(i, frame)
            if isinstance(expr, List):
                fake_ast = AST.ArrayLiteral(ast.dimens[1:], ast.eleType, expr)
                val_j, val_ty = self.visit(fake_ast, o)
            else:
                val_j, val_ty = self.visit(expr, o)
                val_ty = ast.eleType # prevent nils
            store_j = self.emit.emitASTORE(val_ty, frame)
            q += ''.join([dup_j, idx_j, val_j, store_j])

        return q, AST.ArrayType(ast.dimens, ast.eleType)

    def visitStructLiteral(self, ast, param):
        raise BadCoverage()

    def visitConcreteStructLiteral(self, ast: ConcreteStructLiteral, o):
        if "frame" not in o:
            return "", ast.struct
        frame: Frame = o["frame"]

        j_new = self.emit.emitNEW(ast.struct.name, frame)
        j_dup = self.emit.emitDUP(frame)

        field_initializers = []

        for field_name, field_type in ast.struct.elements:
            # find the initializer
            maybe_init: Optional[Tuple[str, AST.Expr]] = next(filter(lambda x: x[0] == field_name, ast.elements), None)
            if maybe_init is None:
                field_init_j, field_init_ty = self.visit(self.make_default_value_ast(field_type), o)
            else:
                field_init_j, field_init_ty = self.visit(maybe_init[1], o)
            field_initializers.append(field_init_j)

        constructor_mtype = StaticCheck.MType([field_type for field_name, field_type in ast.struct.elements], AST.VoidType())
        j_invoke_constructor = self.emit.emitINVOKESPECIAL(frame, f"{ast.struct.name}/<init>", constructor_mtype)
        return j_new + j_dup + ''.join(field_initializers) + j_invoke_constructor, ast.struct

    def visitNilLiteral(self, ast, o):
        if "frame" not in o:
            return "", SimplifierNilType()
        frame: Frame = o["frame"]
        return self.emit.emitPUSHNULL(frame), SimplifierNilType()

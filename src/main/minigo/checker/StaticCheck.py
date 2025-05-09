"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=m_EQ86z90mI
"""

import AST
from Visitor import *
from typing import List, Tuple, Optional, Union, Dict
import StaticError

# Preserved for BTL4

class MType:
    def __init__(self,partype,rettype):
        self.partype = partype
        self.rettype = rettype

    def __str__(self):
        return "MType([" + ",".join(str(x) for x in self.partype) + "]," + str(self.rettype) + ")"

class Symbol:
    def __init__(self,name,mtype,value = None):
        self.name = name
        self.mtype = mtype
        self.value = value

    def __str__(self):
        return "Symbol(" + str(self.name) + "," + str(self.mtype) + ("" if self.value is None else "," + str(self.value)) + ")"

# Actual useful stuff

class InternalError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"Internal checker error: {self.message}"

# Just use classes, man.
# For scope state.

class ScopeObject:
    def __init__(self):
        pass

# For caching resolved types.
# For now this purely only exists because there are comptime expressions that must be evaluated
# to fully resolve array type ASTs.

class ResolvedFunctionTypes:
    return_type: Optional[AST.Type]
    parameter_types: Optional[List[AST.Type]]

    def __init__(self):
        self.return_type = None
        self.parameter_types = None

# For name resolution.

class ScopedSymbol(ScopeObject):
    name: str

    def __init__(self, name: str):
        super().__init__()
        self.name = name

class StructSymbol(ScopedSymbol):
    original_ast: AST.StructType

    associated_method_asts: List[AST.MethodDecl]

    resolved_field_types: Dict[str, AST.Type]
    resolved_method_types: Dict[str, ResolvedFunctionTypes]

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.StructType):
        super().__init__(name)
        self.original_ast = original_ast

        self.associated_method_asts = []

        self.resolved_field_types = dict()
        self.resolved_method_types = dict()

        self.being_checked = False
        self.done_resolving = False

class InterfaceSymbol(ScopedSymbol):
    original_ast: AST.InterfaceType

    resolved_method_types: Dict[str, ResolvedFunctionTypes]

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.InterfaceType):
        super().__init__(name)
        self.original_ast = original_ast

        self.resolved_method_types = dict()

        self.being_checked = False
        self.done_resolving = False

class FunctionSymbol(ScopedSymbol):
    original_ast: AST.AST
    resolved_types: ResolvedFunctionTypes
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.AST):
        super().__init__(name)
        self.original_ast = original_ast
        self.resolved_types = ResolvedFunctionTypes()
        self.done_resolving = False

class VariableSymbol(ScopedSymbol):
    original_ast: Union[AST.VarDecl, AST.Assign, AST.Id]

    resolved_explicit_type: Optional[AST.Type]
    resolved_type: Optional[AST.Type]

    def __init__(self, name: str, original_ast: Union[AST.VarDecl, AST.Assign, AST.Id]):
        super().__init__(name)
        self.original_ast = original_ast # VarDecl for usual vars, Assign for implicit vars from assigns, Id for loops

        self.resolved_explicit_type = None
        self.resolved_type = None

class ConstantSymbol(ScopedSymbol):
    original_ast: AST.ConstDecl
    global_symbol_index: Optional[int]

    resolved_type: Optional[AST.Type]
    resolved_value: Optional[AST.Literal]

    being_checked: bool
    done_resolving: bool

    def __init__(self, name: str, original_ast: AST.ConstDecl):
        super().__init__(name)
        self.original_ast = original_ast
        self.global_symbol_index = None

        self.resolved_type = None
        self.resolved_value = None

        self.being_checked = False
        self.done_resolving = False

class FunctionParameterSymbol(ScopedSymbol):
    original_ast: Union[AST.ParamDecl, AST.Id]
    resolved_type: Optional[AST.Type]

    def __init__(self, name: str, original_ast: Union[AST.ParamDecl, AST.Id], resolved_type: AST.Type):
        super().__init__(name)
        # original_ast can be an identifier because it could be a receiver of a method.
        self.original_ast = original_ast
        self.resolved_type = resolved_type

# For banning illegal returns.

class CurrentFunction(ScopeObject):
    resolved_types: ResolvedFunctionTypes

    def __init__(self, resolved_types: ResolvedFunctionTypes):
        super().__init__()
        self.resolved_types = resolved_types

# Cheap hacks for resolving types for methods.

class UnresolvedMethod(ScopeObject):
    original_ast: AST.MethodDecl
    struct_symbol: Optional[StructSymbol]

    def __init__(self, original_ast: AST.MethodDecl):
        super().__init__()
        self.original_ast = original_ast
        self.struct_symbol = None

# Identifier resolution mode

class IdResolutionMode(ScopeObject):
    def __init__(self):
        super().__init__()

class IsExpressionVisit(IdResolutionMode):
    def __init__(self):
        super().__init__()

class IsTypenameVisit(IdResolutionMode):
    def __init__(self):
        super().__init__()

# For banning writes to consts.

class IsLeftHandSideVisit(ScopeObject):
    def __init__(self):
        super().__init__()

# For banning function/method calls and references to non-consts.

class IsComptimeExpressionVisit(ScopeObject):
    def __init__(self):
        super().__init__()

# For banning breaks and continues outside of loops.

class IsLoopVisit(ScopeObject):
    block: AST.Block
    banned_names: List[str]

    def __init__(self, block: AST.Block, banned_names: List[str]):
        super().__init__()
        self.block = block
        self.banned_names = banned_names

# Special nil type.

class NilType:
    def __init__(self):
        pass

class StaticChecker(BaseVisitor):
    global_declarations: List[ScopeObject]
    root_ast: AST.Program

    def __init__(self, root_ast: AST.Program):
        self.global_declarations = self.create_prelude()
        self.root_ast = root_ast

    @staticmethod
    def hard_compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        if isinstance(a, AST.ArrayType) and isinstance(b, AST.ArrayType):
            return StaticChecker.hard_compare_types(a.eleType, b.eleType) and len(a.dimens) == len(b.dimens) and all(
                isinstance(a, AST.IntLiteral) and isinstance(b, AST.IntLiteral) and a.value == b.value for a, b in
                zip(a.dimens, b.dimens))
        return type(a) == type(b)

    def can_cast_a_to_b(self, a: AST.Type, b: AST.Type):
        # Allow going from nils to struct/interface instances.
        if isinstance(a, NilType) and isinstance(b, AST.Id):
            return True

        # Allow going from ints to floats.
        if isinstance(a, AST.IntType) and isinstance(b, AST.FloatType):
            return True

        # Allow structs to be cast to interfaces.
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            a_id: AST.Id = a
            b_id: AST.Id = b
            if a_id.name == b_id.name:
                return True
            maybe_source_struct: Optional[StructSymbol] = next(filter(lambda x: isinstance(x, StructSymbol) and (x.name == a_id.name), self.global_declarations), None)
            maybe_target_interface: Optional[InterfaceSymbol] = next(filter(lambda x: isinstance(x, InterfaceSymbol) and (x.name == b_id.name), self.global_declarations), None)

            if (maybe_source_struct is None) or (maybe_target_interface is None):
                return False

            has_mismatched_method = False
            for interface_method_name, resolved_interface_method_types in maybe_target_interface.resolved_method_types.items():
                matches = False
                for struct_method_name, resolved_struct_method_types in maybe_source_struct.resolved_method_types.items():
                    if interface_method_name == struct_method_name:
                        return_type_matches = StaticChecker.hard_compare_types(resolved_struct_method_types.return_type, resolved_interface_method_types.return_type)
                        param_types_match = len(resolved_struct_method_types.parameter_types) == len(resolved_interface_method_types.parameter_types)
                        if param_types_match:
                            for i, t in enumerate(resolved_struct_method_types.parameter_types):
                                if not StaticChecker.hard_compare_types(t, resolved_interface_method_types.parameter_types[i]):
                                    param_types_match = False
                                    break

                        matches = return_type_matches and param_types_match
                if not matches:
                    has_mismatched_method = True

            return not has_mismatched_method

        if isinstance(a, AST.ArrayType) and isinstance(b, AST.ArrayType):
            if len(a.dimens) != len(b.dimens):
                return False
            if not all(isinstance(ad, AST.IntLiteral) for ad in a.dimens):
                return False
            if not all(isinstance(bd, AST.IntLiteral) for bd in a.dimens):
                return False
            aq: List[AST.IntLiteral] = a.dimens
            bq: List[AST.IntLiteral] = b.dimens
            if not all(a.value == b.value for a, b in zip(aq, bq)):
                return False
            if isinstance(a.eleType, AST.IntType) and isinstance(b.eleType, AST.FloatType):
                return True
            return self.hard_compare_types(a.eleType, b.eleType)

        return type(a) == type(b)

    def check_nested_list(self, original_ast: AST.ArrayLiteral, ast: AST.NestedList, ele_type: AST.Type, dimens: List[AST.IntLiteral], given_scope: List[ScopeObject]):
        if not isinstance(ast, list):
            raise StaticError.TypeMismatch(ast)
        this_dimen = dimens[0]
        if not isinstance(this_dimen, AST.IntLiteral):
            # TODO: should this be raised here or upstream?
            raise StaticError.TypeMismatch(original_ast)
        if len(ast) != this_dimen.value:
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(original_ast)
        if len(dimens) > 1:
            for sublist in ast:
                self.check_nested_list(original_ast, sublist, ele_type, dimens[1:], given_scope)
        else:
            for ele in ast:
                this_ele_type = self.visit(ele, given_scope) # No need to append IsExpressionVisit.
                if not self.can_cast_a_to_b(this_ele_type, ele_type):
                    raise StaticError.TypeMismatch(original_ast)

    @staticmethod
    def create_prelude():
        get_int = FunctionSymbol("getInt", AST.Id("getInt"))
        get_int.resolved_types.parameter_types = []
        get_int.resolved_types.return_type = AST.IntType()
        get_int.done_resolving = True

        put_int = FunctionSymbol("putInt", AST.Id("putInt"))
        put_int.resolved_types.parameter_types = [AST.IntType()]
        put_int.resolved_types.return_type = AST.VoidType()
        put_int.done_resolving = True

        put_int_ln = FunctionSymbol("putIntLn", AST.Id("putIntLn"))
        put_int_ln.resolved_types.parameter_types = [AST.IntType()]
        put_int_ln.resolved_types.return_type = AST.VoidType()
        put_int_ln.done_resolving = True

        get_float = FunctionSymbol("getFloat", AST.Id("getFloat"))
        get_float.resolved_types.parameter_types = []
        get_float.resolved_types.return_type = AST.FloatType()
        get_float.done_resolving = True

        put_float = FunctionSymbol("putFloat", AST.Id("putFloat"))
        put_float.resolved_types.parameter_types = [AST.FloatType()]
        put_float.resolved_types.return_type = AST.VoidType()
        put_float.done_resolving = True

        put_float_ln = FunctionSymbol("putFloatLn", AST.Id("putFloatLn"))
        put_float_ln.resolved_types.parameter_types = [AST.FloatType()]
        put_float_ln.resolved_types.return_type = AST.VoidType()
        put_float_ln.done_resolving = True

        get_bool = FunctionSymbol("getBool", AST.Id("getBool"))
        get_bool.resolved_types.parameter_types = []
        get_bool.resolved_types.return_type = AST.BoolType()
        get_bool.done_resolving = True

        put_bool = FunctionSymbol("putBool", AST.Id("putBool"))
        put_bool.resolved_types.parameter_types = [AST.BoolType()]
        put_bool.resolved_types.return_type = AST.VoidType()
        put_bool.done_resolving = True

        put_bool_ln = FunctionSymbol("putBoolLn", AST.Id("putBoolLn"))
        put_bool_ln.resolved_types.parameter_types = [AST.BoolType()]
        put_bool_ln.resolved_types.return_type = AST.VoidType()
        put_bool_ln.done_resolving = True

        get_string = FunctionSymbol("getString", AST.Id("getString"))
        get_string.resolved_types.parameter_types = []
        get_string.resolved_types.return_type = AST.StringType()
        get_string.done_resolving = True

        put_string = FunctionSymbol("putString", AST.Id("putString"))
        put_string.resolved_types.parameter_types = [AST.StringType()]
        put_string.resolved_types.return_type = AST.VoidType()
        put_string.done_resolving = True

        put_string_ln = FunctionSymbol("putStringLn", AST.Id("putStringLn"))
        put_string_ln.resolved_types.parameter_types = [AST.StringType()]
        put_string_ln.resolved_types.return_type = AST.VoidType()
        put_string_ln.done_resolving = True

        put_ln = FunctionSymbol("putLn", AST.Id("putLn"))
        put_ln.resolved_types.parameter_types = []
        put_ln.resolved_types.return_type = AST.VoidType()
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
    def make_default_value(self, typename: AST.Type, scoping: Union[int, List[ScopeObject]], make_nested_list: bool = False):
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
                raise InternalError(f"StaticChecker::make_default_value: Given array typename with dimension not of type AST.IntLiteral ({typename})")
            child_type = AST.ArrayType(typename.dimens[1:], typename.eleType) if len(typename.dimens) > 1 else typename.eleType
            vals: AST.NestedList = [self.make_default_value(child_type, scoping, True) for _ in range(d.value)]
            if make_nested_list:
                return vals
            return AST.ArrayLiteral(typename.dimens, typename.eleType, vals)
        elif isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, ScopedSymbol) and (sym.name == typename.name):
                    if isinstance(sym, StructSymbol):
                        return AST.StructLiteral(typename.name, [])
                    elif isinstance(sym, InterfaceSymbol):
                        return AST.NilLiteral()
                    elif (isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol)) and (isinstance(scoping, List) or (i < scoping)):
                        raise StaticError.Undeclared(StaticError.Type(), typename.name)
            raise StaticError.Undeclared(StaticError.Type(), typename.name)
        return AST.NilLiteral()

    # Unified from global_comptime_evaluate and local_comptime_evaluate.
    # Just roll our own recursion here instead of using StaticChecker's cancerous visitor mechanism.
    # For global consts:
    #   - pass an int as a global scope object index limit.
    # For local consts:
    #   - pass a List[ScopeObject] for local scoping.
    def comptime_evaluate(self, ast: AST.Expr, scoping: Union[int, List[ScopeObject]]):
        if isinstance(ast, AST.Id):
            symbols = self.global_declarations if isinstance(scoping, int) else filter(lambda x: isinstance(x, ScopedSymbol), reversed(scoping))
            for i, sym in enumerate(symbols):
                if isinstance(sym, ScopedSymbol) and (sym.name == ast.name):
                    if isinstance(sym, ConstantSymbol):
                        if isinstance(scoping, List) or i < scoping:
                            if sym.being_checked:
                                # Cyclic usage! It doesn't matter what is being raised here:
                                # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26313
                                raise StaticError.TypeMismatch(ast)
                            if isinstance(scoping, int):
                                # In midst of global comptime resolution! Need to resolve this const before using it.
                                self.global_resolve_constant(sym, scoping)
                            return sym.resolved_value
                    elif isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol) or isinstance(sym, FunctionSymbol):
                        # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26183
                        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                    elif isinstance(sym, VariableSymbol) or isinstance(sym, FunctionParameterSymbol):
                        # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26183
                        raise StaticError.TypeMismatch(ast)
                    else:
                        raise InternalError(f"StaticChecker::comptime_evaluate: Ran into symbol of type {sym} in non-exhaustive reflection elif chain")
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
        elif isinstance(ast, AST.FuncCall) or isinstance(ast, AST.MethCall):
            # Function calls are not allowed at compilation-time evaluation.
            raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.ArrayCell):
            receiver = self.comptime_evaluate(ast.arr, scoping)
            if not isinstance(receiver, AST.ArrayLiteral):
                raise StaticError.TypeMismatch(ast)

            inner: AST.NestedList = receiver.value
            resulting_dimens = receiver.dimens

            for it in ast.idx:
                if not isinstance(inner, list):
                    raise StaticError.TypeMismatch(ast)
                e = self.comptime_evaluate(it, scoping)
                if not isinstance(e, AST.IntLiteral):
                    raise StaticError.TypeMismatch(ast)
                if e.value < 0 or e.value >= len(inner):
                    # TODO: Should this be caught only here or in the visitor pattern as well?
                    raise StaticError.TypeMismatch(ast)
                inner = inner[e.value]
                resulting_dimens = resulting_dimens[:-1]

            if isinstance(inner, list):
                return AST.ArrayLiteral(resulting_dimens, receiver.eleType, inner)
        elif isinstance(ast, AST.FieldAccess):
            receiver = self.comptime_evaluate(ast.receiver, scoping)
            field = ast.field
            if not isinstance(receiver, AST.StructLiteral):
                raise StaticError.TypeMismatch(ast)

            # Resolve the type.
            struct_sym = next(filter(lambda s: isinstance(s, StructSymbol) and s.name == receiver.name, self.global_declarations))
            if struct_sym is None:
                # Probably never happens.
                raise StaticError.Undeclared(StaticError.Type(), receiver.name)

            q: Optional[Tuple[str, AST.Expr]] = next(filter(lambda t: t[0] == field, receiver.elements), None)
            if q is None:
                # Need the default value.
                if struct_sym.being_checked:
                    # Cyclic usage! It doesn't matter what is being raised here.
                    raise StaticError.TypeMismatch(ast)
                if ast.field not in struct_sym.resolved_field_types:
                    raise StaticError.Undeclared(StaticError.Field(), field)
                return self.make_default_value(struct_sym.resolved_field_types[ast.field], scoping)
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
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "-":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value - rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) - float(rhs.value))
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "*":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value * rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) * float(rhs.value))
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "/":
                # TODO: Ask prof. Phung what to do when RHS is zero.
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(int(lhs.value / rhs.value))
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) / float(rhs.value))
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "%":
                # TODO: Ask prof. Phung what to do when RHS is zero.
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value % rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == ">":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value > rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "<":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value < rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == ">=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value >= rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "<=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value <= rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "==":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value == rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "!=":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                elif isinstance(lhs, AST.FloatLiteral) and isinstance(rhs, AST.FloatLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.BooleanLiteral(lhs.value != rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "&&":
                if isinstance(lhs, AST.BooleanLiteral) and isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(lhs.value and rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "||":
                if isinstance(lhs, AST.BooleanLiteral) and isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(lhs.value or rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            else:
                raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.UnaryOp):
            rhs = self.comptime_evaluate(ast.body, scoping)
            if ast.op == "!":
                if isinstance(rhs, AST.BooleanLiteral):
                    return AST.BooleanLiteral(not rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "-":
                if isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(-rhs.value)
                elif isinstance(rhs, AST.FloatLiteral):
                    return AST.FloatLiteral(-rhs.value)
                else:
                    raise StaticError.TypeMismatch(ast)
            else:
                raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.StructLiteral):
            symbols = self.global_declarations if isinstance(scoping, int) else filter(lambda x: isinstance(x, ScopedSymbol), reversed(scoping))
            for i, sym in enumerate(symbols):
                if isinstance(sym, ScopedSymbol) and (sym.name == ast.name):
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            # Cyclic usage! It doesn't matter what is being raised here:
                            # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26313
                            raise StaticError.TypeMismatch(ast)
                        self.global_resolve_struct_definition(sym, max(scoping, i) if isinstance(scoping, int) else scoping)

                        elements_ast: List[Tuple[str, AST.Expr]] = ast.elements

                        for j, element in enumerate(elements_ast):
                            field_name, field_value_ast = element
                            for existing_field_name, existing_field_value in elements_ast[:j]:
                                if field_name == existing_field_name:
                                    raise StaticError.Redeclared(StaticError.Field(), field_name)

                            if field_name not in sym.resolved_field_types:
                                raise StaticError.Undeclared(StaticError.Field(), field_name)

                            resolved_field_value = self.comptime_evaluate(field_value_ast, scoping)
                            resolved_field_value_type = self.type_of_literal(resolved_field_value)
                            if not self.can_cast_a_to_b(resolved_field_value_type, sym.resolved_field_types[field_name]):
                                raise StaticError.TypeMismatch(ast)

                        return AST.StructLiteral(ast.name, [
                            (name, self.comptime_evaluate(val, scoping)) for name, val in elements_ast
                        ])
                    else:
                        raise StaticError.Undeclared(StaticError.Type(), ast.name)
            raise StaticError.Undeclared(StaticError.Type(), ast.name)
        else:
            # Probably NilLiteral or ArrayLiteral.
            return ast

    @staticmethod
    def type_of_literal(ast: AST.Literal):
        if isinstance(ast, AST.IntLiteral):
            return AST.IntType()
        elif isinstance(ast, AST.FloatLiteral):
            return AST.FloatType()
        elif isinstance(ast, AST.StringLiteral):
            return AST.StringType()
        elif isinstance(ast, AST.BooleanLiteral):
            return AST.BoolType()
        elif isinstance(ast, AST.ArrayLiteral):
            return AST.ArrayType(ast.dimens, ast.eleType)
        elif isinstance(ast, AST.StructLiteral):
            return AST.Id(ast.name)
        return NilType()

    # Global things get their own set of functions because of complicated identifier dependencies.
    def global_resolve_struct_definition(self, sym: StructSymbol, index_limit: int):
        if sym.done_resolving:
            return AST.Id(sym.name)

        sym.being_checked = True
        for i, element in enumerate(sym.original_ast.elements):
            field_name, field_type = element
            for existing_field_name, existing_field_type in sym.original_ast.elements[:i]:
                if field_name == existing_field_name:
                    raise StaticError.Redeclared(StaticError.Field(), element[0])

            resolved_field_type = self.global_resolve_typename(field_type, index_limit)
            sym.resolved_field_types[field_name] = resolved_field_type
        sym.being_checked = False
        sym.done_resolving = True
        return AST.Id(sym.name)

    def global_resolve_interface_definition(self, sym: InterfaceSymbol, index_limit: int):
        if sym.done_resolving:
            return AST.Id(sym.name)

        if sym.being_checked:
            # Allow interfaces to have methods returning themselves.
            return AST.Id(sym.name)

        sym.being_checked = True
        for prototype in sym.original_ast.methods:
            if prototype.name in sym.resolved_method_types:
                raise StaticError.Redeclared(StaticError.Prototype(), prototype.name)

            resolved_types = ResolvedFunctionTypes()
            resolved_types.return_type = self.global_resolve_typename(prototype.retType, index_limit)
            resolved_types.parameter_types = [self.global_resolve_typename(it, index_limit) for it in prototype.params]

            sym.resolved_method_types[prototype.name] = resolved_types
        sym.being_checked = False
        sym.done_resolving = True
        return AST.Id(sym.name)

    def global_resolve_function_definition(self, sym: FunctionSymbol, index_limit: int):
        if sym.done_resolving:
            return

        ast = sym.original_ast
        if not isinstance(ast, AST.FuncDecl):
            return

        sym.resolved_types.return_type = self.global_resolve_typename(ast.retType, index_limit)
        sym.resolved_types.parameter_types = [self.global_resolve_typename(it.parType, index_limit) for it in ast.params]
        sym.done_resolving = True

    def global_resolve_method_definition(self, recv_struct_sym: StructSymbol, ast: AST.MethodDecl, index_limit: int):
        resolved_types = ResolvedFunctionTypes()
        resolved_types.return_type = self.global_resolve_typename(ast.fun.retType, index_limit)
        resolved_types.parameter_types = [self.global_resolve_typename(it.parType, index_limit) for it in ast.fun.params]

        recv_struct_sym.resolved_method_types[ast.fun.name] = resolved_types

    def global_resolve_constant(self, sym: ConstantSymbol, index_limit: int):
        if sym.done_resolving:
            return

        sym.being_checked = True
        sym.resolved_value = self.comptime_evaluate(sym.original_ast.iniExpr, index_limit)
        sym.resolved_type = self.type_of_literal(sym.resolved_value)
        if sym.original_ast.conType is not None:
            explicit_type = self.global_resolve_typename(sym.original_ast.conType, index_limit)
            if not self.can_cast_a_to_b(sym.resolved_type, explicit_type):
                raise StaticError.TypeMismatch(sym.original_ast)
        sym.being_checked = False
        sym.done_resolving = True

    def global_resolve_typename(self, typename: AST.Type, index_limit: int):
        if isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, ScopedSymbol) and (sym.name == typename.name):
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            # I do not care anymore.
                            return typename
                        return self.global_resolve_struct_definition(sym, index_limit)
                    elif isinstance(sym, InterfaceSymbol):
                        if sym.being_checked:
                            # I do not care anymore.
                            return typename
                        return self.global_resolve_interface_definition(sym, index_limit)
                    elif (i < index_limit) and (isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol)):
                        raise StaticError.Undeclared(StaticError.Type(), typename.name)
            raise StaticError.Undeclared(StaticError.Type(), typename.name)
        elif isinstance(typename, AST.ArrayType):
            dimensions = [self.comptime_evaluate(it, index_limit) for it in typename.dimens]
            if not all(isinstance(dimension, AST.IntLiteral) for dimension in dimensions):
                raise StaticError.TypeMismatch(typename)
            resolved_element_type = self.global_resolve_typename(typename.eleType, index_limit)
            return AST.ArrayType(dimensions, resolved_element_type)
        return typename

    def check(self):
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: List[ScopeObject]):
        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, ScopedSymbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.global_declarations.append(StructSymbol(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, ScopedSymbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.global_declarations.append(InterfaceSymbol(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, ScopedSymbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Function(), thing.name)
                self.global_declarations.append(FunctionSymbol(thing.name, thing))
            elif isinstance(thing, AST.MethodDecl):
                receiver_type = thing.recType

                # Preventative check for ASTGeneration.py/AST.py flaw.
                if not isinstance(receiver_type, AST.Id):
                    raise InternalError(f"StaticChecker::visitProgram: Method with receiver type not of type AST.Id ({receiver_type})")

                self.global_declarations.append(UnresolvedMethod(thing))
            elif isinstance(thing, AST.ConstDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, ScopedSymbol), self.global_declarations):
                    if thing.conName == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Constant(), thing.conName)
                self.global_declarations.append(ConstantSymbol(thing.conName, thing))
            elif isinstance(thing, AST.VarDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, ScopedSymbol), self.global_declarations):
                    if thing.varName == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.varName)
                self.global_declarations.append(VariableSymbol(thing.varName, thing))

        for i, sym in enumerate(self.global_declarations):
            if isinstance(sym, StructSymbol):
                self.global_resolve_struct_definition(sym, i)
            elif isinstance(sym, InterfaceSymbol):
                self.global_resolve_interface_definition(sym, i)
            elif isinstance(sym, FunctionSymbol):
                # Cheap hack to filter out the prelude.
                if isinstance(sym.original_ast, AST.FuncDecl):
                    self.global_resolve_function_definition(sym, i)
            elif isinstance(sym, UnresolvedMethod):
                struct_found = False
                for maybe_struct in self.global_declarations:
                    if isinstance(maybe_struct, ScopedSymbol) and (maybe_struct.name == sym.original_ast.recType.name):
                        if isinstance(maybe_struct, StructSymbol):
                            for existing_method in maybe_struct.associated_method_asts:
                                if existing_method.fun.name == sym.original_ast.fun.name:
                                    raise StaticError.Redeclared(StaticError.Method(), sym.original_ast.fun.name)
                            for existing_field_name, existing_field_type in maybe_struct.original_ast.elements:
                                if existing_field_name == sym.original_ast.fun.name:
                                    raise StaticError.Redeclared(StaticError.Method(), sym.original_ast.fun.name)

                            maybe_struct.associated_method_asts.append(sym.original_ast)
                            sym.struct_symbol = maybe_struct
                            struct_found = True

                            self.global_resolve_method_definition(maybe_struct, sym.original_ast, i)

                            break
                        else:
                            raise StaticError.Undeclared(StaticError.Type(), sym.original_ast.recType.name)
                if not struct_found:
                    raise StaticError.Undeclared(StaticError.Type(), sym.original_ast.recType.name)
            elif isinstance(sym, ConstantSymbol):
                self.global_resolve_constant(sym, i)

        my_scope = given_scope.copy()

        for sym in self.global_declarations:
            if isinstance(sym, StructSymbol):
                my_scope.append(sym)
            elif isinstance(sym, InterfaceSymbol):
                my_scope.append(sym)
            elif isinstance(sym, FunctionSymbol):
                my_scope.append(sym)

        for sym in self.global_declarations:
            if isinstance(sym, StructSymbol):
                self.visit(sym.original_ast, my_scope)
            elif isinstance(sym, InterfaceSymbol):
                self.visit(sym.original_ast, my_scope)
            # Cheap hack to filter out the prelude.
            elif isinstance(sym, FunctionSymbol) and isinstance(sym.original_ast, AST.FuncDecl):
                self.visit(sym.original_ast, my_scope)
            elif isinstance(sym, UnresolvedMethod):
                self.visit(sym.original_ast, my_scope + [sym])
            elif isinstance(sym, ConstantSymbol):
                self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)
            elif isinstance(sym, VariableSymbol):
                sym.resolved_type = self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        explicit_type: Optional[AST.Type] = self.visit(ast.varType, given_scope + [IsTypenameVisit()]) if (ast.varType is not None) else None
        implicit_type: Optional[AST.Type] = self.visit(ast.varInit, given_scope + [IsExpressionVisit()]) if (ast.varInit is not None) else None

        # No voids allowed.
        if isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast.varInit)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.can_cast_a_to_b(implicit_type, explicit_type)):
            raise StaticError.TypeMismatch(ast)

        if (explicit_type is None) and isinstance(implicit_type, NilType):
            # Whatever is raised here doesn't matter.
            # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26184
            raise StaticError.TypeMismatch(ast)

        return explicit_type if explicit_type is not None else implicit_type

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes here either; that's done by the outer layer.
        explicit_type: Optional[AST.Type] = self.visit(ast.conType, given_scope + [IsTypenameVisit()]) if (ast.conType is not None) else None
        implicit_type: Optional[AST.Type] = self.visit(ast.iniExpr, given_scope + [IsComptimeExpressionVisit(), IsExpressionVisit()]) if (ast.iniExpr is not None) else None

        # No voids allowed.
        if isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast.iniExpr)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.can_cast_a_to_b(implicit_type, explicit_type)):
            raise StaticError.TypeMismatch(ast)

        if (explicit_type is None) and isinstance(implicit_type, NilType):
            # Whatever is raised here doesn't matter.
            # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26184
            raise StaticError.TypeMismatch(ast)

        return explicit_type if explicit_type is not None else implicit_type

    def visitFuncDecl(self, ast: AST.FuncDecl, given_scope: List[ScopeObject]):
        self_sym: Optional[FunctionSymbol] = next(filter(lambda x: isinstance(x, FunctionSymbol) and (x.original_ast == ast), reversed(given_scope)), None)
        # Sanity check.
        if self_sym is None:
            raise InternalError("StaticCheck::visitFuncDecl: FunctionSymbol for AST not present during its own visit")

        my_scope = given_scope.copy()
        for i, param in enumerate(ast.params):
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), my_scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            my_scope.append(FunctionParameterSymbol(param.parName, param, self_sym.resolved_types.parameter_types[i]))

        current_function_scope_object = CurrentFunction(self_sym.resolved_types)
        self.visit(ast.body, my_scope + [current_function_scope_object])

    def visitMethodDecl(self, ast: AST.MethodDecl, given_scope: List[ScopeObject]):
        self_sym: Optional[UnresolvedMethod] = next(filter(lambda x: isinstance(x, UnresolvedMethod) and (x.original_ast == ast), reversed(given_scope)), None)
        # Sanity check.
        if self_sym is None:
            raise InternalError("StaticCheck::visitMethodDecl: UnresolvedMethod for AST not present during its own visit")

        for i, param in enumerate(ast.fun.params):
            for existing_param in ast.fun.params[:i]:
                if existing_param.parName == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)

        resolved_types = self_sym.struct_symbol.resolved_method_types[ast.fun.name]

        my_scope = given_scope.copy()
        my_scope.append(FunctionParameterSymbol(ast.receiver, AST.Id(ast.receiver), ast.recType))
        for i, param in enumerate(ast.fun.params):
            my_scope.append(FunctionParameterSymbol(param.parName, param, resolved_types.parameter_types[i]))

        current_function_scope_object = CurrentFunction(resolved_types)
        self.visit(ast.fun.body, my_scope + [current_function_scope_object])

    def visitPrototype(self, ast, param):
        pass # See global_resolve_interface_definition and visitProgram.

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

    def visitArrayType(self, ast: AST.ArrayType, given_scope: List[ScopeObject]):
        # Evaluate indices so we can type-check.
        dimensions = [self.comptime_evaluate(it, given_scope) for it in ast.dimens]
        if not all(isinstance(dimension, AST.IntLiteral) for dimension in dimensions):
            raise StaticError.TypeMismatch(ast)
        # No need to append IsTypenameVisit.
        resolved_element_type = self.visit(ast.eleType, given_scope)
        return AST.ArrayType(dimensions, resolved_element_type)

    def visitStructType(self, ast: AST.StructType, given_scope: List[ScopeObject]):
        pass # See global_resolve_struct_definition.

    def visitInterfaceType(self, ast: AST.InterfaceType, given_scope: List[ScopeObject]):
        pass # See global_resolve_interface_definition.

    def visitBlock(self, ast: AST.Block, given_scope: List[ScopeObject]):
        this_block_names = []

        # Find extra banned names if we're the block of a for loop
        loop_object: Optional[IsLoopVisit] = next(filter(lambda x: isinstance(x, IsLoopVisit), reversed(given_scope)), None)
        if loop_object is not None and loop_object.block == ast:
            this_block_names += loop_object.banned_names

        my_scope = given_scope.copy()

        # Vars and consts within the same block cannot collide names. Inner blocks can shadow.
        for statement in ast.member:
            if isinstance(statement, AST.VarDecl):
                if statement.varName in this_block_names:
                    raise StaticError.Redeclared(StaticError.Variable(), statement.varName)
                this_block_names.append(statement.varName)

                sym = VariableSymbol(statement.varName, statement)
                sym.resolved_type = self.visit(statement, my_scope)
                my_scope.append(sym)
            elif isinstance(statement, AST.ConstDecl):
                if statement.conName in this_block_names:
                    raise StaticError.Redeclared(StaticError.Constant(), statement.conName)
                this_block_names.append(statement.conName)

                sym = ConstantSymbol(statement.conName, statement)
                sym.resolved_type = self.visit(statement, my_scope)
                sym.resolved_value = self.comptime_evaluate(statement.iniExpr, my_scope) if (statement.iniExpr is not None) else None
                my_scope.append(sym)
            elif isinstance(statement, AST.Expr):
                expr_type = self.visit(statement, my_scope + [IsExpressionVisit()])
                # I guess prof. Phung doesn't want any code to discard any values.
                if not isinstance(expr_type, AST.VoidType):
                    raise StaticError.TypeMismatch(statement)
            elif isinstance(statement, AST.Assign) and isinstance(statement.lhs, AST.Id):
                lhs: AST.Id = statement.lhs
                # Is the name not declared? If so, turn it into a variable declaration.
                existing_maybe_variable = next(filter(lambda x: isinstance(x, ScopedSymbol) and (x.name == lhs.name), reversed(my_scope)), None)
                if existing_maybe_variable is None or not (isinstance(existing_maybe_variable, VariableSymbol) or isinstance(existing_maybe_variable, ConstantSymbol) or isinstance(existing_maybe_variable, FunctionParameterSymbol)):
                    this_block_names.append(lhs.name)

                    sym = VariableSymbol(lhs.name, statement)

                    try:
                        implicit_type = self.visit(statement.rhs, my_scope + [IsExpressionVisit()])
                    except StaticError.Undeclared as e:
                        if isinstance(e.k, StaticError.Identifier) and e.n == lhs.name:
                            # TODO: is this kind of useless?
                            raise StaticError.Undeclared(StaticError.Identifier(), lhs.name)
                        raise e
                    # No voids allowed.
                    if isinstance(implicit_type, AST.VoidType):
                        raise StaticError.TypeMismatch(statement)

                    sym.resolved_type = implicit_type
                    my_scope.append(sym)
                else:
                    self.visit(statement, my_scope)
            else:
                # This is probably a statement.
                self.visit(statement, my_scope)

    def visitAssign(self, ast: AST.Assign, given_scope: List[ScopeObject]):
        lhs_type = self.visit(ast.lhs, given_scope + [IsExpressionVisit(), IsLeftHandSideVisit()])
        rhs_type = self.visit(ast.rhs, given_scope + [IsExpressionVisit()])
        if not self.can_cast_a_to_b(rhs_type, lhs_type):
            raise StaticError.TypeMismatch(ast)
        # Return nothing, I guess.

    def visitIf(self, ast: AST.If, given_scope: List[ScopeObject]):
        condition_type = self.visit(ast.expr, given_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            raise StaticError.TypeMismatch(ast)
        self.visit(ast.thenStmt, given_scope)
        if ast.elseStmt is not None:
            self.visit(ast.elseStmt, given_scope)

    def visitForBasic(self, ast: AST.ForBasic, given_scope: List[ScopeObject]):
        condition_type = self.visit(ast.cond, given_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            raise StaticError.TypeMismatch(ast)
        self.visit(ast.loop, given_scope + [IsLoopVisit(ast.loop, [])])

    def visitForStep(self, ast: AST.ForStep, given_scope: List[ScopeObject]):
        my_scope = given_scope.copy()

        banned_names: List[str] = []

        if isinstance(ast.init, AST.VarDecl):
            sym = VariableSymbol(ast.init.varName, ast.init)
            sym.resolved_type = self.visit(ast.init, my_scope)
            my_scope.append(sym)
            banned_names.append(ast.init.varName)
        elif isinstance(ast.init, AST.Assign) and isinstance(ast.init.lhs, AST.Id):
            lhs: AST.Id = ast.init.lhs
            # Is the name not declared? If so, turn it into a variable declaration.
            existing_maybe_variable = next(filter(lambda x: isinstance(x, ScopedSymbol) and (x.name == lhs.name), reversed(my_scope)), None)
            if existing_maybe_variable is None or not (isinstance(existing_maybe_variable, VariableSymbol) or isinstance(existing_maybe_variable, ConstantSymbol) or isinstance(existing_maybe_variable, FunctionParameterSymbol)):
                sym = VariableSymbol(lhs.name, ast.init)

                try:
                    implicit_type = self.visit(ast.init.rhs, my_scope + [IsExpressionVisit()])
                except StaticError.Undeclared as e:
                    if isinstance(e.k, StaticError.Identifier) and e.n == lhs.name:
                        # TODO: is this kind of useless?
                        raise StaticError.Undeclared(StaticError.Identifier(), lhs.name)
                    raise e
                # No voids allowed.
                if isinstance(implicit_type, AST.VoidType):
                    raise StaticError.TypeMismatch(ast)

                sym.resolved_type = implicit_type
                my_scope.append(sym)

                banned_names.append(lhs.name)
            else:
                self.visit(ast.init, my_scope)
        else:
            # This is probably a statement.
            self.visit(ast.init, my_scope)

        condition_type = self.visit(ast.cond, my_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            raise StaticError.TypeMismatch(ast)

        if isinstance(ast.upda.lhs, AST.Id):
            lhs: AST.Id = ast.upda.lhs
            # Is the name not declared? If so, turn it into a variable declaration.
            existing_maybe_variable = next(filter(lambda x: isinstance(x, ScopedSymbol) and (x.name == lhs.name), reversed(my_scope)), None)
            if existing_maybe_variable is None or not (isinstance(existing_maybe_variable, VariableSymbol) or isinstance(existing_maybe_variable, ConstantSymbol) or isinstance(existing_maybe_variable, FunctionParameterSymbol)):
                sym = VariableSymbol(lhs.name, ast.upda)

                try:
                    implicit_type = self.visit(ast.upda.rhs, my_scope + [IsExpressionVisit()])
                except StaticError.Undeclared as e:
                    if isinstance(e.k, StaticError.Identifier) and e.n == lhs.name:
                        # TODO: is this kind of useless?
                        raise StaticError.Undeclared(StaticError.Identifier(), lhs.name)
                    raise e
                # No voids allowed.
                if isinstance(implicit_type, AST.VoidType):
                    raise StaticError.TypeMismatch(ast)

                sym.resolved_type = implicit_type
                my_scope.append(sym)

                banned_names.append(lhs.name)
            else:
                self.visit(ast.upda, my_scope)
        else:
            # This is probably a statement.
            self.visit(ast.upda, my_scope)

        my_scope += [IsLoopVisit(ast.loop, banned_names)]
        self.visit(ast.loop, my_scope)

    def visitForEach(self, ast: AST.ForEach, given_scope: List[ScopeObject]):
        my_scope = given_scope.copy()

        # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26554
        idx_sym = next(filter(lambda x: isinstance(x, ScopedSymbol) and (x.name == ast.idx.name), reversed(my_scope)), None)
        if idx_sym is None or not (isinstance(idx_sym, VariableSymbol) or isinstance(idx_sym, FunctionParameterSymbol)):
            raise StaticError.Undeclared(StaticError.Identifier(), ast.idx.name)
        if not isinstance(idx_sym.resolved_type, AST.IntType):
            raise StaticError.TypeMismatch(ast)

        value_sym = next(filter(lambda x: isinstance(x, ScopedSymbol) and (x.name == ast.value.name), reversed(my_scope)), None)
        if value_sym is None or not (isinstance(value_sym, VariableSymbol) or isinstance(value_sym, FunctionParameterSymbol)):
            raise StaticError.Undeclared(StaticError.Identifier(), ast.value.name)

        iteration_target_type = self.visit(ast.arr, my_scope + [IsExpressionVisit()])
        if not isinstance(iteration_target_type, AST.ArrayType):
            raise StaticError.TypeMismatch(ast)

        required_value_type = iteration_target_type.eleType if len(iteration_target_type.dimens) == 1 else AST.ArrayType(iteration_target_type.dimens[1:], iteration_target_type.eleType)
        if not self.hard_compare_types(required_value_type, value_sym.resolved_type):
            raise StaticError.TypeMismatch(ast)

        my_scope += [IsLoopVisit(ast.loop, [])]
        self.visit(ast.loop, my_scope)

    def visitContinue(self, ast: AST.Continue, given_scope: List[ScopeObject]):
        pass # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26303

    def visitBreak(self, ast: AST.Break, given_scope: List[ScopeObject]):
        pass # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26303

    def visitReturn(self, ast: AST.Return, given_scope: List[ScopeObject]):
        current_function: Optional[CurrentFunction] = next(filter(lambda x: isinstance(x, CurrentFunction), reversed(given_scope)), None)
        if current_function is None:
            return # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26258

        if ast.expr is None:
            if not isinstance(current_function.resolved_types.return_type, AST.VoidType):
                raise StaticError.TypeMismatch(ast)
        else:
            expr_type = self.visit(ast.expr, given_scope + [IsExpressionVisit()])
            if isinstance(current_function.resolved_types.return_type, AST.VoidType):
                raise StaticError.TypeMismatch(ast)
            if not self.hard_compare_types(expr_type, current_function.resolved_types.return_type):
                raise StaticError.TypeMismatch(ast)

    def visitBinaryOp(self, ast: AST.BinaryOp, given_scope: List[ScopeObject]):
        lhs = self.visit(ast.left, given_scope)
        rhs = self.visit(ast.right, given_scope)
        if ast.op == "+":
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.IntType()
            elif (isinstance(lhs, AST.FloatType) or isinstance(lhs, AST.IntType)) and (
                    isinstance(rhs, AST.FloatType) or isinstance(rhs, AST.IntType)):
                return AST.FloatType()
            elif isinstance(lhs, AST.StringType) and isinstance(rhs, AST.StringType):
                return AST.StringType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op in ["-", "*", "/"]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.IntType()
            elif (isinstance(lhs, AST.FloatType) or isinstance(lhs, AST.IntType)) and (
                    isinstance(rhs, AST.FloatType) or isinstance(rhs, AST.IntType)):
                return AST.FloatType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op == "%":
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.IntType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op in [">", "<", ">=", "<=", "==", "!="]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BoolType()
            elif isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.FloatType):
                return AST.BoolType()
            elif isinstance(lhs, AST.StringType) and isinstance(rhs, AST.StringType):
                return AST.BoolType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op in ["&&", "||"]:
            if isinstance(lhs, AST.BoolType) and isinstance(rhs, AST.BoolType):
                return AST.BoolType()
            else:
                raise StaticError.TypeMismatch(ast)
        else:
            raise StaticError.TypeMismatch(ast)

    def visitUnaryOp(self, ast: AST.UnaryOp, given_scope: List[ScopeObject]):
        rhs = self.visit(ast.body, given_scope)
        if ast.op == "!":
            if isinstance(rhs, AST.BoolType):
                return AST.BoolType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op == "-":
            if isinstance(rhs, AST.IntType):
                return AST.IntType()
            elif isinstance(rhs, AST.FloatType):
                return AST.FloatType()
            else:
                raise StaticError.TypeMismatch(ast)
        else:
            raise StaticError.TypeMismatch(ast)

    def visitFuncCall(self, ast: AST.FuncCall, given_scope: List[ScopeObject]):
        for sym in filter(lambda x: isinstance(x, ScopedSymbol), reversed(given_scope)):
            if sym.name == ast.funName:
                if isinstance(sym, FunctionSymbol):
                    # There used to be a IsComptimeExpressionVisit check here, but:
                    # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26129.

                    # Check arguments.
                    if isinstance(sym.original_ast, AST.FuncDecl) and (len(ast.args) != len(sym.original_ast.params)):
                        raise StaticError.TypeMismatch(ast)
                    # Sanity check
                    if isinstance(sym.original_ast, AST.FuncDecl) and (len(sym.original_ast.params) != len(sym.resolved_types.parameter_types)):
                        # Sanity check failed !!??!!!??
                        raise InternalError(
                            f"StaticChecker::visitFuncCall: Ran into function {sym.name} where len(sym.original_ast.params) != len(sym.resolved_types.parameter_types) ({len(sym.original_ast.params)} != {len(sym.resolved_types.parameter_types)})")

                    for i, arg in enumerate(ast.args):
                        arg_type = self.visit(arg, given_scope) # No need to append IsExpressionVisit.
                        if not self.hard_compare_types(arg_type, sym.resolved_types.parameter_types[i]):
                            raise StaticError.TypeMismatch(ast)

                    return sym.resolved_types.return_type
                else:
                    raise StaticError.Undeclared(StaticError.Function(), ast.funName)
        raise StaticError.Undeclared(StaticError.Function(), ast.funName)

    def visitMethCall(self, ast: AST.MethCall, given_scope: List[ScopeObject]):
        receiver_type = self.visit(ast.receiver, given_scope) # No need to append IsExpressionVisit.

        if not isinstance(receiver_type, AST.Id):
            raise StaticError.TypeMismatch(ast)

        for sym in filter(lambda x: isinstance(x, StructSymbol) or isinstance(x, InterfaceSymbol), self.global_declarations):
            if sym.name == receiver_type.name:
                if ast.metName not in sym.resolved_method_types:
                    raise StaticError.Undeclared(StaticError.Method(), ast.metName)

                resolved_method_types: ResolvedFunctionTypes = sym.resolved_method_types[ast.metName]
                # Check arguments.
                if len(ast.args) != len(resolved_method_types.parameter_types):
                    raise StaticError.TypeMismatch(ast)

                for i, arg in enumerate(ast.args):
                    arg_type = self.visit(arg, given_scope) # No need to append IsExpressionVisit.
                    if not self.hard_compare_types(arg_type, resolved_method_types.parameter_types[i]):
                        raise StaticError.TypeMismatch(ast)
                return resolved_method_types.return_type
        raise StaticError.Undeclared(StaticError.Type(), receiver_type.name)

    def visitId(self, ast: AST.Id, given_scope: List[ScopeObject]):
        id_mode: Union[IsTypenameVisit, IsExpressionVisit, None] = next(filter(lambda x: isinstance(x, IsTypenameVisit) or isinstance(x, IsExpressionVisit), reversed(given_scope)), None)
        for sym in filter(lambda x: isinstance(x, ScopedSymbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol):
                    if isinstance(id_mode, IsExpressionVisit):
                        # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26183
                        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                    return ast
                elif isinstance(sym, FunctionSymbol):
                    if isinstance(id_mode, IsTypenameVisit):
                        raise StaticError.Undeclared(StaticError.Type(), ast.name)
                    elif isinstance(id_mode, IsExpressionVisit):
                        # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26183
                        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                    raise InternalError(f"StaticChecker::visitId: Visited identifier {ast} outside of a typename or expression")
                elif isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol) or isinstance(sym, FunctionParameterSymbol):
                    if isinstance(id_mode, IsTypenameVisit):
                        raise StaticError.Undeclared(StaticError.Type(), ast.name)
                    # There used to be a check for IsLeftHandSideVisit here, but:
                    # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26257
                    return sym.resolved_type
                else:
                    return None
        if isinstance(id_mode, IsTypenameVisit):
            raise StaticError.Undeclared(StaticError.Type(), ast.name)
        elif isinstance(id_mode, IsExpressionVisit):
            # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26183
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
        raise InternalError(f"StaticChecker::visitId: Visited identifier {ast} outside of a typename or expression")

    def visitArrayCell(self, ast: AST.ArrayCell, given_scope: List[ScopeObject]):
        receiver_type = self.visit(ast.arr, given_scope) # No need to append IsExpressionVisit.

        if not isinstance(receiver_type, AST.ArrayType):
            raise StaticError.TypeMismatch(ast)

        if len(receiver_type.dimens) < len(ast.idx):
            raise StaticError.TypeMismatch(ast)

        for i, idx in enumerate(ast.idx):
            idx_type = self.visit(idx, given_scope)
            if not isinstance(idx_type, AST.IntType):
                raise StaticError.TypeMismatch(ast)

        if len(receiver_type.dimens) == len(ast.idx):
            return receiver_type.eleType

        return AST.ArrayType(receiver_type.dimens[len(ast.idx):], receiver_type.eleType)

    def visitFieldAccess(self, ast: AST.FieldAccess, given_scope: List[ScopeObject]):
        receiver_type = self.visit(ast.receiver, given_scope) # No need to append IsExpressionVisit.

        if not isinstance(receiver_type, AST.Id):
            raise StaticError.TypeMismatch(ast)

        for sym in filter(lambda x: isinstance(x, StructSymbol), self.global_declarations):
            if sym.name == receiver_type.name:
                if isinstance(sym, StructSymbol):
                    if ast.field not in sym.resolved_field_types:
                        raise StaticError.Undeclared(StaticError.Field(), ast.field)
                    return sym.resolved_field_types[ast.field]
                else:
                    raise StaticError.TypeMismatch(ast)
        raise StaticError.Undeclared(StaticError.Type(), receiver_type.name)

    def visitIntLiteral(self, ast, param):
        return AST.IntType()

    def visitFloatLiteral(self, ast, param):
        return AST.FloatType()

    def visitBooleanLiteral(self, ast, param):
        return AST.BoolType()

    def visitStringLiteral(self, ast, param):
        return AST.StringType()

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, given_scope: List[ScopeObject]):
        dimensions = [self.comptime_evaluate(it, given_scope) for it in ast.dimens]
        if not all(isinstance(dimension, AST.IntLiteral) for dimension in dimensions):
            raise StaticError.TypeMismatch(ast)
        ele_type = self.visit(ast.eleType, given_scope + [IsTypenameVisit()])
        self.check_nested_list(ast, ast.value, ele_type, dimensions, given_scope)
        return AST.ArrayType(dimensions, ele_type)

    def visitStructLiteral(self, ast: AST.StructLiteral, given_scope: List[ScopeObject]):
        # Find the struct name.
        struct_sym: Optional[StructSymbol] = None
        for sym in filter(lambda x: isinstance(x, ScopedSymbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol):
                    struct_sym = sym
                else:
                    raise StaticError.Undeclared(StaticError.Type(), ast.name)
        if struct_sym is None:
            raise StaticError.Undeclared(StaticError.Type(), ast.name)

        for i, element in enumerate(ast.elements):
            field_name, field_value = element
            for existing_field_name, existing_field_value in ast.elements[:i]:
                if field_name == existing_field_name:
                    raise StaticError.Redeclared(StaticError.Field(), field_name)

            if field_name not in struct_sym.resolved_field_types:
                raise StaticError.Undeclared(StaticError.Field(), field_name)

            field_initializer_type = self.visit(field_value, given_scope + [IsExpressionVisit()])
            if not self.can_cast_a_to_b(field_initializer_type, struct_sym.resolved_field_types[field_name]):
                raise StaticError.TypeMismatch(ast)

        return AST.Id(ast.name)

    def visitNilLiteral(self, ast, param):
        return NilType()

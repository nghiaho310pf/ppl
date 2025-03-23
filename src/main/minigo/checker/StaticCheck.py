"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=6hUH7RxU2yQ
"""

import AST
from Visitor import *
from typing import List, Tuple
import StaticError

# Just use classes, man.
# For scope state.

class ScopeObject:
    def __init__(self):
        pass

# For caching resolved types.
# For now this purely only exists because there are comptime expressions that must be evaluated
# to fully resolve array type ASTs.

class ResolvedFunctionTypes:
    def __init__(self):
        self.return_type = None
        self.parameter_types = None

# For name resolution.

class Symbol(ScopeObject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

class StructSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.StructType):
        super().__init__(name)
        self.original_ast = original_ast

        self.resolved_field_types = dict[str, AST.Type]()
        self.resolved_method_types = dict[str, ResolvedFunctionTypes]()

        self.being_checked = False
        self.done_resolving = False

class InterfaceSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.InterfaceType):
        super().__init__(name)
        self.original_ast = original_ast

        self.resolved_method_types = dict[str, ResolvedFunctionTypes]()

        self.being_checked = False
        self.done_resolving = False

class FunctionSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.AST):
        super().__init__(name)
        self.original_ast = original_ast

        self.resolved_types = ResolvedFunctionTypes()

        self.done_resolving = False

class VariableSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.VarDecl | AST.Assign | AST.Id):
        super().__init__(name)
        self.original_ast = original_ast # VarDecl for usual vars, Assign for implicit vars from assigns, Id for loops

        self.resolved_explicit_type = None
        self.resolved_type = None

class ConstantSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ConstDecl):
        super().__init__(name)
        self.original_ast = original_ast

        self.resolved_type = None
        self.resolved_value = None

        self.being_checked = False
        self.done_resolving = False

class FunctionParameterSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ParamDecl | AST.Id, resolved_type: AST.Type):
        super().__init__(name)
        # original_ast can be an identifier because it could be a receiver of a method.
        self.original_ast = original_ast
        self.resolved_type = resolved_type

# For banning illegal returns.

class CurrentFunction(ScopeObject):
    def __init__(self, resolved_types: ResolvedFunctionTypes):
        super().__init__()
        self.resolved_types = resolved_types

# Cheap hacks for resolving types for methods.

class UnresolvedMethod(ScopeObject):
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
    def __init__(self):
        super().__init__()

# # For making sure returns are in place in a function with a return type.
# # Returns are confirmed to not require checks. I'm removing this mechanism since it does not hinder type-checking.
# # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26258
#
# class ReturnBeacon(ScopeObject):
#     def __init__(self):
#         super().__init__()
#         self.has_return = False
#
#     def set_has_return(self):
#         self.has_return = True

# Special nil type.

class NilType:
    def __init__(self):
        pass

class StaticChecker(BaseVisitor):
    global_declarations: List[ScopeObject]

    # Methods get special treatment; they modify other things.
    # They are not const-friendly so they don't really need more processing.
    method_declarations: List[AST.MethodDecl]

    def __init__(self, root_ast):
        self.global_declarations = self.create_prelude()
        self.method_declarations = []

        self.root_ast = root_ast

    @staticmethod
    def hard_compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        if isinstance(a, AST.ArrayType) and isinstance(b, AST.ArrayType):
            if (not StaticChecker.hard_compare_types(a.eleType, b.eleType)) or (len(a.dimens) != len(b.dimens)):
                return False
            for i, dim in enumerate(a.dimens):
                if not isinstance(dim, AST.IntLiteral):
                    return False
                other_dim = b.dimens[i]
                if not isinstance(other_dim, AST.IntLiteral):
                    return False
                if dim.value != other_dim.value:
                    return False
        return type(a) == type(b)

    @staticmethod
    def local_can_cast_a_to_b(a: AST.Type, b: AST.Type, given_scope: List[ScopeObject]):
        # Allow going from nils to struct/interface instances.
        if isinstance(a, NilType) and isinstance(b, AST.Id):
            return True

        # Allow structs to be cast to interfaces.
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            a_id: AST.Id = a
            b_id: AST.Id = b
            if a_id.name == b_id.name:
                return True
            maybe_source_struct: StructSymbol | None = next(filter(lambda x: isinstance(x, StructSymbol) and (x.name == a_id.name), reversed(given_scope)), None)
            maybe_target_interface: InterfaceSymbol | None = next(filter(lambda x: isinstance(x, InterfaceSymbol) and (x.name == b_id.name), reversed(given_scope)), None)

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
            if (not StaticChecker.hard_compare_types(a.eleType, b.eleType)) or (len(a.dimens) != len(b.dimens)):
                return False
            for i, dim in enumerate(a.dimens):
                if not isinstance(dim, AST.IntLiteral):
                    return False
                other_dim = b.dimens[i]
                if not isinstance(other_dim, AST.IntLiteral):
                    return False
                if dim.value != other_dim.value:
                    return False

        return type(a) == type(b)

    @staticmethod
    def local_make_default_value(typename: AST.Type, given_scope: List[ScopeObject], make_nested_list: bool = False):
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
                raise StaticError.TypeMismatch(typename)
            child_type = AST.ArrayType(typename.dimens[1:], typename.eleType) if len(typename.dimens) > 1 else typename.eleType
            vals: AST.NestedList = [StaticChecker.local_make_default_value(child_type, given_scope, True) for _ in range(d.value)]
            if make_nested_list:
                return vals
            return AST.ArrayLiteral(typename.dimens, typename.eleType, vals)
        elif isinstance(typename, AST.Id):
            for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
                if sym.name == typename.name:
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
                        return AST.StructLiteral(typename.name, [
                            (name, StaticChecker.local_make_default_value(resolved_type, given_scope)) for name, resolved_type in sym.resolved_field_types.items()
                        ])
                    elif isinstance(sym, InterfaceSymbol):
                        return AST.NilLiteral()
                    else:
                        raise StaticError.TypeMismatch(typename)
            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
        return AST.NilLiteral()

    # Just roll our own recursion here instead of using StaticChecker's cancerous visitor mechanism.
    @staticmethod
    def local_comptime_evaluate(ast: AST.Expr, given_scope: List[ScopeObject]):
        if isinstance(ast, AST.Id):
            for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
                if sym.name == ast.name:
                    if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol):
                        # I guess we don't allow bare-referring to structs and interfaces?
                        # TODO: ask prof. Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    elif isinstance(sym, FunctionSymbol):
                        # I guess we don't allow bare-referring to functions?
                        # TODO: ask prof. Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    elif isinstance(sym, ConstantSymbol):
                        return sym.resolved_value
                    elif isinstance(sym, VariableSymbol) or isinstance(sym, FunctionParameterSymbol):
                        # Referencing other variables/parameters isn't allowed in constants.
                        # TODO: ask prof. Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    else:
                        # TODO: raise an unreachable case being reached.
                        return None
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
        elif isinstance(ast, AST.FuncCall) or isinstance(ast, AST.MethCall):
            # Function calls are not allowed at compilation-time evaluation.
            raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.ArrayCell):
            # I guess we need to evaluate the entire thing.
            receiver = StaticChecker.local_comptime_evaluate(ast.arr, given_scope)
            if not isinstance(receiver, AST.ArrayLiteral):
                raise StaticError.TypeMismatch(ast)

            inner: AST.NestedList = receiver.value
            resulting_dimens = receiver.dimens

            for it in ast.idx:
                if not isinstance(inner, list):
                    raise StaticError.TypeMismatch(ast)
                e = StaticChecker.local_comptime_evaluate(it, given_scope)
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
            # I guess we need to evaluate the entire thing.
            receiver = StaticChecker.local_comptime_evaluate(ast.receiver, given_scope)
            field = ast.field
            if not isinstance(receiver, AST.StructLiteral):
                raise StaticError.TypeMismatch(ast)

            # Resolve the type.
            for maybe_struct in filter(lambda s: isinstance(s, Symbol), given_scope):
                if maybe_struct.name == receiver.name:
                    if isinstance(maybe_struct, StructSymbol):
                        q: Tuple[str, AST.Expr] | None = next(filter(lambda t: t[0] == field, receiver.elements), None)
                        if q is None:
                            raise StaticError.Undeclared(StaticError.Field(), field)
                        return StaticChecker.local_comptime_evaluate(q[1], given_scope)
                    else:
                        raise StaticError.TypeMismatch(ast)
            # Never happens.
            raise StaticError.Undeclared(StaticError.Identifier(), receiver.name)
        elif isinstance(ast, AST.BinaryOp):
            lhs = StaticChecker.local_comptime_evaluate(ast.left, given_scope)
            rhs = StaticChecker.local_comptime_evaluate(ast.right, given_scope)
            if ast.op == "+":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value + rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) + float(rhs.value))
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.StringLiteral(f"{lhs.value[1:-1]}{rhs.value[1:-1]}")
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
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) % float(rhs.value))
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
            rhs = StaticChecker.local_comptime_evaluate(ast.body, given_scope)
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
            for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
                if sym.name == ast.name:
                    if isinstance(sym, StructSymbol):
                        elements_ast: List[Tuple[str, AST.Expr]] = ast.elements

                        for i, element in enumerate(elements_ast):
                            field_name, field_value_ast = element
                            for existing_field_name, existing_field_value in elements_ast[:i]:
                                if field_name == existing_field_name:
                                    raise StaticError.Redeclared(StaticError.Field(), field_name)

                            if field_name not in sym.resolved_field_types:
                                raise StaticError.Undeclared(StaticError.Field(), field_name)

                            resolved_field_value = StaticChecker.local_comptime_evaluate(field_value_ast, given_scope)
                            resolved_field_value_type = StaticChecker.type_of_literal(resolved_field_value)
                            if not StaticChecker.local_can_cast_a_to_b(resolved_field_value_type,
                                                              sym.resolved_field_types[field_name],
                                                              given_scope):
                                raise StaticError.TypeMismatch(field_value_ast)

                        initialized_field_names = [y[0] for y in elements_ast]
                        uninitialized_fields = filter(lambda x: x[0] not in initialized_field_names, sym.resolved_field_types.items())

                        return AST.StructLiteral(ast.name, [
                            (name, StaticChecker.local_comptime_evaluate(val, given_scope)) for name, val in elements_ast
                        ] + [
                            (name, StaticChecker.local_make_default_value(sym.resolved_field_types[name], given_scope)) for name, typename in uninitialized_fields
                        ])
                    else:
                        raise StaticError.TypeMismatch(ast)
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
        else:
            # Probably NilLiteral or ArrayLiteral.
            return ast

    def check_nested_list(self, original_ast: AST.ArrayLiteral, ast: AST.NestedList, ele_type: AST.Type, dimens: list[AST.IntLiteral], given_scope: list[ScopeObject]):
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
                this_ele_type = self.visit(ele, given_scope + [IsExpressionVisit()])
                if not self.local_can_cast_a_to_b(this_ele_type, ele_type, given_scope):
                    raise StaticError.TypeMismatch(ele)

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

    # Global things get their own set of functions because of complicated identifier dependencies.
    # This might go away in a future refactor.
    def global_can_cast_a_to_b(self, a: AST.Type, b: AST.Type, index_limit: int):
        # Allow going from nils to struct/interface instances.
        if isinstance(a, NilType) and isinstance(b, AST.Id):
            return True

        # Allow structs to be cast to interfaces.
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            a_id: AST.Id = a
            b_id: AST.Id = b
            if a_id.name == b_id.name:
                return True
            maybe_source_struct: StructSymbol | None = next(filter(lambda x: isinstance(x, StructSymbol) and (x.name == a_id.name), self.global_declarations), None)
            maybe_target_interface: InterfaceSymbol | None = next(filter(lambda x: isinstance(x, InterfaceSymbol) and (x.name == b_id.name), self.global_declarations), None)

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
            if (not StaticChecker.hard_compare_types(a.eleType, b.eleType)) or (len(a.dimens) != len(b.dimens)):
                return False
            for i, dim in enumerate(a.dimens):
                if not isinstance(dim, AST.IntLiteral):
                    return False
                other_dim = b.dimens[i]
                if not isinstance(other_dim, AST.IntLiteral):
                    return False
                if dim.value != other_dim.value:
                    return False

        return type(a) == type(b)

    def global_comptime_evaluate(self, ast: AST.Expr, index_limit: int):
        if isinstance(ast, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Symbol) and (sym.name == ast.name):
                    if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol) or isinstance(sym, FunctionSymbol) or isinstance(sym, VariableSymbol):
                        raise StaticError.TypeMismatch(ast)
                    elif (i < index_limit) and isinstance(sym, ConstantSymbol):
                        if sym.being_checked:
                            # Cyclic usage! TODO: what to raise here?
                            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                        self.global_resolve_constant(sym, index_limit)
                        return sym.resolved_value
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
        elif isinstance(ast, AST.FuncCall) or isinstance(ast, AST.MethCall):
            # Function calls are not allowed at compilation-time evaluation.
            raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.ArrayCell):
            # I guess we need to evaluate the entire thing.
            receiver = self.global_comptime_evaluate(ast.arr, index_limit)
            if not isinstance(receiver, AST.ArrayLiteral):
                raise StaticError.TypeMismatch(ast)

            inner: AST.NestedList = receiver.value
            resulting_dimens = receiver.dimens

            for it in ast.idx:
                if not isinstance(inner, list):
                    raise StaticError.TypeMismatch(ast)
                e = self.global_comptime_evaluate(it, index_limit)
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
            # I guess we need to evaluate the entire thing.
            receiver = self.global_comptime_evaluate(ast.receiver, index_limit)
            field = ast.field
            if not isinstance(receiver, AST.StructLiteral):
                raise StaticError.TypeMismatch(ast)

            # Resolve the type.
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Symbol) and (receiver.name == sym.name):
                    if isinstance(sym, StructSymbol):
                        q: Tuple[str, AST.Expr] | None = next(filter(lambda t: t[0] == field, receiver.elements), None)
                        if q is None:
                            raise StaticError.Undeclared(StaticError.Field(), field)
                        return self.global_comptime_evaluate(q[1], index_limit)
                    else:
                        raise StaticError.TypeMismatch(ast)
            # Never happens.
            raise StaticError.Undeclared(StaticError.Identifier(), receiver.name)
        elif isinstance(ast, AST.BinaryOp):
            lhs = self.global_comptime_evaluate(ast.left, index_limit)
            rhs = self.global_comptime_evaluate(ast.right, index_limit)
            if ast.op == "+":
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(lhs.value + rhs.value)
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) + float(rhs.value))
                elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
                    return AST.StringLiteral(f"{lhs.value[1:-1]}{rhs.value[1:-1]}")
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
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) % float(rhs.value))
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
            rhs = self.global_comptime_evaluate(ast.body, index_limit)
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
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Symbol) and (sym.name == ast.name):
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            # Cyclic usage! TODO: what to raise here?
                            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                        # TODO: is extending the index limit here REALLY fine?
                        self.global_resolve_struct_definition(sym, max(index_limit, i))

                        elements_ast: List[Tuple[str, AST.Expr]] = ast.elements

                        for i, element in enumerate(elements_ast):
                            field_name, field_value_ast = element
                            for existing_field_name, existing_field_value in elements_ast[:i]:
                                if field_name == existing_field_name:
                                    raise StaticError.Redeclared(StaticError.Field(), field_name)

                            if field_name not in sym.resolved_field_types:
                                raise StaticError.Undeclared(StaticError.Field(), field_name)

                            resolved_field_value = self.global_comptime_evaluate(field_value_ast, index_limit)
                            resolved_field_value_type = self.type_of_literal(resolved_field_value)
                            if not self.global_can_cast_a_to_b(resolved_field_value_type,
                                                              sym.resolved_field_types[field_name],
                                                              index_limit):
                                raise StaticError.TypeMismatch(field_value_ast)

                        initialized_field_names = [y[0] for y in elements_ast]
                        uninitialized_fields = filter(lambda x: x[0] not in initialized_field_names, sym.resolved_field_types.items())

                        return AST.StructLiteral(ast.name, [
                            (name, self.global_comptime_evaluate(val, index_limit)) for name, val in elements_ast
                        ] + [
                            (name, self.global_make_default_value(sym.resolved_field_types[name], index_limit)) for name, typename in uninitialized_fields
                        ])
                    else:
                        raise StaticError.TypeMismatch(ast)
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
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

    def global_resolve_struct_definition(self, sym: StructSymbol, index_limit: int):
        if sym.done_resolving:
            return

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
            return

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
        sym.resolved_value = self.global_comptime_evaluate(sym.original_ast.iniExpr, index_limit)
        sym.resolved_type = self.type_of_literal(sym.resolved_value)
        if sym.original_ast.conType is not None:
            explicit_type = self.global_resolve_typename(sym.original_ast.conType, index_limit)
            if not self.global_can_cast_a_to_b(sym.resolved_type, explicit_type, index_limit):
                raise StaticError.TypeMismatch(sym.original_ast.iniExpr)
        sym.being_checked = False
        sym.done_resolving = True

    def global_resolve_typename(self, typename: AST.Type, index_limit: int):
        if isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Symbol) and (sym.name == typename.name):
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
                        return self.global_resolve_struct_definition(sym, index_limit)
                    elif isinstance(sym, InterfaceSymbol):
                        return self.global_resolve_interface_definition(sym, index_limit)
                    elif (i < index_limit) and (isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol)):
                        raise StaticError.TypeMismatch(typename)
            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
        elif isinstance(typename, AST.ArrayType):
            dimensions = [self.global_comptime_evaluate(it, index_limit) for it in typename.dimens]
            resolved_element_type = self.global_resolve_typename(typename.eleType, index_limit)
            return AST.ArrayType(dimensions, resolved_element_type)
        return typename

    def global_make_default_value(self, typename: AST.Type, index_limit: int, make_nested_list: bool = False):
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
                raise StaticError.TypeMismatch(typename)
            child_type = AST.ArrayType(typename.dimens[1:], typename.eleType) if len(typename.dimens) > 1 else typename.eleType
            vals: AST.NestedList = [self.global_make_default_value(child_type, index_limit, True) for _ in range(d.value)]
            if make_nested_list:
                return vals
            return AST.ArrayLiteral(typename.dimens, typename.eleType, vals)
        elif isinstance(typename, AST.Id):
            for i, sym in enumerate(self.global_declarations):
                if isinstance(sym, Symbol) and (sym.name == typename.name):
                    if isinstance(sym, StructSymbol):
                        if sym.being_checked:
                            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
                        return AST.StructLiteral(typename.name, [
                            (name, self.global_make_default_value(resolved_type, index_limit)) for name, resolved_type in sym.resolved_field_types.items()
                        ])
                    elif isinstance(sym, InterfaceSymbol):
                        return AST.NilLiteral()
                    elif (i < index_limit) and (isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol)):
                        raise StaticError.TypeMismatch(typename)
            raise StaticError.Undeclared(StaticError.Identifier(), typename.name)
        return AST.NilLiteral()

    def check(self):
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: List[ScopeObject]):
        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, Symbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.global_declarations.append(StructSymbol(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, Symbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.global_declarations.append(InterfaceSymbol(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, Symbol), self.global_declarations):
                    if thing.name == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Function(), thing.name)
                self.global_declarations.append(FunctionSymbol(thing.name, thing))
            elif isinstance(thing, AST.MethodDecl):
                receiver_type = thing.recType

                # Preventative check for ASTGeneration.py/AST.py flaw.
                if not isinstance(receiver_type, AST.Id):
                    raise StaticError.TypeMismatch(receiver_type)

                self.global_declarations.append(UnresolvedMethod(thing))
            elif isinstance(thing, AST.ConstDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, Symbol), self.global_declarations):
                    if thing.conName == existing_unresolved_symbol.name:
                        raise StaticError.Redeclared(StaticError.Constant(), thing.conName)
                self.global_declarations.append(ConstantSymbol(thing.conName, thing))
            elif isinstance(thing, AST.VarDecl):
                for existing_unresolved_symbol in filter(lambda x: isinstance(x, Symbol), self.global_declarations):
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
                    if isinstance(maybe_struct, Symbol) and (maybe_struct.name == sym.original_ast.recType.name):
                        if isinstance(maybe_struct, StructSymbol):
                            for existing_method in maybe_struct.original_ast.methods:
                                if existing_method.fun.name == sym.original_ast.fun.name:
                                    raise StaticError.Redeclared(StaticError.Method(), sym.original_ast.fun.name)
                            maybe_struct.original_ast.methods.append(sym.original_ast)
                            sym.struct_symbol = maybe_struct
                            struct_found = True

                            self.global_resolve_method_definition(maybe_struct, sym.original_ast, i)

                            break
                        else:
                            # TODO: Ask prof. Phung about what to raise here.
                            raise StaticError.TypeMismatch(sym.original_ast)
                if not struct_found:
                    # TODO: Seems it doesn't matter what is being raised here.
                    # https://lms.hcmut.edu.vn/mod/forum/discuss.php?d=26053
                    raise StaticError.Undeclared(StaticError.Identifier(), sym.original_ast.recType.name)
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
                self.visit(sym.original_ast, list(filter(lambda x: x != sym, my_scope)) + [sym])
            elif isinstance(sym, InterfaceSymbol):
                self.visit(sym.original_ast, list(filter(lambda x: x != sym, my_scope)) + [sym])
            # Cheap hack to filter out the prelude.
            elif isinstance(sym, FunctionSymbol) and isinstance(sym.original_ast, AST.FuncDecl):
                self.visit(sym.original_ast, list(filter(lambda x: x != sym, my_scope)) + [sym])
            elif isinstance(sym, UnresolvedMethod):
                self.visit(sym.original_ast, list(filter(lambda x: x != sym, my_scope)) + [sym])
            elif isinstance(sym, ConstantSymbol):
                self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)
            elif isinstance(sym, VariableSymbol):
                self.visit(sym.original_ast, my_scope)
                my_scope.append(sym)

        # TODO: do we return anything? Ask prof. Phung.

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        explicit_type: AST.Type | None = self.visit(ast.varType, given_scope + [IsTypenameVisit()]) if (ast.varType is not None) else None
        implicit_type: AST.Type | None = self.visit(ast.varInit, given_scope + [IsExpressionVisit()]) if (ast.varInit is not None) else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.local_can_cast_a_to_b(implicit_type, explicit_type, given_scope)):
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)

        if (explicit_type is None) and isinstance(implicit_type, NilType):
            # TODO: Ask prof. Phung what to raise here.
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes here either; that's done by the outer layer.
        explicit_type: AST.Type | None = self.visit(ast.conType, given_scope + [IsTypenameVisit()]) if (ast.conType is not None) else None
        implicit_type: AST.Type | None = self.visit(ast.iniExpr, given_scope + [IsComptimeExpressionVisit(), IsExpressionVisit()]) if (ast.iniExpr is not None) else None

        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.local_can_cast_a_to_b(implicit_type, explicit_type, given_scope)):
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)

        if (explicit_type is None) and isinstance(implicit_type, NilType):
            # TODO: Ask prof. Phung what to raise here.
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitFuncDecl(self, ast: AST.FuncDecl, given_scope: List[ScopeObject]):
        # This might be the ugliest part of the entire file to be quite honest.
        if len(given_scope) < 1:
            # !!??!!!??
            raise StaticError.TypeMismatch(ast)

        self_sym = given_scope[-1]
        # Sanity checks.
        if not isinstance(self_sym, FunctionSymbol):
            raise StaticError.TypeMismatch(ast)
        if self_sym.name != ast.name:
            raise StaticError.TypeMismatch(ast)
        my_scope = given_scope.copy()

        # Parameters cannot repeat names within themselves, but they can shadow global variables, structs, interfaces
        # and functions.
        for i, param in enumerate(ast.params):
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), my_scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            my_scope.append(FunctionParameterSymbol(param.parName, param, self_sym.resolved_types.parameter_types[i]))

        current_function_scope_object = CurrentFunction(self_sym.resolved_types)
        self.visit(ast.body, my_scope + [current_function_scope_object])

    def visitMethodDecl(self, ast: AST.MethodDecl, given_scope: List[ScopeObject]):
        # This might be the 2nd ugliest part of the entire file to be quite honest.
        if len(given_scope) < 1:
            # !!??!!!??
            raise StaticError.TypeMismatch(ast)

        self_sym = given_scope[-1]
        # Sanity checks.
        if not isinstance(self_sym, UnresolvedMethod):
            raise StaticError.TypeMismatch(ast)
        if self_sym.original_ast != ast:
            raise StaticError.TypeMismatch(ast)

        # I guess treating the receiver as a parameter symbol is fine for now. It shouldn't interfere with the stuff
        # below which is almost straight-copied from visitFuncDecl.
        my_scope = given_scope + [FunctionParameterSymbol(ast.receiver, AST.Id(ast.receiver), ast.recType)]

        resolved_types = self_sym.struct_symbol.resolved_method_types[ast.fun.name]

        # Parameters cannot repeat names within themselves, but they can shadow global variables, structs, interfaces
        # and functions.
        for i, param in enumerate(ast.fun.params):
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), my_scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            my_scope.append(FunctionParameterSymbol(param.parName, param, resolved_types.parameter_types[i]))

        current_function_scope_object = CurrentFunction(resolved_types)
        self.visit(ast.fun.body, my_scope + [current_function_scope_object])

    def visitPrototype(self, ast, param):
        # TODO: complete this.
        return None

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
        return AST.ArrayType([self.local_comptime_evaluate(it, given_scope) for it in ast.dimens], ast.eleType)

    def visitStructType(self, ast: AST.StructType, given_scope: List[ScopeObject]):
        # This is ugly.
        if len(given_scope) < 1:
            # !!??!!!??
            raise StaticError.TypeMismatch(ast)

        self_sym = given_scope[-1]
        # Sanity checks.
        if not isinstance(self_sym, StructSymbol):
            raise StaticError.TypeMismatch(ast)
        if self_sym.name != ast.name:
            raise StaticError.TypeMismatch(ast)

        for i, element in enumerate(ast.elements):
            field_name, field_type = element
            for existing_field_name, existing_field_type in ast.elements[:i]:
                if field_name == existing_field_name:
                    raise StaticError.Redeclared(StaticError.Field(), element[0])
            resolved_field_type = self.visit(field_type, given_scope + [IsTypenameVisit()])
            self_sym.resolved_field_types[field_name] = resolved_field_type

    def visitInterfaceType(self, ast: AST.InterfaceType, given_scope: List[ScopeObject]):
        pass # See recursively_resolve_interface_definition.

    def visitBlock(self, ast: AST.Block, given_scope: List[ScopeObject]):
        my_scope = given_scope.copy()

        # Vars and consts within the same block cannot collide names. Inner blocks can shadow.
        this_block_names = []
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
                sym.resolved_value = self.local_comptime_evaluate(statement.iniExpr, my_scope) if (statement.iniExpr is not None) else None
                my_scope.append(sym)
            elif isinstance(statement, AST.Expr):
                expr_type = self.visit(statement, my_scope + [IsExpressionVisit()])
                # I guess prof. Phung doesn't want any code to discard any values.
                if not isinstance(expr_type, AST.VoidType):
                    raise StaticError.TypeMismatch(ast)
            elif isinstance(statement, AST.Assign) and isinstance(statement.lhs, AST.Id):
                lhs: AST.Id = statement.lhs
                # Is the name not declared? If so, turn it into a variable declaration.
                existing_maybe_variable = next(filter(lambda x: isinstance(x, Symbol) and (x.name == lhs.name), reversed(my_scope)), None)
                if existing_maybe_variable is None:
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
                        raise StaticError.TypeMismatch(ast)

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
        if not self.local_can_cast_a_to_b(rhs_type, lhs_type, given_scope):
            raise StaticError.TypeMismatch(ast)
        # Return nothing, I guess.

    def visitIf(self, ast: AST.If, given_scope: List[ScopeObject]):
        condition_type = self.visit(ast.expr, given_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            # TODO: Ask prof. Phung whether to pass ast or ast.expr.
            raise StaticError.TypeMismatch(ast.expr)
        self.visit(ast.thenStmt, given_scope)
        if ast.elseStmt is not None:
            self.visit(ast.elseStmt, given_scope)

    def visitForBasic(self, ast: AST.ForBasic, given_scope: List[ScopeObject]):
        condition_type = self.visit(ast.cond, given_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            # TODO: Ask prof. Phung whether to pass ast or ast.expr.
            raise StaticError.TypeMismatch(ast.cond)
        self.visit(ast.loop, given_scope + [IsLoopVisit()])

    def visitForStep(self, ast: AST.ForStep, given_scope: List[ScopeObject]):
        my_scope = given_scope.copy()

        if isinstance(ast.init, AST.VarDecl):
            sym = VariableSymbol(ast.init.varName, ast.init)
            sym.resolved_type = self.visit(ast.init, my_scope)
            my_scope.append(sym)
        elif isinstance(ast.init, AST.Assign) and isinstance(ast.init.lhs, AST.Id):
            lhs: AST.Id = ast.init.lhs
            # Is the name not declared? If so, turn it into a variable declaration.
            existing_maybe_variable = next(filter(lambda x: isinstance(x, Symbol) and (x.name == lhs.name), reversed(my_scope)), None)
            if existing_maybe_variable is None:
                # TODO: should VariableSymbol's 2nd argument type accept assignment statement ASTs too?
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
            else:
                self.visit(ast.init, my_scope)
        else:
            # This is probably a statement.
            self.visit(ast.init, my_scope)

        condition_type = self.visit(ast.cond, my_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            # TODO: Ask prof. Phung whether to pass ast or ast.expr.
            raise StaticError.TypeMismatch(ast.cond)

        self.visit(ast.upda, my_scope)

        my_scope += [IsLoopVisit()]
        self.visit(ast.loop, my_scope)

    def visitForEach(self, ast: AST.ForEach, given_scope: List[ScopeObject]):
        my_scope = given_scope.copy()

        iteration_target_type = self.visit(ast.arr, my_scope + [IsExpressionVisit()])
        if not isinstance(iteration_target_type, AST.ArrayType):
            raise StaticError.TypeMismatch(ast.arr)

        idx_sym = VariableSymbol(ast.idx.name, ast.idx)
        idx_sym.resolved_type = AST.IntType()

        value_sym = VariableSymbol(ast.value.name, ast.value)
        if len(iteration_target_type.dimens) == 1:
            value_sym.resolved_type = iteration_target_type.eleType
        else:
            value_sym.resolved_type = AST.ArrayType(iteration_target_type.dimens[1:], iteration_target_type.eleType)

        my_scope += [idx_sym, value_sym, IsLoopVisit()]
        self.visit(ast.loop, my_scope)

    def visitContinue(self, ast: AST.Continue, given_scope: List[ScopeObject]):
        loop_visit = next(filter(lambda x: isinstance(x, IsLoopVisit), reversed(given_scope)), None)
        if loop_visit is None:
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)

    def visitBreak(self, ast: AST.Break, given_scope: List[ScopeObject]):
        loop_visit = next(filter(lambda x: isinstance(x, IsLoopVisit), reversed(given_scope)), None)
        if loop_visit is None:
            # TODO: Ask prof. Phung about what to raise here.
            raise StaticError.TypeMismatch(ast)

    def visitReturn(self, ast: AST.Return, given_scope: List[ScopeObject]):
        # Are we in a return?
        current_function: CurrentFunction | None = next(filter(lambda x: isinstance(x, CurrentFunction), reversed(given_scope)), None)
        if current_function is None:
            # TODO: what to raise here?
            raise StaticError.Undeclared(StaticError.Function(), "(no function)")

        if isinstance(current_function.resolved_types.return_type, AST.VoidType):
            if ast.expr is not None:
                raise StaticError.TypeMismatch(ast)
        else:
            if ast.expr is None:
                raise StaticError.TypeMismatch(ast)
            expr_type = self.visit(ast.expr, given_scope + [IsExpressionVisit()])
            if not self.local_can_cast_a_to_b(expr_type, current_function.resolved_types.return_type, given_scope):
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
        elif ast.op in ["-", "*", "/", "%"]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.IntType()
            elif (isinstance(lhs, AST.FloatType) or isinstance(lhs, AST.IntType)) and (
                    isinstance(rhs, AST.FloatType) or isinstance(rhs, AST.IntType)):
                return AST.FloatType()
            else:
                raise StaticError.TypeMismatch(ast)
        elif ast.op in [">", "<", ">=", "<=", "==", "!="]:
            if isinstance(lhs, AST.IntType) and isinstance(rhs, AST.IntType):
                return AST.BoolType()
            elif isinstance(lhs, AST.FloatType) and isinstance(rhs, AST.FloatType):
                return AST.BoolType()
            elif isinstance(lhs, AST.StringLiteral) and isinstance(rhs, AST.StringLiteral):
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
            elif isinstance(rhs, AST.FloatLiteral):
                return AST.FloatType()
            else:
                raise StaticError.TypeMismatch(ast)
        else:
            raise StaticError.TypeMismatch(ast)

    def visitFuncCall(self, ast: AST.FuncCall, given_scope: List[ScopeObject]):
        for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
            if sym.name == ast.funName:
                if isinstance(sym, FunctionSymbol):
                    # Referencing other variables isn't allowed in constants.
                    if next(filter(lambda x: isinstance(x, IsComptimeExpressionVisit), reversed(given_scope)), None) is not None:
                        # TODO: Ask prof. Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)

                    # Check arguments.
                    if isinstance(sym.original_ast, AST.FuncDecl) and (len(ast.args) != len(sym.original_ast.params)):
                        raise StaticError.TypeMismatch(ast)
                    # Sanity check
                    if isinstance(sym.original_ast, AST.FuncDecl) and (len(sym.original_ast.params) != len(sym.resolved_types.parameter_types)):
                        # Sanity check failed !!??!!!??
                        raise StaticError.TypeMismatch(ast)

                    for i, arg in enumerate(ast.args):
                        # No need to append IsExpressionVisit (we're already in one.)
                        # TODO: add a sanity check for that.
                        arg_type = self.visit(arg, given_scope)
                        if not self.local_can_cast_a_to_b(arg_type, sym.resolved_types.parameter_types[i], given_scope):
                            raise StaticError.TypeMismatch(ast)

                    return sym.resolved_types.return_type
                else:
                    raise StaticError.TypeMismatch(ast)
        raise StaticError.Undeclared(StaticError.Function(), ast.funName)

    def visitMethCall(self, ast: AST.MethCall, given_scope: List[ScopeObject]):
        # TODO: is adding an IsExpressionVisit instance here even necessary?
        receiver_type = self.visit(ast.receiver, given_scope + [IsExpressionVisit()])
        if isinstance(receiver_type, AST.Id):
            # Resolve the type (again)
            for sym in filter(lambda x: isinstance(x, StructSymbol) or isinstance(x, InterfaceSymbol), reversed(given_scope)):
                if sym.name == receiver_type.name:
                    if isinstance(sym, StructSymbol):
                        for method in sym.original_ast.methods:
                            if method.fun.name == ast.metName:
                                resolved_method_types = sym.resolved_method_types[ast.metName]

                                # Check arguments.
                                if len(ast.args) != len(method.fun.params):
                                    raise StaticError.TypeMismatch(ast)
                                # Sanity check
                                if len(method.fun.params) != len(resolved_method_types.parameter_types):
                                    # Sanity check failed !!??!!!??
                                    raise StaticError.TypeMismatch(ast)

                                for i, arg in enumerate(ast.args):
                                    # No need to append IsExpressionVisit (we're already in one.)
                                    # TODO: add a sanity check for that.
                                    arg_type = self.visit(arg, given_scope)
                                    if not self.local_can_cast_a_to_b(arg_type, resolved_method_types.parameter_types[i], given_scope):
                                        raise StaticError.TypeMismatch(ast)

                                return resolved_method_types.return_type
                        raise StaticError.Undeclared(StaticError.Method(), ast.metName)
                    elif isinstance(sym, InterfaceSymbol):
                        for prototype in sym.original_ast.methods:
                            if prototype.name == ast.metName:
                                resolved_method_types = sym.resolved_method_types[ast.metName]

                                # Check arguments.
                                if len(ast.args) != len(prototype.params):
                                    raise StaticError.TypeMismatch(ast)
                                # Sanity check
                                if len(prototype.params) != len(resolved_method_types.parameter_types):
                                    # Sanity check failed !!??!!!??
                                    raise StaticError.TypeMismatch(ast)

                                for i, arg in enumerate(ast.args):
                                    # No need to append IsExpressionVisit (we're already in one.)
                                    # TODO: add a sanity check for that
                                    arg_type = self.visit(arg, given_scope)
                                    if not self.local_can_cast_a_to_b(arg_type, resolved_method_types.parameter_types[i], given_scope):
                                        raise StaticError.TypeMismatch(ast)

                                return resolved_method_types.return_type
                        raise StaticError.Undeclared(StaticError.Method(), ast.metName)
                    else:
                        # TODO: ???!!!
                        raise StaticError.TypeMismatch(ast)
        else:
            raise StaticError.Undeclared(StaticError.Method(), ast.metName)

    def visitId(self, ast: AST.Id, given_scope: List[ScopeObject]):
        for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol):
                    id_mode: IsTypenameVisit | IsExpressionVisit | None = next(filter(lambda x: isinstance(x, IsTypenameVisit) or isinstance(x, IsExpressionVisit), reversed(given_scope)), None)
                    if isinstance(id_mode, IsTypenameVisit):
                        return ast
                    elif isinstance(id_mode, IsExpressionVisit):
                        # I guess we don't allow bare-referring to structs and interfaces?
                        # TODO: Ask prof. Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    else:
                        # TODO: ???!!!
                        raise StaticError.TypeMismatch(ast)
                elif isinstance(sym, FunctionSymbol):
                    # I guess we don't allow bare-referring to functions?
                    # TODO: Ask prof. Phung about this.
                    raise StaticError.TypeMismatch(ast)
                elif isinstance(sym, ConstantSymbol):
                    maybe_lhs: IsLeftHandSideVisit | None = next(filter(lambda x: isinstance(x, IsLeftHandSideVisit), reversed(given_scope)), None)
                    if isinstance(maybe_lhs, IsLeftHandSideVisit):
                        # TODO: Ask prof. Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    return sym.resolved_type
                elif isinstance(sym, VariableSymbol):
                    # Referencing other variables isn't allowed in constants.
                    if next(filter(lambda x: isinstance(x, IsComptimeExpressionVisit), reversed(given_scope)), None) is not None:
                        # TODO: Ask prof. Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    return sym.resolved_type
                elif isinstance(sym, FunctionParameterSymbol):
                    # Referencing function parameters isn't allowed in constants.
                    if next(filter(lambda x: isinstance(x, IsComptimeExpressionVisit), reversed(given_scope)), None) is not None:
                        # TODO: Ask prof. Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    return sym.resolved_type
                else:
                    return None
        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)

    def visitArrayCell(self, ast, param):
        return None

    def visitFieldAccess(self, ast: AST.FieldAccess, given_scope: List[ScopeObject]):
        # No need to append IsExpressionVisit (we're already in one.)
        # TODO: add a sanity check for that
        receiver_type = self.visit(ast.receiver, given_scope)
        if isinstance(receiver_type, AST.Id):
            # Resolve the type (again)
            for sym in filter(lambda x: isinstance(x, StructSymbol) or isinstance(x, InterfaceSymbol), reversed(given_scope)):
                if sym.name == receiver_type.name:
                    if isinstance(sym, StructSymbol):
                        if ast.field not in sym.resolved_field_types:
                            raise StaticError.Undeclared(StaticError.Field(), ast.field)
                        return sym.resolved_field_types[ast.field]
                    else:
                        raise StaticError.TypeMismatch(ast)
        else:
            raise StaticError.Undeclared(StaticError.Field(), ast.field)

    def visitIntLiteral(self, ast, param):
        return AST.IntType()

    def visitFloatLiteral(self, ast, param):
        return AST.FloatType()

    def visitBooleanLiteral(self, ast, param):
        return AST.BoolType()

    def visitStringLiteral(self, ast, param):
        return AST.StringType()

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, given_scope: List[ScopeObject]):
        dimens = [self.local_comptime_evaluate(it, given_scope) for it in ast.dimens]
        # TODO: is the IsTypenameVisit() instance useless here?
        ele_type = self.visit(ast.eleType, given_scope + [IsTypenameVisit()])
        self.check_nested_list(ast, ast.value, ele_type, dimens, given_scope)
        # TODO: maybe assert ele_type and ast.eleType are the exact same
        return AST.ArrayType(dimens, ele_type)

    def visitStructLiteral(self, ast: AST.StructLiteral, given_scope: List[ScopeObject]):
        # Find the struct name.
        struct_sym: StructSymbol | None = None
        for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol):
                    struct_sym = sym
                else:
                    raise StaticError.TypeMismatch(ast)
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
            if not self.local_can_cast_a_to_b(field_initializer_type, struct_sym.resolved_field_types[field_name], given_scope):
                raise StaticError.TypeMismatch(field_value)

        return AST.Id(ast.name)

    def visitNilLiteral(self, ast, param):
        # TODO: check if this is really fine.
        return NilType()

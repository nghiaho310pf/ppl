"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=6hUH7RxU2yQ
"""

import AST
from Visitor import *
from typing import List
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

    def set_return_type(self, new_type: AST.Type):
        self.return_type = new_type

    def set_parameter_types(self, param_types: List[AST.Type]):
        self.parameter_types = param_types

# For name resolution.

class Symbol(ScopeObject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

class StructSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.StructType):
        super().__init__(name)
        self.original_ast = original_ast
        self.method_resolved_types = dict[str, ResolvedFunctionTypes]()

class InterfaceSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.InterfaceType):
        super().__init__(name)
        self.original_ast = original_ast

class FunctionSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.FuncDecl):
        super().__init__(name)
        self.original_ast = original_ast
        self.resolved_types = ResolvedFunctionTypes()

class VariableSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.VarDecl):
        super().__init__(name)
        self.original_ast = original_ast
        self.resolved_type = None

    def set_type(self, new_type: AST.Type):
        self.resolved_type = new_type

class ConstantSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ConstDecl):
        super().__init__(name)
        self.original_ast = original_ast
        self.resolved_type = None
        self.resolved_value = None

    def set_type(self, new_type: AST.Type):
        self.resolved_type = new_type

    def set_value(self, new_value: AST.Literal):
        self.resolved_value = new_value

class FunctionParameterSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ParamDecl | AST.Id, resolved_type: AST.Type):
        super().__init__(name)
        # original_ast can be an AST.Id because it could be a receiver of a method.
        self.original_ast = original_ast
        self.resolved_type = resolved_type

# For banning illegal returns.

class CurrentFunction(ScopeObject):
    def __init__(self, resolved_types: ResolvedFunctionTypes):
        super().__init__()
        self.resolved_types = resolved_types

# Cheap hack for resolving types for methods.

class CurrentMethod(ScopeObject):
    def __init__(self, name: str):
        super().__init__()
        self.resolved_types = ResolvedFunctionTypes()
        # Only used for a sanity check.
        self.name = name

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

# For banning function/method calls and references to non-consts.

class IsComptimeExpressionVisit(ScopeObject):
    def __init__(self):
        super().__init__()

# For banning breaks and continues outside of loops.

class IsForLoopVisit(ScopeObject):
    def __init__(self):
        super().__init__()

class StaticChecker(BaseVisitor):
    def __init__(self, root_ast):
        self.root_ast = root_ast

    # TODO: Ask Phung about casting from struct vals to opaque interface vals.
    @staticmethod
    def compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        if isinstance(a, AST.ArrayType) and isinstance(b, AST.ArrayType):
            if (not StaticChecker.compare_types(a.eleType, b.eleType)) or (len(a.dimens) != len(b.dimens)):
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

    # Just roll our own recursion here instead of using StaticChecker's cancerous visitor mechanism.
    @staticmethod
    def comptime_evaluate(ast: AST.Expr, given_scope: List[ScopeObject]):
        if isinstance(ast, AST.Id):
            for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
                if sym.name == ast.name:
                    if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol):
                        # I guess we don't allow bare-referring to structs and interfaces?
                        # TODO: ask Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    elif isinstance(sym, FunctionSymbol):
                        # I guess we don't allow bare-referring to functions?
                        # TODO: ask Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    elif isinstance(sym, ConstantSymbol):
                        return sym.resolved_value
                    elif isinstance(sym, VariableSymbol) or isinstance(sym, FunctionParameterSymbol):
                        # Referencing other variables/parameters isn't allowed in constants.
                        # TODO: ask Phung about what error to raise here.
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
            receiver = StaticChecker.comptime_evaluate(ast.arr, given_scope)
            if not isinstance(receiver, AST.ArrayLiteral):
                raise StaticError.TypeMismatch(ast)

            inner: AST.NestedList = receiver.value
            resulting_dimens = receiver.dimens

            for it in ast.idx:
                if not isinstance(inner, list):
                    raise StaticError.TypeMismatch(ast)
                e = StaticChecker.comptime_evaluate(it, given_scope)
                if not isinstance(e, AST.IntLiteral):
                    raise StaticError.TypeMismatch(ast)
                if e.value < 0 or e.value >= len(inner):
                    # TODO: ???!!! Should already be caught by static checking?
                    raise StaticError.TypeMismatch(ast)
                inner = inner[e.value]
                resulting_dimens = resulting_dimens[:-1]

            if isinstance(inner, list):
                return AST.ArrayLiteral(resulting_dimens, receiver.eleType, inner)
        elif isinstance(ast, AST.FieldAccess):
            # I guess we need to evaluate the entire thing.
            receiver = StaticChecker.comptime_evaluate(ast.receiver, given_scope)
            field = ast.field
            if not isinstance(receiver, AST.StructLiteral):
                raise StaticError.TypeMismatch(ast)

            # Resolve the type.
            for maybe_struct in filter(lambda s: isinstance(s, Symbol), given_scope):
                if isinstance(maybe_struct, StructSymbol):
                    struct_found = False
                    if maybe_struct.name == receiver.name:
                        q: AST.Expr | None = next(filter(lambda t: t[0] == field, receiver.elements), None)
                        if q is None:
                            raise StaticError.Undeclared(StaticError.Field(), field)
                        return StaticChecker.comptime_evaluate(q, given_scope)
                    if not struct_found:
                        # This should never happen since we do static checking by visitor pattern first before
                        # actually evaluating the thing.
                        # Original comment: "TODO: this is probably correct but I should ask Phung just to be sure."
                        raise StaticError.Undeclared(StaticError.Type(), receiver.name)
                else:
                    raise StaticError.TypeMismatch(ast)
        elif isinstance(ast, AST.BinaryOp):
            lhs = StaticChecker.comptime_evaluate(ast.left, given_scope)
            rhs = StaticChecker.comptime_evaluate(ast.right, given_scope)
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
                # TODO: what if RHS is zero? Ask Phung.
                if isinstance(lhs, AST.IntLiteral) and isinstance(rhs, AST.IntLiteral):
                    return AST.IntLiteral(int(lhs.value / rhs.value))
                elif (isinstance(lhs, AST.FloatLiteral) or isinstance(lhs, AST.IntLiteral)) and (
                        isinstance(rhs, AST.FloatLiteral) or isinstance(rhs, AST.IntLiteral)):
                    return AST.FloatLiteral(float(lhs.value) / float(rhs.value))
                else:
                    raise StaticError.TypeMismatch(ast)
            elif ast.op == "%":
                # TODO: what if RHS is zero? Ask Phung.
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
            rhs = StaticChecker.comptime_evaluate(ast.body, given_scope)
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
        else:
            return ast

    def check_nested_list(self, original_ast: AST.ArrayLiteral, ast: AST.NestedList, ele_type: AST.Type, dimens: list[AST.IntLiteral], given_scope: list[ScopeObject]):
        if not isinstance(ast, list):
            raise StaticError.TypeMismatch(ast)
        if len(ast) != dimens[0].value:
            # TODO: what to raise here? Ask Phung.
            raise StaticError.TypeMismatch(original_ast)
        if len(dimens) > 1:
            for sublist in ast:
                self.check_nested_list(original_ast, sublist, ele_type, dimens[1:], given_scope)
        else:
            for ele in ast:
                this_ele_type = self.visit(ele, given_scope)
                if not self.compare_types(this_ele_type, ele_type):
                    raise StaticError.TypeMismatch(ele)

    def check(self):
        # TODO: there are pre-defined global methods; add them here.
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: List[ScopeObject]):
        my_scope: List[ScopeObject] = given_scope.copy()

        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), my_scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.visit(thing, my_scope)
                my_scope.append(StructSymbol(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), my_scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.visit(thing, my_scope)
                my_scope.append(InterfaceSymbol(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), my_scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Function(), thing.name)
                # Recursion may be used so we'll append it to scope first before visiting.
                my_scope.append(FunctionSymbol(thing.name, thing))
                self.visit(thing, my_scope)
            elif isinstance(thing, AST.MethodDecl):
                receiver_type = thing.recType

                # Preventative hack-fix for ASTGeneration.py/AST.py flaw.
                if not isinstance(receiver_type, AST.Id):
                    # TODO: do something about this?
                    raise StaticError.TypeMismatch(thing)

                struct_found = False
                for maybe_struct in filter(lambda s: isinstance(s, Symbol), my_scope):
                    if maybe_struct.name == receiver_type.name:
                        if isinstance(maybe_struct, StructSymbol):
                            for existing_method in maybe_struct.original_ast.methods:
                                if existing_method.fun.name == thing.fun.name:
                                    raise StaticError.Redeclared(StaticError.Method(), thing.fun.name)
                            maybe_struct.original_ast.methods.append(thing)
                            struct_found = True

                            # Parameter type and return type resolution is done in visitFuncDecl.
                            # It's dirty but it works.

                            break
                        else:
                            raise StaticError.TypeMismatch(thing)
                if not struct_found:
                    # TODO: this is probably correct but I should ask Phung just to be sure.
                    raise StaticError.Undeclared(StaticError.Type(), receiver_type.name)
                # Recursion may be used so it's added to the struct first above.
                meth_obj = CurrentMethod(thing.fun.name)
                self.visit(thing, my_scope + [meth_obj])
            elif isinstance(thing, AST.VarDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), my_scope):
                    if thing.varName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.varName)
                resolved_type = self.visit(thing, my_scope)
                sym = VariableSymbol(thing.varName, thing)
                sym.set_type(resolved_type)
                my_scope.append(sym)
            elif isinstance(thing, AST.ConstDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), my_scope):
                    if thing.conName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.conName)
                resolved_type = self.visit(thing, my_scope)
                resolved_value = self.comptime_evaluate(thing.iniExpr, my_scope) if (thing.iniExpr is not None) else None
                sym = ConstantSymbol(thing.conName, thing)
                sym.set_type(resolved_type)
                sym.set_value(resolved_value)
                my_scope.append(sym)

        # TODO: do we return anything? Ask Phung.

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        explicit_type: AST.Type | None = self.visit(ast.varType, given_scope + [IsTypenameVisit()]) if (ast.varType is not None) else None
        implicit_type: AST.Type | None = self.visit(ast.varInit, given_scope + [IsExpressionVisit()]) if (ast.varInit is not None) else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: List[ScopeObject]):
        # We don't check name dupes here either; that's done by the outer layer.
        explicit_type: AST.Type | None = self.visit(ast.conType, given_scope + [IsTypenameVisit()]) if (ast.conType is not None) else None
        implicit_type: AST.Type | None = self.visit(ast.iniExpr, given_scope + [IsComptimeExpressionVisit(), IsExpressionVisit()]) if (ast.iniExpr is not None) else None

        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
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
        param_types = []
        for param in ast.params:
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), my_scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            resolved_param_type = self.visit(param.parType, my_scope + [IsTypenameVisit()])
            param_types.append(resolved_param_type)
            my_scope.append(FunctionParameterSymbol(param.parName, param, resolved_param_type))
        self_sym.resolved_types.set_parameter_types(param_types)
        self_sym.resolved_types.set_return_type(self.visit(ast.retType, my_scope + [IsTypenameVisit()]))

        current_function_scope_object = CurrentFunction(self_sym.resolved_types)
        self.visit(ast.body, my_scope + [current_function_scope_object])

    def visitMethodDecl(self, ast: AST.MethodDecl, given_scope: List[ScopeObject]):
        # This might be the 2nd ugliest part of the entire file to be quite honest.
        if len(given_scope) < 1:
            # !!??!!!??
            raise StaticError.TypeMismatch(ast)

        self_sym = given_scope[-1]
        # Sanity checks.
        if not isinstance(self_sym, CurrentMethod):
            raise StaticError.TypeMismatch(ast)
        if self_sym.name != ast.fun.name:
            raise StaticError.TypeMismatch(ast)

        # I guess treating the receiver as a parameter symbol is fine for now. It shouldn't interfere with the stuff
        # below which is almost straight-copied from visitFuncDecl.
        my_scope = given_scope + [FunctionParameterSymbol(ast.receiver, AST.Id(ast), ast.recType)]

        # Parameters cannot repeat names within themselves, but they can shadow global variables, structs, interfaces
        # and functions.
        param_types = []
        for param in ast.fun.params:
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), my_scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            resolved_param_type = self.visit(param.parType, my_scope + [IsTypenameVisit()])
            param_types.append(resolved_param_type)
            my_scope.append(FunctionParameterSymbol(param.parName, param, resolved_param_type))
        self_sym.resolved_types.set_parameter_types(param_types)
        self_sym.resolved_types.set_return_type(ast.fun.retType)

        current_function_scope_object = CurrentFunction(self_sym.resolved_types)
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
        return AST.ArrayType([self.comptime_evaluate(it, given_scope) for it in ast.dimens], ast.eleType)

    def visitStructType(self, ast, param):
        # TODO: complete this.
        return None

    def visitInterfaceType(self, ast, param):
        # TODO: complete this.
        return None

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
                resolved_type = self.visit(statement, my_scope)
                sym.set_type(resolved_type)
                my_scope.append(sym)
            elif isinstance(statement, AST.ConstDecl):
                if statement.conName in this_block_names:
                    raise StaticError.Redeclared(StaticError.Constant(), statement.conName)
                this_block_names.append(statement.conName)

                sym = ConstantSymbol(statement.conName, statement)
                resolved_type = self.visit(statement, my_scope)
                resolved_value = self.comptime_evaluate(statement.iniExpr, my_scope) if (statement.iniExpr is not None) else None
                sym.set_type(resolved_type)
                sym.set_value(resolved_value)
                my_scope.append(sym)
            elif isinstance(statement, AST.Expr):
                expr_type = self.visit(statement, my_scope + [IsExpressionVisit()])
                # I guess Phung doesn't want any code to discard any values.
                if not isinstance(expr_type, AST.VoidType):
                    raise StaticError.TypeMismatch(ast)
            elif isinstance(statement, AST.Assign) and isinstance(statement.lhs, AST.Id):
                lhs: AST.Id = statement.lhs
                # Is the name not declared? If so, turn it into a variable declaration.
                existing_maybe_variable = next(filter(lambda x: isinstance(x, Symbol) and (x.name == lhs.name), reversed(my_scope)), None)
                if existing_maybe_variable is None:
                    this_block_names.append(lhs.name)

                    # TODO: should VariableSymbol's 2nd argument type accept assignment statement ASTs too?
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

                    sym.set_type(implicit_type)
                    my_scope.append(sym)
                else:
                    self.visit(statement, my_scope)
            else:
                # This is probably a statement.
                self.visit(statement, my_scope)

    def visitAssign(self, ast: AST.Assign, given_scope: List[ScopeObject]):
        lhs_type = self.visit(ast.lhs, given_scope + [IsExpressionVisit()])
        rhs_type = self.visit(ast.rhs, given_scope + [IsExpressionVisit()])
        if not self.compare_types(lhs_type, rhs_type):
            raise StaticError.TypeMismatch(ast)
        # Return nothing, I guess.

    def visitIf(self, ast: AST.If, given_scope: List[ScopeObject]):
        condition_type = self.visit(ast.expr, given_scope + [IsExpressionVisit()])
        if not isinstance(condition_type, AST.BoolType):
            # TODO: Ask Phung whether to pass ast or ast.expr.
            raise StaticError.TypeMismatch(ast.expr)
        self.visit(ast.thenStmt, given_scope)
        if ast.elseStmt is not None:
            self.visit(ast.elseStmt, given_scope)

    def visitForBasic(self, ast: AST.ForBasic, given_scope: List[ScopeObject]):
        # TODO: complete this. Use IsForLoopVisit.
        return None

    def visitForStep(self, ast, given_scope: List[ScopeObject]):
        # TODO: complete this. Use IsForLoopVisit.
        return None

    def visitForEach(self, ast, given_scope: List[ScopeObject]):
        # TODO: complete this. Use IsForLoopVisit.
        return None

    def visitContinue(self, ast, given_scope: List[ScopeObject]):
        # TODO: complete this. Use IsForLoopVisit.
        return None

    def visitBreak(self, ast, given_scope: List[ScopeObject]):
        # TODO: complete this. Use IsForLoopVisit.
        return None

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
            if not self.compare_types(expr_type, current_function.resolved_types.return_type):
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
                        # TODO: ask Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)

                    # Check arguments.
                    # TODO: allow implicit casting here.
                    if len(ast.args) != len(sym.original_ast.params):
                        raise StaticError.TypeMismatch(ast)
                    # Sanity check
                    if len(sym.original_ast.params) != len(sym.resolved_types.parameter_types):
                        # Sanity check failed !!??!!!??
                        raise StaticError.TypeMismatch(ast)

                    for i, arg in enumerate(ast.args):
                        # No need to append IsExpressionVisit (we're already in one.) TODO: add a sanity check for that
                        arg_type = self.visit(arg, given_scope)
                        if not self.compare_types(arg_type, sym.resolved_types.parameter_types[i]):
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
            for sym in filter(lambda x: isinstance(x, StructSymbol) or isinstance(x, InterfaceSymbol),
                              reversed(given_scope)):
                if sym.name == receiver_type.name:
                    if isinstance(sym, StructSymbol):
                        for method in sym.original_ast.methods:
                            if method.fun.name == ast.metName:
                                # TODO: count arguments and check their receivers.
                                return method.fun.retType
                        raise StaticError.Undeclared(StaticError.Method(), ast.metName)
                    elif isinstance(sym, InterfaceSymbol):
                        for prototype in sym.original_ast.methods:
                            if prototype.name == ast.metName:
                                # TODO: count arguments and check their receivers.
                                return prototype.retType
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
                        # TODO: ask Phung about this.
                        raise StaticError.TypeMismatch(ast)
                    else:
                        # TODO: ???!!!
                        raise StaticError.TypeMismatch(ast)
                elif isinstance(sym, FunctionSymbol):
                    # I guess we don't allow bare-referring to functions?
                    # TODO: ask Phung about this.
                    raise StaticError.TypeMismatch(ast)
                elif isinstance(sym, ConstantSymbol):
                    return sym.resolved_type
                elif isinstance(sym, VariableSymbol):
                    # Referencing other variables isn't allowed in constants.
                    if next(filter(lambda x: isinstance(x, IsComptimeExpressionVisit), reversed(given_scope)), None) is not None:
                        # TODO: ask Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    return sym.resolved_type
                elif isinstance(sym, FunctionParameterSymbol):
                    # Referencing function parameters isn't allowed in constants.
                    if next(filter(lambda x: isinstance(x, IsComptimeExpressionVisit), reversed(given_scope)), None) is not None:
                        # TODO: ask Phung about what error to raise here.
                        raise StaticError.TypeMismatch(ast)
                    return sym.resolved_type
                else:
                    return None
        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)

    def visitArrayCell(self, ast, param):
        return None

    def visitFieldAccess(self, ast: AST.FieldAccess, given_scope: List[ScopeObject]):
        receiver_type = self.visit(ast.receiver, given_scope + [IsExpressionVisit()])
        if isinstance(receiver_type, AST.Id):
            # Resolve the type (again)
            for sym in filter(lambda x: isinstance(x, StructSymbol) or isinstance(x, InterfaceSymbol), reversed(given_scope)):
                if sym.name == receiver_type.name:
                    if isinstance(sym, StructSymbol):
                        for field_name, field_type in sym.original_ast.elements:
                            if field_name == ast.field:
                                return field_type
                        raise StaticError.Undeclared(StaticError.Field(), ast.field)
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
        dimens = [self.comptime_evaluate(it, given_scope) for it in ast.dimens]
        ele_type = self.visit(ast.eleType, given_scope)
        self.check_nested_list(ast, ast.value, ele_type, dimens, given_scope)
        # TODO: maybe assert ele_type and ast.eleType are the exact same
        return AST.ArrayType(dimens, ele_type)

    def visitStructLiteral(self, ast: AST.StructLiteral, given_scope: List[ScopeObject]):
        # Find the struct name.
        struct_ast: AST.StructType | None = None
        for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol) or isinstance(sym, StructSymbol):
                    struct_ast = sym.original_ast
                elif isinstance(sym, FunctionSymbol) or isinstance(sym, ConstantSymbol) or isinstance(sym, VariableSymbol) or isinstance(sym, FunctionParameterSymbol):
                    raise StaticError.Undeclared(StaticError.Identifier(), ast.name)
                else:
                    return None
        if struct_ast is None:
            raise StaticError.Undeclared(StaticError.Identifier(), ast.name)

        # TODO: check each field exists and that there are no dupes.

        return AST.Id(ast.name)

    def visitNilLiteral(self, ast, param):
        # TODO: should there be a class to express the (lack of a) type of a nil literal?
        return None

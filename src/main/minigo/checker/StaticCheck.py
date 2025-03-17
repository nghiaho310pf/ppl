"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=6hUH7RxU2yQ
"""

import AST
from AST import VoidType
from Visitor import *
# from Utils import Utils
import StaticError
# from functools import reduce

# class MType:
#     def __init__(self, partype, rettype):
#         self.partype = partype
#         self.rettype = rettype
#
#     def __str__(self):
#         return "MType([" + ",".join(str(x) for x in self.partype) + "]," + str(self.rettype) + ")"
#
# class Symbol:
#     def __init__(self,name,mtype,value = None):
#         self.name = name
#         self.mtype = mtype
#         self.value = value
#
#     def __str__(self):
#         return "Symbol(" + str(self.name) + "," + str(self.mtype) + ("" if self.value is None else "," + str(self.value)) + ")"

# Just use classes, man.

class ScopeObject:
    def __init__(self):
        pass

class Symbol(ScopeObject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

class StructSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.StructType):
        super().__init__(name)
        self.original_ast = original_ast

class InterfaceSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.InterfaceType):
        super().__init__(name)
        self.original_ast = original_ast

class FunctionSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.FuncDecl):
        super().__init__(name)
        self.original_ast = original_ast

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

    def set_type(self, new_type: AST.Type):
        self.resolved_type = new_type

class FunctionParameterSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ParamDecl):
        super().__init__(name)
        self.original_ast = original_ast

# Some state, who cares.

class CurrentFunction(ScopeObject):
    def __init__(self, original_ast: AST.FuncDecl):
        super().__init__()
        self.original_ast = original_ast

class IsExpressionVisit(ScopeObject):
    def __init__(self):
        super().__init__()

class IsTypenameVisit(ScopeObject):
    def __init__(self):
        super().__init__()

# class StaticChecker(BaseVisitor,Utils):
class StaticChecker(BaseVisitor):
    def __init__(self, root_ast):
        self.root_ast = root_ast

    # TODO: Ask Phung about casting from struct vals to opaque interface vals.
    @staticmethod
    def compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        return type(a) == type(b)

    def check(self):
        # TODO: there are pre-defined global methods; add them here.
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: list[ScopeObject]):
        scope: list[ScopeObject] = given_scope.copy()

        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.visit(thing, scope)
                scope.append(StructSymbol(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                self.visit(thing, scope)
                scope.append(InterfaceSymbol(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), scope):
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Function(), thing.name)
                # Recursion may be used so we'll append it to scope first.
                scope.append(FunctionSymbol(thing.name, thing))
                self.visit(thing, scope)
            elif isinstance(thing, AST.MethodDecl):
                # Preventative hack-fix for ASTGeneration.py/AST.py flaw.
                if type(thing.recType) is not AST.Id:
                    raise StaticError.TypeMismatch(thing) # TODO: do something about this?
                receiver_type_id: AST.Id = thing.recType # downcast so the IDE actually shuts up about it
                struct_found = False
                for struct in filter(lambda s: isinstance(s, StructSymbol), scope):
                    if struct.name == receiver_type_id.name:
                        for existing_method in struct.original_ast.methods:
                            if existing_method.fun.name == thing.fun.name:
                                raise StaticError.Redeclared(StaticError.Method(), thing.fun.name)
                        struct.original_ast.methods.append(thing)
                        struct_found = True
                        break
                if not struct_found:
                    # TODO: this is probably correct but I should ask Phung just to be sure.
                    raise StaticError.Undeclared(StaticError.Type(), receiver_type_id.name)
                # Recursion may be used so it's added to the struct first above.
                self.visit(thing, scope)
            elif isinstance(thing, AST.VarDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), scope):
                    if thing.varName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.varName)
                resolved_type = self.visit(thing, scope)
                sym = VariableSymbol(thing.varName, thing)
                sym.set_type(resolved_type)
                scope.append(sym)
            elif isinstance(thing, AST.ConstDecl):
                for existing_symbol in filter(lambda x: isinstance(x, Symbol), scope):
                    if thing.conName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.conName)
                resolved_type = self.visit(thing, scope)
                sym = ConstantSymbol(thing.conName, thing)
                sym.set_type(resolved_type)
                scope.append(sym)

        # TODO: do we return anything? Ask Phung.

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: list[ScopeObject]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        explicit_type: AST.Type | None = self.visit(ast.varType, given_scope + [IsTypenameVisit()]) if ast.varType is not None else None
        implicit_type: AST.Type | None = self.visit(ast.varInit, given_scope + [IsExpressionVisit()]) if ast.varInit is not None else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: list[ScopeObject]):
        # We don't check name dupes here either; that's done by the outer layer.
        explicit_type: AST.Type | None = self.visit(ast.conType, given_scope + [IsTypenameVisit()]) if ast.conType is not None else None
        implicit_type: AST.Type | None = self.visit(ast.iniExpr, given_scope + [IsExpressionVisit()]) if ast.iniExpr is not None else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitFuncDecl(self, ast: AST.FuncDecl, given_scope: list[ScopeObject]):
        scope = given_scope + [CurrentFunction(ast)]

        # Parameters cannot repeat names within themselves, but they can shadow global variables, structs, interfaces and
        # functions.
        for param in ast.params:
            for existing_param in filter(lambda x: isinstance(x, FunctionParameterSymbol), scope):
                if existing_param.name == param.parName:
                    raise StaticError.Redeclared(StaticError.Parameter(), param.parName)
            self.visit(param.parType, scope + [IsTypenameVisit()])
            scope.append(FunctionParameterSymbol(param.parName, param))

        # Now check the return type.
        self.visit(ast.retType, scope + [IsTypenameVisit()])

        # Everything is done now; we can visit the inner block.
        self.visit(ast.body, scope)

    def visitMethodDecl(self, ast, param):
        return None

    def visitPrototype(self, ast, param):
        return None

    def visitIntType(self, ast, param):
        return ast

    def visitFloatType(self, ast, param):
        return ast

    def visitBoolType(self, ast, param):
        return ast

    def visitStringType(self, ast, param):
        return ast

    def visitVoidType(self, ast, param):
        return ast

    def visitArrayType(self, ast, param):
        return ast

    def visitStructType(self, ast, param):
        return None

    def visitInterfaceType(self, ast, param):
        return None

    def visitBlock(self, ast: AST.Block, given_scope: list[ScopeObject]):
        scope = given_scope.copy()

        # Vars and consts within the same block cannot collide names. Inner blocks can shadow.
        this_block_names = []
        for statement in ast.member:
            if isinstance(statement, AST.VarDecl):
                if statement.varName in this_block_names:
                    raise StaticError.Redeclared(StaticError.Variable(), statement.varName)
                this_block_names.append(statement.varName)

                sym = VariableSymbol(statement.varName, statement)
                resolved_type = self.visit(statement, scope)
                sym.set_type(resolved_type)
                scope.append(sym)
            elif isinstance(statement, AST.ConstDecl):
                if statement.conName in this_block_names:
                    raise StaticError.Redeclared(StaticError.Constant(), statement.conName)
                this_block_names.append(statement.conName)

                sym = ConstantSymbol(statement.conName, statement)
                resolved_type = self.visit(statement, scope)
                sym.set_type(resolved_type)
                scope.append(sym)
            else:
                # This is probably a statement/expression.
                self.visit(statement, scope + [IsExpressionVisit()])

    def visitAssign(self, ast, param):
        return None

    def visitIf(self, ast, param):
        return None

    def visitForBasic(self, ast, param):
        return None

    def visitForStep(self, ast, param):
        return None

    def visitForEach(self, ast, param):
        return None

    def visitContinue(self, ast, param):
        return None

    def visitBreak(self, ast, param):
        return None

    def visitReturn(self, ast: AST.Return, given_scope: list[ScopeObject]):
        # Are we in a return?
        current_function: CurrentFunction | None = next(filter(lambda x: isinstance(x, CurrentFunction), reversed(given_scope)))
        if current_function is None:
            # TODO: what to raise here?
            raise StaticError.Undeclared(StaticError.Function(), "(no function)")

        if isinstance(current_function.original_ast.retType, VoidType):
            if ast.expr is not None:
                raise StaticError.TypeMismatch(ast)
        else:
            if ast.expr is None:
                raise StaticError.TypeMismatch(ast)
            expr_type = self.visit(ast.expr, given_scope)
            if not self.compare_types(expr_type, current_function.original_ast.retType):
                raise StaticError.TypeMismatch(ast)

    def visitBinaryOp(self, ast, param):
        return None

    def visitUnaryOp(self, ast, param):
        return None

    def visitFuncCall(self, ast, param):
        return None

    def visitMethCall(self, ast: AST.MethCall, given_scope: list[ScopeObject]):
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

    def visitId(self, ast: AST.Id, given_scope: list[ScopeObject]):
        for sym in filter(lambda x: isinstance(x, Symbol), reversed(given_scope)):
            if sym.name == ast.name:
                if isinstance(sym, StructSymbol) or isinstance(sym, InterfaceSymbol):
                    id_mode: IsTypenameVisit | IsExpressionVisit | None = next(filter(lambda x: isinstance(x, IsTypenameVisit) or isinstance(x, IsExpressionVisit), reversed(given_scope)))
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
                    return sym.resolved_type
                elif isinstance(sym, FunctionParameterSymbol):
                    return sym.original_ast.parType
                else:
                    return None
        raise StaticError.Undeclared(StaticError.Identifier(), ast.name)

    def visitArrayCell(self, ast, param):
        return None

    def visitFieldAccess(self, ast: AST.FieldAccess, given_scope: list[ScopeObject]):
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

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, scope: list[ScopeObject]):
        # TODO: check lengths, array type and element type.
        return

    def visitStructLiteral(self, ast: AST.StructLiteral, given_scope: list[ScopeObject]):
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

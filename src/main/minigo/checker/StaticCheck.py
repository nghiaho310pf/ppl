"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=6hUH7RxU2yQ
"""

import AST
from Visitor import *
# from Utils import Utils
import StaticError
from functools import reduce

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

class Symbol:
    def __init__(self, name: str):
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

    def set_type(self, type: AST.Type):
        self.resolved_type = type

class ConstantSymbol(Symbol):
    def __init__(self, name: str, original_ast: AST.ConstDecl):
        super().__init__(name)
        self.original_ast = original_ast

# class StaticChecker(BaseVisitor,Utils):
class StaticChecker(BaseVisitor):
    def __init__(self, root_ast):
        self.root_ast = root_ast

    # TODO: Ask Phung about casting from struct vals to opaque interface vals.
    @staticmethod
    def compare_types(a: AST.Type, b: AST.Type):
        if isinstance(a, AST.Id) and isinstance(b, AST.Id):
            return a.name == b.name
        if type(a) != type(b):
            return False

    def check(self):
        # TODO: there are pre-defined global methods; add them here.
        return self.visit(self.root_ast, [])

    def visitProgram(self, ast: AST.Program, given_scope: list[Symbol]):
        scope: list[Symbol] = given_scope.copy()
        for thing in ast.decl:
            if isinstance(thing, AST.StructType):
                for existing_symbol in scope:
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                scope.append(StructSymbol(thing.name, thing))
            elif isinstance(thing, AST.InterfaceType):
                for existing_symbol in scope:
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Type(), thing.name)
                scope.append(InterfaceSymbol(thing.name, thing))
            elif isinstance(thing, AST.FuncDecl):
                for existing_symbol in scope:
                    if thing.name == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Function(), thing.name)
                scope.append(FunctionSymbol(thing.name, thing))
            elif isinstance(thing, AST.VarDecl):
                for existing_symbol in scope:
                    if thing.varName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.varName)
                scope.append(VariableSymbol(thing.varName, thing))
            elif isinstance(thing, AST.ConstDecl):
                for existing_symbol in scope:
                    if thing.conName == existing_symbol.name:
                        raise StaticError.Redeclared(StaticError.Variable(), thing.conName)
                scope.append(ConstantSymbol(thing.conName, thing))

        # So far we've pretty much only tried to find global duplicates; methods aren't even checked yet.

        # Find methods.
        # This must be done here because methods are declared outside their receivers.
        for thing in ast.decl:
            if isinstance(thing, AST.MethodDecl):
                # Preventative hack-fix for ASTGeneration.py/AST.py flaw.
                if type(thing.recType) is not AST.Id:
                    raise StaticError.TypeMismatch(thing)  # TODO: do something about this?
                receiver_type_id: AST.Id = thing.recType  # downcast so the IDE actually shuts up about it
                for struct in filter(lambda s: isinstance(s, StructSymbol), scope):
                    if struct.name == receiver_type_id.name:
                        for existing_method in struct.original_ast.methods:
                            if existing_method.fun.name == thing.fun.name:
                                raise StaticError.Redeclared(StaticError.Method(), thing.fun.name)
                        struct.original_ast.methods.append(thing)
                        break
                # TODO: this is probably correct but I should ask Phung just to be sure.
                raise StaticError.Undeclared(StaticError.Type(), receiver_type_id.name)

        for thing in ast.decl:
            self.visit(thing, scope)

        # TODO: do we return anything? Ask Phung.

    def visitVarDecl(self, ast: AST.VarDecl, given_scope: list[Symbol]):
        # We don't check name dupes; that's done by the outer layer.
        # Instead, we only visit the inner expression and check for type mismatches.

        explicit_type = self.visit(ast.varType, given_scope) if ast.varType is not None else None
        implicit_type = self.visit(ast.varInit, given_scope) if ast.varInit is not None else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitConstDecl(self, ast: AST.ConstDecl, given_scope: list[Symbol]):
        # We don't check name dupes here either; that's done by the outer layer.
        explicit_type = self.visit(ast.conType, given_scope) if ast.conType is not None else None
        implicit_type = self.visit(ast.iniExpr, given_scope) if ast.iniExpr is not None else None
        # No voids allowed.
        if isinstance(explicit_type, AST.VoidType) or isinstance(implicit_type, AST.VoidType):
            raise StaticError.TypeMismatch(ast)
        if (explicit_type is not None) and (implicit_type is not None) and (not self.compare_types(explicit_type, implicit_type)):
            raise StaticError.TypeMismatch(ast)

        return implicit_type if implicit_type is not None else explicit_type

    def visitFuncDecl(self, ast, param):
        return None

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

    def visitBlock(self, ast, param):
        return None

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

    def visitReturn(self, ast, param):
        return None

    def visitBinaryOp(self, ast, param):
        return None

    def visitUnaryOp(self, ast, param):
        return None

    def visitFuncCall(self, ast, param):
        return None

    def visitMethCall(self, ast, param):
        return None

    def visitId(self, ast, param):
        return None

    def visitArrayCell(self, ast, param):
        return None

    def visitFieldAccess(self, ast, param):
        return None

    def visitIntLiteral(self, ast, param):
        return AST.IntType()

    def visitFloatLiteral(self, ast, param):
        return AST.FloatType()

    def visitBooleanLiteral(self, ast, param):
        return AST.BoolType()

    def visitStringLiteral(self, ast, param):
        return AST.StringType()

    def visitArrayLiteral(self, ast: AST.ArrayLiteral, scope: list[Symbol]):
        return

    def visitStructLiteral(self, ast, param):
        return None

    def visitNilLiteral(self, ast, param):
        return None

    # def visitVarDecl(self, ast, c):
    #     res = self.lookup(ast.varName, c, lambda x: x.name)
    #     if not res is None:
    #         raise Redeclared(Variable(), ast.varName)
    #     if ast.varInit:
    #         initType = self.visit(ast.varInit, c)
    #         if ast.varType is None:
    #             ast.varType = initType
    #         if not type(ast.varType) is type(initType):
    #             raise TypeMismatch(ast)
    #     return Symbol(ast.varName, ast.varType,None)
    #
    #
    # def visitFuncDecl(self,ast, c):
    #     res = self.lookup(ast.name, c, lambda x: x.name)
    #     if not res is None:
    #         raise Redeclared(Function(), ast.name)
    #     return Symbol(ast.name, MType([], ast.retType))
    #
    # def visitIntLiteral(self,ast, c):
    #     return AST.IntType()
    #
    # def visitFloatLiteral(self,ast, c):
    #     return AST.FloatType()
    #
    # def visitId(self,ast,c):
    #     res = self.lookup(ast.name, c, lambda x: x.name)
    #     if res is None:
    #         raise Undeclared(Identifier(), ast.name)
    #     return res.mtype

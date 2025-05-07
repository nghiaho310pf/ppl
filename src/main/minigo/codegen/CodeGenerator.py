"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=I5aT1fRa9Mc
"""

import AST
from Utils import Utils
import StaticCheck
import StaticError
from Emitter import Emitter
from Frame import Frame
from abc import ABC, abstractmethod
from functools import reduce
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

class ClassType(AST.Type):
    def __init__(self, name):
        #value: Id
        self.name = name

    def __str__(self):
        return f"ClassType({self.name})"

    def accept(self, v, param):
        return v.visitClassType(self, param)
    
class CodeGenerator(BaseVisitor,Utils):
    def __init__(self):
        self.className = "MiniGoClass"
        self.astTree = None
        self.path = None
        self.emit = None

    def init(self):
        mem = [
            StaticCheck.Symbol("getInt",StaticCheck.MType([],AST.IntType()),CName("io",True)),
            StaticCheck.Symbol("putInt",StaticCheck.MType([AST.IntType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("putIntLn",StaticCheck.MType([AST.IntType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("getFloat",StaticCheck.MType([],AST.FloatType()),CName("io",True)),
            StaticCheck.Symbol("putFloat",StaticCheck.MType([AST.FloatType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("putFloatLn",StaticCheck.MType([AST.FloatType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("getBool",StaticCheck.MType([],AST.BoolType()),CName("io",True)),
            StaticCheck.Symbol("putBool",StaticCheck.MType([AST.BoolType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("putBoolLn",StaticCheck.MType([AST.BoolType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("getString",StaticCheck.MType([],AST.StringType()),CName("io",True)),
            StaticCheck.Symbol("putString",StaticCheck.MType([AST.StringType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("putStringLn",StaticCheck.MType([AST.StringType()],AST.VoidType()),CName("io",True)),
            StaticCheck.Symbol("putLn",StaticCheck.MType([],AST.VoidType()),CName("io",True))
        ]
        return mem

    def gen(self, ast, dir_):
        gl = self.init()
        self.astTree = ast
        self.path = dir_
        self.emit = Emitter(dir_ + "/" + self.className + ".j")
        self.visit(ast, gl)

    def emitObjectInit(self):
        frame = Frame("<init>", AST.VoidType())
        self.emit.printout(self.emit.emitMETHOD("<init>", StaticCheck.MType([], AST.VoidType()), False, frame))  # Bắt đầu định nghĩa phương thức <init>
        frame.enterScope(True)
        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "this", ClassType(self.className), frame.getStartLabel(), frame.getEndLabel(), frame))  # Tạo biến "this" trong phương thức <init>

        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        self.emit.printout(self.emit.emitREADVAR("this", ClassType(self.className), 0, frame))
        self.emit.printout(self.emit.emitINVOKESPECIAL(frame))


        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()

    # Visitor methods

    def visitProgram(self, ast, c):
        env ={}
        env['env'] = [c]
        self.emit.printout(self.emit.emitPROLOG(self.className, "java.lang.Object", False))
        env = reduce(lambda a,x: self.visit(x,a), ast.decl, env)
        self.emitObjectInit()
        self.emit.printout(self.emit.emitEPILOG())
        return env

    def visitVarDecl(self, ast, o):
        if 'frame' not in o: # global var
            o['env'][0].append(StaticCheck.Symbol(ast.varName, ast.varType, CName(self.className)))
            self.emit.printout(self.emit.emitATTRIBUTE(ast.varName, ast.varType, True, False, str(ast.varInit.value) if ast.varInit else None))
        else:
            frame = o['frame']
            index = frame.getNewIndex()
            o['env'][0].append(StaticCheck.Symbol(ast.varName, ast.varType, Index(index)))
            self.emit.printout(self.emit.emitVAR(index, ast.varName, ast.varType, frame.getStartLabel(), frame.getEndLabel(), frame))
            if ast.varInit:
                self.emit.printout(self.emit.emitPUSHICONST(ast.varInit.value, frame))
                self.emit.printout(self.emit.emitWRITEVAR(ast.varName, ast.varType, index,  frame))
        return o

    def visitConstDecl(self, ast, param):
        return None

    def visitParamDecl(self, ast, o):
        # TODO:
        return o

    def visitFuncDecl(self, ast, o):
        frame = Frame(ast.name, ast.retType)
        isMain = ast.name == "main"
        if isMain:
            mtype = StaticCheck.MType([AST.ArrayType([None],AST.StringType())], AST.VoidType())
        else:
            mtype = StaticCheck.MType(list(map(lambda x: x.parType, ast.params)), ast.retType)
        o['env'][0].append(StaticCheck.Symbol(ast.name, mtype, CName(self.className)))
        env = o.copy()
        env['frame'] = frame
        self.emit.printout(self.emit.emitMETHOD(ast.name, mtype, True, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        env['env'] = [[]] + env['env']
        if isMain:
            self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "args", AST.ArrayType([None],AST.StringType()), frame.getStartLabel(), frame.getEndLabel(), frame))
        else:
            env = reduce(lambda acc,e: self.visit(e,acc),ast.params,env)
        self.visit(ast.body,env)
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(ast.retType) is AST.VoidType:
            self.emit.printout(self.emit.emitRETURN(AST.VoidType(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
        return o

    def visitMethodDecl(self, ast, param):
        return None

    def visitPrototype(self, ast, param):
        return None

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

    def visitStructType(self, ast, param):
        return None

    def visitInterfaceType(self, ast, param):
        return None

    def visitBlock(self, ast, o):
        env = o.copy()
        env['env'] = [[]] + env['env']
        env['frame'].enterScope(False)
        self.emit.printout(self.emit.emitLABEL(env['frame'].getStartLabel(), env['frame']))
        env = reduce(lambda acc,e: self.visit(e,acc),ast.member,env)
        self.emit.printout(self.emit.emitLABEL(env['frame'].getEndLabel(), env['frame']))
        env['frame'].exitScope()
        return o

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

    def visitFuncCall(self, ast, o):
        sym = next(filter(lambda x: x.name == ast.funName, o['env'][-1]),None)
        env = o.copy()
        env['isLeft'] = False
        [self.emit.printout(self.visit(x, env)[0]) for x in ast.args]
        self.emit.printout(self.emit.emitINVOKESTATIC(f"{sym.value.value}/{ast.funName}",sym.mtype, o['frame']))
        return o

    def visitMethCall(self, ast, param):
        return None

    def visitId(self, ast, o):
        sym = next(filter(lambda x: x.name == ast.name, [j for i in o['env'] for j in i]),None)
        if type(sym.value) is Index:
            return self.emit.emitREADVAR(ast.name, sym.mtype, sym.value.value, o['frame']),sym.mtype
        else:
            return self.emit.emitGETSTATIC(f"{self.className}/{sym.name}",sym.mtype,o['frame']),sym.mtype

    def visitArrayCell(self, ast, param):
        return None

    def visitFieldAccess(self, ast, param):
        return None

    def visitIntLiteral(self, ast, o):
        return self.emit.emitPUSHICONST(ast.value, o['frame']), AST.IntType()

    def visitFloatLiteral(self, ast, param):
        return None

    def visitBooleanLiteral(self, ast, param):
        return None

    def visitStringLiteral(self, ast, param):
        return None

    def visitArrayLiteral(self, ast, param):
        return None

    def visitStructLiteral(self, ast, param):
        return None

    def visitNilLiteral(self, ast, param):
        return None

"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=I5aT1fRa9Mc
 * @note https://www.youtube.com/watch?v=rCWrqSqhcJ8
"""
import AST
import CodeGenError
import StaticCheck
from MachineCode import JasminCode


class Emitter():
    def __init__(self, filename):
        self.filename = filename
        self.buff = list()
        self.jvm = JasminCode()

    def getJVMType(self, inType):
        if isinstance(inType, AST.IntType):
            return "I"
        if isinstance(inType, AST.FloatType):
            return "F"
        if isinstance(inType, AST.BoolType):
            return "Z"
        if isinstance(inType, AST.StringType):
            return "Ljava/lang/String;"
        if isinstance(inType, AST.VoidType):
            return "V"

        if isinstance(inType, AST.ArrayType):
            return "[" * len(inType.dimens) + self.getJVMType(inType.eleType)
        if isinstance(inType, StaticCheck.MType):
            return "(" + "".join(list(map(lambda x: self.getJVMType(x), inType.partype))) + ")" + self.getJVMType(inType.rettype)
        if isinstance(inType, AST.StructType):
            return "L" + inType.name + ";"
        if isinstance(inType, AST.InterfaceType):
            return "L" + inType.name + ";"

        if isinstance(inType, str):
            return "L" + inType + ";"

        if inType is None:
            return "Ljava/lang/Object;"

        raise CodeGenError.IllegalOperandException(inType)

    def getFullType(self, inType):
        if isinstance(inType, AST.IntType):
            return "int"
        if isinstance(inType, AST.FloatType):
            return "float"
        if isinstance(inType, AST.BoolType):
            return "boolean"
        if isinstance(inType, AST.StringType):
            return "java/lang/String"
        if isinstance(inType, AST.VoidType):
            return "void"
        if isinstance(inType, AST.StructType) or isinstance(inType, AST.InterfaceType):
            return inType.name
        if isinstance(inType, AST.ArrayType):
            return "[" * len(inType.dimens) + self.getFullType(inType.eleType)
        raise CodeGenError.IllegalOperandException(inType)

    def getNEWARRAYType(self, inType):
        if isinstance(inType, AST.IntType):
            return "int"
        if isinstance(inType, AST.FloatType):
            return "float"
        if isinstance(inType, AST.BoolType):
            return "boolean"
        raise CodeGenError.IllegalOperandException(inType)

    def getANEWARRAYType(self, inType):
        if isinstance(inType, AST.IntType):
            return "I"
        if isinstance(inType, AST.FloatType):
            return "F"
        if isinstance(inType, AST.BoolType):
            return "Z"
        if isinstance(inType, AST.StringType):
            return "java/lang/String"
        if isinstance(inType, AST.VoidType):
            return "V"
        if isinstance(inType, AST.StructType) or isinstance(inType, AST.InterfaceType):
            return inType.name
        if isinstance(inType, AST.ArrayType):
            return "[" * len(inType.dimens) + self.getJVMType(inType.eleType)

    def emitNOP(self, frame):
        return JasminCode.INDENT + "nop" + JasminCode.END

    def emitPUSHICONST(self, in_, frame):
        #in: Int or Sring
        #frame: Frame

        frame.push();
        if type(in_) is int:
            i = in_
            if i >= -1 and i <=5:
                return self.jvm.emitICONST(i)
            elif i >= -128 and i <= 127:
                return self.jvm.emitBIPUSH(i)
            elif i >= -32768 and i <= 32767:
                return self.jvm.emitSIPUSH(i)
        elif type(in_) is str:
            if in_ == "true":
                return self.emitPUSHICONST(1, frame)
            elif in_ == "false":
                return self.emitPUSHICONST(0, frame)
            else:
                return self.emitPUSHICONST(int(in_), frame)

    def emitPUSHFCONST(self, in_, frame):
        #in_: String
        #frame: Frame
        
        f = float(in_)
        frame.push()
        rst = "{0:.4f}".format(f)
        if rst == "0.0" or rst == "1.0" or rst == "2.0":
            return self.jvm.emitFCONST(rst)
        else:
            return self.jvm.emitLDC(f"{in_}")

    def emitPUSHNULL(self, frame):
        frame.push()
        return self.jvm.emitPUSHNULL()

    ''' 
    *    generate code to push a constant onto the operand stack.
    *    @param in the lexeme of the constant
    *    @param typ the type of the constant
    '''
    def emitPUSHCONST(self, in_, typ, frame):
        #in_: String
        #typ: Type
        #frame: Frame
        
        if isinstance(typ, AST.IntType):
            return self.emitPUSHICONST(in_, frame)
        if isinstance(typ, AST.FloatType):
            return self.emitPUSHFCONST(in_, frame)
        if isinstance(typ, AST.BoolType):
            return self.emitPUSHICONST(1 if in_ else 0, frame)
        if isinstance(typ, AST.StringType):
            frame.push()
            return self.jvm.emitLDC(in_)
        raise CodeGenError.IllegalOperandException(in_)

    ##############################################################

    def emitNEW(self, lexeme, frame):
        frame.push()
        return self.jvm.emitNEW(lexeme)

    def emitNEWARRAY(self, in_, frame):
        frame.pop()
        frame.push()
        if isinstance(in_, AST.IntType) or isinstance(in_, AST.FloatType) or isinstance(in_, AST.BoolType):
            return self.jvm.emitNEWARRAY(self.getNEWARRAYType(in_))
        elif isinstance(in_, AST.StructType) or isinstance(in_, AST.InterfaceType) or isinstance(in_, AST.StringType) or isinstance(in_, AST.ArrayType):
            z = self.getANEWARRAYType(in_)

            return self.jvm.emitANEWARRAY(z)
        else:
            raise CodeGenError.IllegalOperandException(str(in_))

    def emitALOAD(self, in_, frame):
        # ..., arrayref, index -> ..., value
        frame.pop()  # index
        if isinstance(in_, AST.IntType):
            return self.jvm.emitIALOAD()
        elif isinstance(in_, AST.FloatType):
            return self.jvm.emitFALOAD()
        elif isinstance(in_, AST.BoolType):
            return self.jvm.emitBALOAD()
        elif isinstance(in_, AST.ArrayType) or isinstance(in_, AST.StructType) or isinstance(in_, AST.InterfaceType) or isinstance(in_, AST.StringType):
            return self.jvm.emitAALOAD()
        else:
            raise CodeGenError.IllegalOperandException(str(in_))

    def emitASTORE(self, in_, frame):
        # ..., arrayref, index, value -> ...
        frame.pop()  # value
        frame.pop()  # index
        frame.pop()  # arrayref
        if isinstance(in_, AST.IntType):
            return self.jvm.emitIASTORE()
        elif isinstance(in_, AST.FloatType):
            return self.jvm.emitFASTORE()
        elif isinstance(in_, AST.BoolType):
            return self.jvm.emitBASTORE()
        elif isinstance(in_, AST.ArrayType) or isinstance(in_, AST.StructType) or isinstance(in_, AST.InterfaceType) or isinstance(in_, AST.StringType):
            return self.jvm.emitAASTORE()
        else:
            raise CodeGenError.IllegalOperandException(str(in_))

    '''    generate the var directive for a local variable.
    *   @param in the index of the local variable.
    *   @param varName the name of the local variable.
    *   @param inType the type of the local variable.
    *   @param fromLabel the starting label of the scope where the variable is active.
    *   @param toLabel the ending label  of the scope where the variable is active.
    '''
    def emitVAR(self, in_, varName, inType, fromLabel, toLabel, frame):
        #in_: Int
        #varName: String
        #inType: Type
        #fromLabel: Int
        #toLabel: Int
        #frame: Frame
        
        return self.jvm.emitVAR(in_, varName, self.getJVMType(inType), fromLabel, toLabel)

    def emitREADVAR(self, name, inType, index, frame):
        #name: String
        #inType: Type
        #index: Int
        #frame: Frame
        #... -> ..., value
        
        frame.push()
        if isinstance(inType, AST.IntType) or isinstance(inType, AST.BoolType):
            return self.jvm.emitILOAD(index)
        if isinstance(inType, AST.FloatType):
            return self.jvm.emitFLOAD(index)
        if isinstance(inType, AST.ArrayType) or isinstance(inType, AST.StructType) or isinstance(inType, AST.InterfaceType) or isinstance(inType, AST.StringType) or isinstance(inType, str):
            return self.jvm.emitALOAD(index)
        raise CodeGenError.IllegalOperandException(name)

    ''' generate the second instruction for array cell access
    *
    '''
    def emitREADVAR2(self, name, typ, frame):
        #name: String
        #typ: Type
        #frame: Frame
        #... -> ..., value

        #frame.push()
        raise CodeGenError.IllegalOperandException(name)

    '''
    *   generate code to pop a value on top of the operand stack and store it to a block-scoped variable.
    *   @param name the symbol entry of the variable.
    '''
    def emitWRITEVAR(self, name, inType, index, frame):
        #name: String
        #inType: Type
        #index: Int
        #frame: Frame
        #..., value -> ...
        
        frame.pop()

        if isinstance(inType, AST.IntType) or isinstance(inType, AST.BoolType):
            return self.jvm.emitISTORE(index)
        if isinstance(inType, AST.FloatType):
            return self.jvm.emitFSTORE(index)
        elif isinstance(inType, AST.ArrayType) or isinstance(inType, AST.StructType) or isinstance(inType, AST.InterfaceType) or isinstance(inType, AST.StringType):
            return self.jvm.emitASTORE(index)
        else:
            raise CodeGenError.IllegalOperandException(name)

    ''' generate the second instruction for array cell access
    *
    '''
    def emitWRITEVAR2(self, name, typ, frame):
        #name: String
        #typ: Type
        #frame: Frame
        #..., value -> ...

        #frame.push()
        raise CodeGenError.IllegalOperandException(name)

    ''' generate the field (static) directive for a class mutable or immutable attribute.
    *   @param lexeme the name of the attribute.
    *   @param in the type of the attribute.
    *   @param isFinal true in case of constant; false otherwise
    '''
    def emitATTRIBUTE(self, lexeme, in_, isStatic, isFinal, value):
        #lexeme: String
        #in_: Type
        #isFinal: Boolean
        #value: String
        if isStatic:
            return self.jvm.emitSTATICFIELD(lexeme, self.getJVMType(in_), isFinal, value)
        else:
            return self.jvm.emitINSTANCEFIELD(lexeme, self.getJVMType(in_), isFinal, value)

    def emitGETSTATIC(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame

        frame.push()
        return self.jvm.emitGETSTATIC(lexeme, self.getJVMType(in_))

    def emitPUTSTATIC(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame
        
        frame.pop()
        return self.jvm.emitPUTSTATIC(lexeme, self.getJVMType(in_))

    def emitGETFIELD(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame

        return self.jvm.emitGETFIELD(lexeme, self.getJVMType(in_))

    def emitPUTFIELD(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame

        frame.pop()
        frame.pop()
        return self.jvm.emitPUTFIELD(lexeme, self.getJVMType(in_))

    ''' generate code to invoke a static method
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name)
    *   @param in the type descriptor of the method.
    '''
    def emitINVOKESTATIC(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame

        typ = in_
        list(map(lambda x: frame.pop(), typ.partype))
        if not type(typ.rettype) is AST.VoidType:
            frame.push()
        return self.jvm.emitINVOKESTATIC(lexeme, self.getJVMType(in_))

    ''' generate code to invoke a special method
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name)
    *   @param in the type descriptor of the method.
    '''
    def emitINVOKESPECIAL(self, frame, lexeme=None, in_=None):
        #lexeme: String
        #in_: Type
        #frame: Frame

        if not lexeme is None and not in_ is None:
            typ = in_
            list(map(lambda x: frame.pop(), typ.partype))
            frame.pop()
            if not type(typ.rettype) is AST.VoidType:
                frame.push()
            return self.jvm.emitINVOKESPECIAL(lexeme, self.getJVMType(in_))
        elif lexeme is None and in_ is None:
            frame.pop()
            return self.jvm.emitINVOKESPECIAL()

    ''' generate code to invoke a virtual method
    * @param lexeme the qualified name of the method(i.e., class-name/method-name)
    * @param in the type descriptor of the method.
    '''
    def emitINVOKEVIRTUAL(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame
        list(map(lambda x: frame.pop(), in_.partype))
        frame.pop()
        if not isinstance(in_, AST.VoidType):
            frame.push()
        return self.jvm.emitINVOKEVIRTUAL(lexeme, self.getJVMType(in_))

    def emitINVOKEINTERFACE(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame
        list(map(lambda x: frame.pop(), in_.partype))
        frame.pop()
        if not isinstance(in_, AST.VoidType):
            frame.push()
        return self.jvm.emitINVOKEINTERFACE(lexeme, self.getJVMType(in_), len(in_.partype) + 1)

    def emitSTRCONCAT(self, frame):
        frame.pop()
        frame.pop()
        frame.push()
        return self.jvm.emitINVOKEVIRTUAL("java/lang/String/concat(Ljava/lang/String;)", "Ljava/lang/String;")

    '''
    *   generate ineg, fneg.
    *   @param in the type of the operands.
    '''
    def emitNEGOP(self, in_, frame):
        #in_: Type
        #frame: Frame
        #..., value -> ..., result

        if type(in_) is AST.IntType:
            return self.jvm.emitINEG()
        else:
            return self.jvm.emitFNEG()

    def emitNOT(self, in_, frame):
        #in_: Type
        #frame: Frame

        label1 = frame.getNewLabel()
        label2 = frame.getNewLabel()
        result = list()
        result.append(self.emitIFTRUE(label1, frame))
        result.append(self.emitPUSHCONST("true", in_, frame))
        result.append(self.emitGOTO(label2, frame))
        result.append(self.emitLABEL(label1, frame))
        result.append(self.emitPUSHCONST("false", in_, frame))
        result.append(self.emitLABEL(label2, frame))
        return ''.join(result)

    '''
    *   generate iadd, isub, fadd or fsub.
    *   @param lexeme the lexeme of the operator.
    *   @param in the type of the operands.
    '''
    def emitADDOP(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame
        #..., value1, value2 -> ..., result

        frame.pop()
        if lexeme == "+":
            if type(in_) is AST.IntType:
                return self.jvm.emitIADD()
            else:
                return self.jvm.emitFADD()
        else:
            if type(in_) is AST.IntType:
                return self.jvm.emitISUB()
            else:
                return self.jvm.emitFSUB()

    '''
    *   generate imul, idiv, fmul or fdiv.
    *   @param lexeme the lexeme of the operator.
    *   @param in the type of the operands.
    '''

    def emitMULOP(self, lexeme, in_, frame):
        #lexeme: String
        #in_: Type
        #frame: Frame
        #..., value1, value2 -> ..., result

        frame.pop()
        if lexeme == "*":
            if type(in_) is AST.IntType:
                return self.jvm.emitIMUL()
            else:
                return self.jvm.emitFMUL()
        else:
            if type(in_) is AST.IntType:
                return self.jvm.emitIDIV()
            else:
                return self.jvm.emitFDIV()

    def emitDIV(self, frame):
        #frame: Frame

        frame.pop()
        return self.jvm.emitIDIV()

    def emitMOD(self, frame):
        #frame: Frame

        frame.pop()
        return self.jvm.emitIREM()

    '''
    *   generate iand
    '''

    def emitANDOP(self, frame):
        #frame: Frame

        frame.pop()
        return self.jvm.emitIAND()

    '''
    *   generate ior
    '''
    def emitOROP(self, frame):
        #frame: Frame

        frame.pop()
        return self.jvm.emitIOR()

    def emitXOROP(self, frame):
        #frame: Frame
        #..., value1, value2 -> ..., result

        frame.pop()
        return JasminCode.INDENT + "ixor" + JasminCode.END

    def emitREOP(self, op, in_, frame):
        #op: String
        #in_: Type
        #frame: Frame
        #..., value1, value2 -> ..., result

        result = list()
        labelF = frame.getNewLabel()
        labelO = frame.getNewLabel()

        frame.pop()
        frame.pop()


        if isinstance(in_, AST.IntType):
            if op == ">":
                result.append(self.jvm.emitIFICMPLE(labelF))
            elif op == ">=":
                result.append(self.jvm.emitIFICMPLT(labelF))
            elif op == "<":
                result.append(self.jvm.emitIFICMPGE(labelF))
            elif op == "<=":
                result.append(self.jvm.emitIFICMPGT(labelF))
            elif op == "!=":
                result.append(self.jvm.emitIFICMPEQ(labelF))
            elif op == "==":
                result.append(self.jvm.emitIFICMPNE(labelF))
        elif isinstance(in_, AST.FloatType):
            result.append(self.jvm.emitFCMPL())
            if op == "<=":
                result.append(self.jvm.emitIFGT(labelF))
            elif op == "<":
                result.append(self.jvm.emitIFGE(labelF))
            elif op == ">":
                result.append(self.jvm.emitIFLE(labelF))
            elif op == ">=":
                result.append(self.jvm.emitIFLT(labelF))
            elif op == "!=":
                result.append(self.jvm.emitIFEQ(labelF))
            elif op == "==":
                result.append(self.jvm.emitIFNE(labelF))
        elif isinstance(in_, AST.StringType):
            if op in {"==", "!="}:
                result.append(self.jvm.emitINVOKEVIRTUAL("java/lang/String/equals", "(Ljava/lang/Object;)Z"))
                if op == "==":
                    result.append(self.jvm.emitIFEQ(labelF))
                else:
                    result.append(self.jvm.emitIFNE(labelF))
            else:
                result.append(self.jvm.emitINVOKEVIRTUAL("java/lang/String/compareTo", "(Ljava/lang/String;)I"))
                if op == ">=":
                    result.append(self.jvm.emitIFLE(labelF))
                elif op == ">":
                    result.append(self.jvm.emitIFLT(labelF))
                elif op == "<":
                    result.append(self.jvm.emitIFGE(labelF))
                elif op == "<=":
                    result.append(self.jvm.emitIFGT(labelF))

        result.append(self.emitPUSHCONST("1", AST.IntType(), frame))
        frame.pop()
        result.append(self.emitGOTO(labelO, frame))
        result.append(self.emitLABEL(labelF, frame))
        result.append(self.emitPUSHCONST("0", AST.IntType(), frame))
        result.append(self.emitLABEL(labelO, frame))
        return ''.join(result)

    def emitRELOP(self, op, in_, true_label, false_label, frame):
        # op: String
        # in_: Type
        # trueLabel: Int
        # falseLabel: Int
        # frame: Frame
        # ..., value1, value2 -> ..., result

        result = list()
        frame.pop()
        frame.pop()

        if isinstance(in_, AST.IntType) or isinstance(in_, AST.BoolType):
            if op == ">":
                result.append(self.jvm.emitIFICMPLE(false_label))
            elif op == ">=":
                result.append(self.jvm.emitIFICMPLT(false_label))
            elif op == "<":
                result.append(self.jvm.emitIFICMPGE(false_label))
            elif op == "<=":
                result.append(self.jvm.emitIFICMPGT(false_label))
            elif op == "!=":
                result.append(self.jvm.emitIFICMPEQ(false_label))
            elif op == "==":
                result.append(self.jvm.emitIFICMPNE(false_label))

        elif isinstance(in_, AST.FloatType):
            result.append(self.jvm.emitFCMPL())
            if op == "<=":
                result.append(self.jvm.emitIFGT(false_label))
            elif op == "<":
                result.append(self.jvm.emitIFGE(false_label))
            elif op == ">":
                result.append(self.jvm.emitIFLE(false_label))
            elif op == ">=":
                result.append(self.jvm.emitIFLT(false_label))
            elif op == "!=":
                result.append(self.jvm.emitIFEQ(false_label))
            elif op == "==":
                result.append(self.jvm.emitIFNE(false_label))

        elif isinstance(in_, AST.StringType):
            if op in {"==", "!="}:
                result.append(self.jvm.emitINVOKEVIRTUAL("java/lang/String/equals", "(Ljava/lang/Object;)Z"))
                if op == "==":
                    result.append(self.jvm.emitIFEQ(false_label))
                else:  # op == "!="
                    result.append(self.jvm.emitIFNE(false_label))
            else:
                result.append(self.jvm.emitINVOKEVIRTUAL("java/lang/String/compareTo", "(Ljava/lang/String;)I"))
                if op == ">=":
                    result.append(self.jvm.emitIFLE(false_label))
                elif op == ">":
                    result.append(self.jvm.emitIFLT(false_label))
                elif op == "<":
                    result.append(self.jvm.emitIFGE(false_label))
                elif op == "<=":
                    result.append(self.jvm.emitIFGT(false_label))

        if true_label is not None:
            result.append(self.jvm.emitGOTO(true_label))
        return ''.join(result)

    def emitINSTANCEFIELD(self, lexeme, typ, isFinal, value):
        return self.jvm.emitINSTANCEFIELD(lexeme, self.getJVMType(typ), isFinal, value)

    '''   generate the method directive for a function.
    *   @param lexeme the qualified name of the method(i.e., class-name/method-name).
    *   @param in the type descriptor of the method.
    *   @param isStatic <code>true</code> if the method is static; <code>false</code> otherwise.
    '''
    def emitMETHOD(self, lexeme, in_, isStatic, frame):
        #lexeme: String
        #in_: Type
        #isStatic: Boolean
        #frame: Frame

        return self.jvm.emitMETHOD(lexeme, self.getJVMType(in_), isStatic)

    '''   generate the end directive for a function.
    '''
    def emitENDMETHOD(self, frame):
        #frame: Frame

        buffer = list()
        buffer.append(self.jvm.emitLIMITSTACK(frame.getMaxOpStackSize()))
        buffer.append(self.jvm.emitLIMITLOCAL(frame.getMaxIndex()))
        buffer.append(self.jvm.emitENDMETHOD())
        return ''.join(buffer)

    def getConst(self, ast):
        #ast: Literal
        if type(ast) is AST.IntLiteral:
            return (str(ast.value), AST.IntType())

    '''   generate code to initialize a local array variable.<p>
    *   @param index the index of the local variable.
    *   @param in the type of the local array variable.
    '''

    '''   generate code to initialize local array variables.
    *   @param in the list of symbol entries corresponding to local array variable.    
    '''

    '''   generate code to jump to label if the value on top of operand stack is true.<p>
    *   ifgt label
    *   @param label the label where the execution continues if the value on top of stack is true.
    '''
    def emitIFTRUE(self, label, frame):
        #label: Int
        #frame: Frame

        frame.pop()
        return self.jvm.emitIFGT(label)

    '''
    *   generate code to jump to label if the value on top of operand stack is false.<p>
    *   ifle label
    *   @param label the label where the execution continues if the value on top of stack is false.
    '''
    def emitIFFALSE(self, label, frame):
        #label: Int
        #frame: Frame

        frame.pop()
        return self.jvm.emitIFLE(label)

    def emitIFICMPGT(self, label, frame):
        #label: Int
        #frame: Frame

        frame.pop()
        return self.jvm.emitIFICMPGT(label)

    def emitIFICMPLT(self, label, frame):
        #label: Int
        #frame: Frame

        frame.pop()
        return self.jvm.emitIFICMPLT(label)    

    '''   generate code to duplicate the value on the top of the operand stack.<p>
    *   Stack:<p>
    *   Before: ...,value1<p>
    *   After:  ...,value1,value1<p>
    '''
    def emitDUP(self, frame):
        #frame: Frame

        frame.push()
        return self.jvm.emitDUP()

    def emitPOP(self, frame):
        #frame: Frame

        frame.pop()
        return self.jvm.emitPOP()

    '''   generate code to exchange an integer on top of stack to a floating-point number.
    '''
    def emitI2F(self, frame):
        #frame: Frame

        return self.jvm.emitI2F()

    ''' generate code to return.
    *   <ul>
    *   <li>ireturn if the type is IntegerType or BooleanType
    *   <li>freturn if the type is RealType
    *   <li>return if the type is null
    *   </ul>
    *   @param in the type of the returned expression.
    '''

    def emitRETURN(self, in_, frame):
        #in_: Type
        #frame: Frame

        if isinstance(in_, AST.IntType) or isinstance(in_, AST.BoolType):
            frame.pop()
            return self.jvm.emitIRETURN()
        if isinstance(in_, AST.ArrayType) or isinstance(in_, AST.StructType) or isinstance(in_, AST.InterfaceType) or isinstance(in_, AST.StringType):
            frame.pop()
            return self.jvm.emitARETURN()
        if isinstance(in_, AST.FloatType):
            frame.pop()
            return self.jvm.emitFRETURN()

        return self.jvm.emitRETURN() # AST.VoidType

    ''' generate code that represents a label	
    *   @param label the label
    *   @return code Label<label>:
    '''
    def emitLABEL(self, label, frame):
        #label: Int
        #frame: Frame

        return self.jvm.emitLABEL(label)

    ''' generate code to jump to a label	
    *   @param label the label
    *   @return code goto Label<label>
    '''
    def emitGOTO(self, label, frame):
        #label: Int
        #frame: Frame

        return self.jvm.emitGOTO(label)

    ''' generate some starting directives for a class.<p>
    *   .source MPC.CLASSNAME.java<p>
    *   .class public MPC.CLASSNAME<p>
    *   .super java/lang/Object<p>
    '''
    def emitPROLOG(self, name, parent, is_abstract):
        #name: String
        #parent: String

        result = list()
        result.append(self.jvm.emitSOURCE(name + ".java"))
        result.append(self.jvm.emitCLASS(("public abstract interface " if is_abstract else "public ") + name))
        result.append(self.jvm.emitSUPER("java/lang/Object" if parent == "" else parent))
        return ''.join(result)

    def emitIMPLEMENTS(self, lexeme: str):
        return self.jvm.emitIMPLEMENTS(lexeme)

    def emitLIMITSTACK(self, num):
        #num: Int

        return self.jvm.emitLIMITSTACK(num)

    def emitLIMITLOCAL(self, num):
        #num: Int

        return self.jvm.emitLIMITLOCAL(num)

    def emitEPILOG(self):
        file = open(self.filename, "w")
        for b in self.buff:
            file.write(b)
        file.close()

    ''' print out the code to screen
    *   @param in the code to be printed out
    '''
    def printout(self, in_):
        #in_: String

        self.buff.append(in_)

    def clearBuff(self):
        self.buff.clear()

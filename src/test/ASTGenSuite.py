import unittest
from TestUtils import TestAST
from AST import *

class ASTGenSuite(unittest.TestCase):
    def test_empty(self):
        input = ""
        expect = "Program([])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1))

    # Struct declarations, 101..

    def test_struct_decl_1(self):
        input = """
            type Synchromach struct {HP int;}; type NghiaHo310Pf struct {HP int;}
            type Synchromach2 struct {HP int;}; type NghiaHo310Pf2 struct {HP int;}
        """
        expect = "Program([StructType(Synchromach,[(HP,IntType)],[]),StructType(NghiaHo310Pf,[(HP,IntType)],[]),StructType(Synchromach2,[(HP,IntType)],[]),StructType(NghiaHo310Pf2,[(HP,IntType)],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 101))

    def test_struct_decl_2(self):
        input = """
            type Synchromach struct {
                HP int
            }

            type NghiaHo310Pf struct {
                x int
                y int
                z int

                sizeHint SizeHint
                size Size
            }
        """
        expect = "Program([StructType(Synchromach,[(HP,IntType)],[]),StructType(NghiaHo310Pf,[(x,IntType),(y,IntType),(z,IntType),(sizeHint,Id(SizeHint)),(size,Id(Size))],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 102))

    def test_struct_decl_3(self):
        input = """
            type Synchromach struct {
                HP int
            };

            type Point struct {
                X float
                Y float
            }

            type Size struct {
                Width float
                Height float
            }

            type DimensionHint struct {
                Min float
                Expand float
            }

            type SizeHint struct {
                X DimensionHint
                Y DimensionHint
            }
        """
        expect = "Program([StructType(Synchromach,[(HP,IntType)],[]),StructType(Point,[(X,FloatType),(Y,FloatType)],[]),StructType(Size,[(Width,FloatType),(Height,FloatType)],[]),StructType(DimensionHint,[(Min,FloatType),(Expand,FloatType)],[]),StructType(SizeHint,[(X,Id(DimensionHint)),(Y,Id(DimensionHint))],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 103))

    def test_struct_decl_4(self):
        input = """
            type Synchromach struct {
                someIntergerArray [16]int
                someFloatGrid [32][32]float
            }
        """
        expect = "Program([StructType(Synchromach,[(someIntergerArray,ArrayType(IntType,[IntLiteral(16)])),(someFloatGrid,ArrayType(FloatType,[IntLiteral(32),IntLiteral(32)]))],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 104))

    # Interface declarations, 201..

    def test_interface_decl_1(self):
        input = """
            type Synchromach interface {
                Add() int
            }
        """
        expect = "Program([InterfaceType(Synchromach,[Prototype(Add,[],IntType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 201))

    def test_interface_decl_2(self):
        input = """
            type Synchromach interface {
                Add1() int
            }

            type NghiaHo310Pf interface {
                Add2() int
            }

            type OpaquePoint interface {
                GetX() float
                GetY() float

                GetLength() float
            }
        """
        expect = "Program([InterfaceType(Synchromach,[Prototype(Add1,[],IntType)]),InterfaceType(NghiaHo310Pf,[Prototype(Add2,[],IntType)]),InterfaceType(OpaquePoint,[Prototype(GetX,[],FloatType),Prototype(GetY,[],FloatType),Prototype(GetLength,[],FloatType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 202))

    def test_interface_decl_3(self):
        input = """
            type Widget interface {
                OnLoad(stack ResourceStack,
                    force boolean) boolean
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],BoolType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 203))

    def test_interface_decl_4(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                ComputeSizeHint() SizeHint
                SetSize(size Size)

                OnDraw(canvas Canvas)
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(ComputeSizeHint,[],Id(SizeHint)),Prototype(SetSize,[Id(Size)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 204))

    def test_interface_decl_6(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean,
                    notify boolean)
                OnUnload()

                ComputeSizeHint() SizeHint
                SetSize(size Size)

                OnDraw(canvas Canvas)
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType,BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(ComputeSizeHint,[],Id(SizeHint)),Prototype(SetSize,[Id(Size)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 205))

    # Function declarations & statements, 301..

    def test_func_decl_1(self):
        input = """
            func X1() {}
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 301))

    def test_func_decl_2(self):
        input = """
            func X1() {
            }
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 302))

    def test_func_decl_3(self):
        input = """
            func X1(
            ) {}
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 303))

    def test_func_decl_4(self):
        input = """
            func X1(
            ) {}
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 304))

    def test_func_decl_5(self):
        input = """ // Ai so thi di ve!!!
            func    // Ai so thi di ve!!!
            X1 (       // Ai so thi di ve!!!
            ) {       // Ai so thi di ve!!!
            }       // Ai so thi di ve!!!
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 305))

    def test_func_decl_6(self):
        input = """
            func X1() {
                ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
            }
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 306))

    def test_func_decl_7(self):
        input = """
            func X1() {;;;;;;;;};;;;;
        """
        expect = "Program([FuncDecl(X1,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 307))

    def test_func_decl_8(self):
        input = """
            func X1(x, y int) {}
        """
        expect = "Program([FuncDecl(X1,[ParDecl(x,IntType),ParDecl(y,IntType)],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 308))

    def test_func_decl_9(self):
        input = """
            func (canvas Canvas) X1(a, b, c string, d, e, f Size) {}
        """
        expect = "Program([MethodDecl(canvas,Id(Canvas),FuncDecl(X1,[ParDecl(a,StringType),ParDecl(b,StringType),ParDecl(c,StringType),ParDecl(d,Id(Size)),ParDecl(e,Id(Size)),ParDecl(f,Id(Size))],VoidType,Block([])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 309))

    def test_func_decl_10(self):
        input = """
            func (db Database) UselessMethod(
                uselessParam1 UselessType1, // !!
                uselessParam2 UselessType1, // !!
                uselessParam3 UselessType2, // !!
                uselessParam4 UselessType3, // !!
                uselessParam5 UselessType4, // !!
                _ UselessType5) {
                const x = uselessParam1.uselessField1
                var y = x +
                    uselessParam2[3] +
                    uselessParam3[4]
                var z = (
                    x + 1 - 2 * 3 / uselessParam4[5] % 6789)

                var q = 2
            }
        """
        expect = "Program([MethodDecl(db,Id(Database),FuncDecl(UselessMethod,[ParDecl(uselessParam1,Id(UselessType1)),ParDecl(uselessParam2,Id(UselessType1)),ParDecl(uselessParam3,Id(UselessType2)),ParDecl(uselessParam4,Id(UselessType3)),ParDecl(uselessParam5,Id(UselessType4)),ParDecl(_,Id(UselessType5))],VoidType,Block([ConstDecl(x,FieldAccess(Id(uselessParam1),uselessField1)),VarDecl(y,BinaryOp(BinaryOp(Id(x),+,ArrayCell(Id(uselessParam2),[IntLiteral(3)])),+,ArrayCell(Id(uselessParam3),[IntLiteral(4)]))),VarDecl(z,BinaryOp(BinaryOp(Id(x),+,IntLiteral(1)),-,BinaryOp(BinaryOp(BinaryOp(IntLiteral(2),*,IntLiteral(3)),/,ArrayCell(Id(uselessParam4),[IntLiteral(5)])),%,IntLiteral(6789)))),VarDecl(q,IntLiteral(2))])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 310))

    # Constant & variable declarations, 401..

    def test_const_decl_1(self):
        input = """
            const x = 1
            const y = 2
            const z = 3
        """
        expect = "Program([ConstDecl(x,IntLiteral(1)),ConstDecl(y,IntLiteral(2)),ConstDecl(z,IntLiteral(3))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 401))

    def test_const_decl_2(self):
        input = """
            const q Size = Size{x: 1, y: 2}
        """
        expect = "Program([ConstDecl(q,Id(Size),StructLiteral(Size,[(x,IntLiteral(1)),(y,IntLiteral(2))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 402))

    def test_const_decl_3(self):
        input = """
            const x float
        """
        expect = "Program([ConstDecl(x,FloatType,None)])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 403))

    def test_const_decl_4(self):
        input = """
            const z string = selectOneOf("hello", "there")
        """
        expect = "Program([ConstDecl(z,StringType,FuncCall(selectOneOf,[StringLiteral(\"hello\"),StringLiteral(\"there\")]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 404))

    def test_const_decl_5(self):
        input = """
            const shader ShaderModule = shaderModuleFromFile("s.spv")
        """
        expect = "Program([ConstDecl(shader,Id(ShaderModule),FuncCall(shaderModuleFromFile,[StringLiteral(\"s.spv\")]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 405))

    def test_var_decl_1(self):
        input = """
            var x = 1
            var y = 2
            var z = 3
        """
        expect = "Program([VarDecl(x,IntLiteral(1)),VarDecl(y,IntLiteral(2)),VarDecl(z,IntLiteral(3))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 406))

    def test_var_decl_2(self):
        input = """
            var q Size = Size{x: 1, y: 2}
        """
        expect = "Program([VarDecl(q,Id(Size),StructLiteral(Size,[(x,IntLiteral(1)),(y,IntLiteral(2))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 407))

    def test_var_decl_3(self):
        input = """
            var x float
        """
        expect = "Program([VarDecl(x,FloatType)])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 408))

    def test_var_decl_4(self):
        input = """
            var z string = selectOneOf("hello", "there")
        """
        expect = "Program([VarDecl(z,StringType,FuncCall(selectOneOf,[StringLiteral(\"hello\"),StringLiteral(\"there\")]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 409))

    def test_var_decl_5(self):
        input = """
            var shader ShaderModule = shaderModuleFromFile("s.spv")
        """
        expect = "Program([VarDecl(shader,Id(ShaderModule),FuncCall(shaderModuleFromFile,[StringLiteral(\"s.spv\")]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 410))

    # Expressions, 501..

    def test_expression_1(self):
        input = """
            var z = 1 + 1
        """
        expect = "Program([VarDecl(z,BinaryOp(IntLiteral(1),+,IntLiteral(1)))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 501))

    def test_expression_2(self):
        input = """
            var z = 2 * 2 + 4 - 48
        """
        expect = "Program([VarDecl(z,BinaryOp(BinaryOp(BinaryOp(IntLiteral(2),*,IntLiteral(2)),+,IntLiteral(4)),-,IntLiteral(48)))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 502))

    def test_expression_3(self):
        input = """
            var z VkDescriptorSetLayoutCreateInfo = VkDescriptorSetLayoutCreateInfo{}
        """
        expect = "Program([VarDecl(z,Id(VkDescriptorSetLayoutCreateInfo),StructLiteral(VkDescriptorSetLayoutCreateInfo,[]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 503))

    def test_expression_4(self):
        input = """
            var z float = 2.0 * 4.0 - 6.0 / 8.0
        """
        expect = "Program([VarDecl(z,FloatType,BinaryOp(BinaryOp(FloatLiteral(2.0),*,FloatLiteral(4.0)),-,BinaryOp(FloatLiteral(6.0),/,FloatLiteral(8.0))))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 504))

    def test_expression_5(self):
        input = """
            var z string = "hello"
        """
        expect = "Program([VarDecl(z,StringType,StringLiteral(\"hello\"))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 505))

    def test_expression_6(self):
        input = """
            var z boolean = 16 < 32
        """
        expect = "Program([VarDecl(z,BoolType,BinaryOp(IntLiteral(16),<,IntLiteral(32)))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 506))

    def test_expression_7(self):
        input = """
            var z = (
                getThisThing() *
                getThatOtherThing() *
                variousOtherThings())
        """
        expect = "Program([VarDecl(z,BinaryOp(BinaryOp(FuncCall(getThisThing,[]),*,FuncCall(getThatOtherThing,[])),*,FuncCall(variousOtherThings,[])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 507))

    def test_expression_8(self):
        input = """
            var z = launch(Options{leaveNoSurvivors: true})
        """
        expect = "Program([VarDecl(z,FuncCall(launch,[StructLiteral(Options,[(leaveNoSurvivors,BooleanLiteral(true))])]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 508))

    def test_expression_9(self):
        input = """
            var z = launch(Options{leaveNoSurvivors: !checkAnyHopeLeft()})
        """
        expect = "Program([VarDecl(z,FuncCall(launch,[StructLiteral(Options,[(leaveNoSurvivors,UnaryOp(!,FuncCall(checkAnyHopeLeft,[])))])]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 509))

    def test_expression_10(self):
        input = """
            var z = exit()
        """
        expect = "Program([VarDecl(z,FuncCall(exit,[]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 510))

    def test_expression_11(self):
        input = """
            var z = 1 + 1
        """
        expect = "Program([VarDecl(z,BinaryOp(IntLiteral(1),+,IntLiteral(1)))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 511))

    def test_expression_12(self):
        input = """
            var z = arr[2 * 2 + 4 - 48].field1
        """
        expect = "Program([VarDecl(z,FieldAccess(ArrayCell(Id(arr),[BinaryOp(BinaryOp(BinaryOp(IntLiteral(2),*,IntLiteral(2)),+,IntLiteral(4)),-,IntLiteral(48))]),field1))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 512))

    def test_expression_13(self):
        input = """
            func main() {
                var z VkDescriptorSetLayoutCreateInfo = VkDescriptorSetLayoutCreateInfo{sType: VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO}
                z.bindingCount := bindings
                z.pBindings := bindings.data()
            }
        """
        expect = "Program([FuncDecl(main,[],VoidType,Block([VarDecl(z,Id(VkDescriptorSetLayoutCreateInfo),StructLiteral(VkDescriptorSetLayoutCreateInfo,[(sType,Id(VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO))])),Assign(FieldAccess(Id(z),bindingCount),Id(bindings)),Assign(FieldAccess(Id(z),pBindings),MethodCall(Id(bindings),data,[]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 513))

    def test_expression_14(self):
        input = """
            func main() {
                var pushConstantRange VkPushConstantRange = VkPushConstantRange{}
                pushConstantRange.offset := 0
                pushConstantRange.size := sizeof(HudPushConstants)
                pushConstantRange.stageFlags := VK_SHADER_STAGE_VERTEX_BIT || VK_SHADER_STAGE_FRAGMENT_BIT
            }
        """
        expect = "Program([FuncDecl(main,[],VoidType,Block([VarDecl(pushConstantRange,Id(VkPushConstantRange),StructLiteral(VkPushConstantRange,[])),Assign(FieldAccess(Id(pushConstantRange),offset),IntLiteral(0)),Assign(FieldAccess(Id(pushConstantRange),size),FuncCall(sizeof,[Id(HudPushConstants)])),Assign(FieldAccess(Id(pushConstantRange),stageFlags),BinaryOp(Id(VK_SHADER_STAGE_VERTEX_BIT),||,Id(VK_SHADER_STAGE_FRAGMENT_BIT)))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 514))

    def test_expression_15(self):
        input = """
            var z string = stringFromCodePoint("hello"[1].toString()[0] * 3 - 4)
        """
        expect = "Program([VarDecl(z,StringType,FuncCall(stringFromCodePoint,[BinaryOp(BinaryOp(ArrayCell(MethodCall(ArrayCell(StringLiteral(\"hello\"),[IntLiteral(1)]),toString,[]),[IntLiteral(0)]),*,IntLiteral(3)),-,IntLiteral(4))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 515))

    def test_expression_16(self):
        input = """
            var z boolean = a[1].f2[3][4][5].f3()[6] - 7 < b[9][10].f11().f12[13][14][15].f16()[17] - 18
        """
        expect = "Program([VarDecl(z,BoolType,BinaryOp(BinaryOp(ArrayCell(MethodCall(ArrayCell(FieldAccess(ArrayCell(Id(a),[IntLiteral(1)]),f2),[IntLiteral(3),IntLiteral(4),IntLiteral(5)]),f3,[]),[IntLiteral(6)]),-,IntLiteral(7)),<,BinaryOp(ArrayCell(MethodCall(ArrayCell(FieldAccess(MethodCall(ArrayCell(Id(b),[IntLiteral(9),IntLiteral(10)]),f11,[]),f12),[IntLiteral(13),IntLiteral(14),IntLiteral(15)]),f16,[]),[IntLiteral(17)]),-,IntLiteral(18))))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 516))

    def test_expression_17(self):
        input = """
            var z = (
                (
                 a[1].f2[3][4][5].f3()[6] - 7 + b[9][10].f11().f12[13][14][15].f16()[17] - 18) *
                getThatOtherThing() *
                variousOtherThings())
        """
        expect = "Program([VarDecl(z,BinaryOp(BinaryOp(BinaryOp(BinaryOp(BinaryOp(ArrayCell(MethodCall(ArrayCell(FieldAccess(ArrayCell(Id(a),[IntLiteral(1)]),f2),[IntLiteral(3),IntLiteral(4),IntLiteral(5)]),f3,[]),[IntLiteral(6)]),-,IntLiteral(7)),+,ArrayCell(MethodCall(ArrayCell(FieldAccess(MethodCall(ArrayCell(Id(b),[IntLiteral(9),IntLiteral(10)]),f11,[]),f12),[IntLiteral(13),IntLiteral(14),IntLiteral(15)]),f16,[]),[IntLiteral(17)])),-,IntLiteral(18)),*,FuncCall(getThatOtherThing,[])),*,FuncCall(variousOtherThings,[])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 517))

    def test_expression_19(self):
        input = """
            var /* */
            z /* */ =
                1 /* */ +
                /* */ 2 + //
                3 /* */ + //
                /* */ 4 + //
                5 /* */ + //
                6
        """
        expect = "Program([VarDecl(z,BinaryOp(BinaryOp(BinaryOp(BinaryOp(BinaryOp(IntLiteral(1),+,IntLiteral(2)),+,IntLiteral(3)),+,IntLiteral(4)),+,IntLiteral(5)),+,IntLiteral(6)))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 519))

    def test_expression_20(self):
        input = """
            var z [3]int = [3]int{1, 2, 3}
        """
        expect = "Program([VarDecl(z,ArrayType(IntType,[IntLiteral(3)]),ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(1),IntLiteral(2),IntLiteral(3)]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 520))

    # Code blocks, 601..

    def test_codeblock_1(self):
        input = """
            func x() {}
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 601))

    def test_codeblock_2(self):
        input = """
            func x() {
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 602))

    def test_codeblock_3(self):
        input = """
            func x(
            ) {
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 603))

    def test_codeblock_4(self):
        input = """
            func x() {
                //
                /* */
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 604))

    def test_codeblock_5(self):
        input = """
            func x() {
                y(1+1)
                y(2+2)
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([FuncCall(y,[BinaryOp(IntLiteral(1),+,IntLiteral(1))]),FuncCall(y,[BinaryOp(IntLiteral(2),+,IntLiteral(2))])]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 605))

    def test_codeblock_6(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 606))

    def test_codeblock_7(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 607))

    def test_codeblock_8(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
                const constant1 = 1
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3)),ConstDecl(constant1,IntLiteral(1))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 608))

    def test_codeblock_9(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
                const constant1 = 1
                const constant2 = 2
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3)),ConstDecl(constant1,IntLiteral(1)),ConstDecl(constant2,IntLiteral(2))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 609))

    def test_codeblock_10(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
                const constant1 = 1
                const constant2 = 2
            }

            func y() {
                const constant1 = 1
                const constant2 = 2

                var local1 = 1
                var local2 = 2
                var local3 = 3
            }

            func z() {
                const constant1 = 1
                const constant2 = 2;
                const constant3 = 3

                var local1 = 1
                var local2 = 2;
                var local3 = 3
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3)),ConstDecl(constant1,IntLiteral(1)),ConstDecl(constant2,IntLiteral(2))])),FuncDecl(y,[],VoidType,Block([ConstDecl(constant1,IntLiteral(1)),ConstDecl(constant2,IntLiteral(2)),VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3))])),FuncDecl(z,[],VoidType,Block([ConstDecl(constant1,IntLiteral(1)),ConstDecl(constant2,IntLiteral(2)),ConstDecl(constant3,IntLiteral(3)),VarDecl(local1,IntLiteral(1)),VarDecl(local2,IntLiteral(2)),VarDecl(local3,IntLiteral(3))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 610))

    # Loops, 701..

    def test_loop_1(self):
        input = """
            func x() {
                var x = 1
                for x < 10 {
                    x := random()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(x,IntLiteral(1)),For(BinaryOp(Id(x),<,IntLiteral(10)),Block([Assign(Id(x),FuncCall(random,[]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 701))

    def test_loop_2(self):
        input = """
            func x() {
                var x = 1
                for x + 10 > 20 {
                    x := random()
                    y := 2
                    for y < 4 {
                        y += x
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(x,IntLiteral(1)),For(BinaryOp(BinaryOp(Id(x),+,IntLiteral(10)),>,IntLiteral(20)),Block([Assign(Id(x),FuncCall(random,[])),Assign(Id(y),IntLiteral(2)),For(BinaryOp(Id(y),<,IntLiteral(4)),Block([Assign(Id(y),BinaryOp(Id(y),+,Id(x)))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 702))

    def test_loop_3(self):
        input = """
            func x() {
                var x = 1
                for x + 10 > 20 {
                    x := random()
                    y := 2
                    for y < 4 {
                        y += x
                        for y < 4 {
                            y += x
                            for y < 4 {
                                y += x
                                y += x
                                y += x
                                y += x
                                y += x
                            }
                        }
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([VarDecl(x,IntLiteral(1)),For(BinaryOp(BinaryOp(Id(x),+,IntLiteral(10)),>,IntLiteral(20)),Block([Assign(Id(x),FuncCall(random,[])),Assign(Id(y),IntLiteral(2)),For(BinaryOp(Id(y),<,IntLiteral(4)),Block([Assign(Id(y),BinaryOp(Id(y),+,Id(x))),For(BinaryOp(Id(y),<,IntLiteral(4)),Block([Assign(Id(y),BinaryOp(Id(y),+,Id(x))),For(BinaryOp(Id(y),<,IntLiteral(4)),Block([Assign(Id(y),BinaryOp(Id(y),+,Id(x))),Assign(Id(y),BinaryOp(Id(y),+,Id(x))),Assign(Id(y),BinaryOp(Id(y),+,Id(x))),Assign(Id(y),BinaryOp(Id(y),+,Id(x))),Assign(Id(y),BinaryOp(Id(y),+,Id(x)))]))]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 703))

    def test_loop_4(self):
        input = """
            func x() {
                for var x = 0; x < 10; x += 1 {
                    print(x)
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([For(VarDecl(x,IntLiteral(0)),BinaryOp(Id(x),<,IntLiteral(10)),Assign(Id(x),BinaryOp(Id(x),+,IntLiteral(1))),Block([FuncCall(print,[Id(x)])]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 704))

    def test_loop_5(self):
        input = """
            func x() {
                for var x = 0; x < 10; x += 1 {
                    for var y = 0; y < 10; y += 1 {
                        print(x + y)
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([For(VarDecl(x,IntLiteral(0)),BinaryOp(Id(x),<,IntLiteral(10)),Assign(Id(x),BinaryOp(Id(x),+,IntLiteral(1))),Block([For(VarDecl(y,IntLiteral(0)),BinaryOp(Id(y),<,IntLiteral(10)),Assign(Id(y),BinaryOp(Id(y),+,IntLiteral(1))),Block([FuncCall(print,[BinaryOp(Id(x),+,Id(y))])]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 705))

    def test_loop_6(self):
        input = """
            func x() {
                for var x = 0; x < 10; x += 1 {
                    for var y = 0; y < 10; y += 1 {
                        for var z = 0; z < 10; z += 1 {
                            print(x + y + z)
                        }
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([For(VarDecl(x,IntLiteral(0)),BinaryOp(Id(x),<,IntLiteral(10)),Assign(Id(x),BinaryOp(Id(x),+,IntLiteral(1))),Block([For(VarDecl(y,IntLiteral(0)),BinaryOp(Id(y),<,IntLiteral(10)),Assign(Id(y),BinaryOp(Id(y),+,IntLiteral(1))),Block([For(VarDecl(z,IntLiteral(0)),BinaryOp(Id(z),<,IntLiteral(10)),Assign(Id(z),BinaryOp(Id(z),+,IntLiteral(1))),Block([FuncCall(print,[BinaryOp(BinaryOp(Id(x),+,Id(y)),+,Id(z))])]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 706))

    def test_loop_7(self):
        input = """
            func x() {
                for i, v := range [2]int{2, 4} {
                    print(i + v)
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([FuncCall(print,[BinaryOp(Id(i),+,Id(v))])]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 707))

    def test_loop_8(self):
        input = """
            func x() {
                for var x = 0; x < 10; x += 1 {
                    for i, v := range [2]int{2, 4} {
                        print(i + v)
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([For(VarDecl(x,IntLiteral(0)),BinaryOp(Id(x),<,IntLiteral(10)),Assign(Id(x),BinaryOp(Id(x),+,IntLiteral(1))),Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([FuncCall(print,[BinaryOp(Id(i),+,Id(v))])]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 708))

    def test_loop_9(self):
        input = """
            func x() {
                for i, v := range [2]int{2, 4} {
                    for z, q := range [3]int{2, 4, 6} {
                        print(i * z + v * q)
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([ForEach(Id(z),Id(q),ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(2),IntLiteral(4),IntLiteral(6)]),Block([FuncCall(print,[BinaryOp(BinaryOp(Id(i),*,Id(z)),+,BinaryOp(Id(v),*,Id(q)))])]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 709))

    def test_loop_10(self):
        input = """
            func x() {
                for i, v := range [2]int{2, 4} {
                    for z, q := range [3]int{2, 4, 6} {
                        print(i * z + v * q)
                        var a = i
                        for a < 10 {
                            a -= z
                            print(a)
                        }
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([ForEach(Id(z),Id(q),ArrayLiteral([IntLiteral(3)],IntType,[IntLiteral(2),IntLiteral(4),IntLiteral(6)]),Block([FuncCall(print,[BinaryOp(BinaryOp(Id(i),*,Id(z)),+,BinaryOp(Id(v),*,Id(q)))]),VarDecl(a,Id(i)),For(BinaryOp(Id(a),<,IntLiteral(10)),Block([Assign(Id(a),BinaryOp(Id(a),-,Id(z))),FuncCall(print,[Id(a)])]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 710))

    # Conditionals, 801..

    def test_conditional_1(self):
        input = """
            func x() {
                if (a > b) {
                    c()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 801))

    def test_conditional_2(self):
        input = """
            func x() {
                if (a > b) {
                    c()
                } else {
                    d()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([FuncCall(d,[])]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 802))

    def test_conditional_3(self):
        input = """
            func x() {
                if (a > b) {
                    c()
                } else if (e > f) {
                    d()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 803))

    def test_conditional_4(self):
        input = """
            func x() {
                if (a > b) {
                    c()
                } else if (e > f) {
                    d()
                } else if (g < h) {
                    i()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 804))

    def test_conditional_5(self):
        input = """
            func x() {
                if (a > b) {
                    if (a > b) {
                        c()
                    } else if (e > f) {
                        d()
                    } else if (g < h) {
                        i()
                    }
                } else if (e > f) {
                    d()
                } else if (g < h) {
                    i()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 805))

    def test_conditional_6(self):
        input = """
            func x() {
                if (a > b) {
                    if (a > b) {
                        c()
                    } else if (e > f) {
                        if (a > b) {
                            if (a > b) {
                                c()
                            } else if (e > f) {
                                d()
                            } else if (g < h) {
                                i()
                            }
                        } else if (e > f) {
                            d()
                        } else if (g < h) {
                            i()
                        }
                    } else if (g < h) {
                        i()
                    }
                } else if (e > f) {
                    d()
                } else if (g < h) {
                    i()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([If(BinaryOp(Id(a),>,Id(b)),Block([If(BinaryOp(Id(a),>,Id(b)),Block([FuncCall(c,[])]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([FuncCall(d,[])]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([FuncCall(i,[])]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 806))

    def test_conditional_7(self):
        input = """
            func x() {
                if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else if (true) { // Ai so thi di ve!!!
                } else {} // Ai so thi di ve!!!
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([If(BooleanLiteral(true),Block([]),Block([]))]))]))]))]))]))]))]))]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 807))

    def test_conditional_8(self):
        input = """
            func x() { // Ai so thi di ve!!!
                if (1) { // Ai so thi di ve!!!
                } else // Ai so thi di ve!!!
                {} // Ai so thi di ve!!!
            } // Ai so thi di ve!!!
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(IntLiteral(1),Block([]),Block([]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 808))

    def test_conditional_9(self):
        input = """
            func x() { // Ai so thi di ve!!!
                if // Ai so thi di ve!!!
                ( // Ai so thi di ve!!!
                    1) { // Ai so thi di ve!!!
                } else // Ai so thi di ve!!!
                { // Ai so thi di ve!!!
                } // Ai so thi di ve!!!
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(IntLiteral(1),Block([]),Block([]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 809))

    def test_conditional_10(self):
        input = """
            func x() { // Ai so thi di ve!!!
            /* ASDASDASD */    if // Ai so thi di ve!!!
            /* ASDASDASD */    ( // Ai so thi di ve!!!
            /* ASDASDASD */        1) { // Ai so thi di ve!!!
            /* ASDASDASD */    } else // Ai so thi di ve!!!
            /* ASDASDASD */    { // Ai so thi di ve!!!
            /* ASDASDASD */    } // Ai so thi di ve!!!
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([If(IntLiteral(1),Block([]),Block([]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 810))

    # Break, continue, return, 901..

    def test_bcr_1(self):
        input = """
            func x() int {
                return 2
            }
        """
        expect = "Program([FuncDecl(x,[],IntType,Block([Return(IntLiteral(2))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 901))

    def test_bcr_2(self):
        input = """
            func x() float {
                return 4.0
            }
        """
        expect = "Program([FuncDecl(x,[],FloatType,Block([Return(FloatLiteral(4.0))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 902))

    def test_bcr_3(self):
        input = """
            func x() int {
                return 3
            }
        """
        expect = "Program([FuncDecl(x,[],IntType,Block([Return(IntLiteral(3))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 903))

    def test_bcr_4(self):
        input = """
            func x() string {
                if (a > b) {
                    return c()
                } else if (e > f) {
                    return d()
                } else if (g < h) {
                    return i()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],StringType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([Return(FuncCall(c,[]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([Return(FuncCall(d,[]))]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([Return(FuncCall(i,[]))]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 904))

    def test_bcr_5(self):
        input = """
            func x() string {
                if (a > b) {
                    if (a > b) {
                        return c()
                    } else if (e > f) {
                        return d()
                    } else if (g < h) {
                        return i()
                    }
                } else if (e > f) {
                    return d()
                } else if (g < h) {
                    return i()
                }
            }
        """
        expect = "Program([FuncDecl(x,[],StringType,Block([If(BinaryOp(Id(a),>,Id(b)),Block([If(BinaryOp(Id(a),>,Id(b)),Block([Return(FuncCall(c,[]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([Return(FuncCall(d,[]))]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([Return(FuncCall(i,[]))]))]))]))]),Block([If(BinaryOp(Id(e),>,Id(f)),Block([Return(FuncCall(d,[]))]),Block([If(BinaryOp(Id(g),<,Id(h)),Block([Return(FuncCall(i,[]))]))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 905))

    def test_bcr_6(self):
        input = """
            func x(y Size) float {
                if (y.Area() > 20) {
                    return 0.0;
                }

                return y.Area()
            }
        """
        expect = "Program([FuncDecl(x,[ParDecl(y,Id(Size))],FloatType,Block([If(BinaryOp(MethodCall(Id(y),Area,[]),>,IntLiteral(20)),Block([Return(FloatLiteral(0.0))])),Return(MethodCall(Id(y),Area,[]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 906))

    def test_bcr_7(self):
        input = """
            func x() int {
                for i, v := range [2]int{2, 4} {
                    break
                    continue
                    return 1
                }
            }
        """
        expect = "Program([FuncDecl(x,[],IntType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([Break(),Continue(),Return(IntLiteral(1))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 907))

    def test_bcr_8(self):
        input = """
            func x() int {
                for i, v := range [2]int{2, 4} {
                    if (v == 2) {
                        return i
                    }
                }
                return -1
            }
        """
        expect = "Program([FuncDecl(x,[],IntType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([If(BinaryOp(Id(v),==,IntLiteral(2)),Block([Return(Id(i))]))])),Return(UnaryOp(-,IntLiteral(1)))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 908))

    def test_bcr_9(self):
        input = """
            func x() { // Ai so thi di ve!!!
                for i, v := range [2]int{2, 4} {
                    if (v < 2) {
                        continue
                    }
                    print(v)
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([If(BinaryOp(Id(v),<,IntLiteral(2)),Block([Continue()])),FuncCall(print,[Id(v)])]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 909))

    def test_bcr_10(self):
        input = """
            func x() { // Ai so thi di ve!!!
                for i, v := range [2]int{2, 4} {
                    if (v < 2) {
                        continue
                    }
                    print(v)
                    if (v > 4) {
                        return 7
                    }
                }
            }
        """
        expect = "Program([FuncDecl(x,[],VoidType,Block([ForEach(Id(i),Id(v),ArrayLiteral([IntLiteral(2)],IntType,[IntLiteral(2),IntLiteral(4)]),Block([If(BinaryOp(Id(v),<,IntLiteral(2)),Block([Continue()])),FuncCall(print,[Id(v)]),If(BinaryOp(Id(v),>,IntLiteral(4)),Block([Return(IntLiteral(7))]))]))]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 910))

    # Usual programs. 1001..

    def test_usual_program_1(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1001))

    def test_usual_program_2(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1002))

    def test_usual_program_3(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint))],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1003))

    def test_usual_program_4(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[])])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1004))

    def test_usual_program_5(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }

            func (mw MyWidget) OnLoad(stack ResourceStack) {
                // TODO
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack))],VoidType,Block([])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1005))

    def test_usual_program_6(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }

            func (mw MyWidget) OnLoad(
                stack ResourceStack,
                force boolean) {
                // TODO
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1006))

    def test_usual_program_7(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }

            func (mw MyWidget) OnLoad(
                stack ResourceStack,
                force boolean) {
                // TODO
            }

            func (mw MyWidget) OnUnload() {
                // TODO
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUnload,[],VoidType,Block([])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1007))

    def test_usual_program_8(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }

            func (mw MyWidget) OnLoad(
                stack ResourceStack,
                force boolean) {
                // TODO
            }

            func (mw MyWidget) OnUnload() {
                // TODO
            }

            func (mw MyWidget) OnUpdate() {
                println("update")
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUnload,[],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUpdate,[],VoidType,Block([FuncCall(println,[StringLiteral(\"update\")])])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1008))

    def test_usual_program_9(self):
        input = """
            type Widget interface {
                OnLoad(
                    stack ResourceStack,
                    force boolean)
                OnUnload()

                OnUpdate()
                OnInput(event InputEvent)

                OnDraw(canvas Canvas)
            }

            type MyWidget struct {
                fixedSizeHint SizeHint
                currentSize Size
            }

            func (mw MyWidget) OnLoad(
                stack ResourceStack,
                force boolean) {
                // TODO
            }

            func (mw MyWidget) OnUnload() {
                // TODO
            }

            func (mw MyWidget) OnUpdate() {
                println("update")
            }

            func (mw MyWidget) OnInput(event InputEvent) {
                println("Got an event:")
                println(event.toString())
            }
        """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUnload,[],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUpdate,[],VoidType,Block([FuncCall(println,[StringLiteral(\"update\")])]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnInput,[ParDecl(event,Id(InputEvent))],VoidType,Block([FuncCall(println,[StringLiteral(\"Got an event:\")]),FuncCall(println,[MethodCall(Id(event),toString,[])])])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1009))

    def test_usual_program_10(self):
        input = """
                    type Widget interface {
                        OnLoad(
                            stack ResourceStack,
                            force boolean)
                        OnUnload()

                        OnUpdate()
                        OnInput(event InputEvent)

                        OnDraw(canvas Canvas)
                    }

                    type MyWidget struct {
                        fixedSizeHint SizeHint
                        currentSize Size
                    }

                    func (mw MyWidget) OnLoad(
                        stack ResourceStack,
                        force boolean) {
                        // TODO
                    }

                    func (mw MyWidget) OnUnload() {
                        // TODO
                    }

                    func (mw MyWidget) OnUpdate() {
                        println("update")
                    }

                    func (mw MyWidget) OnInput(event InputEvent) {
                        println(event.toString())
                    }

                    func (mw MyWidget) OnDraw(canvas Canvas) {
                        canvas.drawRect(currentSize.toRect(), makeBluePaint())
                    }
                """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUnload,[],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUpdate,[],VoidType,Block([FuncCall(println,[StringLiteral(\"update\")])]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnInput,[ParDecl(event,Id(InputEvent))],VoidType,Block([FuncCall(println,[MethodCall(Id(event),toString,[])])]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnDraw,[ParDecl(canvas,Id(Canvas))],VoidType,Block([MethodCall(Id(canvas),drawRect,[MethodCall(Id(currentSize),toRect,[]),FuncCall(makeBluePaint,[])])])))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1010))

    def test_usual_program_11(self):
        input = """
                    type Widget interface {
                        OnLoad(
                            stack ResourceStack,
                            force boolean)
                        OnUnload()

                        OnUpdate()
                        OnInput(event InputEvent)

                        OnDraw(canvas Canvas)
                    }

                    type MyWidget struct {
                        fixedSizeHint SizeHint
                        currentSize Size
                    }

                    func (mw MyWidget) OnLoad(
                        stack ResourceStack,
                        force boolean) {
                        // TODO
                    }

                    func (mw MyWidget) OnUnload() {
                        // TODO
                    }

                    func (mw MyWidget) OnUpdate() {
                        println("update")
                    }

                    func (mw MyWidget) OnInput(event InputEvent) {
                        println(event.toString())
                    }

                    func (mw MyWidget) OnDraw(canvas Canvas) {
                        canvas.drawRect(currentSize.toRect(), makeBluePaint())
                    }

                    func main() {
                        var framework Framework = makeFramework()
                        framework.setTopLevelWidget(MyWidget{})
                    }
                """
        expect = "Program([InterfaceType(Widget,[Prototype(OnLoad,[Id(ResourceStack),BoolType],VoidType),Prototype(OnUnload,[],VoidType),Prototype(OnUpdate,[],VoidType),Prototype(OnInput,[Id(InputEvent)],VoidType),Prototype(OnDraw,[Id(Canvas)],VoidType)]),StructType(MyWidget,[(fixedSizeHint,Id(SizeHint)),(currentSize,Id(Size))],[]),MethodDecl(mw,Id(MyWidget),FuncDecl(OnLoad,[ParDecl(stack,Id(ResourceStack)),ParDecl(force,BoolType)],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUnload,[],VoidType,Block([]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnUpdate,[],VoidType,Block([FuncCall(println,[StringLiteral(\"update\")])]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnInput,[ParDecl(event,Id(InputEvent))],VoidType,Block([FuncCall(println,[MethodCall(Id(event),toString,[])])]))),MethodDecl(mw,Id(MyWidget),FuncDecl(OnDraw,[ParDecl(canvas,Id(Canvas))],VoidType,Block([MethodCall(Id(canvas),drawRect,[MethodCall(Id(currentSize),toRect,[]),FuncCall(makeBluePaint,[])])]))),FuncDecl(main,[],VoidType,Block([VarDecl(framework,Id(Framework),FuncCall(makeFramework,[])),MethodCall(Id(framework),setTopLevelWidget,[StructLiteral(MyWidget,[])])]))])"
        self.assertTrue(TestAST.checkASTGen(input, expect, 1011))
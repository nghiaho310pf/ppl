import unittest
from TestUtils import TestParser

class ParserSuite(unittest.TestCase):
    def test_empty(self):
        input = ""
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,1))

    # Struct declarations, 101..

    def test_struct_decl_1(self):
        input = """
            type Synchromach struct {HP int;}; type NghiaHo310Pf struct {HP int;}
            type Synchromach2 struct {HP int;}; type NghiaHo310Pf2 struct {HP int;}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,101))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,102))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,103))

    def test_struct_decl_4(self):
        input = """
            type Synchromach struct {
                someIntergerArray [16]int
                someFloatGrid [32][32]float
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,104))

    # Interface declarations, 201..

    def test_interface_decl_1(self):
        input = """
            type Synchromach interface {
                Add() int
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,201))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,202))

    def test_interface_decl_3(self):
        input = """
            type Widget interface {
                OnLoad(stack ResourceStack,
                    force boolean) boolean
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,203))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,204))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,205))

    # Function declarations & statements, 301..

    def test_func_decl_1(self):
        input = """
            func X1() {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,301))

    def test_func_decl_2(self):
        input = """
            func X1() {
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,302))

    def test_func_decl_3(self):
        input = """
            func X1(
            ) {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,303))

    def test_func_decl_4(self):
        input = """
            func X1(
            ) {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,304))

    def test_func_decl_5(self):
        input = """ // Ai so thi di ve!!!
            func    // Ai so thi di ve!!!
            X1 (       // Ai so thi di ve!!!
            ) {       // Ai so thi di ve!!!
            }       // Ai so thi di ve!!!
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,305))

    def test_func_decl_6(self):
        input = """
            func X1() {
                ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,306))

    def test_func_decl_7(self):
        input = """
            func X1() {;;;;;;;;};;;;;
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,307))

    def test_func_decl_8(self):
        input = """
            func X1(x, y int) {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,308))

    def test_func_decl_9(self):
        input = """
            func (canvas Canvas) X1(a, b, c string, d, e, f Size) {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,309))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,310))

    # Constant & variable declarations, 401..

    def test_const_decl_1(self):
        input = """
            const x = 1
            const y = 2
            const z = 3
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,401))

    def test_const_decl_2(self):
        input = """
            const q Size = Size{x: 1, y: 2}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,402))

    def test_const_decl_3(self):
        input = """
            const x float
        """
        expect = "Error on line 2 col 26: ;"
        self.assertTrue(TestParser.checkParser(input,expect,403))

    def test_const_decl_4(self):
        input = """
            const z string = selectOneOf("hello", "there")
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,404))

    def test_const_decl_5(self):
        input = """
            const shader ShaderModule = shaderModuleFromFile("s.spv")
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,405))

    def test_var_decl_1(self):
        input = """
            var x = 1
            var y = 2
            var z = 3
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,406))

    def test_var_decl_2(self):
        input = """
            var q Size = Size{x: 1, y: 2}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,407))

    def test_var_decl_3(self):
        input = """
            var x float
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,408))

    def test_var_decl_4(self):
        input = """
            var z string = selectOneOf("hello", "there")
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,409))

    def test_var_decl_5(self):
        input = """
            var shader ShaderModule = shaderModuleFromFile("s.spv")
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,410))

    # Expressions, 501..

    def test_expression_1(self):
        input = """
            var z = 1 + 1
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,501))

    def test_expression_2(self):
        input = """
            var z = 2 * 2 + 4 - 48
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,502))

    def test_expression_3(self):
        input = """
            var z VkDescriptorSetLayoutCreateInfo = VkDescriptorSetLayoutCreateInfo{}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,503))

    def test_expression_4(self):
        input = """
            var z float = 2.0 * 4.0 - 6.0 / 8.0
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,504))

    def test_expression_5(self):
        input = """
            var z string = "hello"
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,505))

    def test_expression_6(self):
        input = """
            var z boolean = 16 < 32
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,506))

    def test_expression_7(self):
        input = """
            var z = (
                getThisThing() *
                getThatOtherThing() *
                variousOtherThings())
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,507))

    def test_expression_8(self):
        input = """
            var z = launch(Options{leaveNoSurvivors: true})
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,508))

    def test_expression_9(self):
        input = """
            var z = launch(Options{leaveNoSurvivors: !checkAnyHopeLeft()})
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,509))

    def test_expression_10(self):
        input = """
            var z = exit()
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,510))

    def test_expression_11(self):
        input = """
            var z = 1 + 1
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,511))

    def test_expression_12(self):
        input = """
            var z = arr[2 * 2 + 4 - 48].field1
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,512))

    def test_expression_13(self):
        input = """
            func main() {
                var z VkDescriptorSetLayoutCreateInfo = VkDescriptorSetLayoutCreateInfo{sType: VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO}
                z.bindingCount := bindings
                z.pBindings := bindings.data()
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,513))

    def test_expression_14(self):
        input = """
            func main() {
                var pushConstantRange VkPushConstantRange = VkPushConstantRange{}
                pushConstantRange.offset := 0
                pushConstantRange.size := sizeof(HudPushConstants)
                pushConstantRange.stageFlags := VK_SHADER_STAGE_VERTEX_BIT || VK_SHADER_STAGE_FRAGMENT_BIT
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,514))

    def test_expression_15(self):
        input = """
            var z string = stringFromCodePoint("hello"[1].toString()[0] * 3 - 4)
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,515))

    def test_expression_16(self):
        input = """
            var z boolean = a[1].f2[3][4][5].f3()[6] - 7 < b[9][10].f11().f12[13][14][15].f16()[17] - 18
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,516))

    def test_expression_17(self):
        input = """
            var z = (
                (
                 a[1].f2[3][4][5].f3()[6] - 7 + b[9][10].f11().f12[13][14][15].f16()[17] - 18) *
                getThatOtherThing() *
                variousOtherThings())
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,517))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,519))

    def test_expression_20(self):
        input = """
            var z [3]int = [3]int{1, 2, 3}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,520))

    # Code blocks, 601..

    def test_codeblock_1(self):
        input = """
            func x() {}
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,601))

    def test_codeblock_2(self):
        input = """
            func x() {
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,602))

    def test_codeblock_3(self):
        input = """
            func x(
            ) {
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,603))

    def test_codeblock_4(self):
        input = """
            func x() {
                //
                /* */
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,604))

    def test_codeblock_5(self):
        input = """
            func x() {
                y(1+1)
                y(2+2)
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,605))

    def test_codeblock_6(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,606))

    def test_codeblock_7(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,607))

    def test_codeblock_8(self):
        input = """
            func x() {
                var local1 = 1
                var local2 = 2
                var local3 = 3
                const constant1 = 1
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,608))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,609))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,610))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,701))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,702))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,703))

    def test_loop_4(self):
        input = """
            func x() {
                for var x = 0; x < 10; x += 1 {
                    print(x)
                }
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,704))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,705))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,706))

    def test_loop_7(self):
        input = """
            func x() {
                for i, v := range [2]int{2, 4} {
                    print(i + v)
                }
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,707))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,708))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,709))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,710))

    # Conditionals, 801..

    def test_conditional_1(self):
        input = """
            func x() {
                if (a > b) {
                    c()
                }
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,801))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,802))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,803))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,804))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,805))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,806))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,807))

    def test_conditional_8(self):
        input = """
            func x() { // Ai so thi di ve!!!
                if (1) { // Ai so thi di ve!!!
                } else // Ai so thi di ve!!!
                {} // Ai so thi di ve!!!
            } // Ai so thi di ve!!!
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,808))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,809))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,810))

    # Break, continue, return, 901..

    def test_bcr_1(self):
        input = """
            func x() int {
                return 2
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,901))

    def test_bcr_2(self):
        input = """
            func x() float {
                return 4.0
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,902))

    def test_bcr_3(self):
        input = """
            func x() int {
                return 3
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,903))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,904))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,905))

    def test_bcr_6(self):
        input = """
            func x(y Size) float {
                if (y.Area() > 20) {
                    return 0.0;
                }
                
                return y.Area()
            }
        """
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,906))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,907))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,908))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,909))

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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,910))

    # Erroneous syntax, 1001..

    def test_code_outside_of_block(self):
        input = """
            func x() {
                return 2
            }
            x + 1
        """
        expect = "Error on line 5 col 13: x"
        self.assertTrue(TestParser.checkParser(input,expect,1001))

    def test_gibberish_nonsense(self):
        input = """
            func func func func
        """
        expect = "Error on line 2 col 18: func"
        self.assertTrue(TestParser.checkParser(input,expect,1002))

    def test_gibberish_nonsense_2(self):
        input = """
            var var var = var var;
        """
        expect = "Error on line 2 col 17: var"
        self.assertTrue(TestParser.checkParser(input,expect,1003))

    def test_return_typename(self):
        input = """
            func x() string {
                return string;
            }
        """
        expect = "Error on line 3 col 24: string"
        self.assertTrue(TestParser.checkParser(input,expect,1004))

    def test_cannot_assign(self):
        input = """
            func x() string {
                2 := 4
            }
        """
        expect = "Error on line 3 col 19: :="
        self.assertTrue(TestParser.checkParser(input,expect,1005))

    def test_missing_newline(self):
        input = """
            func x(y Size) float {
                x := 1 x := 2
            }
        """
        expect = "Error on line 3 col 24: x"
        self.assertTrue(TestParser.checkParser(input,expect,1006))

    def test_missing_newline_2(self):
        input = """
            type X struct {x float;} type Y struct {y float;}
        """
        expect = "Error on line 2 col 38: type"
        self.assertTrue(TestParser.checkParser(input,expect,1007))

    def test_non_literal_array_size(self):
        input = """
            var x = [2+2]int{1, 2, 3, 4}
        """
        expect = "Error on line 2 col 23: +"
        self.assertTrue(TestParser.checkParser(input,expect,1008))

    def test_non_integer_array_size(self):
        input = """
            var x = [2.5]int{1, 2, 3}
        """
        expect = "Error on line 2 col 22: 2.5"
        self.assertTrue(TestParser.checkParser(input,expect,1009))

    def test_double_call(self):
        input = """
            var z boolean = a[1].f2[3][4][5].f3()()[6] - 7 < b[9][10].f11().f12[13][14][15].f16()[17] - 18
        """
        expect = "Error on line 2 col 50: ("
        self.assertTrue(TestParser.checkParser(input,expect,1010))

    # Usual program. 1010.

    def test_usual_program(self):
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
        expect = "successful"
        self.assertTrue(TestParser.checkParser(input,expect,1010))

    # def test_more_complex_program(self):
    #     """More complex program"""
    #     input = """func foo () {
    #     };"""
    #     expect = "successful"
    #     self.assertTrue(TestParser.checkParser(input,expect,202))
    #
    # def test_wrong_miss_close(self):
    #     """Miss ) void main( {}"""
    #     input = """func main({};"""
    #     expect = "Error on line 1 col 11: {"
    #     self.assertTrue(TestParser.checkParser(input,expect,203))
    #
    # def test_wrong_variable(self):
    #     input = """var int;"""
    #     expect = "Error on line 1 col 5: int"
    #     self.assertTrue(TestParser.checkParser(input,expect,204))

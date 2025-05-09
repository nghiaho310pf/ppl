import os
import unittest
import inspect

from TestUtils import TestCodeGen

test_increment = 0

# Enable with environment variable to make tests dump into named folders
ENABLE_FUNCTION_NAME = os.getenv('ENABLE_FUNCTION_NAME') == '1'

def n():
    global test_increment
    v = test_increment
    test_increment += 1

    if ENABLE_FUNCTION_NAME:
        caller_name = inspect.stack()[1].function
        return caller_name

    return v


class CheckCodeGenSuite(unittest.TestCase):
    def test_put_1(self):
        i = """
            func main() {
                putInt(42)
            }
        """
        o = "42"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_put_2(self):
        i = """
            func main() {
                putFloat(3.14)
            }
        """
        o = "3.14"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_put_3(self):
        i = """
            func main() {
                putBool(true)
            }
        """
        o = "true"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_put_4(self):
        i = """
            func main() {
                putBool(false)
            }
        """
        o = "false"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_put_5(self):
        i = """
            func main() {
                putString("Hello, world!")
            }
        """
        o = "Hello, world!"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_put_6(self):
        i = """
            func main() {
                putInt(0)
                putString(" --- ")
                putFloat(1.234)
                putBool(false)
            }
        """
        o = "0 --- 1.234false"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_var_read_1(self):
        i = """
            func main() {
                var x = 1
                putInt(x)
            }
        """
        o = "1"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_var_read_2(self):
        i = """
            func main() {
                var pi = 3.1415
                putFloat(pi)
            }
        """
        o = "3.1415"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_var_read_3(self):
        i = """
            func main() {
                var truth = true
                putBool(truth)
            }
        """
        o = "true"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_var_read_4(self):
        i = """
            func main() {
                var message = "Hello"
                putString(message)
            }
        """
        o = "Hello"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_var_read_5(self):
        i = """
            func main() {
                var a = 10
                var b = 2.5
                var c = false
                var d = "test"
                putInt(a)
                putFloat(b)
                putBool(c)
                putString(d)
            }
        """
        o = "102.5falsetest"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_assignment_1(self):
        i = """
            func main() {
                var x = 0
                x := 5
                putInt(x)
            }
        """
        o = "5"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_assignment_2(self):
        i = """
            func main() {
                var f = 0.0
                f := 2.718
                putFloat(f)
            }
        """
        o = "2.718"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_assignment_3(self):
        i = """
            func main() {
                var flag = false
                flag := true
                putBool(flag)
            }
        """
        o = "true"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_assignment_4(self):
        i = """
            func main() {
                var msg = ""
                msg := "Assignment works"
                putString(msg)
            }
        """
        o = "Assignment works"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_assignment_5(self):
        i = """
            func main() {
                var a = 1
                var b = 2
                a := b
                putInt(a)
            }
        """
        o = "2"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_1(self):
        i = """
            type Point struct { x int; y int }
            func main() {
                p := Point{x: 3, y: 4}
                putInt(p.x)
                putInt(p.y)
            }
        """
        o = "34"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_2(self):
        i = """
            type Point struct { x int; y int }
            func main() {
                p := Point{x: 0, y: 0}
                p.x := 10
                p.y := 20
                putInt(p.x)
                putInt(p.y)
            }
        """
        o = "1020"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_3(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) printX() {
                putInt(p.x)
            }
            func main() {
                pt := Point{x: 7, y: 9}
                pt.printX()
            }
        """
        o = "7"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_4(self):
        i = """
            type Person struct { name string; age int }
            func (p Person) greet() {
                putString("Hi, I'm ")
                putString(p.name)
            }
            func main() {
                me := Person{name: "Alice", age: 30}
                me.greet()
            }
        """
        o = "Hi, I'm Alice"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_5(self):
        i = """
            type S struct { b boolean }
            func (s S) get() boolean { return s.b }
            func main() {
                s := S{b: true}
                if (s.get()) {
                    putString("ok")
                }
            }
        """
        o = "ok"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_6(self):
        i = """
            type Inner struct { val int }
            type Outer struct { val Inner }
    
            func main() {
                o := Outer{val: Inner{val: 42}}
                putInt(o.val.val)
            }
        """
        o = "42"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_7(self):
        i = """
            type Position struct { x int; y int }
            type Entity struct { name string; pos Position }
            func main() {
                e := Entity{name: "hero", pos: Position{x: 5, y: 10}}
                putString(e.name)
                putInt(e.pos.x)
                putInt(e.pos.y)
            }
        """
        o = "hero510"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_struct_8(self):
        i = """
            type A struct { value int }
            func (a A) double() int { return a.value * 2 }
    
            type B struct { a A }
            func main() {
                b := B{a: A{value: 7}}
                putInt(b.a.double())
            }
        """
        o = "14"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_1(self):
        i = """
            func main() {
                var x [2]int
                x[0] := 10
                x[1] := 20
                putInt(x[0])
                putInt(x[1])
            }
        """
        o = "1020"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_2(self):
        i = """
            func main() {
                var y [2][3]int
                y[0][0] := 1
                y[0][1] := 2
                y[0][2] := 3
                y[1][0] := 4
                y[1][1] := 5
                y[1][2] := 6
                putInt(y[0][0])
                putInt(y[1][2])
            }
        """
        o = "16"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_3(self):
        i = """
            func main() {
                var z = [2]int{1, 2}
                putInt(z[0])
                putInt(z[1])
            }
        """
        o = "12"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_4(self):
        i = """
            func main() {
                var q = [2][2]int{{1, 2}, {3, 4}}
                putInt(q[0][0])
                putInt(q[1][1])
            }
        """
        o = "14"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_5(self):
        i = """
            func main() {
                var arr = [3]int{5, 10, 15}
                var sum = arr[0] + arr[1] + arr[2]
                putInt(sum)
            }
        """
        o = "30"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_6(self):
        i = """
            func main() {
                var arr = [3]int{7, 8, 9}
                arr[1] := 20
                putInt(arr[0])
                putInt(arr[1])
                putInt(arr[2])
            }
        """
        o = "7209"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_1(self):
        i = """
            func main() {
                var i = 0
                for i < 5 {
                    putInt(i)
                    i := i + 1
                }
            }
        """
        o = "01234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_2(self):
        i = """
            func main() {
                var x = 10
                for x > 0 {
                    putInt(x)
                    x := x - 1
                }
            }
        """
        o = "10987654321"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_3(self):
        i = """
            func main() {
                var sum = 0
                var i = 1
                for i <= 5 {
                    sum := sum + i
                    i := i + 1
                }
                putInt(sum)
            }
        """
        o = "15"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_4(self):
        i = """
            func main() {
                var count = 0
                for count < 3 {
                    putInt(count)
                    count := count + 1
                }
                putString("done")
            }
        """
        o = "012done"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_5(self):
        i = """
            func main() {
                var i = 0
                var sum = 0
                for i < 4 {
                    sum := sum + i
                    i := i + 1
                }
                putInt(sum)
            }
        """
        o = "6"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_6(self):
        i = """
            func main() {
                var i = 0
                var result = 1
                for i < 5 {
                    result := result * (i + 1)
                    i := i + 1
                }
                putInt(result)
            }
        """
        o = "120"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_7(self):
        i = """
            func main() {
                var x = 5
                for x > 0 {
                    putInt(x)
                    x := x - 2
                }
            }
        """
        o = "531"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_8(self):
        i = """
            func main() {
                var n = 3
                var fact = 1
                for n > 0 {
                    fact := fact * n
                    n := n - 1
                }
                putInt(fact)
            }
        """
        o = "6"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_9(self):
        i = """
            func main() {
                var sum = 0
                var i = 1
                for i < 6 {
                    sum := sum + i
                    i := i + 1
                }
                putInt(sum)
            }
        """
        o = "15"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_while_loop_10(self):
        i = """
            func main() {
                var count = 0
                for count < 3 {
                    count := count + 1
                }
                putInt(count)
            }
        """
        o = "3"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_1(self):
        i = """
            func main() {
                for var i = 0; i < 5; i := i + 1 {
                    putInt(i)
                }
            }
        """
        o = "01234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_2(self):
        i = """
            func main() {
                for var i = 5; i > 0; i := i - 1 {
                    putInt(i)
                }
            }
        """
        o = "54321"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_3(self):
        i = """
            func main() {
                var sum = 0
                for var i = 1; i <= 5; i := i + 1 {
                    sum := sum + i
                }
                putInt(sum)
            }
        """
        o = "15"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_4(self):
        i = """
            func main() {
                for var x = 0; x < 3; x := x + 1 {
                    putInt(x)
                }
                putString(" done")
            }
        """
        o = "012 done"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_5(self):
        i = """
            func main() {
                var result = 1
                for var i = 1; i <= 5; i := i + 1 {
                    result := result * i
                }
                putInt(result)
            }
        """
        o = "120"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_6(self):
        i = """
            func main() {
                for var i = 0; i < 3; i := i + 1 {
                    putInt(i)
                }
                for var j = 5; j > 3; j := j - 1 {
                    putInt(j)
                }
            }
        """
        o = "01254"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_7(self):
        i = """
            func main() {
                var x = 0
                for var i = 0; i < 5; i := i + 1 {
                    x := x + i
                }
                putInt(x)
            }
        """
        o = "10"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_8(self):
        i = """
            func main() {
                for var i = 1; i <= 5; i := i + 1 {
                    if (i % 2 == 0) {
                        putInt(i)
                    }
                }
            }
        """
        o = "246"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_9(self):
        i = """
            func main() {
                for var i = 0; i < 10; i := i + 2 {
                    putInt(i)
                }
            }
        """
        o = "02468"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_cstyle_loop_10(self):
        i = """
            func main() {
                var count = 0
                for var i = 0; i < 5; i := i + 1 {
                    count := count + 1
                }
                putInt(count)
            }
        """
        o = "5"
        self.assertTrue(TestCodeGen.test(i, o, n()))

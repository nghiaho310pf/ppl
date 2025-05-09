"""
 * @author nghia.ho310pf
 * @note https://www.youtube.com/watch?v=I5aT1fRa9Mc
 * @note https://www.youtube.com/watch?v=rCWrqSqhcJ8
"""
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

    def test_array_7(self):
        i = """
            func main() {
                var a = [1]int{42}
                putInt(a[0])
            }
        """
        o = "42"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_8(self):
        i = """
            func main() {
                var m = [2][2]int{{1, 2}, {3, 4}}
                putInt(m[0][0])
                putInt(m[0][1])
                putInt(m[1][0])
                putInt(m[1][1])
            }
        """
        o = "1234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_9(self):
        i = """
            func main() {
                var a = [3]int{0, 1, 2}
                var sum = 0
                for var i = 0; i < 3; i := i + 1 {
                    sum := sum + a[i]
                }
                putInt(sum)
            }
        """
        o = "3"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_10(self):
        i = """
            func main() {
                var m = [2][2]int{{10, 20}, {30, 40}}
                var total = 0
                for var i = 0; i < 2; i := i + 1 {
                    for var j = 0; j < 2; j := j + 1 {
                        total := total + m[i][j]
                    }
                }
                putInt(total)
            }
        """
        o = "100"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_11(self):
        i = """
            func main() {
                var a [2]int
                a[0] := 9
                a[1] := 6
                putInt(a[0] + a[1])
            }
        """
        o = "15"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_12(self):
        i = """
            func main() {
                var m = [1][2][3]int{{{1, 2, 3}, {4, 5, 6}}}
                putInt(m[0][0][0])
                putInt(m[0][1][2])
            }
        """
        o = "16"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_13(self):
        i = """
            func main() {
                var m = [2][2]int{{1, 2}, {3, 4}}
                m[0][1] := 20
                m[1][0] := 30
                putInt(m[0][1])
                putInt(m[1][0])
            }
        """
        o = "2030"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_14(self):
        i = """
            func main() {
                var arr = [2][2]int{{1, 2}, {3, 4}}
                for var i = 0; i < 2; i := i + 1 {
                    for var j = 0; j < 2; j := j + 1 {
                        putInt(arr[i][j])
                    }
                }
            }
        """
        o = "1234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_15(self):
        i = """
            func main() {
                var a = [2][2]int{{1, 2}, {3, 4}}
                var sum = 0
                for var i = 0; i < 2; i := i + 1 {
                    sum := sum + a[i][i]
                }
                putInt(sum)
            }
        """
        o = "5"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_16(self):
        i = """
            func main() {
                var m = [1][2][3]int{{{1, 2, 3}, {4, 5, 6}}}
                var total = 0
                for var i = 0; i < 1; i := i + 1 {
                    for var j = 0; j < 2; j := j + 1 {
                        for var k = 0; k < 3; k := k + 1 {
                            total := total + m[i][j][k]
                        }
                    }
                }
                putInt(total)
            }
        """
        o = "21"
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
                for var i = 1; i <= 6; i := i + 1 {
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

    def test_interface_1(self):
        i = """
            type Printer interface {
                print()
            }

            type A struct {}

            func (a A) print() {
                putString("A")
            }

            func main() {
                var p Printer = A{}
                p.print()
            }
        """
        o = "A"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_interface_2(self):
        i = """
            type Printer interface {
                print()
            }

            type B struct {}

            func (b B) print() {
                putString("B")
            }

            func usePrinter(p Printer) {
                p.print()
            }

            func main() {
                usePrinter(B{})
            }
        """
        o = "B"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_interface_3(self):
        i = """
            type Printer interface {
                print()
            }

            type A struct {}
            type B struct {}

            func (a A) print() {
                putString("A")
            }

            func (b B) print() {
                putString("B")
            }

            func main() {
                var p Printer = A{}
                p.print()
                p := B{}
                p.print()
            }
        """
        o = "AB"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_interface_4(self):
        i = """
            type Printer interface {
                print()
            }

            type Verbose struct {}

            func (v Verbose) print() {
                putString("Verbose")
            }

            func (v Verbose) debug() {
                putString("Debug")
            }

            func main() {
                var p Printer = Verbose{}
                p.print()
            }
        """
        o = "Verbose"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_interface_5(self):
        i = """
            type Printer interface {
                print()
            }

            type A struct {}
            type B struct {}

            func (a A) print() { putString("A") }
            func (b B) print() { putString("B") }

            func doPrint(p Printer) {
                p.print()
            }

            func main() {
                doPrint(A{})
                doPrint(B{})
            }
        """
        o = "AB"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_1(self):
        i = """
            func main() {
                if (true) {
                    putString("yes")
                }
            }
        """
        o = "yes"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_2(self):
        i = """
            func main() {
                if (false) {
                    putString("no")
                } else {
                    putString("yes")
                }
            }
        """
        o = "yes"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_3(self):
        i = """
            func main() {
                var x = 10
                if (x > 5) {
                    putString("big")
                } else {
                    putString("small")
                }
            }
        """
        o = "big"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_4(self):
        i = """
            func main() {
                var x = 3
                if (x > 5) {
                    putString("A")
                } else if (x > 1) {
                    putString("B")
                } else {
                    putString("C")
                }
            }
        """
        o = "B"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_5(self):
        i = """
            func main() {
                var x = 0
                if (x < 0) {
                    putString("neg")
                } else if (x == 0) {
                    putString("zero")
                } else {
                    putString("pos")
                }
            }
        """
        o = "zero"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_6(self):
        i = """
            func main() {
                var a = 3
                var b = 4
                if (a < b) {
                    putString("yes")
                }
            }
        """
        o = "yes"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_7(self):
        i = """
            func main() {
                var a = 3
                var b = 3
                if (a < b) {
                    putString("A")
                } else if (a == b) {
                    putString("B")
                } else {
                    putString("C")
                }
            }
        """
        o = "B"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_8(self):
        i = """
            func main() {
                var x = 2
                var y = 4
                if ((x + y) % 2 == 0) {
                    putString("even")
                } else {
                    putString("odd")
                }
            }
        """
        o = "even"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_9(self):
        i = """
            func main() {
                if (false) {
                    putString("A")
                } else if (false) {
                    putString("B")
                } else {
                    putString("C")
                }
            }
        """
        o = "C"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_if_10(self):
        i = """
            func main() {
                var x = 5
                var y = 10
                if (x > 0) {
                    if (y > 5) {
                        putString("yes")
                    }
                }
            }
        """
        o = "yes"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_1(self):
        i = """
            func hello() {
                putString("hello")
            }
            func main() {
                hello()
            }
        """
        o = "hello"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_2(self):
        i = """
            func greet() {
                putString("hi")
            }
            func main() {
                greet()
                greet()
            }
        """
        o = "hihi"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_3(self):
        i = """
            func printIntTwice(x int) {
                putInt(x)
                putInt(x)
            }
            func main() {
                printIntTwice(7)
            }
        """
        o = "77"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_4(self):
        i = """
            func add(a int, b int) int {
                return a + b
            }
            func main() {
                putInt(add(2, 3))
            }
        """
        o = "5"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_5(self):
        i = """
            func square(x int) int {
                return x * x
            }
            func main() {
                var s = square(4)
                putInt(s)
            }
        """
        o = "16"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_6(self):
        i = """
            func mulAdd(a int, b int, c int) int {
                return a * b + c
            }
            func main() {
                putInt(mulAdd(2, 3, 4))
            }
        """
        o = "10"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_7(self):
        i = """
            func echo(s string) string {
                return s
            }
            func main() {
                putString(echo("abc"))
            }
        """
        o = "abc"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_8(self):
        i = """
            func max(a int, b int) int {
                if (a > b) {
                    return a
                } else {
                    return b
                }
            }
            func main() {
                putInt(max(3, 9))
            }
        """
        o = "9"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_9(self):
        i = """
            func id(x int) int {
                return x
            }
            func main() {
                var a = id(42)
                putInt(a)
            }
        """
        o = "42"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_func_10(self):
        i = """
            func fib(n int) int {
                if (n <= 1) {
                    return n
                } else {
                    return fib(n - 1) + fib(n - 2)
                }
            }
            func main() {
                putInt(fib(7))
            }
        """
        o = "13"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_1(self):
        i = """
            const N = 3
            func main() {
                var a [N]int
                a[0] := 10
                a[1] := 20
                a[2] := 30
                putInt(a[0] + a[1] + a[2])
            }
        """
        o = "60"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_2(self):
        i = """
            const R = 2
            const C = 3
            func main() {
                var m [R][C]int
                m[0][0] := 1
                m[0][1] := 2
                m[0][2] := 3
                m[1][0] := 4
                m[1][1] := 5
                m[1][2] := 6
                putInt(m[0][1] + m[1][2])
            }
        """
        o = "8"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_3(self):
        i = """
            const SIZE = 5
            func main() {
                var a [SIZE]int
                for var i = 0; i < SIZE; i := i + 1 {
                    a[i] := i
                }
                for var i = 0; i < SIZE; i := i + 1 {
                    putInt(a[i])
                }
            }
        """
        o = "01234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_4(self):
        i = """
            const X = 1
            const Y = 2
            const Z = 3
            func main() {
                var a [X][Y][Z]int
                a[0][1][2] := 99
                putInt(a[0][1][2])
            }
        """
        o = "99"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_5(self):
        i = """
            const N = 2
            func fill(a [N]int) {
                a[0] := 5
                a[1] := 6
                putInt(a[0] + a[1])
            }
            func main() {
                fill([2]int{0, 0})
            }
        """
        o = "11"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_6(self):
        i = """
            const A = 1
            const B = 2
            const C = 2
            func main() {
                var arr = [A][B][C]int{{{1, 2}, {3, 4}}}
                putInt(arr[0][0][0])
                putInt(arr[0][1][1])
            }
        """
        o = "14"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_7(self):
        i = """
            const N = 3
            func main() {
                var a = [N]int{1, 2, 3}
                var sum = 0
                for var i = 0; i < N; i := i + 1 {
                    sum := sum + a[i]
                }
                putInt(sum)
            }
        """
        o = "6"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_8(self):
        i = """
            const R = 2
            const C = 2
            func main() {
                var m = [R][C]int{{1, 2}, {3, 4}}
                for var i = 0; i < R; i := i + 1 {
                    for var j = 0; j < C; j := j + 1 {
                        putInt(m[i][j])
                    }
                }
            }
        """
        o = "1234"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_9(self):
        i = """
            const L = 2
            const M = 2
            const N = 2
            func main() {
                var a [L][M][N]int
                a[1][1][1] := 7
                putInt(a[1][1][1])
            }
        """
        o = "7"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_array_const_dim_10(self):
        i = """
            const S = 2
            func main() {
                var a = [S]int{3, 4}
                putInt(a[0] * a[1])
            }
        """
        o = "12"
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_vector_math_1(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) add(q Point) Point {
                return Point{x: p.x + q.x, y: p.y + q.y}
            }
            func main() {
                var p = Point{x: 2, y: 3}
                var q = Point{x: 4, y: 5}
                var r = p.add(q)
                putInt(r.x + r.y)
            }
        """
        o = "14"  # (2+4) + (3+5) = 14
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_vector_math_2(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) subtract(q Point) Point {
                return Point{x: p.x - q.x, y: p.y - q.y}
            }
            func main() {
                var p = Point{x: 6, y: 7}
                var q = Point{x: 3, y: 4}
                var r = p.subtract(q)
                putInt(r.x + r.y)
            }
        """
        o = "6"  # (6-3) + (7-4) = 6
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_vector_math_3(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) scale(s int) Point {
                return Point{x: p.x * s, y: p.y * s}
            }
            func main() {
                var p = Point{x: 3, y: 4}
                var s = 2
                var r = p.scale(s)
                putInt(r.x + r.y)
            }
        """
        o = "14"  # (3*2) + (4*2) = 14
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_vector_math_4(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) dot(q Point) int {
                return p.x * q.x + p.y * q.y
            }
            func main() {
                var p = Point{x: 1, y: 2}
                var q = Point{x: 3, y: 4}
                var r = p.dot(q)
                putInt(r)
            }
        """
        o = "11"  # (1*3) + (2*4) = 11
        self.assertTrue(TestCodeGen.test(i, o, n()))

    def test_vector_math_5(self):
        i = """
            type Point struct { x int; y int }
            func (p Point) length() int {
                return p.x * p.x + p.y * p.y
            }
            func main() {
                var p = Point{x: 3, y: 4}
                var r = p.length()
                putInt(r)
            }
        """
        o = "25"  # (3*3) + (4*4) = 25
        self.assertTrue(TestCodeGen.test(i, o, n()))


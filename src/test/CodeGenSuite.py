import unittest

from TestUtils import TestCodeGen

test_increment = 0


def make_test_number():
    global test_increment
    v = test_increment
    test_increment += 1
    return v


class CheckCodeGenSuite(unittest.TestCase):
    def test_put_1(self):
        input = """
            func main() {
                putInt(42)
            }
        """
        expect = "42"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

    def test_put_2(self):
        input = """
            func main() {
                putFloat(3.14)
            }
        """
        expect = "3.14"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

    def test_put_3(self):
        input = """
            func main() {
                putBool(true)
            }
        """
        expect = "true"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

    def test_put_4(self):
        input = """
            func main() {
                putBool(false)
            }
        """
        expect = "false"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

    def test_put_5(self):
        input = """
            func main() {
                putString("Hello, world!")
            }
        """
        expect = "Hello, world!"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

    def test_put_6(self):
        input = """
            func main() {
                putInt(0)
                putString(" - separator - ")
                putFloat(2.718)
                putBool(false)
            }
        """
        expect = "0 - separator - 2.718false"
        self.assertTrue(TestCodeGen.test(input, expect, make_test_number()))

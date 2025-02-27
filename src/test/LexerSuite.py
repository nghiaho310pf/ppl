import unittest
from TestUtils import TestLexer

class LexerSuite(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(TestLexer.checkLexeme("","<EOF>",1))

    # Newlines, 101..

    def test_one_newline(self):
        self.assertTrue(TestLexer.checkLexeme("a\nb","a,;,b,<EOF>",101))

    def test_several_newlines(self):
        self.assertTrue(TestLexer.checkLexeme("a\n\n\n\nb","a,;,b,<EOF>",102))

    # Identifiers, 201..

    def test_lower_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("abc","abc,<EOF>",201))

    def test_upper_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("ABCDE","ABCDE,<EOF>",202))

    def test_camel_case_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("nghiaHo310Pf","nghiaHo310Pf,<EOF>",203))

    def test_pascal_case_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("NghiaHo310Pf","NghiaHo310Pf,<EOF>",204))

    def test_snake_case_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("nghia_ho_310_pf","nghia_ho_310_pf,<EOF>",205))

    def test_identifier_misc_1(self):
        self.assertTrue(TestLexer.checkLexeme("__doubleUnderscored","__doubleUnderscored,<EOF>",206))

    def test_identifier_misc_2(self):
        self.assertTrue(TestLexer.checkLexeme("__underscores_on_both_sides__","__underscores_on_both_sides__,<EOF>",207))

    def test_identifier_misc_3(self):
        self.assertTrue(TestLexer.checkLexeme("Zero12345","Zero12345,<EOF>",208))

    def test_identifier_misc_4(self):
        self.assertTrue(TestLexer.checkLexeme("Take Flight","Take,Flight,<EOF>",209))

    def test_identifier_misc_5(self):
        self.assertTrue(TestLexer.checkLexeme("Radix Analogue Pulse Tpolm Superglam","Radix,Analogue,Pulse,Tpolm,Superglam,<EOF>",210))

    def test_identifier_mix_1(self):
        self.assertTrue(TestLexer.checkLexeme("XZ4y4itX gve6GvXy qriXOjff PC4tmpnn rDjq7jVu","XZ4y4itX,gve6GvXy,qriXOjff,PC4tmpnn,rDjq7jVu,<EOF>",211))

    def test_identifier_mix_2(self):
        self.assertTrue(TestLexer.checkLexeme("dAX2TwjU FXVswcbg j9VooYqL z9BnCkKk kL0m8a9T","dAX2TwjU,FXVswcbg,j9VooYqL,z9BnCkKk,kL0m8a9T,<EOF>",212))

    def test_identifier_mix_3(self):
        self.assertTrue(TestLexer.checkLexeme("z7VIPRVP wwWQxzlk eXklrN2A mYv0K7nb UqJ5xJum","z7VIPRVP,wwWQxzlk,eXklrN2A,mYv0K7nb,UqJ5xJum,<EOF>",213))

    def test_identifier_mix_4(self):
        self.assertTrue(TestLexer.checkLexeme("VvbKIoUg sdcygXQI SkBZc7xe AwSKpBLK KnvWlwCL","VvbKIoUg,sdcygXQI,SkBZc7xe,AwSKpBLK,KnvWlwCL,<EOF>",214))

    def test_identifier_mix_5(self):
        self.assertTrue(TestLexer.checkLexeme("kAQBztnj XlFO9GF1 z5nUS7rC bIut4x5i MwwxhS5e","kAQBztnj,XlFO9GF1,z5nUS7rC,bIut4x5i,MwwxhS5e,<EOF>",215))

    # Keywords, 301..

    def test_keyword_if(self):
        self.assertTrue(TestLexer.checkLexeme("if","if,<EOF>",301))

    def test_keyword_else(self):
        self.assertTrue(TestLexer.checkLexeme("else","else,<EOF>",302))

    def test_keyword_for(self):
        self.assertTrue(TestLexer.checkLexeme("for","for,<EOF>",303))

    def test_keyword_return(self):
        self.assertTrue(TestLexer.checkLexeme("return","return,<EOF>",304))

    def test_keyword_func(self):
        self.assertTrue(TestLexer.checkLexeme("func","func,<EOF>",305))

    def test_keyword_type(self):
        self.assertTrue(TestLexer.checkLexeme("type","type,<EOF>",306))

    def test_keyword_struct(self):
        self.assertTrue(TestLexer.checkLexeme("struct","struct,<EOF>",307))

    def test_keyword_interface(self):
        self.assertTrue(TestLexer.checkLexeme("interface","interface,<EOF>",308))

    def test_keyword_const(self):
        self.assertTrue(TestLexer.checkLexeme("const","const,<EOF>",309))

    def test_keyword_var(self):
        self.assertTrue(TestLexer.checkLexeme("var","var,<EOF>",310))

    def test_keyword_continue(self):
        self.assertTrue(TestLexer.checkLexeme("continue","continue,<EOF>",311))

    def test_keyword_break(self):
        self.assertTrue(TestLexer.checkLexeme("break","break,<EOF>",312))

    def test_keyword_range(self):
        self.assertTrue(TestLexer.checkLexeme("range","range,<EOF>",313))

    def test_keyword_nil(self):
        self.assertTrue(TestLexer.checkLexeme("nil","nil,<EOF>",314))

    def test_keyword_true(self):
        self.assertTrue(TestLexer.checkLexeme("true","true,<EOF>",315))

    def test_keyword_false(self):
        self.assertTrue(TestLexer.checkLexeme("false","false,<EOF>",316))

    def test_keyword_string(self):
        self.assertTrue(TestLexer.checkLexeme("string","string,<EOF>",317))

    def test_keyword_int(self):
        self.assertTrue(TestLexer.checkLexeme("int","int,<EOF>",318))

    def test_keyword_float(self):
        self.assertTrue(TestLexer.checkLexeme("float","float,<EOF>",319))

    def test_keyword_boolean(self):
        self.assertTrue(TestLexer.checkLexeme("boolean","boolean,<EOF>",320))

    def test_keyword_mix_1(self):
        self.assertTrue(TestLexer.checkLexeme("false false interface return struct true const type","false,false,interface,return,struct,true,const,type,<EOF>",321))

    def test_keyword_mix_2(self):
        self.assertTrue(TestLexer.checkLexeme("struct break const range nil else return for","struct,break,const,range,nil,else,return,for,<EOF>",322))

    def test_keyword_mix_3(self):
        self.assertTrue(TestLexer.checkLexeme("nil continue const nil const if for return","nil,continue,const,nil,const,if,for,return,<EOF>",323))

    def test_keyword_mix_4(self):
        self.assertTrue(TestLexer.checkLexeme("type else continue type for break nil continue","type,else,continue,type,for,break,nil,continue,<EOF>",324))

    def test_keyword_mix_5(self):
        self.assertTrue(TestLexer.checkLexeme("const interface else if func break else type","const,interface,else,if,func,break,else,type,<EOF>",325))

    # Operators, 401..

    def test_operator_add(self):
        self.assertTrue(TestLexer.checkLexeme("+","+,<EOF>",401))

    def test_operator_sub(self):
        self.assertTrue(TestLexer.checkLexeme("-","-,<EOF>",402))

    def test_operator_mul(self):
        self.assertTrue(TestLexer.checkLexeme("*","*,<EOF>",403))

    def test_operator_div(self):
        self.assertTrue(TestLexer.checkLexeme("/","/,<EOF>",404))

    def test_operator_mod(self):
        self.assertTrue(TestLexer.checkLexeme("%","%,<EOF>",405))

    def test_operator_eq(self):
        self.assertTrue(TestLexer.checkLexeme("==","==,<EOF>",406))

    def test_operator_ineq(self):
        self.assertTrue(TestLexer.checkLexeme("!=","!=,<EOF>",407))

    def test_operator_less(self):
        self.assertTrue(TestLexer.checkLexeme("<","<,<EOF>",408))

    def test_operator_less_eq(self):
        self.assertTrue(TestLexer.checkLexeme("<=","<=,<EOF>",409))

    def test_operator_greater(self):
        self.assertTrue(TestLexer.checkLexeme(">",">,<EOF>",410))

    def test_operator_greater_eq(self):
        self.assertTrue(TestLexer.checkLexeme(">=",">=,<EOF>",411))

    def test_operator_logical_and(self):
        self.assertTrue(TestLexer.checkLexeme("&&","&&,<EOF>",412))

    def test_operator_logical_or(self):
        self.assertTrue(TestLexer.checkLexeme("||","||,<EOF>",413))

    def test_operator_logical_not(self):
        self.assertTrue(TestLexer.checkLexeme("!","!,<EOF>",414))

    def test_operator_reassign(self):
        self.assertTrue(TestLexer.checkLexeme(":=",":=,<EOF>",415))

    def test_operator_add_assign(self):
        self.assertTrue(TestLexer.checkLexeme("+=","+=,<EOF>",416))

    def test_operator_sub_assign(self):
        self.assertTrue(TestLexer.checkLexeme("-=","-=,<EOF>",417))

    def test_operator_mul_assign(self):
        self.assertTrue(TestLexer.checkLexeme("*=","*=,<EOF>",418))

    def test_operator_div_assign(self):
        self.assertTrue(TestLexer.checkLexeme("/=","/=,<EOF>",419))

    def test_operator_mod_assign(self):
        self.assertTrue(TestLexer.checkLexeme("%=","%=,<EOF>",420))

    def test_operator_dot(self):
        self.assertTrue(TestLexer.checkLexeme(".",".,<EOF>",421))

    def test_operator_initialize(self):
        self.assertTrue(TestLexer.checkLexeme("=","=,<EOF>",422))

    # Separators, 501..

    def test_separator_paren_left(self):
        self.assertTrue(TestLexer.checkLexeme("(","(,<EOF>",501))

    def test_separator_paren_right(self):
        self.assertTrue(TestLexer.checkLexeme(")","),<EOF>",502))

    def test_separator_brace_left(self):
        self.assertTrue(TestLexer.checkLexeme("{","{,<EOF>",503))

    def test_separator_brace_right(self):
        self.assertTrue(TestLexer.checkLexeme("}","},<EOF>",504))

    def test_separator_bracket_left(self):
        self.assertTrue(TestLexer.checkLexeme("[","[,<EOF>",505))

    def test_separator_bracket_right(self):
        self.assertTrue(TestLexer.checkLexeme("]","],<EOF>",506))

    def test_separator_colon(self):
        self.assertTrue(TestLexer.checkLexeme(":",":,<EOF>",507))

    def test_separator_semicolon(self):
        self.assertTrue(TestLexer.checkLexeme(";",";,<EOF>",508))

    def test_separator_comma(self):
        self.assertTrue(TestLexer.checkLexeme(",",",,<EOF>",509))

    # Integer literals, 601..

    def test_literal_integer_1(self):
        self.assertTrue(TestLexer.checkLexeme("48986989","48986989,<EOF>",601))

    def test_literal_integer_2(self):
        self.assertTrue(TestLexer.checkLexeme("49886192","49886192,<EOF>",602))

    def test_literal_integer_4(self):
        self.assertTrue(TestLexer.checkLexeme("0b100011011111111001000111101","0b100011011111111001000111101,<EOF>",604))

    def test_literal_integer_5(self):
        self.assertTrue(TestLexer.checkLexeme("0b100101110100101101010111011","0b100101110100101101010111011,<EOF>",605))

    def test_literal_integer_7(self):
        self.assertTrue(TestLexer.checkLexeme("0o221724561","0o221724561,<EOF>",607))

    def test_literal_integer_8(self):
        self.assertTrue(TestLexer.checkLexeme("0o700332656","0o700332656,<EOF>",608))

    def test_literal_integer_10(self):
        self.assertTrue(TestLexer.checkLexeme("0x93e0dd","0x93e0dd,<EOF>",610))

    def test_literal_integer_11(self):
        self.assertTrue(TestLexer.checkLexeme("0x3a73516","0x3a73516,<EOF>",611))

    # String literals, 701..

    def test_literal_string_1(self):
        self.assertTrue(TestLexer.checkLexeme('hello',"hello,<EOF>",701))

    def test_literal_string_2(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "hello there"
        ""","\"hello there\",;,<EOF>",702))

    def test_literal_string_3(self):
        self.assertTrue(TestLexer.checkLexeme('"hi" "bye"',"\"hi\",\"bye\",<EOF>",703))

    def test_literal_string_4(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "if else const boolean := <><>"
        ""","\"if else const boolean := <><>\",;,<EOF>",704))

    def test_literal_string_5(self):
        self.assertTrue(TestLexer.checkLexeme('""',"\"\",<EOF>",705))

    def test_literal_string_escapes_1(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "\\thello\\nthere"
        ""","\"\\thello\\nthere\",;,<EOF>",706))

    def test_literal_string_escapes(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "\\nhello\\tthere"
        ""","\"\\nhello\\tthere\",;,<EOF>",706))

    # Comments, 801..

    def test_comment(self):
        self.assertTrue(TestLexer.checkLexeme("""
            // https://www.youtube.com/watch?v=7qeG0BnJxus
        ""","<EOF>",801))

    def test_multiline_comment(self):
        self.assertTrue(TestLexer.checkLexeme("""
            /**
                https://www.youtube.com/watch?v=TjI3jTRLbpc
            */
        ""","<EOF>",802))

    def test_nested_multiline_comment(self):
        self.assertTrue(TestLexer.checkLexeme("""
            /**
                pre
                /**
                    https://www.youtube.com/watch?v=XMzHVMVaBZ0
                */
                post
            */
        ""","<EOF>",803))

    # Automatic semicolon insertion, 901..

    def test_asi_1(self):
        self.assertTrue(TestLexer.checkLexeme("""
            func X() {
                1+1
            }
        ""","func,X,(,),{,1,+,1,;,},;,<EOF>",901))

    def test_asi_2(self):
        self.assertTrue(TestLexer.checkLexeme("""
            func X() {
                (
                    1+1)
            }
        ""","func,X,(,),{,(,1,+,1,),;,},;,<EOF>",902))

    def test_asi_3(self):
        self.assertTrue(TestLexer.checkLexeme("""
            func X() {
                sup
            }
        ""","func,X,(,),{,sup,;,},;,<EOF>",903))

    # Erroneous syntax, 1001..

    def test_error_char_1(self):
        self.assertTrue(TestLexer.checkLexeme("?","ErrorToken ?",1001))

    def test_error_char_2(self):
        self.assertTrue(TestLexer.checkLexeme("!!->????","!,!,-,>,ErrorToken ?",1002))

    def test_error_char_3(self):
        self.assertTrue(TestLexer.checkLexeme("!!->???? |","!,!,-,>,ErrorToken ?",1003))

    def test_unclosed_string(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "hello
        ""","Unclosed string: \"hello",1004))

    def test_illegal_escape(self):
        self.assertTrue(TestLexer.checkLexeme("""
            "h\ello
        ""","Illegal escape in string: \"h\e",1005))


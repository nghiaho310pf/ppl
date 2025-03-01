grammar MiniGo;

@lexer::header {
from lexererr import *
from antlr4.Token import CommonToken
}

@lexer::members {
previous_token_type = None

def emit(self):
    tk = self.type
    if tk == self.UNCLOSE_STRING:
        result = super().emit();
        raise UncloseString(result.text);
    elif tk == self.ILLEGAL_ESCAPE:
        result = super().emit();
        raise IllegalEscape(result.text);
    elif tk == self.ERROR_CHAR:
        result = super().emit();
        raise ErrorToken(result.text);
    else:
        return super().emit();

def nextToken(self):
    token = super().nextToken()

    if token is None:
        self.previous_token_type = None
        return token

    if token.type == self.NEWLINES:
        inject_targets = [
            self.IDENTIFIER,
            self.LITERAL_DECIMAL_INT,
            self.LITERAL_BINARY_INT,
            self.LITERAL_OCTAL_INT,
            self.LITERAL_HEX_INT,
            self.LITERAL_FLOAT,
            self.LITERAL_STRING,
            self.KEYWORD_NIL,
            self.KEYWORD_INT,
            self.KEYWORD_FLOAT,
            self.KEYWORD_BOOLEAN,
            self.KEYWORD_STRING,
            self.KEYWORD_RETURN,
            self.KEYWORD_BREAK,
            self.KEYWORD_CONTINUE,
            self.SEPARATOR_PAREN_RIGHT,
            self.SEPARATOR_BRACE_RIGHT,
            self.SEPARATOR_BRACKET_RIGHT
        ]

        if self.previous_token_type in inject_targets:
            injected = CommonToken(type=self.SEPARATOR_SEMICOLON)
            injected.text = ";"
            injected.line = token.line
            injected.column = token.column

            self.previous_token_type = token.type

            return injected
        else:
            self.previous_token_type = token.type

            return self.nextToken()

    self.previous_token_type = token.type
    return token
}

options{
	language=Python3;
}

// Top-level syntax

program: separation_chain? declaration_chain? separation_chain? EOF;

declaration_chain: (
    struct_declaration
    | interface_declaration
    | function_declaration
    | constant_declaration
    | variable_declaration
) (separation_chain declaration_chain)?;

// Struct syntax

struct_declaration: KEYWORD_TYPE IDENTIFIER KEYWORD_STRUCT
    SEPARATOR_BRACE_LEFT
    struct_field_chain? separation_chain
    SEPARATOR_BRACE_RIGHT;

struct_field_chain: IDENTIFIER typename (separation_chain struct_field_chain)?;

// Interface syntax

interface_declaration: KEYWORD_TYPE IDENTIFIER KEYWORD_INTERFACE SEPARATOR_BRACE_LEFT
    interface_method_chain? separation_chain
    SEPARATOR_BRACE_RIGHT;

interface_method_chain: (
    IDENTIFIER
    SEPARATOR_PAREN_LEFT
    function_parameter_chain?
    SEPARATOR_PAREN_RIGHT typename?
) (separation_chain interface_method_chain)?;

// Function/method syntax

function_declaration: KEYWORD_FUNC function_receiver_type? IDENTIFIER
    SEPARATOR_PAREN_LEFT function_parameter_chain? SEPARATOR_PAREN_RIGHT typename?
    codeblock;

function_receiver_type: SEPARATOR_PAREN_LEFT IDENTIFIER typename SEPARATOR_PAREN_RIGHT;

// Things that look and quack like functions (and various parts of it)

function_parameter_chain: comma_separated_identifier_chain typename (comma_separation function_parameter_chain)?;
comma_separated_identifier_chain: IDENTIFIER (comma_separation comma_separated_identifier_chain)?;

// Constant and variable declaration syntax

constant_declaration: KEYWORD_CONST IDENTIFIER typename? OPERATOR_INITIALIZE expression;
variable_declaration: KEYWORD_VAR IDENTIFIER (typename? OPERATOR_INITIALIZE expression | typename);

// Statement syntax

codeblock: SEPARATOR_BRACE_LEFT separation_chain? (statement_chain separation_chain?)? SEPARATOR_BRACE_RIGHT;

statement_chain: statement (separation_chain statement_chain)?;

statement:
    constant_declaration
    | variable_declaration
    | assigning_statement
    | conditional_statement
    | while_loop_statement
    | c_style_for_loop_statement
    | iteration_for_loop_statement
    | function_call
    | expression
    | break_statement
    | continue_statement
    | return_statement;

// Assignment & assigning-operation syntax

assigning_statement: assignment_left_hand_side assigning_operator expression;

assigning_operator:
    OPERATOR_REASSIGN
    | OPERATOR_ADD_ASSIGN
    | OPERATOR_DIV_ASSIGN
    | OPERATOR_MUL_ASSIGN
    | OPERATOR_SUB_ASSIGN
    | OPERATOR_MOD_ASSIGN;

assignment_left_hand_side:
    IDENTIFIER
    | assignment_left_hand_side struct_member_selection
    | assignment_left_hand_side array_indexing_chain;

// Conditionals and loops

conditional_statement:
    KEYWORD_IF SEPARATOR_PAREN_LEFT expression SEPARATOR_PAREN_RIGHT
    codeblock
    conditional_statement_else_tail?;

conditional_statement_else_tail: KEYWORD_ELSE (codeblock | conditional_statement);

while_loop_statement: KEYWORD_FOR expression codeblock;

c_style_for_loop_initialization: assigning_statement | variable_declaration;

c_style_for_loop_statement:
    KEYWORD_FOR
    c_style_for_loop_initialization semicolon_separation
    expression semicolon_separation
    assigning_statement
    codeblock;

iteration_for_loop_statement:
    KEYWORD_FOR IDENTIFIER comma_separation IDENTIFIER OPERATOR_REASSIGN KEYWORD_RANGE expression
    codeblock;

// Break, continue, return

break_statement: KEYWORD_BREAK;
continue_statement: KEYWORD_CONTINUE;
return_statement: KEYWORD_RETURN expression?;

// Expression syntax

expression: expression OPERATOR_LOGICAL_OR expression_tier_6 | expression_tier_6;
expression_tier_6: expression_tier_6 OPERATOR_LOGICAL_AND expression_tier_5 | expression_tier_5;
expression_tier_5: expression_tier_5 (
    OPERATOR_EQ
    | OPERATOR_INEQ
    | OPERATOR_LESS
    | OPERATOR_LESS_EQ
    | OPERATOR_GREATER
    | OPERATOR_GREATER_EQ
) expression_tier_4 | expression_tier_4;
expression_tier_4: expression_tier_4 (OPERATOR_ADD | OPERATOR_SUB) expression_tier_3 | expression_tier_3;
expression_tier_3: expression_tier_3 (OPERATOR_MUL | OPERATOR_DIV | OPERATOR_MOD) expression_tier_2 | expression_tier_2;
expression_tier_2: (OPERATOR_LOGICAL_NOT | OPERATOR_SUB) expression_tier_2 | expression_tier_1;

expression_tier_1:
    IDENTIFIER
    | literal_nil
    | literal_int
    | literal_float
    | literal_struct
    | literal_bool
    | literal_string
    | literal_array
    | SEPARATOR_PAREN_LEFT expression SEPARATOR_PAREN_RIGHT
    | expression_tier_1 method_call
    | expression_tier_1 struct_member_selection
    | expression_tier_1 array_indexing_chain
    | function_call;

function_call: IDENTIFIER call_syntax;

// Struct/interface members, array indexing, and function calling syntax

struct_member_selection: OPERATOR_DOT IDENTIFIER;
array_indexing_chain: SEPARATOR_BRACKET_LEFT expression SEPARATOR_BRACKET_RIGHT array_indexing_chain?;
call_syntax: SEPARATOR_PAREN_LEFT comma_separated_expression_chain? SEPARATOR_PAREN_RIGHT;

method_call: OPERATOR_DOT IDENTIFIER call_syntax;

comma_separated_expression_chain: expression (comma_separation comma_separated_expression_chain)?;

// Typename syntax

typename: primitive_typename | IDENTIFIER | array_typename;
non_array_typename: primitive_typename | IDENTIFIER;

primitive_typename: KEYWORD_STRING | KEYWORD_INT | KEYWORD_FLOAT | KEYWORD_BOOLEAN;
array_typename: array_dimension_chain non_array_typename;

array_dimension_chain: SEPARATOR_BRACKET_LEFT (literal_int | IDENTIFIER) SEPARATOR_BRACKET_RIGHT array_dimension_chain?;

// Literal syntax

literal_nil: KEYWORD_NIL;
literal_bool: KEYWORD_TRUE | KEYWORD_FALSE;
literal_int: LITERAL_DECIMAL_INT | LITERAL_BINARY_INT | LITERAL_OCTAL_INT | LITERAL_HEX_INT;
literal_float: LITERAL_FLOAT;
literal_string: LITERAL_STRING;

literal_struct: IDENTIFIER SEPARATOR_BRACE_LEFT struct_field_initializer_chain? SEPARATOR_BRACE_RIGHT;
struct_field_initializer_chain: IDENTIFIER SEPARATOR_COLON expression (comma_separation struct_field_initializer_chain)?;

literal_array: array_dimension_chain non_array_typename SEPARATOR_BRACE_LEFT array_literal_value_chain SEPARATOR_BRACE_RIGHT;
array_literal_value_chain: array_literal_value (comma_separation array_literal_value_chain)?;

array_literal_value:
    IDENTIFIER
    | literal_nil
    | literal_bool
    | literal_int
    | literal_float
    | literal_string
    | literal_struct
    | SEPARATOR_BRACE_LEFT array_literal_value_chain SEPARATOR_BRACE_RIGHT;

// Separation & "automatic" semicolon insertion

separation_chain: SEPARATOR_SEMICOLON separation_chain?;
semicolon_separation: SEPARATOR_SEMICOLON;

comma_separation: SEPARATOR_COMMA;

// The below is just lexing.

KEYWORD_IF: 'if';
KEYWORD_ELSE: 'else';
KEYWORD_FOR: 'for';
KEYWORD_RETURN: 'return';
KEYWORD_FUNC: 'func';
KEYWORD_TYPE: 'type';
KEYWORD_STRUCT: 'struct';
KEYWORD_INTERFACE: 'interface';
KEYWORD_CONST: 'const';
KEYWORD_VAR: 'var';
KEYWORD_CONTINUE: 'continue';
KEYWORD_BREAK: 'break';
KEYWORD_RANGE: 'range';
KEYWORD_NIL: 'nil';
KEYWORD_TRUE: 'true';
KEYWORD_FALSE: 'false';

KEYWORD_STRING: 'string';
KEYWORD_INT: 'int';
KEYWORD_FLOAT: 'float';
KEYWORD_BOOLEAN: 'boolean';

OPERATOR_ADD: '+';
OPERATOR_SUB: '-';
OPERATOR_MUL: '*';
OPERATOR_DIV: '/';
OPERATOR_MOD: '%';

OPERATOR_EQ: '==';
OPERATOR_INEQ: '!=';
OPERATOR_LESS: '<';
OPERATOR_LESS_EQ: '<=';
OPERATOR_GREATER: '>';
OPERATOR_GREATER_EQ: '>=';

OPERATOR_LOGICAL_AND: '&&';
OPERATOR_LOGICAL_OR: '||';
OPERATOR_LOGICAL_NOT: '!';

OPERATOR_REASSIGN: ':=';
OPERATOR_ADD_ASSIGN: '+=';
OPERATOR_SUB_ASSIGN: '-=';
OPERATOR_MUL_ASSIGN: '*=';
OPERATOR_DIV_ASSIGN: '/=';
OPERATOR_MOD_ASSIGN: '%=';

OPERATOR_DOT: '.';

OPERATOR_INITIALIZE: '=';

SEPARATOR_PAREN_LEFT: '(';
SEPARATOR_PAREN_RIGHT: ')';
SEPARATOR_BRACE_LEFT: '{';
SEPARATOR_BRACE_RIGHT: '}';
SEPARATOR_BRACKET_LEFT: '[';
SEPARATOR_BRACKET_RIGHT: ']';

SEPARATOR_COLON: ':';
SEPARATOR_SEMICOLON: ';';
SEPARATOR_COMMA: ',';

IDENTIFIER: [a-zA-Z_][a-zA-Z0-9_]*;

fragment NONZERO_DECIMAL_DIGIT: [1-9];
fragment DECIMAL_DIGIT: [0-9];
fragment BINARY_DIGIT: [01];
fragment OCTAL_DIGIT: [0-7];
fragment HEX_DIGIT: [0-9a-fA-F];
fragment FLOAT_EXPONENT: [eE] [+-]? DECIMAL_DIGIT+;

LITERAL_DECIMAL_INT: DECIMAL_DIGIT | NONZERO_DECIMAL_DIGIT DECIMAL_DIGIT+;
LITERAL_BINARY_INT: '0' [bB] BINARY_DIGIT+;
LITERAL_OCTAL_INT: '0' [oO] OCTAL_DIGIT+;
LITERAL_HEX_INT: '0' [xX] HEX_DIGIT+;
LITERAL_FLOAT: DECIMAL_DIGIT+ '.' DECIMAL_DIGIT* FLOAT_EXPONENT?;

fragment LITERAL_STRING_TEXT: (('\\' [rnt"\\]) | ~[\r\n"\\])*;

LITERAL_STRING: '"' LITERAL_STRING_TEXT '"';

NEWLINES: [\r\n]+;

WHITESPACE: [ \f\t\r]+ -> skip; // skip spaces, tabs
COMMENT_LINE: '//' ~[\r\n]* -> skip;
COMMENT_BLOCK: '/*' (COMMENT_BLOCK | COMMENT_TEXT)* '*/' -> skip;
fragment COMMENT_TEXT: ~[*] | [*]~[/];

ERROR_CHAR: .;

UNCLOSE_STRING: '"' LITERAL_STRING_TEXT ('\n' | '\r\n' | EOF ) {
    self.text = self.text.replace('\r', '').replace('\n', '')
};

ILLEGAL_ESCAPE:	'"' LITERAL_STRING_TEXT '\\' ~[rnt"\\];

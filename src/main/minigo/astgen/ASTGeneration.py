from MiniGoVisitor import MiniGoVisitor
from MiniGoParser import MiniGoParser
from AST import *

from src.main.minigo.utils.AST import VoidType

class ASTGeneration(MiniGoVisitor):
    # See: program
    def visitProgram(self, ctx: MiniGoParser.ProgramContext):
        return Program(self.visit(ctx.declaration_chain()))

    # See: declaration_chain
    def visitDeclaration_chain(self, ctx: MiniGoParser.Declaration_chainContext):
        declarations = []
        if ctx.struct_declaration():
            declarations.append(self.visit(ctx.struct_declaration()))
        if ctx.interface_declaration():
            declarations.append(self.visit(ctx.interface_declaration()))
        if ctx.function_declaration():
            declarations.append(self.visit(ctx.function_declaration()))
        if ctx.constant_declaration():
            declarations.append(self.visit(ctx.constant_declaration()))
        if ctx.variable_declaration():
            declarations.append(self.visit(ctx.variable_declaration()))

        if ctx.declaration_chain():
            return declarations + self.visit(ctx.declaration_chain())

        return declarations

    # See: struct_declaration
    def visitStruct_declaration(self, ctx: MiniGoParser.Struct_declarationContext):
        struct_name = ctx.IDENTIFIER().getText()
        struct_fields = self.visit(ctx.struct_field_chain()) if ctx.struct_field_chain() else []

        # TODO:

    # See: struct_field_chain
    def visitStruct_field_chain(self, ctx: MiniGoParser.Struct_field_chainContext):
        return self.visitChildren(ctx)

    # See: interface_declaration
    def visitInterface_declaration(self, ctx: MiniGoParser.Interface_declarationContext):
        return self.visitChildren(ctx)

    # See: interface_method_chain
    def visitInterface_method_chain(self, ctx: MiniGoParser.Interface_method_chainContext):
        return self.visitChildren(ctx)

    # See: function_declaration
    def visitFunction_declaration(self, ctx: MiniGoParser.Function_declarationContext):
        receiver_name, receiver_type = self.visit(ctx.function_receiver_type()) if ctx.function_receiver_type() else (None, None)

        function_name = ctx.IDENTIFIER().getText()
        function_args = self.visit(ctx.function_parameter_chain()) if ctx.function_parameter_chain() else []
        function_return_type = self.visit(ctx.typename()) if ctx.typename() else VoidType()
        function_body = self.visit(ctx.codeblock())

        func = FuncDecl(
            function_name,
            function_args,
            function_return_type,
            function_body
        )

        if receiver_name is not None:
            return MethodDecl(receiver_name, receiver_type, func)

        return func

    # See: function_receiver_type
    def visitFunction_receiver_type(self, ctx: MiniGoParser.Function_receiver_typeContext):
        receiver_name = ctx.IDENTIFIER()
        receiver_type = self.visit(ctx.typename())

        return receiver_name, receiver_type

    # See: function_parameter_chain
    def visitFunction_parameter_chain(self, ctx: MiniGoParser.Function_parameter_chainContext):
        return self.visitChildren(ctx)

    # See: comma_separated_identifier_chain
    def visitComma_separated_identifier_chain(self, ctx: MiniGoParser.Comma_separated_identifier_chainContext):
        one_identifier = [ctx.IDENTIFIER().getText()]
        if ctx.comma_separated_identifier_chain():
            return one_identifier + self.visit(ctx.comma_separated_identifier_chain())
        return one_identifier

    # See: constant_declaration
    def visitConstant_declaration(self, ctx: MiniGoParser.Constant_declarationContext):
        return self.visitChildren(ctx)

    # See: variable_declaration
    def visitVariable_declaration(self, ctx: MiniGoParser.Variable_declarationContext):
        variable_name = ctx.IDENTIFIER().getText()
        variable_type = self.visit(ctx.typename()) if ctx.typename() else None
        variable_initialization = self.visit(ctx.expression()) if ctx.expression() else None

        return VarDecl(variable_name, variable_type, variable_initialization)

    # See: initialized_primitive_variable_declaration
    def visitInitialized_primitive_variable_declaration(self, ctx: MiniGoParser.Initialized_primitive_variable_declarationContext):
        return self.visitChildren(ctx)

    # See: codeblock
    def visitCodeblock(self, ctx: MiniGoParser.CodeblockContext):
        return Block(self.visit(ctx.statement_chain()) if ctx.statement_chain() else [])

    # See: statement_chain
    def visitStatement_chain(self, ctx: MiniGoParser.Statement_chainContext):
        one_statement = [self.visit(ctx.statement())]
        if ctx.statement_chain():
            return one_statement + self.visit(ctx.statement_chain())
        return one_statement

    # See: statement
    def visitStatement(self, ctx: MiniGoParser.StatementContext):
        if ctx.constant_declaration():
            return self.visit(ctx.constant_declaration())
        if ctx.variable_declaration():
            return self.visit(ctx.variable_declaration())
        if ctx.assigning_statement():
            return self.visit(ctx.assigning_statement())
        if ctx.conditional_statement():
            return self.visit(ctx.conditional_statement())
        if ctx.while_loop_statement():
            return self.visit(ctx.while_loop_statement())
        if ctx.c_style_for_loop_statement():
            return self.visit(ctx.c_style_for_loop_statement())
        if ctx.iteration_for_loop_statement():
            return self.visit(ctx.iteration_for_loop_statement())
        if ctx.direct_function_call():
            return self.visit(ctx.direct_function_call())
        if ctx.expression():
            return self.visit(ctx.expression())
        if ctx.break_statement():
            return self.visit(ctx.break_statement())
        if ctx.continue_statement():
            return self.visit(ctx.continue_statement())
        if ctx.return_statement():
            return self.visit(ctx.return_statement())

    # See: assigning_statement
    def visitAssigning_statement(self, ctx: MiniGoParser.Assigning_statementContext):
        return self.visitChildren(ctx)

    # See: assigning_operator
    def visitAssigning_operator(self, ctx: MiniGoParser.Assigning_operatorContext):
        return self.visitChildren(ctx)

    # See: assignment_left_hand_side
    def visitAssignment_left_hand_side(self, ctx: MiniGoParser.Assignment_left_hand_sideContext):
        return self.visitChildren(ctx)

    # See: conditional_statement
    def visitConditional_statement(self, ctx: MiniGoParser.Conditional_statementContext):
        return self.visitChildren(ctx)

    # See: while_loop_statement
    def visitWhile_loop_statement(self, ctx: MiniGoParser.While_loop_statementContext):
        return self.visitChildren(ctx)

    # See: c_style_for_loop_initialization
    def visitC_style_for_loop_initialization(self, ctx: MiniGoParser.C_style_for_loop_initializationContext):
        return self.visitChildren(ctx)

    # See: c_style_for_loop_statement
    def visitC_style_for_loop_statement(self, ctx: MiniGoParser.C_style_for_loop_statementContext):
        return self.visitChildren(ctx)

    # See: iteration_for_loop_statement
    def visitIteration_for_loop_statement(self, ctx: MiniGoParser.Iteration_for_loop_statementContext):
        return self.visitChildren(ctx)

    # See: break_statement
    def visitBreak_statement(self, ctx: MiniGoParser.Break_statementContext):
        return Break()

    # See: continue_statement
    def visitContinue_statement(self, ctx: MiniGoParser.Continue_statementContext):
        return Continue()

    # See: return_statement
    def visitReturn_statement(self, ctx: MiniGoParser.Return_statementContext):
        return Return(self.visit(ctx.expression()) if ctx.expression() else None)

    # See: expression
    def visitExpression(self, ctx: MiniGoParser.ExpressionContext):
        return self.visitChildren(ctx)

    # See: expression_tier_6
    def visitExpression_tier_6(self, ctx: MiniGoParser.Expression_tier_6Context):
        return self.visitChildren(ctx)

    # See: expression_tier_5
    def visitExpression_tier_5(self, ctx: MiniGoParser.Expression_tier_5Context):
        return self.visitChildren(ctx)

    # See: expression_tier_4
    def visitExpression_tier_4(self, ctx: MiniGoParser.Expression_tier_4Context):
        return self.visitChildren(ctx)

    # See: expression_tier_3
    def visitExpression_tier_3(self, ctx: MiniGoParser.Expression_tier_3Context):
        return self.visitChildren(ctx)

    # See: expression_tier_2
    def visitExpression_tier_2(self, ctx: MiniGoParser.Expression_tier_2Context):
        return self.visitChildren(ctx)

    # See: expression_tier_1
    def visitExpression_tier_1(self, ctx: MiniGoParser.Expression_tier_1Context):
        return self.visitChildren(ctx)

    # See: direct_function_call
    def visitDirect_function_call(self, ctx: MiniGoParser.Direct_function_callContext):
        return self.visitChildren(ctx)

    # See: method_call
    def visitMethod_call(self, ctx: MiniGoParser.Method_callContext):
        method_name = ctx.IDENTIFIER().getText()
        call_args = self.visit(ctx.call_syntax())

        return method_name, call_args

    # See: struct_member_selection
    def visitStruct_member_selection(self, ctx: MiniGoParser.Struct_member_selectionContext):
        return self.visitChildren(ctx)

    # See: array_indexing
    def visitArray_indexing(self, ctx: MiniGoParser.Array_indexingContext):
        return self.visitChildren(ctx)

    # See: call_syntax
    def visitCall_syntax(self, ctx: MiniGoParser.Call_syntaxContext):
        return self.visit(ctx.function_call_parameter_chain())

    # See: function_call_parameter_chain
    def visitFunction_call_parameter_chain(self, ctx: MiniGoParser.Function_call_parameter_chainContext):
        one_parameter_expression = [self.visit(ctx.expression())]
        if ctx.function_call_parameter_chain():
            return one_parameter_expression + self.visit(ctx.function_call_parameter_chain())
        return one_parameter_expression

    # See: typename
    def visitTypename(self, ctx: MiniGoParser.TypenameContext):
        if ctx.primitive_typename():
            return self.visit(ctx.primitive_typename())
        if ctx.IDENTIFIER():
            return StructType(ctx.IDENTIFIER().getText(), [], [])

    # See: non_array_typename
    def visitNon_array_typename(self, ctx: MiniGoParser.Non_array_typenameContext):
        return self.visitChildren(ctx)

    # See: primitive_typename
    def visitPrimitive_typename(self, ctx: MiniGoParser.Primitive_typenameContext):
        if ctx.KEYWORD_STRING():
            return StringType()
        if ctx.KEYWORD_INT():
            return IntType()
        if ctx.KEYWORD_FLOAT():
            return FloatType()
        if ctx.KEYWORD_BOOLEAN():
            return BoolType()

    # See: array_typename
    def visitArray_typename(self, ctx: MiniGoParser.Array_typenameContext):
        return self.visitChildren(ctx)

    # See: array_dimension_chain
    def visitArray_dimension_chain(self, ctx: MiniGoParser.Array_dimension_chainContext):
        return self.visitChildren(ctx)

    # See: literal_nil
    def visitLiteral_nil(self, ctx:MiniGoParser.Literal_nilContext):
        return NilLiteral()

    # See: literal_bool
    def visitLiteral_bool(self, ctx: MiniGoParser.Literal_boolContext):
        return self.visitChildren(ctx)

    # See: literal_int
    def visitLiteral_int(self, ctx: MiniGoParser.Literal_intContext):
        return self.visitChildren(ctx)

    # See: literal_float
    def visitLiteral_float(self, ctx: MiniGoParser.Literal_floatContext):
        return self.visitChildren(ctx)

    # See: literal_string
    def visitLiteral_string(self, ctx: MiniGoParser.Literal_stringContext):
        return self.visitChildren(ctx)

    # See: literal_struct
    def visitLiteral_struct(self, ctx: MiniGoParser.Literal_structContext):
        return self.visitChildren(ctx)

    # See: struct_field_initializer_chain
    def visitStruct_field_initializer_chain(self, ctx: MiniGoParser.Struct_field_initializer_chainContext):
        return self.visitChildren(ctx)

    # See: literal_array
    def visitLiteral_array(self, ctx: MiniGoParser.Literal_arrayContext):
        return self.visitChildren(ctx)

    # See: array_literal_value_chain
    def visitArray_literal_value_chain(self, ctx: MiniGoParser.Array_literal_value_chainContext):
        return self.visitChildren(ctx)

    # See: array_literal_value
    def visitArray_literal_value(self, ctx: MiniGoParser.Array_literal_valueContext):
        return self.visitChildren(ctx)

    # # See: separation_chain
    # def visitSeparation_chain(self, ctx: MiniGoParser.Separation_chainContext):
    #     return self.visitChildren(ctx)
    #
    # # See: semicolon_separation
    # def visitSemicolon_separation(self, ctx: MiniGoParser.Semicolon_separationContext):
    #     return self.visitChildren(ctx)
    #
    # # See: comma_separation
    # def visitComma_separation(self, ctx: MiniGoParser.Comma_separationContext):
    #     return self.visitChildren(ctx)

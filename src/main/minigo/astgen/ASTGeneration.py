from MiniGoVisitor import MiniGoVisitor
from MiniGoParser import MiniGoParser
from AST import *

class ASTGeneration(MiniGoVisitor):
    # See: program
    def visitProgram(self, ctx: MiniGoParser.ProgramContext):
        declarations = self.visit(ctx.declaration_chain()) if ctx.declaration_chain() else []
        return Program(declarations)

    # See: declaration_chain
    def visitDeclaration_chain(self, ctx: MiniGoParser.Declaration_chainContext):
        one_declaration = None
        if ctx.struct_declaration():
            one_declaration = [self.visit(ctx.struct_declaration())]
        if ctx.interface_declaration():
            one_declaration = [self.visit(ctx.interface_declaration())]
        if ctx.function_declaration():
            one_declaration = [self.visit(ctx.function_declaration())]
        if ctx.constant_declaration():
            one_declaration = [self.visit(ctx.constant_declaration())]
        if ctx.variable_declaration():
            one_declaration = [self.visit(ctx.variable_declaration())]
        return (one_declaration + self.visit(ctx.declaration_chain())) if ctx.declaration_chain() else one_declaration

    # See: struct_declaration
    def visitStruct_declaration(self, ctx: MiniGoParser.Struct_declarationContext):
        struct_name = ctx.IDENTIFIER().getText()
        struct_fields = self.visit(ctx.struct_field_chain()) if ctx.struct_field_chain() else []

        # NOTE: Nothing in methods for now, apparently it's filled out in static analysis.
        return StructType(struct_name, struct_fields, [])

    # See: struct_field_chain
    def visitStruct_field_chain(self, ctx: MiniGoParser.Struct_field_chainContext):
        field_name = ctx.IDENTIFIER().getText()
        field_type = self.visit(ctx.typename())

        one_struct_field = [(field_name, field_type)]
        return (one_struct_field + self.visit(ctx.struct_field_chain())) if ctx.struct_field_chain() else one_struct_field

    # See: interface_declaration
    def visitInterface_declaration(self, ctx: MiniGoParser.Interface_declarationContext):
        interface_name = ctx.IDENTIFIER().getText()
        interface_methods = self.visit(ctx.interface_method_chain()) if ctx.interface_method_chain() else []

        return InterfaceType(interface_name, interface_methods)

    # See: interface_method_chain
    def visitInterface_method_chain(self, ctx: MiniGoParser.Interface_method_chainContext):
        method_name = ctx.IDENTIFIER().getText()
        named_parameters = self.visit(ctx.function_parameter_chain()) if ctx.function_parameter_chain() else []
        return_type = self.visit(ctx.typename()) if ctx.typename() else VoidType()

        # Prototype wants UNNAMED parameters so we just drop the name.
        unnamed_parameters = [typename for parameter_name, typename in named_parameters]

        one_method = [Prototype(method_name, unnamed_parameters, return_type)]
        return (one_method + self.visit(ctx.interface_method_chain())) if ctx.interface_method_chain() else one_method

    # See: function_declaration
    def visitFunction_declaration(self, ctx: MiniGoParser.Function_declarationContext):
        receiver_name, receiver_type = self.visit(ctx.function_receiver_type()) if ctx.function_receiver_type() else (None, None)

        function_name = ctx.IDENTIFIER().getText()
        function_args = self.visit(ctx.function_parameter_chain()) if ctx.function_parameter_chain() else []
        function_return_type = self.visit(ctx.typename()) if ctx.typename() else VoidType()
        function_body = self.visit(ctx.codeblock())

        # FuncDecl wants INSTANCES OF VarDecl so we just transform it
        arg_decls = [VarDecl(name, typename, None) for name, typename in function_args]

        func = FuncDecl(
            function_name,
            arg_decls,
            function_return_type,
            function_body
        )

        return MethodDecl(receiver_name, receiver_type, func) if receiver_name is not None else func

    # See: function_receiver_type
    def visitFunction_receiver_type(self, ctx: MiniGoParser.Function_receiver_typeContext):
        receiver_name = ctx.IDENTIFIER().getText()
        receiver_type = self.visit(ctx.typename())

        return receiver_name, receiver_type

    # See: function_parameter_chain
    def visitFunction_parameter_chain(self, ctx: MiniGoParser.Function_parameter_chainContext):
        parameter_names = self.visit(ctx.comma_separated_identifier_chain())
        typename = self.visit(ctx.typename())

        parameters = [(parameter_name, typename) for parameter_name in parameter_names]
        return (parameters + self.visit(ctx.function_parameter_chain())) if ctx.function_parameter_chain() else parameters

    # See: comma_separated_identifier_chain
    def visitComma_separated_identifier_chain(self, ctx: MiniGoParser.Comma_separated_identifier_chainContext):
        one_identifier = [ctx.IDENTIFIER().getText()]
        return (one_identifier + self.visit(ctx.comma_separated_identifier_chain())) if ctx.comma_separated_identifier_chain() else one_identifier

    # See: constant_declaration
    def visitConstant_declaration(self, ctx: MiniGoParser.Constant_declarationContext):
        constant_name = ctx.IDENTIFIER().getText()
        constant_type = self.visit(ctx.typename()) if ctx.typename() else None
        constant_initialization = self.visit(ctx.expression()) if ctx.expression() else None

        return ConstDecl(constant_name, constant_type, constant_initialization)

    # See: variable_declaration
    def visitVariable_declaration(self, ctx: MiniGoParser.Variable_declarationContext):
        variable_name = ctx.IDENTIFIER().getText()
        variable_type = self.visit(ctx.typename()) if ctx.typename() else None
        variable_initialization = self.visit(ctx.expression()) if ctx.expression() else None

        return VarDecl(variable_name, variable_type, variable_initialization)

    # See: codeblock
    def visitCodeblock(self, ctx: MiniGoParser.CodeblockContext):
        return Block(self.visit(ctx.statement_chain()) if ctx.statement_chain() else [])

    # See: statement_chain
    def visitStatement_chain(self, ctx: MiniGoParser.Statement_chainContext):
        one_statement = [self.visit(ctx.statement())]
        return (one_statement + self.visit(ctx.statement_chain())) if ctx.statement_chain() else one_statement

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
        if ctx.function_call():
            return self.visit(ctx.function_call())
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
        lhs = self.visit(ctx.assignment_left_hand_side())
        rhs = self.visit(ctx.expression())

        operator_ctx: MiniGoParser.Assigning_operatorContext = ctx.assigning_operator()
        if operator_ctx.OPERATOR_REASSIGN():
            return Assign(lhs, rhs)
        if operator_ctx.OPERATOR_ADD_ASSIGN():
            return Assign(lhs, BinaryOp("+", lhs, rhs))
        if operator_ctx.OPERATOR_DIV_ASSIGN():
            return Assign(lhs, BinaryOp("/", lhs, rhs))
        if operator_ctx.OPERATOR_MUL_ASSIGN():
            return Assign(lhs, BinaryOp("*", lhs, rhs))
        if operator_ctx.OPERATOR_SUB_ASSIGN():
            return Assign(lhs, BinaryOp("-", lhs, rhs))
        if operator_ctx.OPERATOR_MOD_ASSIGN():
            return Assign(lhs, BinaryOp("%", lhs, rhs))

    # See: assigning_operator
    def visitAssigning_operator(self, ctx: MiniGoParser.Assigning_operatorContext):
        # Note that this is unused!
        operator_str = ctx.getText()
        return operator_str

    # See: assignment_left_hand_side
    def visitAssignment_left_hand_side(self, ctx: MiniGoParser.Assignment_left_hand_sideContext):
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())
        if ctx.struct_member_selection():
            receiver = self.visit(ctx.assignment_left_hand_side())
            selection = self.visit(ctx.struct_member_selection())
            return FieldAccess(receiver, selection)
        if ctx.array_indexing():
            receiver = self.visit(ctx.assignment_left_hand_side())
            indices = self.visit(ctx.array_indexing())
            return ArrayCell(receiver, indices)

    # See: conditional_statement
    def visitConditional_statement(self, ctx: MiniGoParser.Conditional_statementContext):
        condition = self.visit(ctx.expression())
        then_block = self.visit(ctx.codeblock())
        else_tail = self.visit(ctx.conditional_statement_else_tail()) if ctx.conditional_statement_else_tail() else None

        return If(condition, then_block, else_tail)

    # See: conditional_statement_else_tail
    def visitConditional_statement_else_tail(self, ctx:MiniGoParser.Conditional_statement_else_tailContext):
        if ctx.codeblock():
            return self.visit(ctx.codeblock())
        if ctx.conditional_statement():
            return Block([self.visit(ctx.conditional_statement())])

    # See: while_loop_statement
    def visitWhile_loop_statement(self, ctx: MiniGoParser.While_loop_statementContext):
        condition = self.visit(ctx.expression())
        block = self.visit(ctx.codeblock())

        return ForBasic(condition, block)

    # See: c_style_for_loop_initialization
    def visitC_style_for_loop_initialization(self, ctx: MiniGoParser.C_style_for_loop_initializationContext):
        if ctx.assigning_statement():
            return self.visit(ctx.assigning_statement())
        return self.visit(ctx.variable_declaration())

    # See: c_style_for_loop_statement
    def visitC_style_for_loop_statement(self, ctx: MiniGoParser.C_style_for_loop_statementContext):
        initialization = self.visit(ctx.c_style_for_loop_initialization())
        condition = self.visit(ctx.expression())
        updater = self.visit(ctx.assigning_statement())
        block = self.visit(ctx.codeblock())

        return ForStep(initialization, condition, updater, block)

    # See: iteration_for_loop_statement
    def visitIteration_for_loop_statement(self, ctx: MiniGoParser.Iteration_for_loop_statementContext):
        index_var_identifier = ctx.IDENTIFIER(0)
        value_var_identifier = ctx.IDENTIFIER(1)
        target = self.visit(ctx.expression())
        block = self.visit(ctx.codeblock())

        return ForEach(index_var_identifier, value_var_identifier, target, block)

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
        if ctx.expression():
            return BinaryOp("||", self.visit(ctx.expression()), self.visit(ctx.expression_tier_6()))
        return self.visit(ctx.expression_tier_6())

    # See: expression_tier_6
    def visitExpression_tier_6(self, ctx: MiniGoParser.Expression_tier_6Context):
        if ctx.expression_tier_6():
            return BinaryOp("&&", self.visit(ctx.expression_tier_6()), self.visit(ctx.expression_tier_5()))
        return self.visit(ctx.expression_tier_5())

    # See: expression_tier_5
    def visitExpression_tier_5(self, ctx: MiniGoParser.Expression_tier_5Context):
        if ctx.expression_tier_5():
            operator = None
            if ctx.OPERATOR_EQ():
                operator = ctx.OPERATOR_EQ().getText()
            if ctx.OPERATOR_INEQ():
                operator = ctx.OPERATOR_INEQ().getText()
            if ctx.OPERATOR_LESS():
                operator = ctx.OPERATOR_LESS().getText()
            if ctx.OPERATOR_LESS_EQ():
                operator = ctx.OPERATOR_LESS_EQ().getText()
            if ctx.OPERATOR_GREATER():
                operator = ctx.OPERATOR_GREATER().getText()
            if ctx.OPERATOR_GREATER_EQ():
                operator = ctx.OPERATOR_GREATER_EQ().getText()
            return BinaryOp(operator, self.visit(ctx.expression_tier_5()), self.visit(ctx.expression_tier_4()))
        return self.visit(ctx.expression_tier_4())

    # See: expression_tier_4
    def visitExpression_tier_4(self, ctx: MiniGoParser.Expression_tier_4Context):
        if ctx.expression_tier_4():
            operator = None
            if ctx.OPERATOR_ADD():
                operator = ctx.OPERATOR_ADD().getText()
            if ctx.OPERATOR_SUB():
                operator = ctx.OPERATOR_SUB().getText()
            return BinaryOp(operator, self.visit(ctx.expression_tier_4()), self.visit(ctx.expression_tier_3()))
        return self.visit(ctx.expression_tier_3())

    # See: expression_tier_3
    def visitExpression_tier_3(self, ctx: MiniGoParser.Expression_tier_3Context):
        if ctx.expression_tier_3():
            operator = None
            if ctx.OPERATOR_MUL():
                operator = ctx.OPERATOR_MUL().getText()
            if ctx.OPERATOR_DIV():
                operator = ctx.OPERATOR_DIV().getText()
            if ctx.OPERATOR_MOD():
                operator = ctx.OPERATOR_MOD().getText()
            return BinaryOp(operator, self.visit(ctx.expression_tier_3()), self.visit(ctx.expression_tier_2()))
        return self.visit(ctx.expression_tier_2())

    # See: expression_tier_2
    def visitExpression_tier_2(self, ctx: MiniGoParser.Expression_tier_2Context):
        if ctx.expression_tier_2():
            operator = None
            if ctx.OPERATOR_LOGICAL_NOT():
                operator = ctx.OPERATOR_LOGICAL_NOT().getText()
            if ctx.OPERATOR_SUB():
                operator = ctx.OPERATOR_SUB().getText()
            return UnaryOp(operator, self.visit(ctx.expression_tier_2()))
        return self.visit(ctx.expression_tier_1())

    # See: expression_tier_1
    def visitExpression_tier_1(self, ctx: MiniGoParser.Expression_tier_1Context):
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())

        if ctx.literal_nil():
            return self.visit(ctx.literal_nil())
        if ctx.literal_int():
            return self.visit(ctx.literal_int())
        if ctx.literal_float():
            return self.visit(ctx.literal_float())
        if ctx.literal_struct():
            return self.visit(ctx.literal_struct())
        if ctx.literal_bool():
            return self.visit(ctx.literal_bool())
        if ctx.literal_string():
            return self.visit(ctx.literal_string())
        if ctx.literal_array():
            return self.visit(ctx.literal_array())

        if ctx.expression():
            return self.visit(ctx.expression())

        if ctx.method_call():
            receiver = self.visit(ctx.expression_tier_1())
            method_name, call_args = self.visit(ctx.method_call())
            return MethCall(receiver, method_name, call_args)
        if ctx.struct_member_selection():
            receiver = self.visit(ctx.expression_tier_1())
            field_name = self.visit(ctx.struct_member_selection())
            return FieldAccess(receiver, field_name)
        if ctx.array_indexing():
            receiver = self.visit(ctx.expression_tier_1())
            indices = self.visit(ctx.array_indexing())
            return ArrayCell(receiver, indices)

        if ctx.function_call():
            return self.visit(ctx.function_call())

    # See: function_call
    def visitFunction_call(self, ctx: MiniGoParser.Function_callContext):
        function_name = ctx.IDENTIFIER().getText()
        call_args = self.visit(ctx.call_syntax())

        return FuncCall(function_name, call_args)

    # See: method_call
    def visitMethod_call(self, ctx: MiniGoParser.Method_callContext):
        method_name = ctx.IDENTIFIER().getText()
        call_args = self.visit(ctx.call_syntax())

        return method_name, call_args

    # See: struct_member_selection
    def visitStruct_member_selection(self, ctx: MiniGoParser.Struct_member_selectionContext):
        return ctx.IDENTIFIER().getText()

    # See: array_indexing
    def visitArray_indexing(self, ctx: MiniGoParser.Array_indexingContext):
        return self.visit(ctx.comma_separated_expression_chain())

    # See: call_syntax
    def visitCall_syntax(self, ctx: MiniGoParser.Call_syntaxContext):
        return self.visit(ctx.comma_separated_expression_chain()) if ctx.comma_separated_expression_chain() else []

    # See: comma_separated_expression_chain
    def visitComma_separated_expression_chain(self, ctx: MiniGoParser.Comma_separated_expression_chainContext):
        one_parameter = [self.visit(ctx.expression())]
        return (one_parameter + self.visit(ctx.comma_separated_expression_chain())) if ctx.comma_separated_expression_chain() else one_parameter

    # See: typename
    def visitTypename(self, ctx: MiniGoParser.TypenameContext):
        if ctx.primitive_typename():
            return self.visit(ctx.primitive_typename())
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())
        if ctx.array_typename():
            return self.visit(ctx.array_typename())

    # See: non_array_typename
    def visitNon_array_typename(self, ctx: MiniGoParser.Non_array_typenameContext):
        if ctx.primitive_typename():
            return self.visit(ctx.primitive_typename())
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())

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
        cell_type = self.visit(ctx.non_array_typename())
        dimensions = self.visit(ctx.array_dimension_chain())

        return ArrayType(dimensions, cell_type)

    # See: array_dimension_chain
    def visitArray_dimension_chain(self, ctx: MiniGoParser.Array_dimension_chainContext):
        one_dimension = [self.visit(ctx.literal_int()) if ctx.literal_int() else Id(ctx.IDENTIFIER().getText())]
        return (one_dimension + self.visit(ctx.array_dimension_chain())) if ctx.array_dimension_chain() else one_dimension

    # See: literal_nil
    def visitLiteral_nil(self, ctx:MiniGoParser.Literal_nilContext):
        return NilLiteral()

    # See: literal_bool
    def visitLiteral_bool(self, ctx: MiniGoParser.Literal_boolContext):
        if ctx.KEYWORD_TRUE():
            return BooleanLiteral(True)
        return BooleanLiteral(False)

    # See: literal_int
    def visitLiteral_int(self, ctx: MiniGoParser.Literal_intContext):
        if ctx.LITERAL_DECIMAL_INT():
            return IntLiteral(int(ctx.LITERAL_DECIMAL_INT().getText()))
        if ctx.LITERAL_BINARY_INT():
            return IntLiteral(int(ctx.LITERAL_BINARY_INT().getText(), 2))
        if ctx.LITERAL_OCTAL_INT():
            return IntLiteral(int(ctx.LITERAL_OCTAL_INT().getText(), 8))
        if ctx.LITERAL_HEX_INT():
            return IntLiteral(int(ctx.LITERAL_HEX_INT().getText(), 16))

    # See: literal_float
    def visitLiteral_float(self, ctx: MiniGoParser.Literal_floatContext):
        return FloatLiteral(float(ctx.LITERAL_FLOAT().getText()))

    # See: literal_string
    def visitLiteral_string(self, ctx: MiniGoParser.Literal_stringContext):
        return StringLiteral(ctx.LITERAL_STRING().getText())

    # See: literal_struct
    def visitLiteral_struct(self, ctx: MiniGoParser.Literal_structContext):
        struct_name = ctx.IDENTIFIER().getText()
        field_initializers = self.visit(ctx.struct_field_initializer_chain()) if ctx.struct_field_initializer_chain() else []

        return StructLiteral(struct_name, field_initializers)

    # See: struct_field_initializer_chain
    def visitStruct_field_initializer_chain(self, ctx: MiniGoParser.Struct_field_initializer_chainContext):
        field_name = ctx.IDENTIFIER().getText()
        field_value = self.visit(ctx.expression())

        one_field = [(field_name, field_value)]
        return (one_field + self.visit(ctx.struct_field_initializer_chain())) if ctx.struct_field_initializer_chain() else one_field

    # See: literal_array
    def visitLiteral_array(self, ctx: MiniGoParser.Literal_arrayContext):
        cell_type = self.visit(ctx.non_array_typename())
        dimensions = self.visit(ctx.array_dimension_chain())
        vals = self.visit(ctx.array_dimension_chain())
        return ArrayLiteral(dimensions, cell_type, vals)

    # See: array_literal_value_chain
    def visitArray_literal_value_chain(self, ctx: MiniGoParser.Array_literal_value_chainContext):
        one_value = [self.visit(ctx.array_literal_value())]
        return (one_value + self.visit(ctx.array_literal_value_chain())) if ctx.array_literal_value_chain() else one_value

    # See: array_literal_value
    def visitArray_literal_value(self, ctx: MiniGoParser.Array_literal_valueContext):
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())
        if ctx.literal_nil():
            return self.visit(ctx.literal_nil())
        if ctx.literal_bool():
            return self.visit(ctx.literal_bool())
        if ctx.literal_int():
            return self.visit(ctx.literal_int())
        if ctx.literal_float():
            return self.visit(ctx.literal_float())
        if ctx.literal_string():
            return self.visit(ctx.literal_string())
        if ctx.literal_struct():
            return self.visit(ctx.literal_struct())
        return self.visit(ctx.array_literal_value_chain())

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

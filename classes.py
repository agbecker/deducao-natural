from enum import Enum
import re

# Symbols
land = '∧'
lor = '∨'
lnot = '¬'
lto = '→'

# Precedence of operations
NOT = 0
AND = 1
OR = 2
IMPLY = 3

logical_symbols = {lnot:NOT, land:AND, lor:OR, lto:IMPLY}
logical_symbols_lookup = {NOT:lnot, AND:land, OR:lor, IMPLY:lto, None:'None'}

# Rules
ANDE1 = 0
ANDE2 = 1
ANDI = 2
ORI1 = 3
ORI2 = 4
ORE = 5
TOI = 6
TOE = 7
FE = 8
FI = 9
NOTI = 10
NOTNOT = 11
EM = 12

class Formula():
    def __init__(self, literal):
        self.parse_literal(literal)

    def preprocess_literal(self, literal):
        while re.fullmatch(r'\(.+\)', literal):
            literal = literal[1:-1]

        literal = re.sub(r'or|\|+|\\/', lor, literal)
        literal = re.sub(r'and|&+|/\\', land, literal)
        literal = re.sub(r'not|!|~', lnot, literal)
        literal = re.sub(r'->|to', lto, literal)
        return literal.replace(' ', '')

    def parse_literal(self, literal):
        literal = self.preprocess_literal(literal)

        # Obtains the operator and subformulas
        depth = 0
        op = None   # Outermost operator on the formula
        op_position = 0
        
        for i, c in enumerate(literal):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif c in logical_symbols:
                pre = logical_symbols[c]
                if op is None or op < pre:
                    op = pre
                    op_position = i        

        self.operator = op
        if self.operator is None:
            self.subformulas = [literal] # Atomic variable formula

        elif self.operator == NOT:
            self.subformulas = [literal[1:]]
        
        else:
            self.subformulas = [literal[:op_position], literal[op_position+1:]]

    def __str__(self):
        if self.operator is None:
            return self.subformulas[0]
        if self.operator is NOT:
            return f'{lnot}{self.subformulas[0]}'
        else:
            return f'{self.subformulas[0]}{logical_symbols_lookup[self.operator]}{self.subformulas[1]}'
        
    def __repr__(self):
        ret = str(self)
        ret += f'\nOperator: {logical_symbols_lookup[self.operator]}'
        ret += f'\nSubformulas: {self.subformulas}\n'
        return ret
    
    def __eq__(self, other):
        if type(other) is not Formula:
            return False
        
        return self.operator == other.operator and self.subformulas == other.subformulas

class FormulaNode():
    def __init__(self, formula, parent = None, child = None):
        if type(formula) is str:
            formula = Formula(formula)
        self.formula = formula
        self.operator = formula.operator
        self.subformulas = formula.subformulas

        # Parent and child are rules.
        # A formula with no parent is an unresolved branch.
        # Only the root formula will have no child.
        self.parent = parent
        self.child = child

    def __str__(self):
        return str(self.formula)
    
    def expand(self, rule):
        if not self.rule_fits_operation(rule):
            return
        
        rule_node = RuleNode(rule, child=self)
        self.parent = rule_node
        rule_node.expand()
        
    def rule_fits_operation(self, rule):
        operator = self.formula.operator

        # And só é gerado pela inclusão
        if operator == AND:
            return rule == ANDI
        
        # Or só é gerado pelas inclusões
        if operator == OR:
            return rule in (ORI1, ORI2) or rule == EM and self.check_excluded_middle(self.formula)
        
        # Implicação só é gerada pela inclusão
        if operator == IMPLY:
            return rule == TOI
        
        # Negação só é gerada pela inclusão
        if operator == NOT:
            return rule == NOTI
        
        # As seguintes regras podem gerar fórmulas em qualquer formato:
        # Exclusões do and, exclusão do or, exclusão do false, exclusão da implicação, exclusão da dupla negação
        return operator is None and rule in (ANDE1, ANDE2, ORE, FE, TOE, NOTNOT)

    def check_excluded_middle(self, formula):
        pass

class RuleNode():
    def __init__(self, rule, parents = [], child = None):
        self.rule = rule # The rule being applied

        # Parents and child are all formulas.
        # The number of parents and their respective types are determined by the rule type
        # All rules have exactly one child
        self.child = child
        self.parents = parents

    def expand(self):
        if self.rule == ANDI:
            self.and_inclusion()

    def and_inclusion(self):
        left = self.child.subformulas[0]
        right = self.child.subformulas[1]

        self.parents = [FormulaNode(left), FormulaNode(right)]


root = FormulaNode('((p&q))')
print(root)

root.expand(ANDI)
for p in root.parent.parents:
    print(p)

#### Pensamentos
# Se tiver uma disjunção, clicar VI1 ou VI2 resolve automaticamente, botando como pai o lado esquerdo ou direito
# Analogamente, AI bota os dois lados como pais
# AE vai requerer escrever o outro lado da expressão (ou talvez a expressão completa?)
# Da mesma forma, VE requer escrever a disjunção em análise (mas reaproveita o filho)

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

class FormulaNode():
    def __init__(self, formula, parent = None, child = None):
        self.formula = formula

        # Parent and child are rules.
        # A formula with no parent is an unresolved branch.
        # Only the root formula will have no child.
        self.parent = parent
        self.child = child

class RuleNode():
    def __init__(self, type, parents = [], child = None):
        self.type = type

        # Parents and child are all formulas.
        # The number of parents and their respective types are determined by the rule type
        # All rules have exactly one child
        pass


a = Formula('((p&q->not q||r))')
print(repr(a))

b = Formula(a.subformulas[1])
print(repr(b))

c = Formula(b.subformulas[1])
print(repr(c))

#### Pensamentos
# Se tiver uma disjunção, clicar VI1 ou VI2 resolve automaticamente, botando como pai o lado esquerdo ou direito
# Analogamente, AI bota os dois lados como pais
# AE vai requerer escrever o outro lado da expressão (ou talvez a expressão completa?)
# Da mesma forma, VE requer escrever a disjunção em análise (mas reaproveita o filho)

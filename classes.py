from enum import Enum
import re

# Symbols
land = '∧'
lor = '∨'
lnot = '¬'
lto = '→'
lfalse = '⊥'

# Precedence of operations
FALSE = -1
NOT = 0
AND = 1
OR = 2
IMPLY = 3

logical_symbols = {lnot:NOT, land:AND, lor:OR, lto:IMPLY}
logical_symbols_lookup = {NOT:lnot, AND:land, OR:lor, IMPLY:lto, None:'None', FALSE:lfalse}

# Rules
ANDE1 = 0
ANDE2 = 1
ANDI = 2
ORI1 = 3
ORI2 = 4
ORE = 5
TOI = 6
TOE = 7
FE = NOTE = 8
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

        if literal == lfalse:
            self.operator = FALSE
            self.subformulas = []
            return

        # Obtains the operator and subformulas
        depth = 0
        op = None   # Outermost operator on the formula
        op_position = 0
        
        for i, c in enumerate(literal):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif depth == 0 and c in logical_symbols:
                pre = logical_symbols[c]
                if op is None or op < pre:
                    op = pre
                    op_position = i        

        self.operator = op
        if self.operator is None:
            self.subformulas = [literal] # Atomic variable formula

        elif self.operator == NOT:
            sub = literal[1:]
            sub = Formula(sub)
            if sub.operator is not None and sub.operator > NOT:
                sub = f'({sub})'
            self.subformulas = [str(sub)]
        
        else:
            left = literal[:op_position]
            right = literal[op_position+1:]

            left = Formula(left)
            right = Formula(right)

            if left.operator is not None and left.operator > op:
                left = f'({left})'
            if right.operator is not None and right.operator > op:
                right = f'({right})'

            self.subformulas = [left, right]

    def __str__(self):
        if self.operator == FALSE:
            return lfalse
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
    def __init__(self, formula, tree, branch, parent = None, child = None):
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

        # The tree all nodes belong to
        self.tree = tree
        self.branch = branch

    def __str__(self):
        return str(self.formula)
    
    def expand(self, rule):
        if not self.rule_fits_operation(rule):
            return
        
        rule_node = RuleNode(rule, child=self, tree=self.tree, branch=self.branch,)
        self.parent = rule_node
        rule_node.expand()
        
    def rule_fits_operation(self, rule):
        # As seguintes regras podem gerar fórmulas em qualquer formato:
        # Exclusões do and, exclusão do or, exclusão do false, exclusão da implicação, exclusão da dupla negação
        if rule in (ANDE1, ANDE2, ORE, FE, TOE, NOTNOT):
            return True

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
        
        

    def check_excluded_middle(self, formula):
        pass

class RuleNode():
    def __init__(self, rule, tree, branch, parents = [], child = None):
        self.rule = rule # The rule being applied

        # Parents and child are all formulas.
        # The number of parents and their respective types are determined by the rule type
        # All rules have exactly one child
        self.child = child
        self.parents = parents

        self.tree = tree
        self.branch = branch

    def expand(self):
        # Rules which can automatically deduce the parent(s), without specification
        if self.rule == ANDI:
            self.and_inclusion()

        if self.rule == FE:
            self.false_elim()

        if self.rule == ORI1:
            self.or_intro_left()

        if self.rule == ORI2:
            self.or_intro_right()

        if self.rule == NOTNOT:
            self.double_not()

        if self.rule == TOI:
            self.imply_intro()

        if self.rule == NOTI:
            self.not_intro()

        # Rules which require further input

    def and_inclusion(self):
        left = self.child.subformulas[0]
        right = self.child.subformulas[1]

        self.parents = [FormulaNode(left, self.tree, self.branch+'0'), FormulaNode(right, self.tree, self.branch+'1')]
        self.tree.add_branch(self.branch+'0')
        self.tree.add_branch(self.branch+'1')

    def false_elim(self):
        self.parents = [FormulaNode(lfalse, self.tree, self.branch)]

    def not_intro(self):
        pre = self.child.subformulas[0]

        self.parents = [FormulaNode(lfalse, self.tree, self.branch+'0')]
        self.tree.add_branch(self.branch+'0', pre)

    def double_not(self):
        formula = str(self.child)
        # Must include parenthesis if not atomic
        if self.child.operator is not None:
            formula = f'({formula})'

        self.parents = [FormulaNode(f'!!{formula}', self.tree, self.branch)]

    def imply_intro(self):
        pre = self.child.subformulas[0]
        cons = self.child.subformulas[1]

        self.parents = [FormulaNode(cons, self.tree, self.branch+'0')]
        self.tree.add_branch(self.branch+'0', pre)

    def or_intro_left(self):
        left = self.child.subformulas[0]
        self.parents = [FormulaNode(left, self.tree, self.branch)]

    def or_intro_right(self):
        right = self.child.subformulas[1]
        self.parents = [FormulaNode(right, self.tree, self.branch)]

class Tree():
    def __init__(self, goal, hypotheses = []):
        self.root = FormulaNode(goal, tree=self, branch='0')
        self.hypotheses = [Formula(h) for h in hypotheses]
        
        # Branches
        self.branches = {'0'}
        self.active_branches = {'0'}
        self.branch_assumptions = {'0':[]}

    def add_branch(self, new_branch, assumption = None):
        self.branches.add(new_branch)
        self.active_branches.add(new_branch)

        old_branch = new_branch[:-1]
        self.branch_assumptions[new_branch] = [x for x in self.branch_assumptions[old_branch]]
        if assumption is not None:
            self.branch_assumptions[new_branch].append(assumption)

    def get_hypotheses(self, node):
        branch = node.branch
        assumptions = self.branch_assumptions[branch]
        return self.hypotheses + assumptions

tree = Tree('!p', ['!t'])
root = tree.root
print(root)

root.expand(NOTI)
for p in root.parent.parents:
    print(p, p.branch)
    print(tree.get_hypotheses(p))
print(tree.get_hypotheses(root))

# for h in tree.hypotheses:
#     print(h)

#### Pensamentos
# Preciso achar uma maneira de tratar o False/Bottom, em termos de enumeração.
# Também preciso desenvolver um tracking de que ramo o usuário está atualmente,
# pra monitorar as hipóteses assumidas de cada ramo. Acho que fazer os nodos guardarem o menor ramo ao qual pertencem e,
# toda vez que uma operação gera uma bifurcação ou introdução de hipótese, fazer eles solicitarem à árvore um novo número de ramo.
# O ramo então copia a lista de hipóteses do ramo ao qual já pertencia e vai adicionando suas novas.
# O programa verifica o ramo em análise para listar as hipóteses ativas.
# Também preciso identificar quando um nodo de regra foi satisfeito e propagar seu fechamento pra baixo
# Até que a árvore detecte que todos os ramos foram fechados
# E, auxiliarmente, ser capaz de reverter a árvore a um estado anterior, cortando um ramo.
# Além de ser capaz de identificar o ramo/nodo atualmente em análise
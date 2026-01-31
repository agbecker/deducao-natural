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
HYP = 13

class Formula():
    def __init__(self, literal):
        self.parse_literal(literal)

    def deparenthise(self, literal):
        while literal[0] == '(' and literal[-1] == ')':
            depth = 0
            n = len(literal)
            for i, c in enumerate(literal):
                if c == '(':
                    depth += 1
                if c == ')':
                    depth -= 1
                    if depth == 0 and i < n-1:
                        return literal
            literal = literal[1:-1]
        return literal

    def preprocess_literal(self, literal):
        literal = self.deparenthise(literal)

        literal = re.sub(r'or|\|+|\\/', lor, literal)
        literal = re.sub(r'and|&+|/\\', land, literal)
        literal = re.sub(r'not|!|~', lnot, literal)
        literal = re.sub(r'->|to', lto, literal)
        return literal.replace(' ', '')
    
    def check_syntax_errors(self, literal):
        # Verifica ocorrência de letras em sequência
        if s := re.search(r'\w\w', literal):
            msg = f'Proposições devem ser compostas por uma única letra. Sua fórmula contém o trecho [{s.group()}].'
            raise FormulaSyntaxError(msg)
        
        # Verifica erros de parênteses
        count_open = literal.count('(')
        count_close = literal.count(')')

        if count_open != count_close:
            if count_open > count_close:
                msg = "Há um parênteses '(' na sua fórmula que não foi fechado."
            else:
                msg = "Há um fecha parênteses ')' sobrando na sua fórmula."
            raise FormulaSyntaxError(msg)
        
        # Verifica operadores sem variáveis
        if s := re.search(r'[(∧∨¬→][∧∨→)]', literal):
            msg = f"O seguinte trecho inclui um operador sem variável: [{s.group()}]"
            raise FormulaSyntaxError(msg)
        
        if literal[0] in '∧∨→':
            msg = "Há um operador sem proposição no começo da fórmula."
            raise FormulaSyntaxError(msg)
        
        if literal[-1] in '∧∨¬→':
            msg = "Há um operador sem proposição no final da fórmula."
            raise FormulaSyntaxError(msg)

    def parse_literal(self, literal):
        if type(literal) is Formula:
            literal = str(literal)
        literal = self.preprocess_literal(literal)

        self.check_syntax_errors(literal)

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
                if depth < 0:
                    raise FormulaSyntaxError('Você fechou um parênteses que nunca abriu.')
            elif depth == 0 and c in logical_symbols:
                pre = logical_symbols[c]
                if op is None or op < pre:
                    op = pre
                    op_position = i        
        if depth != 0:
            raise FormulaSyntaxError('Você abriu um parênteses que nunca fechou.')

        self.operator = op
        if self.operator is None:
            self.subformulas = [literal] # Atomic variable formula

        elif self.operator == NOT:
            sub = literal[1:]
            sub = Formula(sub)
            self.subformulas = [str(sub)]
        
        else:
            left = literal[:op_position]
            right = literal[op_position+1:]

            left = Formula(left)
            right = Formula(right)

            self.subformulas = [str(left), str(right)]

    def __str__(self):
        if self.operator == FALSE:
            return lfalse
        if self.operator is None:
            return self.subformulas[0]
        if self.operator is NOT:
            sub = Formula(self.subformulas[0])
            if sub.operator is not None and sub.operator > NOT:
                sub = f'({sub})'
            return f'{lnot}{sub}'
        else:
            left = Formula(self.subformulas[0])
            right = Formula(self.subformulas[1])

            if left.operator is not None and left.operator >= self.operator:
                left = f'({left})'
            if right.operator is not None and right.operator > self.operator:
                right = f'({right})'
            return f'{left}{logical_symbols_lookup[self.operator]}{right}'
        
    def __repr__(self):
        ret = str(self)
        ret += f'\nOperator: {logical_symbols_lookup[self.operator]}'
        ret += f'\nSubformulas: {self.subformulas}\n'
        return ret
    
    def __eq__(self, other):
        if type(other) is not Formula:
            if type(other) is str:
                other = Formula(other)
            else:
                return False

        return self.operator == other.operator and self.subformulas == other.subformulas
    
class FormulaSyntaxError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    def __str__(self):
        return super().__str__()

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
        self.tree.set_branch_top(self)

    def __str__(self):
        return str(self.formula)
    
    def expand(self, rule, hyp = None):
        if not self.rule_fits_operation(rule, hyp):
            return
        
        rule_node = RuleNode(rule, child=self, tree=self.tree, branch=self.branch)
        self.parent = rule_node
        rule_node.expand()
        
    def rule_fits_operation(self, rule, hi):
        # As seguintes regras podem gerar fórmulas em qualquer formato:
        # Exclusões do and, exclusão do or, exclusão do false, exclusão da implicação, exclusão da dupla negação
        if rule in (ANDE1, ANDE2, ORE, FE, TOE, NOTNOT):
            return True
        
        if rule == HYP:
            i = int(hi[1:]) # Converts to int
            hypotheses = self.tree.get_hypotheses(self)
            n = len(hypotheses)
            return i < n and self.check_hypothesis(hypotheses[i])
        
        operator = self.formula.operator

        # And só é gerado pela inclusão
        if operator == AND:
            return rule == ANDI
        
        # Or só é gerado pelas inclusões ou resolve pelo terceiro excluído
        if operator == OR:
            return rule in (ORI1, ORI2) or rule == EM and self.check_excluded_middle(self.formula)
        
        # Implicação só é gerada pela inclusão
        if operator == IMPLY:
            return rule == TOI
        
        # Negação só é gerada pela inclusão
        if operator == NOT:
            return rule == NOTI
        
        if operator == FALSE:
            return rule == FI 

    def check_excluded_middle(self, formula):
        left = Formula(formula.subformulas[0])
        right = Formula(formula.subformulas[1])

        if right.operator == NOT:
            right_sub = right.subformulas[0]
            return left == right_sub
        
        return False

    def check_hypothesis(self, hypothesis):
        return self.formula == hypothesis

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

        elif self.rule == FE:
            self.false_elim()

        elif self.rule == ORI1:
            self.or_intro_left()

        elif self.rule == ORI2:
            self.or_intro_right()

        elif self.rule == NOTNOT:
            self.double_not()

        elif self.rule == TOI:
            self.imply_intro()

        elif self.rule == NOTI:
            self.not_intro()

        elif self.rule == EM:
            self.excluded_middle()

        elif self.rule == HYP:
            self.by_hypothesis()

        # Rules which require further input

        elif self.rule == ANDE1:
            self.and_elim_left()

        elif self.rule == ANDE2:
            self.and_elim_right()

        elif self.rule == ORE:
            self.or_elim()

        elif self.rule == FI:
            self.false_introduction()

        elif self.rule == TOE:
            self.imply_elim()

    def and_inclusion(self):
        left = self.child.subformulas[0]
        right = self.child.subformulas[1]

        left_node = FormulaNode(left, self.tree, self.branch+'0')
        right_node = FormulaNode(right, self.tree, self.branch+'1')
        self.parents = [left_node, right_node]

        self.tree.add_branch(left_node.branch)
        self.tree.add_branch(right_node.branch)
        self.tree.look_at(left_node)

    def false_elim(self):
        node = FormulaNode(lfalse, self.tree, self.branch)
        self.parents = [node]
        self.tree.look_at(node)

    def not_intro(self):
        pre = self.child.subformulas[0]

        node = FormulaNode(lfalse, self.tree, self.branch+'0')
        self.parents = [node]
        self.tree.add_branch(node.branch, pre)
        self.tree.look_at(node)

    def double_not(self):
        formula = str(self.child)
        # Must include parenthesis if not atomic
        if self.child.operator is not None:
            formula = f'({formula})'

        node = FormulaNode(f'!!{formula}', self.tree, self.branch)
        self.parents = [node]
        self.tree.look_at(node)

    def imply_intro(self):
        pre = self.child.subformulas[0]
        cons = self.child.subformulas[1]

        cons_node = FormulaNode(cons, self.tree, self.branch+'0')
        self.parents = [cons_node]
        self.tree.add_branch(cons_node.branch, pre)
        self.tree.look_at(cons_node)

    def or_intro_left(self):
        left = self.child.subformulas[0]
        left_node = FormulaNode(left, self.tree, self.branch)
        self.parents = [left_node]
        self.tree.look_at(left_node)

    def or_intro_right(self):
        right = self.child.subformulas[1]
        right_node = FormulaNode(right, self.tree, self.branch)
        self.parents = [right_node]
        self.tree.look_at(right_node)


    def and_elim_left(self):
        left = self.child
        right_input = input('Informe o lado direito da conjunção: ')
        right = Formula(right_input)

        if left.operator is not None and left.operator > AND:
            left = f'({left})'
        if right.operator is not None and right.operator > AND:
            right = f'({right})'

        node = FormulaNode(f'{left}&{right}', self.tree, self.branch)
        self.parents = [node]
        self.tree.look_at(node)

    def and_elim_right(self):
        right = self.child
        left_input = input('Informe o lado esquerdo da conjunção: ')
        left = Formula(left_input)

        if left.operator is not None and left.operator > AND:
            left = f'({left})'
        if right.operator is not None and right.operator > AND:
            right = f'({right})'

        node = FormulaNode(f'{left}&{right}', self.tree, self.branch)
        self.parents = [node]
        self.tree.look_at(node)

    def false_introduction(self):
        statement = input('Informe a fórmula a ser negada: ')
        true_st = Formula(statement)

        false_st = true_st
        if false_st.operator is not None and false_st.operator > NOT:
            false_st = f'({false_st})'
        false_st = f'!{false_st}'

        true_node = FormulaNode(true_st, self.tree, self.branch+'0')
        false_node = FormulaNode(false_st, self.tree, self.branch+'1')
        self.parents = [true_node, false_node]
        self.tree.add_branch(true_node.branch)
        self.tree.add_branch(false_node.branch)
        self.tree.look_at(true_node)

    def imply_elim(self):
        pre = input('Informe a premissa: ')
        pre = Formula(pre)
        cons = self.child
        full_st = f'({pre})->{cons}'

        imply_node = FormulaNode(full_st, self.tree, self.branch+'0')
        pre_node = FormulaNode(pre, self.tree, self.branch+'1')
        self.parents = [imply_node, pre_node]
        self.tree.add_branch(imply_node.branch)
        self.tree.add_branch(pre_node.branch)
        self.tree.look_at(imply_node)

    def or_elim(self):
        disj = input('Informe a disjunção: ')
        disj = Formula(disj)
        node_disj = FormulaNode(disj, self.tree, self.branch+'0')
        self.tree.add_branch(node_disj.branch)

        child = self.child
        left = disj.subformulas[0]
        right = disj.subformulas[1]
        route1 = FormulaNode(child, self.tree, self.branch+'1')
        route2 = FormulaNode(child, self.tree, self.branch+'2')

        self.parents = [node_disj, route1, route2]
        self.tree.add_branch(route1.branch, left)
        self.tree.add_branch(route2.branch, right)
        self.tree.look_at(node_disj)

    def excluded_middle(self):
        self.tree.close_branch(self.branch)

    def by_hypothesis(self):
        self.tree.close_branch(self.branch)

class Tree():
    def __init__(self, goal, hypotheses = []):
        self.branches = {'0':None}
        self.active_branches = {'0'}
        self.branch_assumptions = {'0':[]}

        self.root = FormulaNode(goal, tree=self, branch='0')
        self.hypotheses = hypotheses

        self.ongoing = True
        self.focus_node = self.root

    def set_branch_top(self, node):
        branch = node.branch
        self.branches[branch] = node

    def add_branch(self, new_branch, assumption = None):
        self.active_branches.add(new_branch)

        old_branch = new_branch[:-1]
        self.branch_assumptions[new_branch] = [x for x in self.branch_assumptions[old_branch]]
        if assumption is not None:
            self.branch_assumptions[new_branch].append(assumption)

    def get_hypotheses(self, node):
        branch = node.branch
        assumptions = self.branch_assumptions[branch]
        return self.hypotheses + assumptions
    
    def show_hypotheses(self):
        hypotheses = self.get_hypotheses(self.focus_node)
        for i, h in enumerate(hypotheses):
            print(f'h{i}: {h}')
    
    def close_branch(self, branch):
        if branch == '0':
            self.end_deduction()
            return

        self.active_branches.remove(branch)
        sub_branch = branch[:-1]

        if self.has_upper_branches(sub_branch):
            focus_branch = self.find_leftmost_from(sub_branch)
            self.focus_node = self.branches[focus_branch]
            return

        self.close_branch(sub_branch)        

    def has_upper_branches(self, branch):
        # Checks that there are open branches with the branch as prefix, not including itself
        n = len(branch)
        sprouts = [b for b in self.active_branches if len(b) > n and b[:n] == branch]
        
        return len(sprouts) > 0

    def find_leftmost_from(self, branch):
        n = len(branch)
        sprouts = [b for b in self.active_branches if len(b) > n and b[:n] == branch]
        
        return sorted(sprouts)[0]

    def end_deduction(self):
        self.ongoing = False
        print('Parabéns! Você provou o teorema!')

    def look_at(self, node):
        self.focus_node = node

    def expand(self, rule, hyp = None):
        self.focus_node.expand(rule, hyp)

if __name__ == '__main__':
    while True:
        try:
            goal = input('Informe a fórmula a ser provada: ')
            goal = Formula(goal)
            break
        except FormulaSyntaxError as e:
            print('Fórmula incorreta devido ao seguinte erro:')
            print(e)
            print('Tente novamente.')
    hypotheses = []
    while True:
        hyp = input('Informe uma hipótese. Escreva "fim" para encerrar. ').strip()
        if hyp.lower() == 'fim':
            break
        try:
            hyp = Formula(hyp)
            hypotheses.append(hyp)
        except FormulaSyntaxError as e:
            print('Fórmula incorreta devido ao seguinte erro:')
            print(e)
            print('Tente novamente.')

    tree = Tree(goal, hypotheses)

    while tree.ongoing:
        print(tree.focus_node)
        action = input('Informe a operação a realizar: ').strip()

        if action == '?':
            tree.show_hypotheses()

        elif re.fullmatch(r'h\d', action):
            tree.expand(HYP, action)
        
        else:
            try:
                action = eval(action.upper())
                tree.expand(action)
            except:
                print('Entrada inválida.')
        # print(tree.focus_node.branch)

# print(eval('ANDI'))

# tree = Tree('p&q')
# root = tree.root
# print(root)

# root.expand(ORE)
# for p in root.parent.parents:
#     print(p, p.branch)
#     print(tree.get_hypotheses(p))
# print(tree.get_hypotheses(root))

# for h in tree.hypotheses:
#     print(h)

#### Pensamentos
# Também preciso identificar quando um nodo de regra foi satisfeito e propagar seu fechamento pra baixo
# Até que a árvore detecte que todos os ramos foram fechados
# E, auxiliarmente, ser capaz de reverter a árvore a um estado anterior, cortando um ramo.
# Além de ser capaz de identificar o ramo/nodo atualmente em análise

# Criar mecanismo para reconhecimento de nodo igual a hipótese ou igual ao terceiro excluído
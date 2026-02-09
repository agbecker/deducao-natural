from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                               QScrollArea, QStackedWidget, QMessageBox, QGraphicsView,
                               QGraphicsScene, QGraphicsLineItem, QGraphicsTextItem)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QFont, QFontMetrics, QPen, QColor, QTransform, QCursor
import sys

# Importar suas classes (ajuste o nome do arquivo conforme necessário)
from formula import (Formula, FormulaSyntaxError, Tree, FormulaNode, RuleNode,
                     ANDE1, ANDE2, ANDI, ORI1, ORI2, ORE, TOI, TOE, FE, FI, 
                     NOTI, NOTNOT, EM, HYP)


class ClickableTextItem(QGraphicsTextItem):
    """Item de texto clicável que representa um nodo da árvore"""
    
    def __init__(self, text, node, canvas):
        super().__init__(text)
        self.node = node
        self.canvas = canvas
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        """Detecta clique no nodo"""
        if event.button() == Qt.LeftButton:
            self.canvas.set_focus_node(self.node)
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Efeito visual ao passar o mouse"""
        if self.node != self.canvas.tree.focus_node:
            self.setDefaultTextColor(QColor(100, 100, 100))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove efeito visual ao sair com o mouse"""
        if self.node != self.canvas.tree.focus_node:
            self.setDefaultTextColor(QColor(0, 0, 0))
        super().hoverLeaveEvent(event)


class ProofCanvas(QGraphicsView):
    """Canvas para desenhar a árvore de prova com zoom e drag"""
    
    def __init__(self, tree=None):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configurações de visualização
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Habilita drag do canvas
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Permite interação suave
        self.setInteractive(True)
        
        # Configurações de zoom
        self.zoom_factor = 1.15
        self.current_scale = 1.0
        
        # Árvore de prova
        self.tree = tree
        
        # Espaçamentos
        self.vertical_spacing = 80
        self.horizontal_spacing = 60
        self.rule_line_length = 100
        
        # Fonte para fórmulas
        self.formula_font = QFont("DejaVu Sans", 12)
        self.rule_font = QFont("DejaVu Sans", 9)
        
        # Desenha a árvore inicial se existir
        if self.tree:
            self.draw_tree()
    
    def wheelEvent(self, event):
        """Implementa zoom com scroll do mouse"""
        # Calcula o fator de zoom
        if event.angleDelta().y() > 0:
            factor = self.zoom_factor
        else:
            factor = 1.0 / self.zoom_factor
        
        # Limita o zoom
        new_scale = self.current_scale * factor
        if 0.1 <= new_scale <= 10.0:
            self.scale(factor, factor)
            self.current_scale = new_scale
    
    def set_tree(self, tree):
        """Define a árvore e redesenha"""
        self.tree = tree
        self.draw_tree()
    
    def set_focus_node(self, node):
        """Muda o nodo em foco e atualiza a visualização"""
        if self.tree:
            self.tree.look_at(node)
            self.draw_tree()
            
            # Notifica o ProofScreen para atualizar as hipóteses
            parent = self.parent()
            while parent:
                if isinstance(parent, ProofScreen):
                    parent.update_hypotheses_bar()
                    break
                parent = parent.parent()
    
    def draw_tree(self):
        """Desenha toda a árvore de prova"""
        self.scene.clear()
        
        if not self.tree:
            return
        
        # Calcula posições de todos os nodos
        positions = self.calculate_positions(self.tree.root)
        
        # Desenha todos os nodos e regras
        self.draw_node_recursive(self.tree.root, positions)
    
    def calculate_positions(self, root_node):
        """Calcula as posições x, y de cada nodo na árvore com detecção de overlap"""
        positions = {}
        widths = {}  # Armazena a largura real em pixels de cada nodo
        
        # Calcula a largura em pixels de um texto
        metrics = QFontMetrics(self.formula_font)
        
        def get_text_width(node):
            """Retorna a largura em pixels do texto da fórmula"""
            text = str(node.formula)
            return metrics.horizontalAdvance(text)
        
        # DFS para calcular largura mínima necessária de cada subárvore
        def calculate_subtree_width(node):
            """Calcula a largura mínima necessária para a subárvore em pixels"""
            if node is None:
                return 0
            
            node_id = id(node)
            
            # Largura do próprio nodo
            own_width = get_text_width(node)
            widths[node_id] = own_width
            
            if not hasattr(node, 'parent') or node.parent is None:
                # É uma folha (topo da árvore de dedução)
                return own_width + self.horizontal_spacing
            
            # Tem parent (regra)
            rule = node.parent
            
            # Calcula largura necessária para todos os parents
            children_widths = [calculate_subtree_width(p) for p in rule.parents]
            total_children_width = sum(children_widths)
            
            # A largura da subárvore é o máximo entre a largura própria e a dos filhos
            subtree_width = max(own_width + self.horizontal_spacing, total_children_width)
            
            return subtree_width
        
        # Posiciona os nodos usando DFS com ajuste de espaçamento
        def position_node(node, x, y, available_width):
            """Posiciona um nodo e seus ancestrais dentro do espaço disponível"""
            if node is None:
                return
            
            node_id = id(node)
            
            # Posiciona o nodo atual
            positions[node_id] = (x, y)
            
            if hasattr(node, 'parent') and node.parent is not None:
                # Tem regra acima
                rule = node.parent
                rule_y = y - self.vertical_spacing
                
                # Calcula larguras das subárvores dos parents
                parent_widths = [calculate_subtree_width(p) for p in rule.parents]
                total_parent_width = sum(parent_widths)
                
                # Se os parents precisam de mais espaço, usa o necessário
                spacing_width = max(available_width, total_parent_width)
                
                # Posiciona os parents distribuídos uniformemente
                if len(rule.parents) == 1:
                    # Um único parent: centraliza
                    parent_x = x
                    position_node(rule.parents[0], parent_x, rule_y, parent_widths[0])
                else:
                    # Múltiplos parents: distribui o espaço
                    current_x = x - spacing_width / 2
                    
                    for i, parent in enumerate(rule.parents):
                        # Posiciona no centro do espaço alocado para este parent
                        parent_x = current_x + parent_widths[i] / 2
                        position_node(parent, parent_x, rule_y, parent_widths[i])
                        current_x += parent_widths[i]
                
                # Posiciona a regra
                positions[id(rule)] = (x, y - self.vertical_spacing / 2)
        
        # Calcula largura total necessária
        total_width = calculate_subtree_width(root_node)
        
        # Inicia o posicionamento a partir da raiz
        start_x = max(total_width / 2, 300)  # Pelo menos 300px do centro
        start_y = 100
        
        position_node(root_node, start_x, start_y, total_width)
        
        return positions
    
    def draw_node_recursive(self, node, positions):
        """Desenha um nodo e seus ancestrais recursivamente"""
        node_id = id(node)
        
        if node_id not in positions:
            return
        
        x, y = positions[node_id]
        
        # Desenha a fórmula
        formula_text = str(node.formula)
        text_item = ClickableTextItem(formula_text, node, self)
        text_item.setFont(self.formula_font)
        
        # Define a cor: vermelho para focus_node, preto para os demais
        if node == self.tree.focus_node:
            text_item.setDefaultTextColor(QColor(255, 0, 0))
        else:
            text_item.setDefaultTextColor(QColor(0, 0, 0))
        
        # Centraliza o texto
        text_rect = text_item.boundingRect()
        text_item.setPos(x - text_rect.width() / 2, y - text_rect.height() / 2)
        
        self.scene.addItem(text_item)
        
        # Se tem parent (regra), desenha a regra e conecta aos parents
        if hasattr(node, 'parent') and node.parent is not None:
            rule = node.parent
            rule_id = id(rule)
            
            if rule_id in positions:
                rule_x, rule_y = positions[rule_id]
                
                # Calcula a largura da linha com base na posição dos parents
                if len(rule.parents) > 1:
                    parent_positions = [positions[id(p)] for p in rule.parents if id(p) in positions]
                    if parent_positions:
                        leftmost_x = min(px for px, py in parent_positions)
                        rightmost_x = max(px for px, py in parent_positions)
                        line_length = max(rightmost_x - leftmost_x, 80)
                        line_center = (leftmost_x + rightmost_x) / 2
                    else:
                        line_length = self.rule_line_length
                        line_center = rule_x
                else:
                    line_length = self.rule_line_length
                    line_center = rule_x
                
                # Desenha linha horizontal da regra
                line = QGraphicsLineItem(
                    line_center - line_length / 2, rule_y,
                    line_center + line_length / 2, rule_y
                )
                line.setPen(QPen(QColor(0, 0, 0), 2))
                self.scene.addItem(line)
                
                # Desenha nome da regra
                rule_name = self.get_rule_name(rule.rule)
                rule_text = QGraphicsTextItem(rule_name)
                rule_text.setFont(self.rule_font)
                rule_text.setPos(line_center + line_length / 2 + 5, rule_y - 10)
                self.scene.addItem(rule_text)
                
                # Conecta aos parents
                for parent in rule.parents:
                    self.draw_node_recursive(parent, positions)
    
    def get_rule_name(self, rule):
        """Retorna o nome legível da regra"""
        rule_names = {
            ANDE1: "∧E₁",
            ANDE2: "∧E₂",
            ANDI: "∧I",
            ORI1: "∨I₁",
            ORI2: "∨I₂",
            ORE: "∨E",
            TOI: "→I",
            TOE: "→E",
            FE: "⊥E",
            FI: "⊥I",
            NOTI: "¬I",
            NOTNOT: "¬¬E",
            EM: "EM",
            HYP: "Hip"
        }
        return rule_names.get(rule, f"R{rule}")


class InitialScreen(QWidget):
    """Tela inicial para entrada de teorema e hipóteses"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hypothesis_inputs = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Título
        title = QLabel("Assistente de Provas por Dedução Natural")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instruções
        instructions = QLabel("Digite a fórmula a ser provada e as hipóteses (opcionais)")
        instructions.setStyleSheet("font-size: 12px; color: #666;")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Campo para o teorema
        theorem_label = QLabel("Teorema a provar:")
        theorem_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(theorem_label)
        
        self.theorem_input = QLineEdit()
        self.theorem_input.setPlaceholderText("Ex: p->q, (p&q)->r, etc.")
        self.theorem_input.setStyleSheet("padding: 8px; font-size: 14px;")
        layout.addWidget(self.theorem_input)
        
        # Dica de símbolos
        symbols_hint = QLabel("Símbolos: & ou and (∧), | ou or (∨), ! ou not (¬), -> ou to (→)")
        symbols_hint.setStyleSheet("font-size: 10px; color: #888; font-style: italic;")
        layout.addWidget(symbols_hint)
        
        # Área de hipóteses
        hypothesis_label = QLabel("Hipóteses:")
        hypothesis_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(hypothesis_label)
        
        # Container com scroll para hipóteses
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(150)
        scroll_area.setMaximumHeight(300)
        
        self.hypothesis_container = QWidget()
        self.hypothesis_layout = QVBoxLayout()
        self.hypothesis_layout.setSpacing(10)
        self.hypothesis_container.setLayout(self.hypothesis_layout)
        
        scroll_area.setWidget(self.hypothesis_container)
        layout.addWidget(scroll_area)
        
        # Adiciona a primeira caixa de hipótese
        self.add_hypothesis_input()
        
        # Botão para adicionar mais hipóteses
        add_hyp_btn = QPushButton("+ Adicionar Hipótese")
        add_hyp_btn.clicked.connect(self.add_hypothesis_input)
        add_hyp_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        layout.addWidget(add_hyp_btn)
        
        # Layout para botões de ação
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Botão Limpar
        clear_btn = QPushButton("Limpar")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        buttons_layout.addWidget(clear_btn)
        
        # Botão para iniciar prova
        self.prove_btn = QPushButton("Provar")
        self.prove_btn.clicked.connect(self.start_proof)
        self.prove_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(self.prove_btn)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def add_hypothesis_input(self):
        """Adiciona um novo campo de entrada de hipótese"""
        hyp_input = QLineEdit()
        hyp_input.setPlaceholderText(f"Hipótese {len(self.hypothesis_inputs) + 1}")
        hyp_input.setStyleSheet("padding: 8px; font-size: 14px;")
        
        self.hypothesis_layout.addWidget(hyp_input)
        self.hypothesis_inputs.append(hyp_input)
    
    def clear_all(self):
        """Limpa o teorema e remove todas as hipóteses extras"""
        # Limpa o campo do teorema
        self.theorem_input.clear()
        
        # Remove todos os campos de hipótese
        while self.hypothesis_layout.count():
            item = self.hypothesis_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Limpa a lista
        self.hypothesis_inputs.clear()
        
        # Adiciona uma nova hipótese vazia
        self.add_hypothesis_input()
    
    def start_proof(self):
        """Valida as entradas e inicia a tela de prova"""
        # Valida teorema
        theorem_text = self.theorem_input.text().strip()
        if not theorem_text:
            QMessageBox.warning(self, "Erro", "Por favor, informe o teorema a ser provado.")
            return
        
        try:
            theorem = Formula(theorem_text)
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro na Fórmula", f"Erro no teorema:\n{str(e)}")
            return
        
        # Valida hipóteses
        hypotheses = []
        for i, hyp_input in enumerate(self.hypothesis_inputs):
            hyp_text = hyp_input.text().strip()
            if hyp_text:  # Só processa se não estiver vazio
                try:
                    hyp = Formula(hyp_text)
                    hypotheses.append(hyp)
                except FormulaSyntaxError as e:
                    QMessageBox.warning(self, "Erro na Fórmula", 
                                       f"Erro na hipótese {i+1}:\n{str(e)}")
                    return
        
        # Cria a árvore de prova
        tree = Tree(theorem, hypotheses)
        
        # Notifica o parent (MainWindow) para mudar para a tela de prova
        parent = self.parent()
        while parent and not isinstance(parent, MainWindow):
            parent = parent.parent()
        
        if parent:
            parent.start_proof_screen(tree)


class ProofScreen(QWidget):
    """Tela de prova com canvas e controles"""
    
    def __init__(self, tree=None, parent=None):
        super().__init__(parent)
        self.tree = tree
        self.init_ui()
        
        if tree:
            self.canvas.set_tree(tree)
            self.update_hypotheses_bar()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra superior com hipóteses
        hyp_scroll = QScrollArea()
        hyp_scroll.setMaximumHeight(60)
        hyp_scroll.setWidgetResizable(True)
        hyp_scroll.setStyleSheet("background-color: #f5f5f5; border-bottom: 2px solid #ccc;")
        
        self.hyp_container = QWidget()
        self.hyp_layout = QHBoxLayout()
        self.hyp_layout.setContentsMargins(10, 5, 10, 5)
        self.hyp_container.setLayout(self.hyp_layout)
        hyp_scroll.setWidget(self.hyp_container)
        
        main_layout.addWidget(hyp_scroll)
        
        # Layout central (canvas + barra lateral)
        central_layout = QHBoxLayout()
        
        # Canvas de prova (área principal)
        self.canvas = ProofCanvas()
        central_layout.addWidget(self.canvas, stretch=1)
        
        # Barra lateral direita com regras
        rules_scroll = QScrollArea()
        rules_scroll.setMaximumWidth(200)
        rules_scroll.setWidgetResizable(True)
        rules_scroll.setStyleSheet("background-color: #fafafa; border-left: 2px solid #ccc;")
        
        rules_container = QWidget()
        self.rules_layout = QVBoxLayout()
        self.rules_layout.setContentsMargins(10, 10, 10, 10)
        self.rules_layout.setSpacing(8)
        
        # Adiciona botões de regras
        self.create_rule_buttons()
        
        rules_container.setLayout(self.rules_layout)
        rules_scroll.setWidget(rules_container)
        
        central_layout.addWidget(rules_scroll)
        
        main_layout.addLayout(central_layout)
        
        # Adiciona botão "Voltar" no canto inferior direito
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        back_btn = QPushButton("← Voltar")
        back_btn.clicked.connect(self.go_back)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        bottom_layout.addWidget(back_btn)
        
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
    
    def create_rule_buttons(self):
        """Cria os botões de regras de dedução"""
        rules = [
            ("∧E₁ (And Elim Esq)", ANDE1),
            ("∧E₂ (And Elim Dir)", ANDE2),
            ("∧I (And Intro)", ANDI),
            ("∨I₁ (Or Intro Esq)", ORI1),
            ("∨I₂ (Or Intro Dir)", ORI2),
            ("∨E (Or Elim)", ORE),
            ("→I (Imply Intro)", TOI),
            ("→E (Modus Ponens)", TOE),
            ("⊥E (False Elim)", FE),
            ("⊥I (False Intro)", FI),
            ("¬I (Not Intro)", NOTI),
            ("¬¬E (Double Not)", NOTNOT),
            ("EM (Exc. Médio)", EM),
        ]
        
        for rule_name, rule_const in rules:
            btn = QPushButton(rule_name)
            btn.clicked.connect(lambda checked, r=rule_const: self.apply_rule(r))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #2196F3;
                }
            """)
            self.rules_layout.addWidget(btn)
        
        self.rules_layout.addStretch()
    
    def update_hypotheses_bar(self):
        """Atualiza a barra de hipóteses baseada no nodo em foco"""
        # Limpa hipóteses antigas
        while self.hyp_layout.count():
            item = self.hyp_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.tree:
            return
        
        # Obtém hipóteses do nodo em foco
        hypotheses = self.tree.get_hypotheses(self.tree.focus_node)
        
        for i, hyp in enumerate(hypotheses):
            btn = QPushButton(f"h{i}: {str(hyp)}")
            btn.clicked.connect(lambda checked, idx=i: self.apply_hypothesis(idx))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #fff3e0;
                    border: 1px solid #ff9800;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffe0b2;
                }
            """)
            self.hyp_layout.addWidget(btn)
        
        self.hyp_layout.addStretch()
    
    def apply_rule(self, rule):
        """Aplica uma regra ao nodo em foco"""
        if not self.tree or not self.tree.ongoing:
            return
        
        # Regras que precisam de input adicional
        if rule in [ANDE1, ANDE2, ORE, FI, TOE]:
            self.apply_rule_with_input(rule)
        else:
            # Regras automáticas
            self.tree.expand(rule)
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
            # Verifica se a prova foi concluída
            if not self.tree.ongoing:
                QMessageBox.information(self, "Parabéns!", 
                                       "Você provou o teorema com sucesso!")
    
    def apply_rule_with_input(self, rule):
        """Aplica regras que requerem input do usuário"""
        from PySide6.QtWidgets import QInputDialog
        
        if rule == ANDE1:
            text, ok = QInputDialog.getText(self, "∧E₁", 
                                           "Informe o lado direito da conjunção:")
            if ok and text:
                self.apply_and_elim_left(text)
        
        elif rule == ANDE2:
            text, ok = QInputDialog.getText(self, "∧E₂", 
                                           "Informe o lado esquerdo da conjunção:")
            if ok and text:
                self.apply_and_elim_right(text)
        
        elif rule == ORE:
            text, ok = QInputDialog.getText(self, "∨E", 
                                           "Informe a disjunção:")
            if ok and text:
                self.apply_or_elim(text)
        
        elif rule == FI:
            text, ok = QInputDialog.getText(self, "⊥I", 
                                           "Informe a fórmula a ser negada:")
            if ok and text:
                self.apply_false_intro(text)
        
        elif rule == TOE:
            text, ok = QInputDialog.getText(self, "→E", 
                                           "Informe a premissa:")
            if ok and text:
                self.apply_imply_elim(text)
    
    def apply_and_elim_left(self, right_text):
        """Implementa ∧E₁ com input do usuário"""
        try:
            from formula import land, AND
            
            right = Formula(right_text)
            left = self.tree.focus_node.formula
            
            if left.operator is not None and left.operator > AND:
                left_str = f'({left})'
            else:
                left_str = str(left)
            
            if right.operator is not None and right.operator > AND:
                right_str = f'({right})'
            else:
                right_str = str(right)
            
            conjunction = Formula(f'{left_str}{land}{right_str}')
            
            rule_node = RuleNode(ANDE1, child=self.tree.focus_node, 
                               tree=self.tree, branch=self.tree.focus_node.branch)
            self.tree.focus_node.parent = rule_node
            
            parent_node = FormulaNode(conjunction, self.tree, 
                                     self.tree.focus_node.branch, child=rule_node)
            rule_node.parents = [parent_node]
            
            self.tree.look_at(parent_node)
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro", f"Fórmula inválida:\n{str(e)}")
    
    def apply_and_elim_right(self, left_text):
        """Implementa ∧E₂ com input do usuário"""
        try:
            from formula import land, AND
            
            left = Formula(left_text)
            right = self.tree.focus_node.formula
            
            if left.operator is not None and left.operator > AND:
                left_str = f'({left})'
            else:
                left_str = str(left)
            
            if right.operator is not None and right.operator > AND:
                right_str = f'({right})'
            else:
                right_str = str(right)
            
            conjunction = Formula(f'{left_str}{land}{right_str}')
            
            rule_node = RuleNode(ANDE2, child=self.tree.focus_node, 
                               tree=self.tree, branch=self.tree.focus_node.branch)
            self.tree.focus_node.parent = rule_node
            
            parent_node = FormulaNode(conjunction, self.tree, 
                                     self.tree.focus_node.branch, child=rule_node)
            rule_node.parents = [parent_node]
            
            self.tree.look_at(parent_node)
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro", f"Fórmula inválida:\n{str(e)}")
    
    def apply_or_elim(self, disj_text):
        """Implementa ∨E com input do usuário"""
        try:
            disj = Formula(disj_text)
            node_disj = FormulaNode(disj, self.tree, self.tree.focus_node.branch+'0')
            self.tree.add_branch(node_disj.branch)
            
            child = self.tree.focus_node.formula
            left = disj.subformulas[0]
            right = disj.subformulas[1]
            
            route1 = FormulaNode(child, self.tree, self.tree.focus_node.branch+'1')
            route2 = FormulaNode(child, self.tree, self.tree.focus_node.branch+'2')
            
            rule_node = RuleNode(ORE, child=self.tree.focus_node,
                               tree=self.tree, branch=self.tree.focus_node.branch)
            self.tree.focus_node.parent = rule_node
            rule_node.parents = [node_disj, route1, route2]
            
            self.tree.add_branch(route1.branch, left)
            self.tree.add_branch(route2.branch, right)
            self.tree.look_at(node_disj)
            
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro", f"Fórmula inválida:\n{str(e)}")
    
    def apply_false_intro(self, statement_text):
        """Implementa ⊥I com input do usuário"""
        try:
            from formula import lnot, NOT
            
            true_st = Formula(statement_text)
            
            if true_st.operator is not None and true_st.operator > NOT:
                false_st = f'({true_st})'
            else:
                false_st = str(true_st)
            false_st = f'{lnot}{false_st}'
            
            rule_node = RuleNode(FI, child=self.tree.focus_node,
                               tree=self.tree, branch=self.tree.focus_node.branch)
            self.tree.focus_node.parent = rule_node
            
            true_node = FormulaNode(true_st, self.tree, self.tree.focus_node.branch+'0')
            false_node = FormulaNode(false_st, self.tree, self.tree.focus_node.branch+'1')
            
            rule_node.parents = [true_node, false_node]
            self.tree.add_branch(true_node.branch)
            self.tree.add_branch(false_node.branch)
            self.tree.look_at(true_node)
            
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro", f"Fórmula inválida:\n{str(e)}")
    
    def apply_imply_elim(self, pre_text):
        """Implementa →E com input do usuário"""
        try:
            pre = Formula(pre_text)
            cons = self.tree.focus_node.formula
            full_st = f'({pre})->{cons}'
            
            rule_node = RuleNode(TOE, child=self.tree.focus_node,
                               tree=self.tree, branch=self.tree.focus_node.branch)
            self.tree.focus_node.parent = rule_node
            
            imply_node = FormulaNode(full_st, self.tree, self.tree.focus_node.branch+'0')
            pre_node = FormulaNode(pre, self.tree, self.tree.focus_node.branch+'1')
            
            rule_node.parents = [imply_node, pre_node]
            self.tree.add_branch(imply_node.branch)
            self.tree.add_branch(pre_node.branch)
            self.tree.look_at(imply_node)
            
            self.canvas.draw_tree()
            self.update_hypotheses_bar()
            
        except FormulaSyntaxError as e:
            QMessageBox.warning(self, "Erro", f"Fórmula inválida:\n{str(e)}")
    
    def apply_hypothesis(self, hyp_index):
        """Aplica uma hipótese ao nodo em foco"""
        if not self.tree or not self.tree.ongoing:
            return
        
        self.tree.expand(HYP, f'h{hyp_index}')
        self.canvas.draw_tree()
        self.update_hypotheses_bar()
        
        if not self.tree.ongoing:
            QMessageBox.information(self, "Parabéns!", 
                                   "Você provou o teorema com sucesso!")
    
    def go_back(self):
        """Volta para a tela inicial"""
        reply = QMessageBox.question(
            self, 
            "Voltar", 
            "Deseja realmente voltar para a tela inicial? A prova atual será perdida.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            parent = self.parent()
            while parent and not isinstance(parent, MainWindow):
                parent = parent.parent()
            
            if parent:
                parent.return_to_initial_screen()


class MainWindow(QMainWindow):
    """Janela principal que gerencia as telas"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistente de Dedução Natural")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central com stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Cria as telas
        self.initial_screen = InitialScreen(self)
        self.proof_screen = None
        
        # Adiciona tela inicial
        self.stacked_widget.addWidget(self.initial_screen)
    
    def start_proof_screen(self, tree):
        """Inicia a tela de prova com a árvore fornecida"""
        # Remove tela de prova antiga se existir
        if self.proof_screen:
            self.stacked_widget.removeWidget(self.proof_screen)
            self.proof_screen.deleteLater()
        
        # Cria nova tela de prova
        self.proof_screen = ProofScreen(tree, self)
        self.stacked_widget.addWidget(self.proof_screen)
        
        # Muda para a tela de prova
        self.stacked_widget.setCurrentWidget(self.proof_screen)
    
    def return_to_initial_screen(self):
        """Volta para a tela inicial"""
        self.stacked_widget.setCurrentWidget(self.initial_screen)


def main():
    app = QApplication(sys.argv)
    
    # Configurações de fonte para suportar símbolos matemáticos
    app.setFont(QFont("DejaVu Sans", 10))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
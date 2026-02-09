# Assistente para Dedução Natural

Esta é uma ferramenta didática para o auxílio do ensino de lógica para a computação. Ela fornece aos alunos uma interface gráfica simples e intuitiva para a construção de provas por dedução natural para lógica proposicional.

# Uso da ferramenta

## Definição do objetivo

Ao iniciar o programa, o usuário deve informar a fórmula a ser provada e, opcionalmente, as hipóteses assumidas para a prova.

A seguinte notação deve ser usada para a escrita das fórmulas:

* Proposições devem ser letras minúsculas
* A negação lógica (¬) pode ser representada usando `!`, `~` ou `not`
* O E lógico (∧) pode ser representado usando `&`, `&&`, `and` ou `/\`
* O OU lógico (∨) pode ser representado usando `|`, `||`, `or` ou `\/`
* A implicação lógica (→) pode ser representada usando `->` ou `to`
* Parênteses podem ser usados, contanto que balanceados. A associatividade do programa é à direita para todos os operadores.

## Dedução da fórmula

A tela de prova é composta de três elementos:

1. A árvore de dedução
2. A lista de regras, na barra lateral direita
3. A lista de hipóteses, na barra superior

Inicialmente, a árvore é composta apenas pela fórmula a ser provada (teorema). Ela é construída pela aplicação sucessiva de regras e hipóteses.

A cada momento, uma fórmula na árvore está em foco. Esta fórmula é representada em vermelho, e será a ela que se aplicará a próxima regra ou hipótese. É possível mudar a fórmula em foco a qualquer momento, clicando em outra fórmula na árvore. Se for aplicada uma regra a uma fórmula interna (onde já havia sido aplicada outra regra), a aplicação anterior é sobrescrita. Assim, é possível corrigir eventuais enganos no processo de dedução.

Regras são aplicadas clicando no botão da regra correspondente. Uma regra só será aplicada se a fórmula for de um formato compatível (ex.: a inclusão do E só pode ser aplicada em conjunções).

Algumas regras requerem a escrita de uma fórmula auxiliar. Essa escrita se dá conforme as mesmas regras da escrita das fórmulas na tela inicial. As regras de dedução que requerem escrita são:
* Eliminação do E à esquerda, onde deve-se informar o lado direito da conjunção original;
* Eliminação do E à direita, onde deve-se informar o lado esquerdo da conjunção original;
* Eliminação do OU, onde deve-se informar a disjunção a eliminar;
* Eliminação da implicação, onde deve-se informar o lado esquerdo da implicação original;
* Introdução da contradição, onde deve-se informar a forma verdadeira da expressão a gerar contradição (ex.: informar `p` para gerar ambos `p` e `¬p`)

Hipóteses são aplicadas clicando-se no botão de hipótese correspondente à fórmula em foco. A lista de hipóteses atual é própria de cada fórmula, correpondente às hipóteses informadas na tela inicial mais quaisquer hipóteses assumidas naquele ramo de dedução. A aplicação de uma hipótese fecha um ramo da árvore.

Uma prova é concluída quando todos os ramos forem fechados. Um ramo só pode ser fechado pela aplicação de uma hipótese ou da regra do terceiro excluído (EM).


# Créditos

Este programa foi desenvolvido por Álvaro Guglielmin Becker.

A interface gráfica foi feita usando a biblioteca PySide6, com assistência da ferramenta Claude 4.5 Sonnet.
# Paciência Spider 2 Naipes

Projeto Prático da disciplina de Estrutura de Dados 2, Uniube 2025/2

Curso: Inteligência Artificial e Ciência de Dados

Professora: Silvia Brandão

Aluno: Raphael Felix - 5174803

## Definições do projeto

Linguagem utilizada: Python com a biblioteca Arcade.

Objetivo: Desenvolver versões digitais de jogos de cartas da família Paciência, aplicando estruturas de dados
adequadas (pilhas, listas, árvores) e algoritmos de busca/ordenação, de forma a consolidar o aprendizado
prático dos conceitos vistos nas disciplinas de Estruturas de Dados 1 e 2.

Jogo: Paciência Spide 2 Naipes.

Regras do jogo:
- O objetivo é organizar todas as cartas em sequência decrescente do Rei (K) até o Ás (A) no mesmo naipe.
- Quando uma sequência completa é formada (K-Q-J-10-9-8-7-6-5-4-3-2-A), ela é removida do tabuleiro.
- O jogo termina com a vitória quando todas as oito sequências forem removidas.
- São usadas duas baralhos padrão (104 cartas no total).
- Na versão de 2 naipes, usa-se apenas Espadas (♠) e Copas (♥) — cada uma duplicada.
- O tabuleiro tem 10 colunas:
    - As quatro primeiras colunas iniciam com 6 cartas cada.
    - As seis colunas restantes iniciam com 5 cartas cada.
- Somente a carta do topo de cada coluna fica virada para cima, as demais ficam viradas para baixo.
- O restante das cartas (50) forma o estoque (ou “monte”), usado para dar novas cartas durante o jogo.
- Você pode mover a carta de topo de uma coluna para outra coluna se ela for um valor imediatamente menor do que a carta de destino.
- O naipe não precisa ser igual para mover cartas individuais.
- Você pode mover grupos de cartas em sequência decrescente se todas forem do mesmo naipe.
- Qualquer carta (ou sequência) pode ser movida para uma coluna vazia.
- Quando todas as colunas têm pelo menos uma carta, você pode clicar no estoque para distribuir 10 novas cartas — uma em cada coluna.
    - As cartas novas sempre vêm viradas para cima.
    - Não é permitido distribuir novas cartas se alguma coluna estiver vazia.
- Quando uma sequência de 13 cartas (K → A) do mesmo naipe for formada, ela é automaticamente removida do tabuleiro.
- Cada sequência removida aumenta a pontuação e libera espaço.
- Vitória: todas as 104 cartas foram organizadas e removidas.
- Derrota: o jogador não consegue mais fazer movimentos válidos e não há mais cartas no estoque.

### 1. Diagrama de Classes – Núcleo do Jogo
```mermaid
classDiagram
    direction LR

    class Suit {
        <<enumeration>>
        +S: str
        +H: str
    }

    class Card {
        +value: int
        +suit: str
        +face_up: bool
        +id: str
        +label() str
        +one_below(other: Card) bool
    }

    class Sequence {
        +cards: List<Card>
        +is_desc_same_suit() bool
        +top() Card
        +base() Card
        +size() int
    }

    class Move {
        +origem_col: int
        +origem_idx: int
        +destino_col: int
        +qtd_cartas: int
        +viradas_no_fim: List<Card>
        +seq_removida: List<Card>
        +tipo: str  "move|deal"
        +deal_cartas: List<(int, Card)>
    }

    class Column {
        +cards: List<Card>
        +push_seq(seq: Sequence) void
        +pop_n(n: int) Sequence
        +top() Card
        +empty() bool
        +reveal_top_if_needed() void
        +movable_subsequence_from(idx: int) Sequence
    }

    class Stock {
        +cards: List<Card>
        +available() bool
    }

    class Deck {
        +create_two_suits_double_deck() List<Card$
    }

    class Game {
        -rng: Random
        +columns: List<Column>
        +stock: Stock
        +removed_sequences: int
        +historico: List<Move>
        +_start() void
        +can_receive(dest: Column, seq: Sequence) bool
        +move(col_i: int, idx: int, col_j: int) bool
        +undo() bool
        +deal() bool
        +reset(seed: Optional[int]) void
    }

    %% Relações
    Sequence *-- Card
    Column *-- Card
    Stock *-- Card
    Move *-- Card

    Game o-- Column
    Game o-- Stock
    Game o-- Move
    Game ..> Deck
    Game ..> Sequence
    Game ..> Suit
```

### 2. Diagrama de Classes – Incluindo a Camada Visual (Arcade)
```mermaid
classDiagram
    direction LR

    class Game {
        +columns: List<Column>
        +stock: Stock
        +removed_sequences: int
        +historico: List<Move>
        +move(col_i, idx, col_j) bool
        +deal() bool
        +undo() bool
        +reset(seed) void
    }

    class Column {
        +cards: List<Card>
    }

    class Card {
        +value: int
        +suit: str
        +face_up: bool
        +label() str
    }

    class Sequence {
        +cards: List<Card>
    }

    class Move {
        +tipo: str
    }

    class Stock {
        +cards: List<Card>
    }

    class DragState {
        +active: bool
        +from_col: int
        +from_idx: int
        +seq: Sequence
        +mouse_dx: float
        +mouse_dy: float
        +valid_target_col: int
        +reset() void
    }

    class ArcadeWindow {
        <<abstract>>
    }

    class SpiderView {
        +game: Game
        +drag: DragState
        +_mouse_x: float
        +_mouse_y: float
        +on_draw() void
        +on_mouse_press(x,y,btn,mod) void
        +on_mouse_motion(x,y,dx,dy) void
        +on_mouse_release(x,y,btn,mod) void
        +on_key_press(symbol,mod) void
        +pick_column_card(x,y) (int,int)
        +target_column_from_point(x,y) int
        +draw_card(card, col_i, idx, dragging, dx, dy) void
    }

    SpiderView --|> ArcadeWindow

    SpiderView o-- Game
    SpiderView o-- DragState

    SpiderView ..> Column
    SpiderView ..> Card
    SpiderView ..> Sequence
    DragState ..> Sequence
```

### 3. Diagrama de Sequência – Movimento de Cartas
```mermaid
sequenceDiagram
    actor Player
    participant SpiderView
    participant Game
    participant Column_from as Column(origem)
    participant Column_to as Column(destino)

    Player->>SpiderView: Arrasta cartas e solta sobre coluna destino
    SpiderView->>SpiderView: target_column_from_point(x,y)
    SpiderView->>Game: move(from_col, from_idx, to_col)

    Game->>Column_from: movable_subsequence_from(from_idx)
    Column_from-->>Game: Sequence(seq) ou None

    Game->>Game: can_receive(Column_to, seq)?
    alt movimento válido
        Game->>Column_from: pop_n(len(seq))
        Column_from-->>Game: Sequence(moved)
        Game->>Column_to: push_seq(moved)

        Game->>Column_from: reveal_top_if_needed()
        Game->>Game: verifica K→A mononaipe no destino
        Game->>Game: registra Move em historico
        Game-->>SpiderView: True
    else movimento inválido
        Game-->>SpiderView: False
    end

    SpiderView-->>Player: Atualiza desenho conforme novo estado
```

### 4. Diagrama de Sequência – deal() + undo() de distribuição
```mermaid
sequenceDiagram
    actor Player
    participant SpiderView
    participant Game
    participant Stock
    participant Col0 as Column[0..9]

    Player->>SpiderView: Pressiona Espaço
    SpiderView->>Game: deal()

    Game->>Game: verifica colunas vazias?
    Game->>Stock: verifica se len(cards) >= 10
    alt pode distribuir
        Game->>Game: cria Move(tipo="deal")
        loop 10 colunas
            Game->>Stock: pop()
            Stock-->>Game: card
            Game->>Col0: append(card)
            Game->>Move: registra (col_idx, card) em deal_cartas
        end
        Game->>Game: historico.append(Move)
        Game-->>SpiderView: True
    else bloqueia distribuição
        Game-->>SpiderView: False
    end

    Player->>SpiderView: Pressiona U (undo)
    SpiderView->>Game: undo()

    Game->>Game: move = historico.pop()
    alt move.tipo == "deal"
        loop reversed(move.deal_cartas)
            Game->>Col0: pop()  # remove carta distribuída
            Col0-->>Game: card
            Game->>Stock: push(card face_down)
        end
        Game-->>SpiderView: True
    end

    SpiderView-->>Player: Atualiza mesa com estado anterior
```

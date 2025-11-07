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

### Diagrama UML
```mermaid
classDiagram
    direction LR

    class Carta {
        +valor: int
        +naipe: Naipe
        +virada: bool
        +id: str
        +__repr__() str
        +mesmo_naipe(c: Carta) bool
        +um_abaixo_de(c: Carta) bool
    }

    class Naipe {
        <<enumeration>>
        ESPADAS
        COPAS
    }

    class Pilha {
        +cartas: List<Carta>
        +topo() Carta
        +vazia() bool
        +tamanho() int
        +pode_receber(seq: Sequencia) bool
        +push_seq(seq: Sequencia) void
        +pop_n(n: int) Sequencia
    }
    <<abstract>> Pilha

    class Coluna {
        +revele_topo_se_preciso() void
        +subsequencia_movivel(desde_index: int) Sequencia
    }

    class Estoque {
        +disponivel() bool
        +dar_10(colunas: List<Coluna>) void
    }

    class Baralho {
        -cartas: List<Carta>
        +criar_doispacos() Baralho
        +embaralhar(rng) void
        +comprar() Carta
        +restantes() int
    }

    class Sequencia {
        +cartas: List<Carta>
        +eh_descendente_mesmo_naipe() bool
        +tamanho() int
        +base() Carta
        +topo() Carta
    }

    class Jogo {
        +colunas: List<Coluna>
        +estoque: Estoque
        +sequencias_removidas: int
        +historico: List<Movimento>
        +iniciar(seed) void
        +mover(col_i: int, idx: int, col_j: int) bool
        +distribuir() bool
        +checar_e_remover_completas(col: Coluna) int
        +ha_movimentos_validos() bool
        +vitoria() bool
        +desfazer() bool
    }

    class Movimento {
        +origem_col: int
        +origem_idx: int
        +destino_col: int
        +seq: Sequencia
        +gerou_remocao: bool
        +viradas_no_fim: List<Carta>
    }

    Pilha <|-- Coluna
    Pilha <|-- Estoque
    Coluna o-- Sequencia
    Sequencia *-- Carta
    Jogo o-- Coluna
    Jogo o-- Estoque
    Jogo o-- Movimento
    Baralho o-- Carta
```

---

### Estados e Fluxo Essencial

```mermaid
stateDiagram-v2
    [*] --> Iniciando
    Iniciando --> Jogando: distribuir inicial (10 colunas)
    Jogando --> Distribuindo: ação "dar 10" (todas colunas não vazias?)
    Distribuindo --> Jogando
    Jogando --> Vitoria: 8 sequências removidas
    Jogando --> Travado: sem movimentos e estoque vazio
```
---

### Diagrama de Sequência

```mermaid
sequenceDiagram
    participant UI
    participant Jogo
    participant ColOrigem as Coluna[origem]
    participant ColDestino as Coluna[destino]

    UI->>Jogo: mover(col_i, idx, col_j)
    Jogo->>ColOrigem: subsequencia_movivel(idx)
    ColOrigem-->>Jogo: Sequencia(seq) (descendente e mononaipe?)
    Jogo->>ColDestino: pode_receber(seq)?
    ColDestino-->>Jogo: true
    Jogo->>ColOrigem: pop_n(seq.tamanho())
    Jogo->>ColDestino: push_seq(seq)
    Jogo->>Jogo: checar_e_remover_completas(ColDestino)
    Jogo->>ColOrigem: revele_topo_se_preciso()
    Jogo-->>UI: sucesso
```
---

### Camada de Visualização

```mermaid
classDiagram
    direction LR

    class CardSprite {
        +model: Carta
        +on_draw()
        +on_update(dt)
        +hitbox
    }

    class DragController {
        +seq_em_drag: Sequencia
        +origem_col: int
        +origem_idx: int
        +start_drag(x, y)
        +update_drag(x, y)
        +drop(target_col: int)
    }

    class SpiderView {
        +jogo: Jogo
        +sprites: SpriteList
        +on_draw()
        +on_mouse_press()
        +on_mouse_release()
        +on_key_press()
    }

    SpiderView --|> ArcadeWindow
    CardSprite o-- Carta
    SpiderView o-- Jogo
    SpiderView o-- CardSprite
    SpiderView o-- DragController
```
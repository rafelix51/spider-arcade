"""
Spider (2 naipes) — Protótipo simples com Arcade 3.3.3 (compatível Python 3.13)
- Retângulos e textos (sem assets).
- Drag & drop de sequência válida (mesmo naipe, descendente).
- Distribuição do estoque (barra de espaço).
- Remoção automática K→A mononaipe.
- Contador de movimentos (inclui move, undo, deal).
- Timer iniciado no primeiro movimento e parado ao fim do jogo.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import arcade

# =========================
# Configs visuais / layout
# =========================
SCREEN_W = 1200
SCREEN_H = 800
SCREEN_TITLE = "Spider (2 Naipes) — Protótipo Arcade 3.3.3"

CARD_W = 80
CARD_H = 110
COL_SPACING_X = 100
COL_LEFT = 90
COL_TOP_Y = SCREEN_H - 140
STACK_DY = 28  # deslocamento vertical entre cartas da coluna

STOCK_POS = (SCREEN_W - 80, SCREEN_H - 130)
STOCK_W, STOCK_H = 90, 120

BG_COLOR = arcade.color.DARK_SPRING_GREEN
CARD_COLOR = arcade.color.ANTI_FLASH_WHITE
CARD_BACK = arcade.color.DARK_BLUE_GRAY
CARD_BORDER = arcade.color.BLACK
VALID_HIGHLIGHT = arcade.color.APPLE_GREEN
INVALID_HIGHLIGHT = arcade.color.RED_DEVIL

FONT_SIZE = 14

# =========================
# Núcleo do jogo (modelo)
# =========================

class Suit:
    S = "S"  # espadas
    H = "H"  # copas

SUIT_LABEL = {Suit.S: "♠", Suit.H: "♥"}

SUIT_COLOR = {
    Suit.S: arcade.color.BLACK,
    Suit.H: arcade.color.DARK_RED
}

@dataclass
class Card:
    value: int          # 1=A ... 13=K
    suit: str           # "S" | "H"
    face_up: bool = False
    id: str = ""

    def label(self) -> str:
        faces = {1: "A", 11: "J", 12: "Q", 13: "K"}
        v = faces.get(self.value, str(self.value))
        return f"{v}{SUIT_LABEL[self.suit]}"

    def one_below(self, other: "Card") -> bool:
        return self.value == other.value - 1

@dataclass
class Sequence:
    cards: List[Card]

    def is_desc_same_suit(self) -> bool:
        if len(self.cards) <= 1:
            return True
        s = self.cards[0].suit
        for i in range(1, len(self.cards)):
            if self.cards[i].suit != s:
                return False
            if self.cards[i].value != self.cards[i - 1].value - 1:
                return False
        return True

    def top(self) -> Card:
        return self.cards[-1]

    def base(self) -> Card:
        return self.cards[0]

    def size(self) -> int:
        return len(self.cards)

@dataclass
class Move:
    origem_col: int
    origem_idx: int
    destino_col: int
    qtd_cartas: int
    viradas_no_fim: List[Card] = field(default_factory=list)
    seq_removida: List[Card] = field(default_factory=list)
    tipo: str = "move"  # "move" ou "deal"
    deal_cartas: List[Tuple[int, Card]] = field(default_factory=list)

class Column:
    def __init__(self) -> None:
        self.cards: List[Card] = []

    def push_seq(self, seq: Sequence) -> None:
        self.cards.extend(seq.cards)

    def pop_n(self, n: int) -> Sequence:
        seq = self.cards[-n:]
        self.cards = self.cards[:-n]
        return Sequence(seq)

    def top(self) -> Optional[Card]:
        return self.cards[-1] if self.cards else None

    def empty(self) -> bool:
        return not self.cards

    def reveal_top_if_needed(self) -> None:
        if self.cards and not self.cards[-1].face_up:
            self.cards[-1].face_up = True

    def movable_subsequence_from(self, idx: int) -> Optional[Sequence]:
        if idx < 0 or idx >= len(self.cards):
            return None
        for c in self.cards[idx:]:
            if not c.face_up:
                return None
        seq = Sequence(self.cards[idx:])
        if seq.is_desc_same_suit() or len(seq.cards) == 1:
            return seq
        return None

class Stock:
    def __init__(self) -> None:
        self.cards: List[Card] = []

    def available(self) -> bool:
        return len(self.cards) >= 10

class Deck:
    @staticmethod
    def create_two_suits_double_deck() -> List[Card]:
        cards: List[Card] = []
        for deck_i in range(2):
            for suit in (Suit.S, Suit.H):
                for v in range(1, 14):
                    cards.append(Card(value=v, suit=suit, id=f"{suit}{v}-{deck_i}"))
            # duplicar S e H para completar 104 cartas
            for suit in (Suit.S, Suit.H):
                for v in range(1, 14):
                    cards.append(Card(value=v, suit=suit, id=f"{suit}{v}-x{deck_i}"))
        assert len(cards) == 104
        return cards

class Game:
    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is None:
            self.rng = random.Random()
        else:
            self.rng = random.Random(seed)
        self.columns: List[Column] = [Column() for _ in range(10)]
        self.stock = Stock()
        self.removed_sequences = 0
        self.historico: List[Move] = []
        self._start()

    def _start(self) -> None:
        cards = Deck.create_two_suits_double_deck()
        self.rng.shuffle(cards)

        deal_counts = [6] * 4 + [5] * 6
        idx = 0
        for col_i, count in enumerate(deal_counts):
            for _ in range(count):
                self.columns[col_i].cards.append(cards[idx])
                idx += 1
            if self.columns[col_i].cards:
                self.columns[col_i].cards[-1].face_up = True

        self.stock.cards = cards[idx:]

    def can_receive(self, dest: Column, seq: Sequence) -> bool:
        if dest.empty():
            return True
        top = dest.top()
        assert top is not None
        if seq.size() == 1:
            return seq.top().one_below(top)
        return seq.is_desc_same_suit() and seq.base().one_below(top)

    def move(self, col_i: int, idx: int, col_j: int) -> bool:
        if col_i == col_j:
            return False

        col_from = self.columns[col_i]
        col_to = self.columns[col_j]

        seq = col_from.movable_subsequence_from(idx)
        if seq is None:
            return False
        if not self.can_receive(col_to, seq):
            return False

        move_info = Move(col_i, idx, col_j, len(seq.cards))

        # Efetivar movimento
        moved = col_from.pop_n(len(seq.cards))
        col_to.push_seq(moved)

        # Revelar topo da coluna de origem (se necessário) e registrar para undo
        top_before = col_from.top()
        was_face_down = top_before is not None and not top_before.face_up
        col_from.reveal_top_if_needed()
        top_after = col_from.top()
        if was_face_down and top_after is top_before and top_after is not None and top_after.face_up:
            move_info.viradas_no_fim.append(top_after)

        # Verificar se gerou sequência completa no destino (K -> A mononaipe)
        if len(col_to.cards) >= 13:
            top13 = col_to.cards[-13:]
            seq_top = Sequence(top13)
            if seq_top.is_desc_same_suit() and seq_top.base().value == 13 and seq_top.top().value == 1:
                move_info.seq_removida = top13.copy()
                col_to.cards = col_to.cards[:-13]
                self.removed_sequences += 1
                col_to.reveal_top_if_needed()

        self.historico.append(move_info)
        return True

    def undo(self) -> bool:
        """Desfaz o último movimento (normal ou distribuição), se houver."""
        if not self.historico:
            return False

        move = self.historico.pop()

        # Desfazer distribuição do estoque
        if move.tipo == "deal":
            for col_idx, expected_card in reversed(move.deal_cartas):
                col = self.columns[col_idx]
                if not col.cards:
                    return False
                card = col.cards.pop()
                card.face_up = False
                self.stock.cards.append(card)
            return True

        # Movimentos normais
        dest = self.columns[move.destino_col]
        origem = self.columns[move.origem_col]

        # Restaura sequência removida, se houve
        if move.seq_removida:
            dest.cards.extend(move.seq_removida)
            self.removed_sequences -= 1
            return True

        # Volta cartas movidas
        moved_back = dest.pop_n(move.qtd_cartas)
        origem.cards.extend(moved_back.cards)

        # Desvira cartas que foram viradas nesse movimento
        for c in move.viradas_no_fim:
            c.face_up = False

        return True

    def deal(self) -> bool:
        """Distribui 10 cartas (1 por coluna) e registra no histórico para permitir undo."""
        if any(col.empty() for col in self.columns):
            return False
        if len(self.stock.cards) < 10:
            return False

        move = Move(
            origem_col=-1,
            origem_idx=-1,
            destino_col=-1,
            qtd_cartas=10,
            tipo="deal"
        )

        for col_idx, col in enumerate(self.columns):
            card = self.stock.cards.pop()
            card.face_up = True
            col.cards.append(card)
            move.deal_cartas.append((col_idx, card))

        self.historico.append(move)
        return True

    def reset(self, seed: Optional[int] = None) -> None:
        self.__init__(seed=seed)

# =========================
# Camada de visual (Arcade)
# =========================

def col_x(col_idx: int) -> float:
    return COL_LEFT + col_idx * COL_SPACING_X

def card_rect(col_idx: int, row_idx: int,
              dragging=False, dx=0, dy=0) -> Tuple[float, float, float, float]:
    x = col_x(col_idx)
    y = COL_TOP_Y - row_idx * STACK_DY
    if dragging:
        x += dx
        y += dy
    return x, y, CARD_W, CARD_H

class DragState:
    def __init__(self) -> None:
        self.active = False
        self.from_col = -1
        self.from_idx = -1
        self.seq: Optional[Sequence] = None
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
        self.valid_target_col = -1

    def reset(self):
        self.__init__()

class SpiderView(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_W, SCREEN_H, SCREEN_TITLE)
        arcade.set_background_color(BG_COLOR)
        self.game = Game()
        self.drag = DragState()
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        # Estatísticas de jogo
        self.moves_count = 0
        self.timer_running = False
        self.elapsed_time = 0.0
        self.game_finished = False

    # ---------- helpers de estado ----------
    def _reset_stats(self):
        self.moves_count = 0
        self.timer_running = False
        self.elapsed_time = 0.0
        self.game_finished = False

    def _register_action(self):
        """Registra uma ação do jogador (move, undo, deal) bem-sucedida."""
        if not self.timer_running and not self.game_finished:
            self.timer_running = True
        self.moves_count += 1

    def _check_game_finished(self):
        """Marca fim de jogo quando todas as sequências foram removidas."""
        if not self.game_finished:
            # Spider 2 naipes: 104 cartas / 13 = 8 sequências
            if self.game.removed_sequences >= 8:
                self.game_finished = True
                self.timer_running = False

    # ---------- ciclo do arcade ----------
    def on_update(self, delta_time: float):
        if self.timer_running and not self.game_finished:
            self.elapsed_time += delta_time
        self._check_game_finished()

    # ------------- util de hit-test -------------
    def pick_column_card(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        for ci, col in enumerate(self.game.columns):
            if not col.cards:
                cx = col_x(ci)
                rect = arcade.rect.XYWH(cx, COL_TOP_Y, CARD_W, CARD_H)
                if rect.left <= x <= rect.right and rect.bottom - STACK_DY * 2 <= y <= rect.top:
                    return (ci, -1)
                continue
            for idx in range(len(col.cards) - 1, -1, -1):
                rx, ry, rw, rh = card_rect(ci, idx)
                rect = arcade.rect.XYWH(rx, ry, rw, rh)
                if rect.left <= x <= rect.right and rect.bottom <= y <= rect.top:
                    return (ci, idx)
        return None

    def target_column_from_point(self, x: float, y: float) -> Optional[int]:
        hit = self.pick_column_card(x, y)
        if hit is None:
            return None
        col_idx, _ = hit
        return col_idx

    # ------------- eventos -------------
    def on_draw(self):
        self.clear()

        # Estoque
        stock_count = len(self.game.stock.cards)

        if stock_count > 0:
            max_layers = 3
            layers = min(max_layers, stock_count)
            for i in range(layers):
                offset = i * 3
                r = arcade.rect.XYWH(
                    STOCK_POS[0] + offset,
                    STOCK_POS[1] + offset,
                    STOCK_W,
                    STOCK_H,
                )
                arcade.draw_rect_filled(r, CARD_BACK)
                arcade.draw_rect_outline(r, CARD_BORDER, 2)

                inner = arcade.rect.XYWH(
                    r.center_x,
                    r.center_y,
                    STOCK_W - 12,
                    STOCK_H - 16,
                )
                arcade.draw_rect_outline(inner, arcade.color.LIGHT_GRAY, 1)

            arcade.draw_text(
                f"{stock_count}",
                STOCK_POS[0],
                STOCK_POS[1] - STOCK_H / 2 - 24,
                arcade.color.WHITE,
                FONT_SIZE,
                anchor_x="center",
            )
        else:
            arcade.draw_rect_outline(
                arcade.rect.XYWH(STOCK_POS[0], STOCK_POS[1], STOCK_W, STOCK_H),
                arcade.color.LIGHT_GRAY,
                2,
            )
            arcade.draw_text(
                "Vazio",
                STOCK_POS[0],
                STOCK_POS[1] - STOCK_H / 2 - 24,
                arcade.color.LIGHT_GRAY,
                FONT_SIZE,
                anchor_x="center",
            )

        # Colunas e cartas
        for ci, col in enumerate(self.game.columns):
            cx = col_x(ci)
            arcade.draw_rect_outline(
                arcade.rect.XYWH(cx, COL_TOP_Y, CARD_W, CARD_H),
                CARD_BORDER,
                1,
            )

            for idx, card in enumerate(col.cards):
                dragging_this = self.drag.active and self.drag.from_col == ci and idx >= self.drag.from_idx
                if dragging_this:
                    continue
                self.draw_card(card, ci, idx)

        # Seq em drag (por cima)
        if self.drag.active and self.drag.seq is not None:
            base_idx = self.drag.from_idx
            for k, card in enumerate(self.drag.seq.cards):
                ci = self.drag.from_col
                idx = base_idx + k
                self.draw_card(card, ci, idx, dragging=True,
                               dx=self.drag.mouse_dx, dy=self.drag.mouse_dy)

            tgt = self.target_column_from_point(self._mouse_x, self._mouse_y)
            if tgt is not None:
                color = VALID_HIGHLIGHT if self.drag.valid_target_col == tgt else INVALID_HIGHLIGHT
                arcade.draw_rect_outline(
                    arcade.rect.XYWH(col_x(tgt), COL_TOP_Y,
                                     CARD_W + 6, CARD_H + 6),
                    color,
                    3,
                )

        # Timer formatado
        total_seconds = int(self.elapsed_time)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        status = " | FIM DE JOGO" if self.game_finished else ""

        # HUD
        arcade.draw_text(
            f"Seq. removidas: {self.game.removed_sequences}"
            f"  | Movimentos: {self.moves_count}"
            f"  | Tempo: {time_str}{status}"
            f"  | U desfazer"
            f"  | Espaço distribuir"
            f"  | R reiniciar",
            20,
            20,
            arcade.color.WHITE,
            FONT_SIZE,
        )

    def draw_card(self, card: Card, ci: int, idx: int,
                  dragging=False, dx=0, dy=0):
        x, y, w, h = card_rect(ci, idx, dragging, dx, dy)
        r = arcade.rect.XYWH(x, y, w, h)
        if card.face_up:
            arcade.draw_rect_filled(r, CARD_COLOR)
            arcade.draw_rect_outline(r, CARD_BORDER, 2)

            text_color = SUIT_COLOR.get(card.suit, arcade.color.BLACK)

            arcade.draw_text(
                card.label(),
                x - w / 2 + 6,
                y - h / 2 + 6,
                text_color,
                FONT_SIZE,
            )

            arcade.draw_text(
                card.label(),
                x + w / 2 - 6,
                y + h / 2 - 22,
                text_color,
                FONT_SIZE,
                anchor_x="right",
            )
        else:
            arcade.draw_rect_filled(r, CARD_BACK)
            arcade.draw_rect_outline(r, CARD_BORDER, 2)

            inner = arcade.rect.XYWH(x, y, w - 10, h - 10)
            arcade.draw_rect_outline(inner, arcade.color.LIGHT_GRAY, 1)

            center = arcade.rect.XYWH(x, y, w - 26, h - 40)
            arcade.draw_rect_filled(center, arcade.color.DARK_BLUE_GRAY)
            arcade.draw_rect_outline(center, arcade.color.LIGHT_GRAY, 1)

            arcade.draw_line(
                center.left + 6,
                center.bottom + 6,
                center.right - 6,
                center.top - 6,
                arcade.color.LIGHT_GRAY,
                1,
            )
            arcade.draw_line(
                center.left + 6,
                center.top - 6,
                center.right - 6,
                center.bottom + 6,
                arcade.color.LIGHT_GRAY,
                1,
            )

            arcade.draw_text(
                "🕷",
                x,
                y - 8,
                arcade.color.LIGHT_GRAY,
                20,
                anchor_x="center",
            )

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self._mouse_x, self._mouse_y = x, y
        hit = self.pick_column_card(x, y)
        if hit is None:
            return
        col_idx, card_idx = hit
        if card_idx == -1:
            return

        col = self.game.columns[col_idx]
        if not col.cards[card_idx].face_up:
            return

        seq = col.movable_subsequence_from(card_idx)
        if seq is None:
            return

        self.drag.active = True
        self.drag.from_col = col_idx
        self.drag.from_idx = card_idx
        self.drag.seq = seq

        rx, ry, rw, rh = card_rect(col_idx, card_idx)
        self.drag.mouse_dx = x - rx
        self.drag.mouse_dy = y - ry

        tgt = self.target_column_from_point(x, y)
        self.drag.valid_target_col = -1
        if tgt is not None and self.game.can_receive(self.game.columns[tgt], seq):
            self.drag.valid_target_col = tgt

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self._mouse_x, self._mouse_y = x, y
        if not self.drag.active or self.drag.seq is None:
            return
        tgt = self.target_column_from_point(x, y)
        self.drag.valid_target_col = -1
        if tgt is not None and self.game.can_receive(self.game.columns[tgt], self.drag.seq):
            self.drag.valid_target_col = tgt

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        self._mouse_x, self._mouse_y = x, y
        if not self.drag.active or self.drag.seq is None:
            self.drag.reset()
            return

        tgt = self.target_column_from_point(x, y)
        action_done = False
        if tgt is not None and self.drag.valid_target_col == tgt:
            if self.game.move(self.drag.from_col, self.drag.from_idx, tgt):
                action_done = True

        self.drag.reset()

        if action_done:
            self._register_action()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.SPACE:
            if self.game.deal():
                self._register_action()
        elif symbol == arcade.key.U:
            if self.game.undo():
                self._register_action()
        elif symbol == arcade.key.R:
            self.game.reset()
            self._reset_stats()
        elif symbol == arcade.key.ESCAPE:
            arcade.close_window()

def main():
    SpiderView()
    arcade.run()

if __name__ == "__main__":
    main()

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum, auto


class Color(StrEnum):
    Black = auto()
    White = auto()
    def char(self) -> str:
        return str(self)[0]


# class PlayerColor(StrEnum):
#     Black = "black"
#     White = "white"


class PieceType(StrEnum):
    Road = auto()
    Stone = auto()
    Capstone = auto()

    def char(self) -> str:
        return str(self)[0].upper()


@dataclass
class Piece:
    type: PieceType
    color: Color

    def __str__(self):
        return f"{self.type.char()}{self.color.char()}"




class Player:
    def __init__(self, color: Color):
        self.color = color

type TilePointer = tuple[int, int]

@dataclass
class Tile:
    pieces: list[Piece]

    def __str__(self) -> str:
        pieces_str = ", ".join(map(str, self.pieces))
        return f"[{pieces_str}]"

    def __bool__(self) -> bool:
        return not self.is_empty()

    def owner(self) -> Color | None:
        if not self.pieces:
            return None
        top_piece = self.pieces[-1]
        if top_piece.type in (PieceType.Road, PieceType.Capstone):
            return top_piece.color
        return None

    def is_empty(self) -> bool:
        return not self.pieces

    def top_piece(self) -> Piece:
        if self.is_empty():
            raise ValueError("Tile is empty")
        return self.pieces[-1]

    def add_pieces(self, pieces: Iterable[Piece]) -> None:
        self.pieces.extend(pieces)


class Board:
    size: int
    board: list[list[Tile]]

    def __init__(self, boardsize: int):
        self.size = boardsize
        self.board = create_board(boardsize)

    def __str__(self) -> str:
        board_visual = []
        for y in range(self.size):
            row_visual = []
            for x in range(self.size):
                row_visual.append(f"{self.board[y][x]}")
            board_visual.append(" ".join(row_visual))  # must be string for .join
        return "\n".join(board_visual)

    def tiles(self) -> Iterator[Tile]:
        for row in self.board:
            yield from row

    def non_empty_tiles(self) -> Iterator[Tile]:
        for tile in self.tiles():
            if tile:
                yield tile

    def move(self, src:TilePointer, dst:TilePointer) -> None:
        pass

    def get_tile(self, ptr:TilePointer) -> Tile:
        x, y = ptr
        if x in range(self.size) and y in range(self.size):
            return self.board[y][x]
        raise ValueError("Tile index out of bounds")

    def add_pieces(self, ptr:TilePointer, pieces: Iterable[Piece]) -> None:
        self.get_tile(ptr).add_pieces(pieces)

    def clear_tile(self, ptr:TilePointer) -> None:
        self.get_tile(ptr).clear()

    def is_legal_move(self) -> bool:
        pass

    def is_full(self) -> bool:
        return any(self.non_empty_tiles())

    def get_winner(self) -> Color | None:
        if self.is_full():
            white_points = 0
            black_points = 0  # TODO: add "+ komi"
            for tile in self.non_empty_tiles():
                owner = tile.owner()
                if owner == Color.White:
                    white_points += 1
                if owner == Color.Black:
                    black_points += 1
            if white_points > black_points:
                return Color.White
            if white_points < black_points:
                return Color.Black
        return None


@dataclass
class Game:
    turncount: int
    player: Color
    komi: float
    board: Board


def start_menu() -> None:
    boardsize = int(input("Choose board size: "))
    board = Board(boardsize)
    komi = 0.5  # TODO: add as input
    # game = Game(board, komi=komi, turncount=0)

    #manual inputs
    board.add_pieces((0,0), [Piece(PieceType.Road, Color.White)])
    print(board)
    if board.get_winner() is not None:
        print(f"The {board.get_winner()} player is the winner.")


def create_board(size: int) -> list:
    return [[Tile([]) for _ in range(size)] for _ in range(size)]


def turn() -> None:
    pass


if __name__ == "__main__":
    print(
        "Welcome to Tak, an abstract tactical board game.\n"
        "When prompted, enter your move.\n"
        "Enjoy the game.\n"
    )
    start_menu()

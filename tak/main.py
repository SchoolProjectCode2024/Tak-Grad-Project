from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum, auto


class Color(StrEnum):
    Black = auto()
    White = auto()
    def char(self) -> str:
        return str(self)[0]

class PieceType(StrEnum):
    Road = auto()
    Wall = auto()
    Capstone = auto()

    def char(self) -> str:
        return str(self)[0].upper()

@dataclass
class Piece:
    type: PieceType
    color: Color

    def __str__(self):
        return f"{self.type.char()}{self.color.char()}"

    def __iter__(self):
        yield self

class Player:
    color: Color
    piece_counter: int
    capstone_counter: int

    def __init__(self, color: Color, board_size: int):
        self.color = color
        self.piece_counter = self.add_starting_pieces(board_size, PieceType.Road)
        self.capstone_counter = self.add_starting_pieces(board_size, PieceType.Capstone)

    def add_starting_pieces(self, board_size: int, type: PieceType) -> int:  # noqa: A002, PLR0911, PLR0912
        """values = {
            (4, Road): 15,
            (4, Capstone): 0
        }

        return values[board_size,type]"""
        if board_size == 4:
            if type == PieceType.Road:
                return 15
            if type == PieceType.Capstone:
                return 0
        if board_size == 5:
            if type == PieceType.Road:
                return 21
            if type == PieceType.Capstone:
                return 1
        if board_size == 6:
            if type == PieceType.Road:
                return 30
            if type == PieceType.Capstone:
                return 1
        if board_size == 7:
            if type == PieceType.Road:
                return 40
            if type == PieceType.Capstone:
                return 2
        if board_size == 8:
            if type == PieceType.Road:
                return 50
            if type == PieceType.Capstone:
                return 2
        raise ValueError("Invalid board size - cant add pieces.")

    def has_pieces(self) -> bool:
        return self.piece_counter + self.capstone_counter != 0

type TilePointer = tuple[int, int]

@dataclass
class Tile:
    pieces: list[Piece]

    def __str__(self) -> str:
        pieces_str = ", ".join(map(str, self.pieces)) if not self.is_empty() else "  "
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
        self.board = self.create_board(boardsize)
    #unindexed
    """ def __str__(self) -> str:
        board_visual = []
        for y in range(self.size):
            row_visual = []
            for x in range(self.size):
                row_visual.append(f"{self.board[y][x]}")
            board_visual.append(" ".join(row_visual))  # must be string for .join
        return "\n".join(board_visual) """
    #indexed
    def __str__(self) -> str:
        board_visual = []
        index_row = [""]
        for y in range(self.size):
            row_visual = [str(self.size - y)]
            for x in range(self.size):
                row_visual.append(f"{self.board[y][x]}")
            board_visual.append(" ".join(row_visual))  # must be string for .join
        for i in range(self.size):
            index_row.append(str(i + 1))
        board_visual.append("    ".join(index_row))
        return "\n".join(board_visual)

    def create_board(self, size: int) -> list:
        return [[Tile([  ]) for _ in range(size)] for _ in range(size)]

    def tiles(self) -> Iterator[Tile]:
        for row in self.board:
            yield from row

    def non_empty_tiles(self) -> Iterator[Tile]:
        for tile in self.tiles():
            if tile:
                yield tile
    def get_row(self, x: int) -> Iterator[Tile]:
            yield from self[x]

    def get_column(self, y: int) -> Iterator[Tile]:
        for x in range(self.size):
            yield self[y][x]

    def move(self, src:TilePointer, dst:TilePointer, amount:int) -> None:
        pass

    def get_tile(self, ptr:TilePointer) -> Tile | None:
        x, y = ptr
        if x in range(self.size) and y in range(self.size):
            return self.board[y][x]
        return None
    def add_pieces(self, ptr:TilePointer, pieces: Iterable[Piece]) -> None:
        self.get_tile(ptr).add_pieces(pieces)

    def clear_tile(self, ptr:TilePointer) -> None:
        self.get_tile(ptr).clear()

    def is_legal_move(self) -> bool:
        pass

    def is_full(self) -> bool:
        return all(self.tiles())

    def endscreen() -> None:
        pass


@dataclass
class Game:
    turn_count: int
    player_white: Player
    player_black: Player
    komi: float
    board: Board

    def __init__(self, size: int, komi: float):
        self.board = Board(size)
        self.komi = komi
        self.player_white = Player(Color.White, size)
        self.player_black = Player(Color.Black, size)
        self.turn_count = 0

    def turn(self) -> None:
        self.turn_count = self.turn_count + 1
        turn_color = self.turn_color()
        turn_input = input("Input action:").split()
        instructions = self.parse_move_input(turn_input)
        if instructions[0] == "place":
            ptr = instructions[1]
            piece = Piece(instructions[2], turn_color)
            self.board.add_pieces(ptr, piece)
        elif instructions[0] == "move":
            src = instructions[1]
            dst = instructions[2]
            amount = instructions[3]
            self.board.move(src, dst, amount)

        print(self.board)

    def get_winner(self) -> Color | None | str:  # noqa: PLR0912
            if self.is_full() or not self.player_white.has_pieces() or not self.player_black.has_pieces():  # noqa: E501
                white_points = 0
                black_points = self.komi
                for tile in self.board.non_empty_tiles():
                    owner = tile.owner()
                    if owner == Color.White:
                        white_points += 1
                    if owner == Color.Black:
                        black_points += 1

                if white_points > black_points:
                    return Color.White
                if white_points < black_points:
                    return Color.Black
                if white_points == black_points:
                    return "tie"

            #check if board can contain a connection
            current_color = self.turn_color()
            both_colors = [Color.White, Color.Black]
            both_colors.remove(current_color)
            colors = [current_color, both_colors[0]]
            conn_hor = True
            conn_ver = True
            for color in colors:
                for i in range(self.board.size):
                    this_row = False
                    this_column = False
                    for tile in self.board.get_row(i):
                        if tile.owner() == color:
                            this_row = True
                    for tile in self.board.get_column(i):
                        if tile.owner() == color:
                            this_column = True
                    if not this_column:
                        conn_hor = False
                        break
                    if not this_row:
                        conn_ver = False
                        break
                if conn_ver or conn_hor:  # noqa: SIM102
                    if self.check_connection(color):
                        return color
            return None

    def check_connection(self, color: Color) -> bool:  # noqa: PLR0912
        for tile in (self.board.get_column(0) + self.board.get_row(0)):
            if tile.owner() == color:
                checked = []
                new_checked = []
                new_checked.append(tile)
                while new_checked:
                    checked.append(new_checked[-1])
                    new_checked.remove(new_checked[-1])
                    y_org, x_org = self.board.get_tile(new_checked[-1])
                    for x in range(x_org-1, x_org+2):
                        if x != x_org:
                            new_tile = self.board.get_tile(x, y_org)
                            if not (new_tile in checked or new_tile in new_checked):
                                new_checked.append(new_tile)
                        if x == x_org:
                            for y in range(y_org - 1, y_org + 2):
                                new_tile = self.board.get_tile(x, y)
                                if not (new_tile in checked or new_tile in new_checked):
                                    new_checked.append(new_tile)
                x_0, x_max, y_0, y_max = (False,) * 4
                for link in checked:
                    x, y = self.board.get_tile(link)
                    if x == 0:
                        x_0 = True
                    if x == self.board.size:
                        x_max = True
                    if y == 0:
                        y_0 = True
                    if y == self.board.size:
                        y_max = True
                if (x_0 and x_max) or (y_0 and y_max):
                    return True
        return False

    def turn_color(self) -> Color:
        if self.turn_count > 2:
            turn_color = Color.Black if self.turn_count % 2 else Color.White
        else:
            turn_color = Color.White if self.turn_count % 2 else Color.Black
        return turn_color

    def running_game(self) -> None:
        while self.board.get_winner() is None:
            self.turn()
        if self.board.get_winner() is Color:
            print(f"The {self.board.get_winner()} player is the winner.")
        if self.board.get_winner() == "tie":
            print("The game is a tie")
        print("Finish the rest.")

    def parse_move_input(self, turn_input: list) -> list:  # noqa: PLR0912
        #parse action type
        instructions = []
        if turn_input[0] == "P" or "M":
            if turn_input[0] == "P":
                instructions.append("place")
            if turn_input[0] == "M":
                instructions.append("move")
        else:
            raise ValueError("Incorrect input - action type.")
        #parse placing
        if turn_input[0] == "P":
            #parse placement
            coordinates = turn_input[1].split(",")
            x = int(coordinates[0])  - 1
            y = self.board.size - int(coordinates[1])
            if isinstance(self.board.get_tile((x, y)), Tile):
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")
            #parse piece type
            if turn_input[2] == "R":
                instructions.append(PieceType.Road)
            elif turn_input[2] == "W":
                instructions.append(PieceType.Wall)
            elif turn_input[2] == "C":
                instructions.append(PieceType.Capstone)
            else:
                raise ValueError("Incorrect input - not a valid piece.")
        #parse moving
        if turn_input[0] == "M":
            #parse org placement
            coordinates = turn_input[1].split(",")
            x = int(coordinates[0])  - 1
            y = self.board.size - int(coordinates[1])
            if self.board.get_tile((x, y)):
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")

            #parse new placement
            coordinates = turn_input[2].split(",")
            x = int(coordinates[0])  - 1
            y = self.board.size - int(coordinates[1])
            if self.board.get_tile((x, y)):
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")

            #parse moved amount
            if int(turn_input[3]) is int:
                instructions.append(int(turn_input[3]))
            elif len(turn_input) < 4:
                instructions.append(1)
            else:
                raise ValueError("Incorrect input - improper amount.")

        return instructions

def start_menu() -> None:
    size = int(input("Choose board size (4 - 8): "))
    if size not in range(4, 9):
        raise ValueError("Not a valid board size")
    komi = float(input("Choose komi: "))
    if komi % 0.5 != 0:
        raise ValueError("Komi should be noted in multiples of 0.5")
    cur_game = Game(size, komi)
    cur_game.running_game()
    #manual inputs
    """cur_game.board.add_pieces((0,0), [Piece(PieceType.Road, Color.White)])
    print(cur_game.board)"""

    #game end


if __name__ == "__main__":
    print("""
        Welcome to Tak, an abstract tactical board game.
        When prompted, enter your move in the format of:
        Placing a piece: ["P" x,y ("R" for Road, "W" for Wall, "C" for Capstone)]
        Moving a piece: ["M" (org x),(org y) (new x),(new y) (amount, blank for 1)]
        Enjoy the game.\n
        """
    )
    start_menu()

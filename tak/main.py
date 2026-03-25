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
        values = {
            (4, PieceType.Road): 15,
            (4, PieceType.Capstone): 0,
            (5, PieceType.Road): 21,
            (5, PieceType.Capstone): 1,
            (6, PieceType.Road): 30,
            (6, PieceType.Capstone): 1,
            (7, PieceType.Road): 40,
            (7, PieceType.Capstone): 2,
            (8, PieceType.Road): 50,
            (8, PieceType.Capstone): 2,
        }
        return values[board_size,type]
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
            raise ValueError("Tile is empty.")
        return self.pieces[-1]

    def add_pieces(self, pieces: Iterable[Piece]) -> None:
        self.pieces.extend(pieces)


class Board:
    size: int
    board: list[list[Tile]]

    def __init__(self, boardsize: int):
        self.size = boardsize
        self.board = self.create_board(boardsize)

    # unindexed
    """ def __str__(self) -> str:
        board_visual = []
        for y in range(self.size):
            row_visual = []
            for x in range(self.size):
                row_visual.append(f"{self.board[y][x]}")
            board_visual.append(" ".join(row_visual))  # must be string for .join
        return "\n".join(board_visual) """

    # indexed
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
        return [[Tile([]) for _ in range(size)] for _ in range(size)]

    def tiles(self) -> Iterator[Tile]:
        for row in self.board:
            yield from row

    def non_empty_tiles(self) -> Iterator[Tile]:
        for tile in self.tiles():
            if tile:
                yield tile

    def get_row(self, y: int) -> Iterator[Tile]:
        yield from self.board[y]

    def get_column(self, x: int) -> Iterator[Tile]:
        for y in range(self.size):
            yield self.board[y][x]

    def place(self, ptr: TilePointer, piece: Piece, color: Color) -> None:
        if self.check_placing_legality(ptr, piece, color):
            self.add_pieces(ptr, piece)
        else:
            raise ValueError("Ptr doesnt point to an empty tile.")

    def check_placing_legality(self, ptr: TilePointer, piece: Piece, color: Color) -> bool:
        if not self.get_tile(ptr).is_empty():
            raise ValueError("Tile not empty.")
        return True

    def move(
        self, src: TilePointer, dst: TilePointer, amount: int, color: Color
    ) -> None:
        tower = []

        if amount not in range(len(self.get_tile(src).pieces) + 1):
            raise ValueError("Not enough pieces in src.")

        for _ in range(amount):
            tower.append(self.get_tile(src).pieces.pop())
            
        if not self.check_move_legality(src, dst, amount, color, tower):
            raise ValueError("Move not legal.")

        (x_og, y_og), (x_new, y_new) = src, dst
        x_shift = x_new - x_og
        y_shift = y_new - y_og
        new_tile_ptr = (x_og + x_shift, y_og + y_shift)
        i = 1
        current_piece = tower.pop()
        self.get_tile(new_tile_ptr).pieces.append(current_piece)
        while tower:
            pot_tile = self.get_tile((x_og + x_shift * (i + 1), y_og + y_shift * (i + 1)))
            if not pot_tile.is_empty():
                pot_tile_top_type = pot_tile.top_piece().type
            else:
                pot_tile_top_type = None
            if (
                pot_tile is not None
                and pot_tile_top_type != PieceType.Capstone
                and (pot_tile_top_type != PieceType.Wall
                or tower[-1].type == PieceType.Capstone)
                and input("Place another piece? Non-empty to move:") != ""
            ):
                i = i + 1
                new_tile_ptr = (x_og + x_shift * i, y_og + y_shift * i)
            current_piece = tower.pop()
            if (
            current_piece.type == PieceType.Capstone
            and not self.get_tile(new_tile_ptr).is_empty()
            and self.get_tile(new_tile_ptr).top_piece().type == PieceType.Wall
            ):
                crush(new_tile_ptr)
            self.get_tile(new_tile_ptr).pieces.append(current_piece)

    def check_move_legality(self, src: TilePointer, dst: TilePointer, amount: int, color: Color, tower: list) -> bool:
        if self.get_tile(src).is_empty():
            raise ValueError("Move src is empty")
            return False

        move_options = self.neighbors(src)
        if dst not in move_options:
            raise ValueError("Dst not a neighbor of src.")
            return False

        if self.get_tile(src) is None or self.get_tile(dst) is None:
            raise ValueError("Src tile or dst tile not a valid tile.")
            return False

        dst_tile = self.get_tile(dst)
        if not (
                dst_tile.is_empty()
                or dst_tile.top_piece().type == PieceType.Road
                or (dst_tile.top_piece().type != PieceType.Wall
                and tower[-1].type == PieceType.Capstone)
            ):  
            raise ValueError("Dst tile not accesible")
            return False

        if self.get_tile(src).top_piece().color != color:
            raise ValueError("Src tile is not owned by you.")
            return False
        return True

    def in_board(self, ptr: TilePointer) -> bool:
        x, y = ptr
        return x in range(self.size) and y in range(self.size)

    def get_tile(self, ptr: TilePointer) -> Tile | None:
        if self.in_board(ptr):
            x, y = ptr
            return self.board[y][x]
        return None

    def get_tile_ptr(self, tile: Tile) -> TilePointer:
        for y in range(self.size):
            for x in range(self.size):
                if tile is self.get_tile((x, y)):
                    return (x, y)
        raise ValueError("Tile not in board.")

    def add_pieces(self, ptr: TilePointer, pieces: Iterable[Piece]) -> None:
        self.get_tile(ptr).add_pieces(pieces)

    def clear_tile(self, ptr: TilePointer) -> None:
        if self.get_tile(ptr):
            tile = self.get_tile(ptr)
            tile.clear()

    def crush(self, ptr: TilePointer) -> None:
        tile = self.get_tile(ptr)
        if tile.top_piece().type == PieceType.Wall:
            tile.top_piece().type = PieceType.Road

    def is_legal_move(self) -> bool:
        pass

    def is_full(self) -> bool:
        return all(self.tiles())

    def neighbors(self, ptr: TilePointer) -> Iterator[TilePointer]:
        x_og, y_og = ptr
        for dx, dy in (1, 0), (-1, 0), (0, 1), (0, -1):
            ptr = x_og + dx, y_og + dy
            if self.in_board(ptr):
                yield ptr


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

            place_type = piece.type
            for player in (self.player_white, self.player_black):
                if player.color == turn_color:
                    placing_player = player
            
            if piece.type == PieceType.Capstone and player.capstone_counter == 0:
                raise ValueError("Playet doesnt have capstones to place.")
            if piece.type != PieceType.Capstone and player.piece_counter == 0:
                raise ValueError("Player doesnt have piece to place.")

            self.board.place(ptr, piece, turn_color)
        elif instructions[0] == "move":
            src = instructions[1]
            dst = instructions[2]
            amount = instructions[3]
            self.board.move(src, dst, amount, turn_color)
        else:
            raise SyntaxError("Invalid turn input")

        print(self.board)

    def get_winner(self) -> Color | None | str:  # noqa: PLR0912
        if (
            self.board.is_full()
            or not self.player_white.has_pieces()
            or not self.player_black.has_pieces()
        ):
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

        # check if board can contain a connection
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
                for tile in list(self.board.get_row(i)):
                    if tile.owner() == color:
                        this_row = True
                for tile in list(self.board.get_column(i)):
                    if tile.owner() == color:
                        this_column = True
                if not this_column:
                    conn_hor = False
                if not this_row:
                    conn_ver = False
                if not conn_ver and not conn_hor:
                    break
            if conn_ver or conn_hor:  # noqa: SIM102
                if self.check_connection(color):
                    return color
        return None

    def check_connection(self, color: Color) -> bool:
        base_column = list(self.board.get_column(0))
        base_row = list(self.board.get_row(0))
        for tile in base_column + base_row:
            if tile.owner() != color:
                continue

            visited = []
            stack = [self.board.get_tile_ptr(tile)]
            while stack:
                current_tile_ptr = stack.pop()
                if current_tile_ptr not in visited:
                    visited.append(current_tile_ptr)
                for new_tile_ptr in self.board.neighbors(current_tile_ptr):
                    if (
                        self.board.get_tile(new_tile_ptr).owner() == color
                        and new_tile_ptr not in visited
                        and new_tile_ptr not in stack
                    ):
                        stack.append(new_tile_ptr)

            x_0, x_max, y_0, y_max = (False,) * 4
            for link in visited:
                x, y = link
                if x == 0:
                    x_0 = True
                if x == self.board.size - 1:
                    x_max = True
                if y == 0:
                    y_0 = True
                if y == self.board.size - 1:
                    y_max = True
            if (x_0 and x_max) or (y_0 and y_max):
                return True
        return False

    def turn_color(self) -> Color:
        if self.turn_count <= 2:
            return Color.Black if self.turn_count % 2 else Color.White

        return Color.White if self.turn_count % 2 else Color.Black

    def running_game(self) -> None:
        while self.get_winner() is None:
            self.turn()
        if self.get_winner() == "white" or self.get_winner() == "black":
            print(f"The {self.get_winner()} player is the winner.")
        if self.get_winner() == "tie":
            print("The game is a tie")
        print("Finish the rest.")

    def parse_move_input(self, turn_input: list) -> list:  # noqa: PLR0912
        # parse action type
        instructions = []
        if turn_input[0] == "P":
            instructions.append("place")
        elif turn_input[0] == "M":
            instructions.append("move")
        else:
            raise ValueError("Incorrect input - action type.")
        # parse placing
        if turn_input[0] == "P":
            # parse placement
            coordinates = str(turn_input[1]).split(",")
            x = int(coordinates[0]) - 1
            y = self.board.size - int(coordinates[1])
            if isinstance(self.board.get_tile((x, y)), Tile):
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")
            # parse piece type
            if turn_input[2] == "R":
                instructions.append(PieceType.Road)
            elif turn_input[2] == "W":
                instructions.append(PieceType.Wall)
            elif turn_input[2] == "C":
                instructions.append(PieceType.Capstone)
            else:
                raise ValueError("Incorrect input - not a valid piece.")
        # parse moving
        if turn_input[0] == "M":
            # parse org placement
            coordinates = str(turn_input[1]).split(",")
            x = int(coordinates[0]) - 1
            y = self.board.size - int(coordinates[1])
            if self.board.get_tile((x, y)) is not None:
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")

            # parse new placement
            coordinates = str(turn_input[2]).split(",")
            x = int(coordinates[0]) - 1
            y = self.board.size - int(coordinates[1])
            if self.board.get_tile((x, y)) is not None:
                instructions.append((x, y))
            else:
                raise ValueError("Incorrect input - not a valid tile.")

            # parse moved amount
            if len(turn_input) < 4:
                instructions.append(1)
            elif int(turn_input[3]) in range(self.board.size):
                instructions.append(int(turn_input[3]))
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
    # pregame manual inputs
    cur_game.board.add_pieces((0, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((0, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((0, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((0, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((1, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((2, 0), [Piece(PieceType.Road, Color.Black)])
    cur_game.board.add_pieces((0, 2), [Piece(PieceType.Wall, Color.Black)])
    print(cur_game.board)
    cur_game.running_game()

    # manual inputs
    """cur_game.board.add_pieces((0,0), [Piece(PieceType.Road, Color.White)])
    print(cur_game.board)"""

    # game end


def endscreen() -> None:
    pass


def pregame_inputs() -> None:
    pass


if __name__ == "__main__":
    print("""
        Welcome to Tak, an abstract tactical board game.
        When prompted, enter your move in the format of:
        Placing a piece: ["P" x,y ("R" for Road, "W" for Wall, "C" for Capstone)]
        Moving a piece: ["M" (org x),(org y) (new x),(new y) (amount, blank for 1)]
        Enjoy the game.\n
        """)
    start_menu()

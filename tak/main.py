from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum, auto


class InputError(Exception):
    pass


class MoveInputError(Exception):
    pass


class PlaceInputError(Exception):
    pass


class RulesError(Exception):
    pass

class PlaceError(Exception):
    pass

class MoveError(Exception):
    pass

class AmountError(Exception):
    pass

class Color(StrEnum):
    Black = auto()
    White = auto()

    def char(self) -> str:
        return str(self)[0]


class PieceType(StrEnum):
    FlatStone = auto()
    StandingStone = auto()
    Capstone = auto()

    def char(self) -> str:
        return str(self)[0]


@dataclass
class Piece:
    type: PieceType
    color: Color

    def __str__(self):
        return f"{self.type.char().lower()}{self.color.char().upper()}"

    def __iter__(self):
        yield self


class Player:
    color: Color
    piece_counter: int
    capstone_counter: int

    def __init__(self, color: Color, board_size: int):
        self.color = color
        self.piece_counter = self.add_starting_pieces(board_size, PieceType.FlatStone)
        self.capstone_counter = self.add_starting_pieces(board_size, PieceType.Capstone)

    def add_starting_pieces(self, board_size: int, piece_type: PieceType) -> int:
        values = {
            (4, PieceType.FlatStone): 15,
            (4, PieceType.Capstone): 0,
            (5, PieceType.FlatStone): 21,
            (5, PieceType.Capstone): 1,
            (6, PieceType.FlatStone): 30,
            (6, PieceType.Capstone): 1,
            (7, PieceType.FlatStone): 40,
            (7, PieceType.Capstone): 2,
            (8, PieceType.FlatStone): 50,
            (8, PieceType.Capstone): 2,
        }
        return values[board_size, piece_type]

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
        if top_piece.type in (PieceType.FlatStone, PieceType.Capstone):
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

    # indexed
    def __str__(self) -> str:
        x_idx = {
            (1): "a",
            (2): "b",
            (3): "c",
            (4): "d",
            (5): "e",
            (6): "f",
            (7): "g",
            (8): "h",
        }
        max_len = 0
        for tile in self.non_empty_tiles():
            cur_len = len(tile.pieces)
            max_len = max(cur_len, max_len)
        board_visual = []
        index_row = [" "]
        for y in range(self.size):
            row_visual = [str(self.size - y)]
            for x in range(self.size):
                tile_str = str(self.board[y][x])
                row_visual.append(tile_str.center(max_len * 4))

            board_visual.append("  ".join(row_visual))  # must be string for .join
        for i in range(self.size):
            idx = x_idx[i + 1]
            idx_width = 4 if max_len < 2 else max_len * 4
            index_row.append(idx.center(idx_width))

        board_visual.append("  ".join(index_row))
        if max_len < 3:
            return "\n".join(board_visual)
        return "\n\n".join(board_visual)

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

    def place(self, ptr: TilePointer, piece: Piece) -> None:
        if self.check_placing_legality(ptr):
            self.add_pieces(ptr, piece)
        else:
            raise PlaceError("Ptr doesnt point to an empty tile.")

    def check_placing_legality(self, ptr: TilePointer) -> bool:
        if not self.get_tile(ptr).is_empty():
            raise ValueError("Tile not empty.")
        return True

    def move(
        self, src: TilePointer, dst: TilePointer, amount: int, color: Color
    ) -> None:
        tower = []

        if amount not in range(len(self.get_tile(src).pieces) + 1):
            raise AmountError("Not enough pieces in src.")

        for i in range(amount):
            tower.append(self.get_tile(src).pieces[-i - 1])

        if not self.check_move_legality(src, dst, color, tower):
            raise MoveError("Move not legal.")

        for _ in range(amount):
            self.get_tile(src).pieces.pop()

        (x_og, y_og), (x_new, y_new) = src, dst
        x_shift = x_new - x_og
        y_shift = y_new - y_og
        new_tile_ptr = (x_og + x_shift, y_og + y_shift)
        i = 1
        current_piece = tower.pop()
        self.get_tile(new_tile_ptr).pieces.append(current_piece)
        while tower:
            pot_tile = self.get_tile(
                (x_og + x_shift * (i + 1), y_og + y_shift * (i + 1))
            )
            if not pot_tile.is_empty():
                pot_tile_top_type = pot_tile.top_piece().type
            else:
                pot_tile_top_type = None

            print(self)
            tower_visual = []
            for tile in tower:
                tower_visual.append(str(tile))
            print(tower_visual)

            if (
                pot_tile is not None
                and pot_tile_top_type != PieceType.Capstone
                and (
                    pot_tile_top_type != PieceType.StandingStone
                    or tower[-1].type == PieceType.Capstone
                )
                and input("Place another piece? Non-empty to move:") != ""
            ):
                i = i + 1
                new_tile_ptr = (x_og + x_shift * i, y_og + y_shift * i)
            current_piece = tower.pop()
            self.get_tile(new_tile_ptr).pieces.append(current_piece)
        if (
            len(self.get_tile(new_tile_ptr).pieces) > 1
            and self.get_tile(new_tile_ptr).pieces[-1].type == PieceType.Capstone
            and self.get_tile(new_tile_ptr).pieces[-2].type == PieceType.StandingStone
        ):
            self.crush(new_tile_ptr)

    def check_move_legality(
        self, src: TilePointer, dst: TilePointer, color: Color, tower: list
    ) -> bool:
        if self.get_tile(src).is_empty():
            raise MoveError("Move src is empty")

        neighbors = self.neighbors(src)
        move_options = list(neighbors)
        if dst not in move_options:
            raise MoveError("Dst not a neighbor of src.")

        if self.get_tile(src) is None or self.get_tile(dst) is None:
            raise MoveError("Src tile or dst tile not a valid tile.")

        dst_tile = self.get_tile(dst)
        if not (
            dst_tile.is_empty()
            or dst_tile.top_piece().type == PieceType.FlatStone
            or (
                dst_tile.top_piece().type == PieceType.StandingStone
                and tower[-1].type == PieceType.Capstone
            )
        ):
            raise MoveError("Dst tile not accesible")

        if self.get_tile(src).top_piece().color != color:
            raise MoveError("Src tile is not owned by you.")
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
        if (
            tile.pieces[-2].type == PieceType.StandingStone
            and tile.pieces[-1].type == PieceType.Capstone
        ):
            tile.pieces[-2].type = PieceType.FlatStone

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

    def turn(self) -> None:  # noqa: PLR0912, PLR0915
        self.turn_count = self.turn_count + 1
        turn_color = self.turn_color()
        for player in (self.player_white, self.player_black):
            if player.color == turn_color:
                cur_player = player
        if self.turn_count > 2:
            print(f"{turn_color[:1].upper() + turn_color[1:]} player's turn.")
            print(f"{cur_player.piece_counter} pieces left.")
            print(f"{cur_player.capstone_counter} capstones left.")
        else:
            colors = [Color.White, Color.Black]
            colors.remove(turn_color)
            color = colors[0]
            color = color[:1].upper() + color[1:]
            print(f"{color} player's turn.")
        while True:
            while True:
                try:
                    turn_input = input("Input action:").split()
                    instructions = self.parse_move_input(turn_input)
                    if instructions is None:
                        raise InputError  # noqa: TRY301
                    break
                except InputError:
                    print("Improper input form, try again.")
                except PlaceInputError:
                    print("Incorrect input - not a valid tile.")
                except RulesError:
                    print("Incorrect input - not a valid piece type.")
                except MoveInputError:
                    print("Incorrect input - not a valid tile.")

            try:
                if instructions[0] == "place":
                    ptr = instructions[1]
                    piece = Piece(instructions[2], turn_color)
                    if self.turn_count < 2 and piece.type != PieceType.FlatStone:
                        raise RulesError("First move must be placing a flat stone.")  # noqa: TRY301

                    if piece.type == PieceType.Capstone:
                        if cur_player.capstone_counter == 0:
                            raise ValueError("Player doesn't have capstones to place.")  # noqa: TRY301
                        cur_player.capstone_counter = cur_player.capstone_counter - 1
                    else:
                        if cur_player.piece_counter == 0:
                            raise ValueError("Player doesn't have pieces to place.")  # noqa: TRY301
                        cur_player.piece_counter = cur_player.piece_counter - 1
                    self.board.place(ptr, piece)

                elif instructions[0] == "move":
                    if self.turn_count > 2:
                        src = instructions[1]
                        dst = instructions[2]
                        amount = instructions[3]
                        self.board.move(src, dst, amount, turn_color)
                else:
                    raise SyntaxError("Invalid turn input")
                break
            except ValueError:
                if cur_player.capstone_counter == 0:
                    print("Player doesn't have capstones to place.")
                else:
                    print("Player doesn't have pieces to place.")
            except RulesError:
                print("First move must be placing a flat stone.")
            except PlaceError:
                print("Ptr doesnt point to an empty tile.")
            except MoveError:
                print("Move not legal.")
            except AmountError:
                print("Not enough pieces in src.")

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
        if input("Press Enter to play again.") == "":
            start_menu()

    def parse_move_input(self, turn_input: list) -> list | None:  # noqa: PLR0912
        try:
            # parse action type
            x_coord = {
                ("a"): 0,
                ("b"): 1,
                ("c"): 2,
                ("d"): 3,
                ("e"): 4,
                ("f"): 5,
                ("g"): 6,
                ("h"): 7,
            }
            instructions = []
            if str(turn_input[0]).upper() == "P":
                instructions.append("place")
            elif str(turn_input[0]).upper() == "M":
                instructions.append("move")
            else:
                raise InputError("Incorrect input - action type.")
            # parse placing
            if instructions[0] == "place":
                # parse placement
                coordinates = list(turn_input[1])
                x = x_coord[coordinates[0].lower()]
                y = self.board.size - int(coordinates[1])
                if isinstance(self.board.get_tile((x, y)), Tile):
                    instructions.append((x, y))
                else:
                    raise PlaceInputError("Incorrect input - not a valid tile.")
                # parse piece type
                if str(turn_input[2]).upper() == "F":
                    instructions.append(PieceType.FlatStone)
                elif str(turn_input[2]).upper() == "S":
                    instructions.append(PieceType.StandingStone)
                elif str(turn_input[2]).upper() == "C":
                    instructions.append(PieceType.Capstone)
                else:
                    raise RulesError("Incorrect input - not a valid piece type.")
            # parse moving
            if instructions[0] == "move":
                # parse org placement
                coordinates = list(turn_input[1])
                x = x_coord[coordinates[0]]
                y = self.board.size - int(coordinates[1])
                if self.board.get_tile((x, y)) is not None:
                    instructions.append((x, y))
                else:
                    raise MoveInputError("Incorrect input - not a valid tile.")

                # parse new placement
                coordinates = list(turn_input[2])
                x = x_coord[coordinates[0]]
                y = self.board.size - int(coordinates[1])
                if self.board.get_tile((x, y)) is not None:
                    instructions.append((x, y))
                else:
                    raise MoveInputError("Incorrect input - not a valid tile.")

                # parse moved amount
                if len(turn_input) < 4 and instructions[0] == "move":
                    instructions.append(1)
                elif int(turn_input[3]) in range(self.board.size):
                    instructions.append(int(turn_input[3]))
                else:
                    raise PlaceInputError("Incorrect input - improper amount.")
        except:  # noqa: E722
            return None
        return instructions


def start_menu() -> None:
    while True:
        size = input("Choose board size (4 - 8): ")
        try:
            if len(size) == 1 and size.isdigit():
                size = int(size)
                if size in range(4, 9):
                    break
            raise ValueError("Not a valid board size.")  # noqa: TRY301
        except ValueError:
                print("Not a valid board size.")
    while True:
        komi = input("Choose komi: ")
        try:
            if not float(komi) and float(komi) != 0:
                raise ValueError("Komi should be noted in multiples of 0.5")  # noqa: TRY301
            komi = float(komi)
            if komi % 0.5 != 0:
                raise ValueError("Komi should be noted in multiples of 0.5")  # noqa: TRY301
            break
        except ValueError:
            print("Komi should be noted in multiples of 0.5")
    cur_game = Game(size, komi)
    print(cur_game.board)
    cur_game.running_game()


if __name__ == "__main__":
    print("""
        Welcome to Tak, an abstract tactical board game.
        When prompted, enter your move in the format of:
        Placing a piece: ["p" xy ("F" for FlatStone, "S" for StandingStone, "C" for Capstone)]
        Moving a piece: ["m" (org xy) (new xy) (amount- blank counts 1)]
        Enjoy the game.\n
        """)  # noqa: E501
    start_menu()

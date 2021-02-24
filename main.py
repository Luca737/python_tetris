import itertools
from collections import namedtuple
from math import sqrt
from random import shuffle
from collections import deque

import pygame as pg

Block = namedtuple("Block", "row col")
Offset = namedtuple("Offset", "row col rot")
Size = namedtuple("Size", "width height")

# --- Settings ---

settings = {
    "height": 22,
    "width": 10,
    "fps": 30,
    "key_repeat_interval": 90,
    "auto_down_interval": 500,
    "block_size": 30,
    "boundary": 30,
    "number_of_next_tetraminos": 6,  # Minimum 0, maximum 6
}

grid_color = (100, 100, 100)
background_color = (200, 200, 200)
tetramino_colores = [(0, 255, 255), (128, 0, 128), (0, 128, 0), (255, 0, 0),
                     (255, 165, 0), (0, 0, 255), (255, 255, 0)]


# --- Tetraminos ---

I = [

    [0, 0, 0, 0,
     1, 1, 1, 1,
     0, 0, 0, 0,
     0, 0, 0, 0],

    [0, 0, 1, 0,
     0, 0, 1, 0,
     0, 0, 1, 0,
     0, 0, 1, 0],

    [0, 0, 0, 0,
     0, 0, 0, 0,
     1, 1, 1, 1,
     0, 0, 0, 0],

    [0, 1, 0, 0,
     0, 1, 0, 0,
     0, 1, 0, 0,
     0, 1, 0, 0],

]

T = [

    [0, 1, 0,
     1, 1, 1,
     0, 0, 0],

    [0, 1, 0,
     0, 1, 1,
     0, 1, 0],

    [0, 0, 0,
     1, 1, 1,
     0, 1, 0],

    [0, 1, 0,
     1, 1, 0,
     0, 1, 0],

]

S = [

    [1, 1, 0,
     0, 1, 1,
     0, 0, 0],

    [0, 0, 1,
     0, 1, 1,
     0, 1, 0],

    [0, 0, 0,
     1, 1, 0,
     0, 1, 1],

    [0, 1, 0,
     1, 1, 0,
     1, 0, 0],

]

Z = [

    [0, 1, 1,
     1, 1, 0,
     0, 0, 0],

    [0, 1, 0,
     0, 1, 1,
     0, 0, 1],

    [0, 0, 0,
     0, 1, 1,
     1, 1, 0],

    [1, 0, 0,
     1, 1, 0,
     0, 1, 0],

]

L = [

    [0, 0, 1,
     1, 1, 1,
     0, 0, 0],

    [0, 1, 0,
     0, 1, 0,
     0, 1, 1],

    [0, 0, 0,
     1, 1, 1,
     1, 0, 0],

    [1, 1, 0,
     0, 1, 0,
     0, 1, 0],

]

J = [

    [1, 0, 0,
     1, 1, 1,
     0, 0, 0],

    [0, 1, 1,
     0, 1, 0,
     0, 1, 0],

    [0, 0, 0,
     1, 1, 1,
     0, 0, 1],

    [0, 1, 0,
     0, 1, 0,
     1, 1, 0],

]

O = [

    [1, 1,
     1, 1],

]

TETRAMINOS = [I, T, S, Z, L, J, O]
tetraminos_size = []

# Converting all Tetraminos into relative coordinates.
for piece, tetra in enumerate(TETRAMINOS):

    # Check if the tetramino is in a valid 'sqare' List.
    dim = sqrt(len(tetra[0]))
    if not dim.is_integer():
        print("Tetramino must be defined in a sqare List.")
        exit(1)
    dim = int(dim)
    tetraminos_size.append(dim)

    # Generate relative tetramino blocks.
    for r_index, rotation in enumerate(tetra):
        blocks = []
        for i, block in enumerate(rotation):
            if block == 1:
                blocks.append(Block(i // dim, i % dim))

        TETRAMINOS[piece][r_index] = blocks


class Tetramino():

    def __init__(self, piece_type, rotation, row, col):

        self.type = piece_type
        self.rotation = rotation
        self.row = row
        self.col = col
        self._col = col  # Backup for reset.

    def reset(self):
        self.rotation = 0
        self.row = 0
        self.col = self._col

    def rotate(self, amount):
        self.rotation = self.new_rotation_state(amount)

    def get_rotated(self, relative_rotation):
        for block in TETRAMINOS[self.type][self.new_rotation_state(relative_rotation)]:
            yield Block(self.row + block.row, self.col + block.col)

    def new_rotation_state(self, amount):
        return (self.rotation + amount) % len(TETRAMINOS[self.type])

    def __iter__(self):
        for block in TETRAMINOS[self.type][self.rotation]:
            yield Block(self.row + block.row, self.col + block.col)

    def __str__(self):
        return str(self.type)


class Bag():

    def __init__(self, width):
        self.width = width
        self.number_of_tetraminos = len(TETRAMINOS)
        self.refresh_bag()

    def next_tetramino(self):

        if len(self.bag) == 0:
            self.refresh_bag()

        t_type = self.bag.pop()
        rotation = 0
        row = 0
        col = int((self.width - tetraminos_size[t_type]) / 2)

        return Tetramino(t_type, rotation, row, col)

    def refresh_bag(self):
        self.bag = list(range(self.number_of_tetraminos))
        shuffle(self.bag)


class Board():
    """Stores the locked blocks"""

    def __init__(self, size):
        self.width, self.height = size
        self.clear_board()

    def clear_board(self):
        self.board = [[0 for i in range(self.width)]
                      for j in range(self.height)]

    def has_collision(self, tetramino, offset):
        for block in tetramino.get_rotated(offset.rot):
            row, col = block.row + offset.row, block.col + offset.col
            if not (0 <= row < self.height
                    and 0 <= col < self.width
                    and self.board[row][col] == 0):
                return True
        return False

    def lock_tetramino_and_clear_full_lines(self, tetramino):
        rows_to_check = set()
        for block in tetramino:
            rows_to_check.add(block.row)
            self.board[block.row][block.col] = tetramino.type + 1

        # Check if lines are full.
        rows_to_remove = []
        for row in rows_to_check:
            if all(self.board[row][col] for col in range(self.width)):
                rows_to_remove.append(row)

        if len(rows_to_remove) == 0:
            return 0

        # Remove lines if any.
        # The rows are sorted in ascending order.
        # But we want to delete the later rows so reverse it.
        rows_to_remove.sort(reverse=True)
        for row in rows_to_remove:
            del self.board[row]

        # Add empty line back to the begining of the array.
        number_of_line_cleared = len(rows_to_remove)
        self.board = [[0 for i in range(self.width)]
                      for j in range(number_of_line_cleared)] + self.board

        return number_of_line_cleared

    def __iter__(self):
        return itertools.product(range(self.height), range(self.width))


class Game():
    def __init__(self, size):
        pg.init()
        self.size = size
        self.score = 0
        self.lines_cleared = 0
        self.tetrises = 0
        self.bag = Bag(size.width)
        self.current_tetramino = self.bag.next_tetramino()
        self.next_tetraminos = deque(
            [self.bag.next_tetramino() for i in range(settings["number_of_next_tetraminos"])])
        self.held_tetramino = None
        # True if the current Tetramino was in hold.
        self.held_current = False
        self.renderer = Render(settings["block_size"], size)
        self.board = Board(size)
        self.player_is_dead = False
        self.down_pressed = False

        # Keep track which key was last pressed.
        self.move_left = False
        # Number indicating how many left and right keys are pressed.
        self.lr_keys_pressed = 0
        self.lr_time_passed = 0

        # Interval in millis.
        self.key_repeat_interval = settings["key_repeat_interval"]

        # Auto down movement interval.
        self.auto_down_movement_interval = settings["auto_down_interval"]
        self.down_time_passed = 0

    def reset(self):
        self.board.clear_board()
        self.bag.refresh_bag()
        self.player_is_dead = False
        self.score = 0
        self.lines_cleared = 0
        self.tetrises = 0
        self.lr_time_passed = 0
        self.down_time_passed = 0
        self.held_current = False
        self.held_tetramino = None

    def swap_held(self):
        if not self.held_current:
            self.held_current = True
            if self.held_tetramino is not None and not self.board.has_collision(self.held_tetramino, Offset(0, 0, 0)):
                self.current_tetramino.reset()
                self.current_tetramino, self.held_tetramino = self.held_tetramino, self.current_tetramino
            else:
                self.current_tetramino.reset()
                self.held_tetramino = self.current_tetramino
                self.set_next_tetramino()

    def drop_tetramino(self):
        while not self.board.has_collision(self.current_tetramino, Offset(1, 0, 0)):
            self.current_tetramino.row += 1
        self.lock_tetramino_and_get_next()

    def set_next_tetramino(self):
        self.next_tetraminos.append(self.bag.next_tetramino())
        self.current_tetramino = self.next_tetraminos.popleft()

    def lock_tetramino_and_get_next(self):
        lines = self.board.lock_tetramino_and_clear_full_lines(
            self.current_tetramino)
        self.lines_cleared += lines
        if lines == 4:
            self.tetrises += 1

        self.set_next_tetramino()
        self.held_current = False

        self.lr_time_passed = 0
        self.down_time_passed = 0

        # Player has Lost if there is a collision at the start.
        if self.board.has_collision(self.current_tetramino, Offset(0, 0, 0)):
            self.player_is_dead = True
            self.reset()

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.request_movement("Down")
                    self.down_time_passed = 0
                    self.down_pressed = True

                elif event.key == pg.K_a:
                    self.move_left = True
                    self.lr_keys_pressed += 1
                    self.request_movement("Left")
                    self.lr_time_passed = 0

                elif event.key == pg.K_d:
                    self.move_left = False
                    self.lr_keys_pressed += 1
                    self.request_movement("Right")
                    self.lr_time_passed = 0

                elif event.key == pg.K_w or event.key == pg.K_RIGHT:
                    self.request_movement("TurnR")

                elif event.key == pg.K_LEFT:
                    self.request_movement("TurnL")

                elif event.key == pg.K_DOWN:
                    self.swap_held()

                elif event.key == pg.K_SPACE:
                    self.drop_tetramino()

            elif event.type == pg.KEYUP:
                if event.key == pg.K_s:
                    self.down_pressed = False

                elif event.key == pg.K_a:
                    self.move_left = False
                    self.lr_keys_pressed -= 1

                elif event.key == pg.K_d:
                    self.move_left = True
                    self.lr_keys_pressed -= 1

    def request_movement(self, direction):
        if direction == "Down":
            if self.board.has_collision(self.current_tetramino, Offset(1, 0, 0)):
                self.lock_tetramino_and_get_next()
            else:
                self.current_tetramino.row += 1

        elif direction == "Right":
            if not self.board.has_collision(self.current_tetramino, Offset(0, 1, 0)):
                self.current_tetramino.col += 1

        elif direction == "Left":
            if not self.board.has_collision(self.current_tetramino, Offset(0, -1, 0)):
                self.current_tetramino.col -= 1

        elif direction == "TurnR":
            if not self.board.has_collision(self.current_tetramino, Offset(0, 0, 1)):
                self.current_tetramino.rotate(1)

        elif direction == "TurnL":
            if not self.board.has_collision(self.current_tetramino, Offset(0, 0, -1)):
                self.current_tetramino.rotate(-1)

    def check_timers(self, time_passed):
        if self.lr_keys_pressed:
            self.lr_time_passed += time_passed
            if self.lr_time_passed >= self.key_repeat_interval:
                movement = "Left" if self.move_left else "Right"
                self.request_movement(movement)
                self.lr_time_passed %= self.key_repeat_interval

        self.down_time_passed += time_passed
        interval = self.key_repeat_interval if self.down_pressed else self.auto_down_movement_interval
        if self.down_time_passed >= interval:
            self.request_movement("Down")
            self.down_time_passed %= interval

    def update(self, time_passed):
        self.check_events()
        self.check_timers(time_passed)

        with self.renderer:
            self.renderer.render_board(self.board)
            self.renderer.render_tetramino(self.current_tetramino)
            self.renderer.render_next_tetraminos(self.next_tetraminos)
            self.renderer.render_grid()
            if self.held_tetramino is not None:
                self.renderer.render_held_tetramino(self.held_tetramino)

    def start(self):
        # Enableing only those inputs that are required
        pg.event.set_allowed(None)
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN,
                              pg.KEYUP, pg.USEREVENT])
        clock = pg.time.Clock()
        fps = settings["fps"]
        while True:
            time_passed = clock.tick(fps)
            self.update(time_passed)


class Render():
    def __init__(self, block_size, board_size):
        self.block_size = block_size  # Single value since it's a square
        self.board_size = board_size
        self.boundary = settings["boundary"]
        self.tetramino_scale = 0.5  # Size proportional to block_size
        self.fsb = 5 * self.tetramino_scale  # Five scaled blocks size
        self.board_pixel_size = Size(
            block_size * board_size.width,
            block_size * board_size.height
        )
        self.window_size = (
            round(self.board_pixel_size.width + self.fsb * self.block_size +
                  (2 + self.fsb) * block_size + 2 * self.boundary),
            round(self.board_pixel_size.height + 2 * self.boundary)
        )
        self.screen = pg.display.set_mode(self.window_size)
        self.board_surface = pg.Surface(
            (self.board_pixel_size.width, self.board_pixel_size.height)
        )
        self.next_tetramino_surface = pg.Surface(
            (self.fsb * block_size,
             4 * self.tetramino_scale * block_size * settings["number_of_next_tetraminos"])
        )
        self.held_tetramino_surface = pg.Surface((
            round(self.fsb * block_size),
            round(self.fsb * block_size)
        ))

    def render_board(self, board):
        for row, col in board:
            color = board.board[row][col]
            if color:
                x = col * self.block_size
                y = row * self.block_size
                pg.draw.rect(self.board_surface, tetramino_colores[color - 1],
                             pg.Rect(x, y, self.block_size, self.block_size))

    def render_grid(self):
        end_y = self.board_size.height * self.block_size
        for i in range(self.board_size.width + 1):
            x = i * self.block_size
            pg.draw.line(self.board_surface, grid_color, (x, 0), (x, end_y))

        end_x = self.board_size.width * self.block_size
        for i in range(self.board_size.height + 1):
            y = i * self.block_size
            pg.draw.line(self.board_surface, grid_color, (0, y), (end_x, y))

    def render_tetramino(self, tetramino):
        for row, col in tetramino:
            x = col * self.block_size
            y = row * self.block_size
            pg.draw.rect(self.board_surface, tetramino_colores[tetramino.type],
                         pg.Rect(x, y, self.block_size, self.block_size))

    def render_next_tetraminos(self, tetraminos):
        for i, tetramino in enumerate(tetraminos):
            x_cord = 0.5 * self.tetramino_scale * self.block_size
            y_cord = x_cord + i * 4 * self.tetramino_scale * self.block_size
            for row, col in TETRAMINOS[tetramino.type][0]:
                x = col * self.block_size * self.tetramino_scale + x_cord
                y = row * self.block_size * self.tetramino_scale + y_cord
                pg.draw.rect(self.next_tetramino_surface, tetramino_colores[tetramino.type],
                             pg.Rect(x, y, self.block_size * self.tetramino_scale,
                                     self.block_size * self.tetramino_scale))

    def render_held_tetramino(self, tetramino):
        offset = 0.5 * self.tetramino_scale * self.block_size
        for row, col in TETRAMINOS[tetramino.type][0]:
            x = col * self.block_size * self.tetramino_scale + offset
            y = row * self.block_size * self.tetramino_scale + offset
            pg.draw.rect(self.held_tetramino_surface, tetramino_colores[tetramino.type],
                         pg.Rect(x, y, self.block_size * self.tetramino_scale,
                                 self.block_size * self.tetramino_scale))

    def __enter__(self):
        self.screen.fill((20, 20, 20))
        self.board_surface.fill(background_color)
        self.next_tetramino_surface.fill(background_color)
        self.held_tetramino_surface.fill(background_color)

    def __exit__(self, what, are, these):
        self.screen.blit(self.board_surface,
                         (self.boundary + 1 + self.fsb * self.block_size + self.block_size, self.boundary + 1))
        self.screen.blit(self.next_tetramino_surface,
                         (self.boundary + 1 + self.board_pixel_size.width + self.fsb * self.block_size + 2 * self.block_size,
                          self.boundary + 1))
        self.screen.blit(self.held_tetramino_surface,
                         (self.boundary + 1, self.boundary + 1))
        pg.display.update()


if __name__ == "__main__":
    game = Game(Size(settings["width"], settings["height"]))
    game.start()

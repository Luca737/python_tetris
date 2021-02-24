import itertools
from collections import namedtuple
from math import sqrt
from random import shuffle
from collections import deque

import pygame as pg

Block = namedtuple("Block", "row col")
Offset = namedtuple("Offset", "row col rot")
Size = namedtuple("Size", "width height")

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

tetraminos = [I, T, S, Z, L, J, O]
tetramino_colores = [(0, 255, 255), (128, 0, 128), (0, 128, 0), (255, 0, 0),
                     (255, 165, 0), (0, 0, 255), (255, 255, 0)]
background_color = (200, 200, 200)

tetraminos_size = []

# Converting all Tetraminos into relative coordinates.
for piece, tetra in enumerate(tetraminos):

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

        tetraminos[piece][r_index] = blocks


class Tetramino():

    def __init__(self, piece_type, rotation, row, col):

        self.type = piece_type
        self.rotation = rotation
        self.row = row
        self.col = col

    def rotate(self, amount):
        self.rotation = self.new_rotation_state(amount)

    def get_rotated(self, relative_rotation):
        for block in tetraminos[self.type][self.new_rotation_state(relative_rotation)]:
            yield Block(self.row + block.row, self.col + block.col)

    def new_rotation_state(self, amount):
        return (self.rotation + amount) % len(tetraminos[self.type])

    def __iter__(self):
        for block in tetraminos[self.type][self.rotation]:
            yield Block(self.row + block.row, self.col + block.col)

    def __str__(self):
        return str(self.type)


class Bag():

    def __init__(self, width):
        self.width = width
        self.number_of_tetraminos = len(tetraminos)
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
            [self.bag.next_tetramino() for i in range(6)])
        self.renderer = Render(30, size)
        self.board = Board(size)
        self.player_is_dead = False

        # Keep track which key was last pressed.
        self.move_left = False
        # Number indicating how many left and right keys are pressed.
        self.lr_keys_pressed = 0

        # Interval in millis.
        self.key_repeat_interval = 80

        # Auto down movement interval.
        self.auto_down_movement_interval = 500

        pg.time.set_timer(pg.USEREVENT+1, self.auto_down_movement_interval)

    def reset(self):
        self.board.clear_board()
        self.bag.refresh_bag()
        self.player_is_dead = False
        self.score = 0
        self.lines_cleared = 0
        self.tetrises = 0

    def drop_tetramino(self):
        while not self.board.has_collision(self.current_tetramino, Offset(1, 0, 0)):
            self.current_tetramino.row += 1
        self.lock_tetramino_and_get_next()

    def lock_tetramino_and_get_next(self):
        lines = self.board.lock_tetramino_and_clear_full_lines(
            self.current_tetramino)
        self.lines_cleared += lines
        if lines == 4:
            self.tetrises += 1

        self.current_tetramino = self.next_tetraminos.popleft()
        self.next_tetraminos.append(self.bag.next_tetramino())

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
                    print("hi0")
                    self.request_movement("Down")
                    pg.time.set_timer(pg.USEREVENT+1, 0)
                    pg.time.set_timer(pg.USEREVENT+1, self.key_repeat_interval)

                elif event.key == pg.K_a:
                    self.move_left = True
                    self.lr_keys_pressed += 1
                    self.request_movement("Left")
                    pg.time.set_timer(pg.USEREVENT+2, self.key_repeat_interval)

                elif event.key == pg.K_d:
                    self.move_left = False
                    self.lr_keys_pressed += 1
                    self.request_movement("Right")
                    pg.time.set_timer(pg.USEREVENT+2, self.key_repeat_interval)

                elif event.key == pg.K_w or event.key == pg.K_RIGHT:
                    self.request_movement("TurnR")

                elif event.key == pg.K_LEFT:
                    self.request_movement("TurnL")

                elif event.key == pg.K_SPACE:
                    self.drop_tetramino()

            elif event.type == pg.KEYUP:
                if event.key == pg.K_s:
                    print("hi1")
                    pg.time.set_timer(pg.USEREVENT+1, 0)
                    pg.time.set_timer(
                        pg.USEREVENT+1, self.auto_down_movement_interval)

                elif event.key == pg.K_a:
                    self.move_left = False
                    self.lr_keys_pressed -= 1
                    if self.lr_keys_pressed == 0:
                        pg.time.set_timer(pg.USEREVENT+2, 0)

                elif event.key == pg.K_d:
                    self.move_left = True
                    self.lr_keys_pressed -= 1
                    if self.lr_keys_pressed == 0:
                        pg.time.set_timer(pg.USEREVENT+2, 0)

            # Repeated down movement.
            elif event.type == pg.USEREVENT+1:
                self.request_movement("Down")

            # Repeated left / right movement.
            elif event.type == pg.USEREVENT+2:
                if self.move_left:
                    self.request_movement("Left")
                else:
                    self.request_movement("Right")

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

    def update(self):
        with self.renderer:
            self.renderer.render_board(self.board)
            self.renderer.render_tetramino(self.current_tetramino)
            self.renderer.render_grid()

        self.check_events()

    def start(self):
        # Enableing only those inputs that are required
        pg.event.set_allowed(None)
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN,
                              pg.KEYUP, pg.USEREVENT])
        clock = pg.time.Clock()
        while True:
            clock.tick(30)
            self.update()


class Render():
    def __init__(self, block_size, board_size):
        self.block_size = block_size  # Single value since it's a square
        self.board_size = board_size
        self.boundary = 30
        self.board_pixel_size = Size(block_size * board_size.width,
                                     block_size * board_size.height)
        self.window_size = (2 * self.board_pixel_size.width + 2 * self.boundary,
                            self.board_pixel_size.height + 2 * self.boundary)
        self.board_rect = pg.Rect(self.boundary + 1, self.boundary + 1,
                                  self.board_pixel_size.width, self.board_pixel_size.height)

        pg.display.set_mode(self.window_size)
        self.surface = pg.display.get_surface()

    def render_board(self, board):
        pg.draw.rect(self.surface, background_color, self.board_rect)
        for row, col in board:
            color = board.board[row][col]
            if color:
                x = col * self.block_size + self.boundary + 1
                y = row * self.block_size + self.boundary + 1
                pg.draw.rect(self.surface, tetramino_colores[color - 1],
                             pg.Rect(x, y, self.block_size, self.block_size))

    def render_grid(self):
        start_y = self.boundary + 1
        end_y = self.board_size.height * self.block_size + self.boundary + 1
        for i in range(self.board_size.width + 1):
            x = i * self.block_size + self.boundary + 1
            pg.draw.line(self.surface, grid_color, (x, start_y), (x, end_y))
        start_x = start_y
        end_x = self.board_size.width * self.block_size + self.boundary + 1
        for i in range(self.board_size.height + 1):
            y = i * self.block_size + self.boundary + 1
            pg.draw.line(self.surface, grid_color, (start_x, y), (end_x, y))

    def render_tetramino(self, tetramino):
        for row, col in tetramino:
            x = col * self.block_size + self.boundary + 1
            y = row * self.block_size + self.boundary + 1
            pg.draw.rect(self.surface, tetramino_colores[tetramino.type],
                         pg.Rect(x, y, self.block_size, self.block_size))

    def render_next_tetraminos(self, tetraminos):
        pass

    def __enter__(self):
        self.surface.fill((20, 20, 20))

    def __exit__(self, what, are, these):
        pg.display.update()


if __name__ == "__main__":
    grid_color = (100, 100, 100)
    game = Game(Size(10, 22))
    game.start()
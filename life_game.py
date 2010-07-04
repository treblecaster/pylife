#!/opt/local/bin/python2.4

"""
Small driver program to simulate a game of Conway's life.
"""

import sys
import time
import Numeric

graphics_lib = None

try:
    import pygame
except ImportError:
    pass
else:
    from pygame.locals import QUIT
    graphics_lib = 'pygame'

if not graphics_lib:
    try:
    	import curses
	import traceback
    except ImportError:
    	pass
    else:
    	graphics_lib = 'curses'


if not graphics_lib:
    print "Could not find an appropriate graphics library"
    raise ImportError


class Cell(object):
    """Individual cell"""

    def __init__(self):
        self.alive_curr_gen = False
        self.alive_next_gen = False
        self.generation_cnt = 0


class GameTable(object):
    """Game of life table"""

    def __init__(self, seed_file=None):
        self.screen = None
        self.scale_screen = None
        self.cells = []

        self._init_graphics()

        # 2-D array that cooresponds to pixels on surface
        self.px_arr = Numeric.zeros((self.xscale, self.yscale), 'i')

        # Create 2-D list of cells to coorespond to pixel array
        for xx in range(self.xscale):
            self.cells.append([])
            for yy in range(self.yscale):
                self.cells[xx].append(Cell())

        self._init_configuration(seed_file)
        self._center_on_alive_cells()
        self._prepare_generation()
        self.advance_generation()
        self._drawfield()

    def _init_pygame_graphics(self):
    	width = 640
	height = 480
	scale = 4
        self.xscale = width / scale
        self.yscale = height / scale
	
        pygame.init()
        self.screen = pygame.display.set_mode((width, height), 0, 8)
        self.scale_screen = pygame.surface.Surface((self.xscale, self.yscale),
                                                    0, 8)
        white = (255, 255, 255)
        black = (0, 0, 0)
        red = (255, 0, 0)
        green = (0, 255, 0)
        blue = (0, 0, 255)

        self.screen.fill(black)
        self.scale_screen.fill(black)
        self.screen.set_palette([black, red, green, blue, white])
        self.scale_screen.set_palette([black, red, green, blue, white])

    def _init_curses_graphics(self):
        self.screen = curses.initscr()
        curses.curs_set(0)
    	self.yscale, self.xscale = self.screen.getmaxyx()
	
	# This is necessary, maybe due to return character?
	self.xscale = self.xscale - 1

    def _init_graphics(self):
        """Setup graphics (game board), etc."""
    	if graphics_lib == 'pygame':
	    self._init_pygame_graphics()
	elif graphics_lib == 'curses':
	    self._init_curses_graphics()

    def _init_configuration(self, seed_file):
        """Setup initial alive cells"""

        if seed_file == None:
            return self._default_configuration()

        return self._parse_configuration_file(seed_file)

    def _default_configuration(self):
        """Setup hard-coded default alive cells"""
        for ii in range(20):
            self.cells[ii][50].alive_curr_gen = True

    def _parse_configuration_file(self, seed_file):
        """Parse given configuration file for starting generation"""
        try:
            file_obj = open(seed_file, 'r')
        except IOError:
            print "Unable to open file '%s', defaulting seed " % (seed_file)
            return self._default_configuration()

        xx = 0
        yy = 0

        for line in file_obj:
            # Signals 'comment' line to be skipped
            if line[0] != "!":
                if yy > self.yscale:
                    raise IOError("File height (%d) too large for game " \
                                    "table height (%d)" % (yy, self.yscale))
                for char in line:
                    if xx > self.xscale:
                        raise IOError("File width (%d) too wide for game" \
                                        "table width (%d)" % (xx, self.xscale))
                    if char == "O":
                        self.cells[xx][yy].alive_curr_gen = True
                    xx = xx + 1
                xx = 0
                yy = yy + 1

    def _pygame_drawfield(self):
        pygame.surfarray.blit_array(self.scale_screen, self.px_arr)
        temp = pygame.transform.scale(self.scale_screen,
                                        self.screen.get_size())
        self.screen.blit(temp, (0, 0))
        pygame.display.update()

    def _curses_drawfield(self):
        self.screen.erase()
        for yy in range(self.yscale):
            for xx in range(self.xscale):
                color = self.px_arr[xx][yy]
                if (color >= 4):
                    self.screen.addstr(yy, xx, "o", curses.A_DIM)
                elif (color == 3):
                    self.screen.addstr(yy, xx, "o")
                elif (color == 2):
                    self.screen.addstr(yy, xx, "o", curses.A_BOLD)
                elif (color == 1):
                    self.screen.addstr(yy, xx, "o", curses.A_BOLD)
                else:
                    self.screen.addstr(yy, xx, " ")
        self.screen.refresh()

    def _drawfield(self):
        """Draw board"""
    	if graphics_lib == 'pygame':
	    self._pygame_drawfield()
	elif graphics_lib == 'curses':
	    self._curses_drawfield()

    def _prepare_generation(self):
        """Apply rules of life to each cell"""
        for xx in range(self.xscale):
            for yy in range(self.yscale):
                cnt = self._count_neighbors(xx, yy)
                if self.cells[xx][yy].alive_curr_gen:
                    if cnt < 2 or cnt > 3:
                        self.cells[xx][yy].alive_next_gen = False
                    else:
                        self.cells[xx][yy].alive_next_gen = True
                else:
                    if cnt == 3:
                        self.cells[xx][yy].alive_next_gen = True

                if self.cells[xx][yy].alive_next_gen:
                    self.cells[xx][yy].generation_cnt += 1
                else:
                    self.cells[xx][yy].generation_cnt = 0

    def _count_neighbors(self, xx, yy):
        """Count neighbors for given cell"""

        neighbors = 0
        left = xx - 1
        right = xx + 1
        up = yy - 1
        down = yy + 1

        # Check horizontal neighbors
        if left >= 0 and self.cells[left][yy].alive_curr_gen:
            neighbors += 1
        if right < self.xscale and self.cells[right][yy].alive_curr_gen:
            neighbors += 1

        # Check vertial neighbors
        if up >= 0 and self.cells[xx][up].alive_curr_gen:
            neighbors += 1
        if down < self.yscale and self.cells[xx][down].alive_curr_gen:
            neighbors += 1

        # Check top diagonal neighbors
        if left >= 0 and up >= 0 and self.cells[left][up].alive_curr_gen:
            neighbors += 1
        if right < self.xscale and up >= 0 and \
                self.cells[right][up].alive_curr_gen:
            neighbors += 1

        # Check bottom diagonal neighbors
        if left >= 0 and down < self.yscale and \
                self.cells[left][down].alive_curr_gen:
            neighbors += 1
        if right < self.xscale and down < self.yscale and \
                self.cells[right][down].alive_curr_gen:
            neighbors += 1

        return neighbors

    def advance_generation(self):
        """Advance all cells by 1 generation"""
        self._prepare_generation()

        for xx in range(self.xscale):
            for yy in range(self.yscale):
                self.cells[xx][yy].alive_curr_gen = \
                    self.cells[xx][yy].alive_next_gen

                color = 0
                if self.cells[xx][yy].generation_cnt > 0:
                    if self.cells[xx][yy].generation_cnt >= 4:
                        color = 4
                    else:
                        color = self.cells[xx][yy].generation_cnt

                self.px_arr[xx][yy] = color

        self._drawfield()

    def _center_on_alive_cells(self):
        """Center the table on the alive cells"""

        # Initialize min and max to opposite extremes
        x_min = self.xscale
        x_max = 0
        y_min = self.yscale
        y_max = 0

        # Find the bounds of the alive cells
        for xx in range(self.xscale):
            for yy in range(self.yscale):
                if self.cells[xx][yy].alive_curr_gen:
                    if yy > y_max:
                        y_max = yy
                    if yy < y_min:
                        y_min = yy
                    if xx > x_max:
                        x_max = xx
                    if xx < x_min:
                        x_min = xx

        # Shift right
        while self.xscale - x_max > x_min + 1:
            x_max = x_max + 1
            x_min = x_min + 1
            self.cells.insert(0, self.cells.pop())
        else:
            # Shift left
            while x_min > self.xscale - x_max + 1:
                x_min = x_min - 1
                x_max = x_max - 1
                self.cells.append(self.cells.pop(0))

        # Shift up
        while self.yscale - y_max > y_min + 1:
            y_max = y_max + 1
            y_min = y_min + 1
            for xx in range(self.xscale):
                self.cells[xx].insert(0, self.cells[xx].pop())
        else:
            # Shift down
            while y_min > self.yscale - y_max + 1:
                y_max = y_max - 1
                y_min = y_min - 1
                for xx in range(self.xscale):
                    self.cells[xx].append(self.cells[xx].pop(0))


def setup(filename):
    """Setup table to simulate game"""
    return GameTable(filename)


def run(table):
    """Run through game of life simulation"""
    while True:
        # FIXME: Catch keyboard
        time.sleep(1)

    	if graphics_lib == 'pygame':
            for event in pygame.event.get():
            	if event.type == QUIT:
                    return

        table.advance_generation()

def teardown():
    """Stop simulating game and cleanup graphics"""
    if graphics_lib == 'pygame':
    	pygame.display.quit()
    	pygame.quit()
    elif graphics_lib == 'curses':
    	curses.nocbreak()
    	curses.echo()
    	curses.endwin()


def main():
    """Main entry point for driver program"""
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    table = setup(filename)
    run(table)
    teardown()

if __name__ == "__main__":
    try:
	main()
    except:
    	teardown()
    	if graphics_lib == 'curses':
	    # print error message re exception
	    traceback.print_exc()


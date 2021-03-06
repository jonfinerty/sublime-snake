#
#  Created by jon finerty - 2013
#

import sublime
import sublime_plugin

# GLOBAL SETTINGS
SNAKE_ON = False
SNAKE_DIRECTION = 'right'
SNAKE_INTENDED_DIRECTION = 'right'
SNAKE_SCORE = 0
SNAKE_STARTING_LENGTH = 10
SNAKE_STARTING_SPEED = 80
SNAKE_SPEED_INCREASE_RATE = 0.98
SNAKE_GROWTH_RATE = 2  # for every X characters the snake will grow 1 segment
SNAKE_GROWTH_PROGRESS = 0
SNAKE_X_BOUNDARY = 0
SNAKE_Y_BOUNDARY = 0

# AMAZING SNAKE GRAPHICS
SNAKE_HEAD = u"\u25CF"
SNAKE_VERTICAL_SEGMENT = u"\u2588"
SNAKE_HORIZONTAL_SEGMENT = u"\u25A0"
SNAKE_TAIL_LEFT = u"\u25BA"
SNAKE_TAIL_RIGHT = u"\u25C4"
SNAKE_TAIL_UP = u"\u25BC"
SNAKE_TAIL_DOWN = u"\u25B2"


# Fancy new movement key event listener
class snakeEventListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        global SNAKE_ON
        if key == "snake_running":
            if SNAKE_ON:
                return True
        return False


# commands for registering turn intentions
class set_snake_rightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION
        if SNAKE_DIRECTION != 'left':
            SNAKE_INTENDED_DIRECTION = 'right'


class set_snake_leftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION
        if SNAKE_DIRECTION != 'right':
            SNAKE_INTENDED_DIRECTION = 'left'


class set_snake_upCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION
        if SNAKE_DIRECTION != 'down':
            SNAKE_INTENDED_DIRECTION = 'up'


class set_snake_downCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION
        if SNAKE_DIRECTION != 'up':
            SNAKE_INTENDED_DIRECTION = 'down'


class snake_start_gameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_ON, SNAKE_SCORE, SNAKE_X_BOUNDARY, SNAKE_Y_BOUNDARY
        global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION, SNAKE_GROWTH_PROGRESS

        # reset stuff
        SNAKE_SCORE = 0
        SNAKE_DIRECTION = "right"
        SNAKE_INTENDED_DIRECTION = "right"
        SNAKE_GROWTH_PROGRESS = 0

        if not SNAKE_ON:

            SNAKE_ON = True

            templateView = self.view
            window = templateView.window()

            # Set up copy of current window, so work is not lost.
            # grab current file info
            entireFileRegion = sublime.Region(0, templateView.size())
            fileText = templateView.substr(entireFileRegion)
            syntax = templateView.settings().get('syntax')
            pos = templateView.sel()
            tabSize = templateView.settings().get('tab_size')
            wrap_width = templateView.settings().get("wrap_width")
            word_wrap = templateView.settings().get("word_wrap")

            # copy across and set syntax
            snakeView = window.new_file()
            snakeView.set_scratch(True)
            snakeView.set_name("SNAKE")
            window.focus_view(snakeView)
            snakeView.insert(edit, 0, fileText + "\n")
            snakeView.set_syntax_file(syntax)

            # replace word wrap with newlines
            if word_wrap or word_wrap == "auto":
                if wrap_width == 0:
                    lineLength = snakeView.viewport_extent()[0]
                    wrap_width = int(lineLength / snakeView.em_width())
                entireSnakeViewRegion = sublime.Region(0, snakeView.size())
                lines = snakeView.split_by_newlines(entireSnakeViewRegion)
                adjustment = 0
                for line in lines:
                    position = wrap_width
                    while position < line.size():
                        snakeView.insert(edit, line.a + position - 1, "\n")
                        adjustment = adjustment + 1
                        position = position + wrap_width

            # replace tabs with spaces
            snakeStartingX, snakeStartingY = snakeView.rowcol(pos[0].a)
            # expand tabs tends to break stuff, check for tabs first?
            tabs = snakeView.find_all("\t")
            tabReplacement = " " * tabSize
            for tab in tabs:
                tabActualLocation = snakeView.find("\t", tab.a)
                snakeView.replace(edit, tabActualLocation, tabReplacement)

            # find longest line
            entireSnakeViewRegion = sublime.Region(0, snakeView.size())
            lines = snakeView.split_by_newlines(entireSnakeViewRegion)
            maxLineLength = 0
            for line in lines:
                if line.size() > maxLineLength:
                    maxLineLength = line.size()

            # add on necessary space to end of lines
            totalPaddingOffset = 0
            for line in lines:
                paddingSize = (maxLineLength - line.size()) + 1
                paddingString = (" " * (paddingSize - 1)) + "|"
                snakeView.insert(edit,
                                 line.b + totalPaddingOffset,
                                 paddingString)
                totalPaddingOffset = totalPaddingOffset + paddingSize

            # set word wrap to maximum line length, otherwise pain
            snakeView.settings().set("wrap_width", 0)
            snakeView.settings().set("word_wrap", False)

            # Add border to bottom of code so its more obvious
            SNAKE_Y_BOUNDARY = maxLineLength
            SNAKE_X_BOUNDARY = len(lines)
            bottomBorder = ("_" * maxLineLength) + "|\n"
            snakeView.insert(edit, snakeView.size(), bottomBorder)

            # Create default snake -
            # consists of a set of positions (stored as text_points)
            snakeStartingPoint = snakeView.text_point(snakeStartingX, 0)
            snakeEndingPoint = snakeStartingPoint + SNAKE_STARTING_LENGTH + 1
            snake = list(range(snakeStartingPoint, snakeEndingPoint))
            snakeHeadIndex = SNAKE_STARTING_LENGTH
            updateSpeed = SNAKE_STARTING_SPEED

            # draw initial snake
            drawSnakeTail(edit, snakeView, snake[0], snake[1])
            for segment in snake[1:-1]:
                editPosition(edit,
                             snakeView,
                             segment,
                             SNAKE_HORIZONTAL_SEGMENT)
            drawSnakeHead(edit, snakeView, snake[-1])
            snakeView.show_at_center(snakeStartingPoint)

            # start snake update timeout loop
            sublime.set_timeout(lambda: renderSnake(edit,
                                                    snakeView,
                                                    snake,
                                                    snakeHeadIndex,
                                                    updateSpeed), updateSpeed)
        else:
            SNAKE_ON = False


def renderSnake(edit, snakeView, snake, snakeHeadIndex, updateSpeed):
    global SNAKE_ON, SNAKE_SCORE, SNAKE_X_BOUNDARY, SNAKE_X_BOUNDARY
    global SNAKE_GROWTH_RATE, SNAKE_GROWTH_PROGRESS
    global SNAKE_DIRECTION, SNAKE_INTENDED_DIRECTION

    if SNAKE_ON:
        SNAKE_SCORE = SNAKE_SCORE + 1

        # Get position of cell to be eaten
        newPosX, newPosY = snakeView.rowcol(snake[snakeHeadIndex])
        if SNAKE_INTENDED_DIRECTION == "right":
            newPosY = newPosY + 1
        elif SNAKE_INTENDED_DIRECTION == "left":
            newPosY = newPosY - 1
        elif SNAKE_INTENDED_DIRECTION == "up":
            newPosX = newPosX - 1
        else:
            newPosX = newPosX + 1

        SNAKE_DIRECTION = SNAKE_INTENDED_DIRECTION

        newPoint = snakeView.text_point(newPosX, newPosY)

        snakeView.show_at_center(newPoint)
        eatenChar = snakeView.substr(newPoint)

        # draw new head
        drawSnakeHead(edit, snakeView, newPoint)

        # redraw over old head
        oldHeadPoint = snake[snakeHeadIndex]
        drawSnakeSegment(edit,
                         snakeView,
                         oldHeadPoint,
                         newPoint,
                         snake[snakeHeadIndex - 1])

        # DEATH CONDITIONS
        # check boundary lose conditions
        if (newPosX >= SNAKE_X_BOUNDARY or newPosY >= SNAKE_Y_BOUNDARY):
            gameOver()

        # see if lost by eating oneself
        for segment in snake:
            if newPoint == segment:
                gameOver()

        # see if eaten a wall
        if eatenChar == "\n":
            gameOver()

        if eatenChar != " " and SNAKE_GROWTH_PROGRESS == (SNAKE_GROWTH_RATE-1):
            # grow snake
            SNAKE_SCORE = SNAKE_SCORE + 1
            snakeHeadIndex = snakeHeadIndex + 1
            snake.insert(snakeHeadIndex, newPoint)
            if (updateSpeed > 10):
                updateSpeed = updateSpeed * SNAKE_SPEED_INCREASE_RATE
            SNAKE_GROWTH_PROGRESS = 0
        else:
            if eatenChar != " ":
                SNAKE_GROWTH_PROGRESS = SNAKE_GROWTH_PROGRESS + 1
            tailIndex = snakeHeadIndex + 1
            if tailIndex >= len(snake):
                tailIndex = 0
            # clear old tail
            clearPosition(edit, snakeView, snake[tailIndex])

            # draw new tail
            if tailIndex + 1 >= len(snake):
                newTailIndex = 0
            else:
                newTailIndex = tailIndex + 1
            if newTailIndex + 1 >= len(snake):  # refactor this tripe
                newTailContext = 0
            else:
                newTailContext = newTailIndex + 1

            drawSnakeTail(edit,
                          snakeView,
                          snake[newTailIndex],
                          snake[newTailContext])

            # update head index
            snakeHeadIndex = tailIndex
            snake[snakeHeadIndex] = newPoint

        sublime.status_message("SNAKE_SCORE: " + str(SNAKE_SCORE))
        sublime.set_timeout(lambda: renderSnake(edit,
                                                snakeView,
                                                snake,
                                                snakeHeadIndex,
                                                updateSpeed), int(updateSpeed))
    else:
        # reset arrow key functionality
        SNAKE_ON = False
        SNAKE_DIRECTION = "right"


def gameOver():
    global SNAKE_ON
    sublime.error_message("Game Over!\nYour SNAKE_SCORE was: " +
                          str(SNAKE_SCORE))
    SNAKE_ON = False


def drawSnakeTail(edit, snakeView, tailPos, nextSegPos):
    global SNAKE_TAIL
    # work out how tail joins to body, to pick correct
    # orientation tail graphics
    tailX, tailY = snakeView.rowcol(tailPos)
    segX, segY = snakeView.rowcol(nextSegPos)
    if segX > tailX:
        editPosition(edit, snakeView, tailPos, SNAKE_TAIL_DOWN)
    elif segX < tailX:
        editPosition(edit, snakeView, tailPos, SNAKE_TAIL_UP)
    elif segY > tailY:
        editPosition(edit, snakeView, tailPos, SNAKE_TAIL_RIGHT)
    else:
        editPosition(edit, snakeView, tailPos, SNAKE_TAIL_LEFT)


def drawSnakeSegment(edit, snakeView, segPos, prevPos, nextPos):
    global SNAKE_SEGMENT
    # this will need expanding for snake corners
    prevX, prevY = snakeView.rowcol(prevPos)
    nextX, nextY = snakeView.rowcol(nextPos)
    segX, segY = snakeView.rowcol(segPos)
    if segY == prevY and segY == nextY:
        editPosition(edit, snakeView, segPos, SNAKE_VERTICAL_SEGMENT)
    else:
        editPosition(edit, snakeView, segPos, SNAKE_HORIZONTAL_SEGMENT)


def drawSnakeHead(edit, snakeView, headPos):
    global SNAKE_HEAD
    editPosition(edit, snakeView, headPos, SNAKE_HEAD)


def clearPosition(edit, snakeView, position):
    editPosition(edit, snakeView, position, " ")


def editPosition(edit, snakeView, position, symbol):
    snakeView.run_command('edit_snake_position',
                          {'position': position, 'symbol': symbol})


class edit_snake_positionCommand(sublime_plugin.TextCommand):
    def run(self, edit, position, symbol):
        region = sublime.Region(position, position + 1)
        self.view.replace(edit, region, symbol)

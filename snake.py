#
#  Created by jon finerty - 2013
#

import sublime
import sublime_plugin

# GLOBAL SETTINGS
SNAKE_ON = False
SNAKE_DIRECTION = 'right'
SNAKE_SCORE = 0
SNAKE_STARTING_LENGTH = 10
SNAKE_STARTING_SPEED = 100
SNAKE_SPEED_INCREASE_RATE = 0.99
SNAKE_X_BOUNDARY = 0
SNAKE_Y_BOUNDARY = 0


# OVERWRITE ARROW KEYS - but pass through to old commands
class set_snake_rightCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'left':
            SNAKE_DIRECTION = 'right'
        if SNAKE_ON == False:
            self.view.run_command("move", {
                                    "by": "characters",
                                    "forward": True
                                 })


class set_snake_leftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'right':
            SNAKE_DIRECTION = 'left'
        if SNAKE_ON == False:
            self.view.run_command("move", {
                                    "by": "characters",
                                    "forward": False
                                 })


class set_snake_upCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'down':
            SNAKE_DIRECTION = 'up'
        if SNAKE_ON == False:
            self.view.run_command("move", {
                                    "by": "lines",
                                    "forward": False
                                 })


class set_snake_downCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'up':
            SNAKE_DIRECTION = 'down'
        if SNAKE_ON == False:
            self.view.run_command("move", {
                                    "by": "lines",
                                    "forward": True
                                 })


class SnakeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_ON, SNAKE_SCORE, SNAKE_X_BOUNDARY, SNAKE_Y_BOUNDARY, SNAKE_DIRECTION

        # reset stuff
        SNAKE_SCORE = 0
        SNAKE_DIRECTION = "right"

        if SNAKE_ON == False:

            SNAKE_ON = True

            templateView = self.view
            window = templateView.window()

            # Set up copy of current window, so work is not lost.
            entireFileRegion = sublime.Region(0, templateView.size())
            fileText = templateView.substr(entireFileRegion)
            syntax = templateView.settings().get('syntax')
            pos = templateView.sel()

            # copy across and set syntax
            snakeView = window.new_file()
            snakeView.set_scratch(True)
            snakeView.set_name("SNAKE")
            window.focus_view(snakeView)
            edit = snakeView.begin_edit()
            snakeView.insert(edit, 0, fileText + "\n")
            snakeView.end_edit(edit)
            snakeView.set_syntax_file(syntax)

            # replace tabs with spaces
            edit = snakeView.begin_edit()
            snakeStartingX, snakeStartingY = snakeView.rowcol(pos[0].a)
            # expand tabs tends to break stuff, check for tabs first?
            tabs = snakeView.find("\t", 0)
            if tabs != None:
                snakeView.run_command("expand_tabs", {"set_translate_tabs": True})
            snakeView.end_edit(edit)

            # find longest line
            entireSnakeViewRegion = sublime.Region(0, snakeView.size())
            lines = snakeView.split_by_newlines(entireSnakeViewRegion)
            maxLineLength = 0
            for line in lines:
                if line.size() > maxLineLength:
                    maxLineLength = line.size()

            # add on nessacary space to end of lines
            edit = snakeView.begin_edit()
            totalPaddingOffset = 0
            for line in lines:
                paddingSize = (maxLineLength - line.size()) + 1
                paddingString = (" " * (paddingSize - 1)) + "|"
                snakeView.insert(edit,
                                line.b + totalPaddingOffset,
                                paddingString)
                totalPaddingOffset = totalPaddingOffset + paddingSize
            snakeView.end_edit(edit)

            # set word wrap to maximum line length, otherwise pain
            snakeView.settings().set("wrap_width", 0)
            snakeView.settings().set("word_wrap", False)

            # Add border to bottom of code so its more obvious
            edit = snakeView.begin_edit()
            SNAKE_Y_BOUNDARY = maxLineLength
            SNAKE_X_BOUNDARY = len(lines)
            bottomBorder = ("_" * maxLineLength) + "|\n"
            snakeView.insert(edit, snakeView.size(), bottomBorder)
            snakeView.end_edit(edit)

            # Create default snake -
            # consists of a set of positions (stored as text_points)
            snakeStartingPoint = snakeView.text_point(
                                    snakeStartingX,
                                    0)
            snakeEndingPoint = snakeStartingPoint + SNAKE_STARTING_LENGTH + 1
            snake = range(snakeStartingPoint, snakeEndingPoint)
            snakeHeadIndex = SNAKE_STARTING_LENGTH
            updateSpeed = SNAKE_STARTING_SPEED

            # draw initial snake
            edit = snakeView.begin_edit()
            for segment in snake:
                segmentRegion = sublime.Region(segment, segment + 1)
                snakeView.replace(edit, segmentRegion, u"\u2588")
            snakeView.end_edit(edit)
            snakeView.show_at_center(snakeStartingPoint)

            # start snake update timeout loop
            sublime.set_timeout(lambda: renderSnake(snakeView,
                                                    snake,
                                                    snakeHeadIndex,
                                                    updateSpeed), updateSpeed)
        else:
            SNAKE_ON = False


def renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed):
    global SNAKE_DIRECTION, SNAKE_ON, SNAKE_SCORE, SNAKE_X_BOUNDARY, SNAKE_X_BOUNDARY

    if SNAKE_ON:
        SNAKE_SCORE = SNAKE_SCORE + 1

        # 'Render' new snake position
        edit = snakeView.begin_edit()

        # Get position of cell to be eaten
        newPosX, newPosY = snakeView.rowcol(snake[snakeHeadIndex])
        if SNAKE_DIRECTION == "right":
            newPosY = newPosY + 1
        elif SNAKE_DIRECTION == "left":
            newPosY = newPosY - 1
        elif SNAKE_DIRECTION == "up":
            newPosX = newPosX - 1
        else:
            newPosX = newPosX + 1

        # check boundary lose conditions
        if (newPosX >= SNAKE_X_BOUNDARY or newPosY >= SNAKE_Y_BOUNDARY):
            gameOver()
        newPoint = snakeView.text_point(newPosX, newPosY)

        snakeView.show_at_center(newPoint)
        eatenChar = snakeView.substr(newPoint)

        # draw head
        newPointRegion = sublime.Region(newPoint, newPoint + 1)
        snakeView.replace(edit, newPointRegion, u"\u2588")

        # see if lost by eating oneself
        for segment in snake:
            if newPoint == segment:
                gameOver()

        if eatenChar == " ":  # don't grow
            tailIndex = snakeHeadIndex + 1
            if tailIndex >= len(snake):
                tailIndex = 0
            tailPos = snake[tailIndex]
            tailRegion = sublime.Region(tailPos, tailPos + 1)
            snakeView.replace(edit, tailRegion, " ")
            snakeHeadIndex = tailIndex
            snake[snakeHeadIndex] = newPoint
        elif eatenChar == "\n":  # eaten a wall, die
            gameOver()
        else:  # grow snake
            SNAKE_SCORE = SNAKE_SCORE + 1
            snakeHeadIndex = snakeHeadIndex + 1
            snake.insert(snakeHeadIndex, newPoint)
            if (updateSpeed > 1):
                updateSpeed = updateSpeed * SNAKE_SPEED_INCREASE_RATE

        snakeView.end_edit(edit)

        sublime.status_message("SNAKE_SCORE: " + str(SNAKE_SCORE))
        sublime.set_timeout(lambda: renderSnake(snakeView,
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

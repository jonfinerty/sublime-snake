#   Created by jon finerty - 2013
#
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


# OVERWRITE ARROW KEYS - but pass through to old commands
class set_snake_rightCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'left':
            SNAKE_DIRECTION = 'right'
        if SNAKE_ON == False:
            self.view.run_command("move", {"by": "characters", "forward": True})

class set_snake_leftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'right':
            SNAKE_DIRECTION = 'left'
        if SNAKE_ON == False:
            self.view.run_command("move", {"by": "characters", "forward": False})

class set_snake_upCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'down':
            SNAKE_DIRECTION = 'up'
        if SNAKE_ON == False:
            self.view.run_command("move", {"by": "lines", "forward": False})

class set_snake_downCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_DIRECTION
        if SNAKE_DIRECTION != 'up':
            SNAKE_DIRECTION = 'down'
        if SNAKE_ON == False:
            self.view.run_command("move", {"by": "lines", "forward": True})

class SnakeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global SNAKE_ON, SNAKE_SCORE

        SNAKE_SCORE = 0

        if SNAKE_ON == False :

            SNAKE_ON = True

            templateView = self.view;
            window = templateView.window();

            # Set up copy of current window, so work is not lost.
            fileText = templateView.substr(sublime.Region(0, templateView.size()))
            syntax = templateView.settings().get('syntax')
            pos = templateView.sel()

            # copy across and set syntax
            snakeView = window.new_file()
            snakeView.set_scratch(True)
            window.focus_view(snakeView)
            edit = snakeView.begin_edit()
            snakeView.insert(edit, 0, fileText)
            snakeView.end_edit(edit)
            snakeView.set_syntax_file(syntax)

            # replace tabs with spaces
            edit = snakeView.begin_edit()
            snakeStartingX, snakeStartingY = snakeView.rowcol(pos[0].a)
            snakeView.run_command("expand_tabs", {"set_translate_tabs": True})
            snakeView.end_edit(edit)

            

            # fill in file with spaces
            lines = snakeView.split_by_newlines(sublime.Region(0, snakeView.size()))
            maxLineLength = 0
            for line in lines :
                if line.size() > maxLineLength:
                    maxLineLength = line.size()

            
            # add on nessacary space to end of lines
            edit = snakeView.begin_edit()
            adjustment = 0
            for line in lines :
                paddingSize = (maxLineLength - line.size())
                addOn = " " * paddingSize
                snakeView.insert(edit, line.b+adjustment, addOn)
                adjustment = adjustment+paddingSize
            snakeView.end_edit(edit)
            
            
            # Create default snake - consists of a set of positions (stored as text_points) 
            snakeStartingPoint = snakeView.text_point(snakeStartingX, snakeStartingY)
            snake = range(snakeStartingPoint, snakeStartingPoint+SNAKE_STARTING_LENGTH+1)
            snakeHeadIndex = SNAKE_STARTING_LENGTH
            updateSpeed = SNAKE_STARTING_SPEED
            # draw initial snake
            edit = snakeView.begin_edit()
            for segment in snake:           
                snakeView.replace(edit,sublime.Region(segment, segment+1), u"\u2588")
            snakeView.end_edit(edit);       
            snakeView.show_at_center(snakeStartingPoint)    
            sublime.set_timeout(lambda: renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed), updateSpeed)
        else :
            SNAKE_ON = False

def renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed):
    global SNAKE_DIRECTION, SNAKE_ON, SNAKE_SCORE       
    
    if SNAKE_ON:
        SNAKE_SCORE = SNAKE_SCORE + 1
        # 'Render' snake
        edit = snakeView.begin_edit()
        
        # update tail segment to be new head and draw it, no other cells need to be altered     
        newPosX, newPosY = snakeView.rowcol(snake[snakeHeadIndex])
        if SNAKE_DIRECTION == "right" :
            newPosY = newPosY + 1
        elif SNAKE_DIRECTION == "left" :
            newPosY = newPosY - 1
        elif SNAKE_DIRECTION == "up" :
            newPosX = newPosX - 1
        else :
            newPosX = newPosX + 1
        
        newPoint = snakeView.text_point(newPosX, newPosY)
        # scroll to new point
        snakeView.show_at_center(newPoint)  
        eatenChar = snakeView.substr(newPoint)
        # draw head
        snakeView.replace(edit, sublime.Region(newPoint, newPoint+1), u"\u2588")
        # redraw old head
        snakeView.replace(edit, sublime.Region(snake[snakeHeadIndex], snake[snakeHeadIndex]+1), u"\u2588")

        # see if lost by eating oneself
        for segment in snake:
            if newPoint == segment:
                sublime.error_message("Game Over!\nYour SNAKE_SCORE was: " + str(SNAKE_SCORE));
                SNAKE_ON = False

        if eatenChar == " " : # don't grow
            tailIndex = snakeHeadIndex + 1
            if tailIndex >= len(snake) :
                tailIndex = 0           
            snakeView.replace(edit, sublime.Region(snake[tailIndex], snake[tailIndex]+1), " ")          
            snakeHeadIndex = tailIndex
            snake[snakeHeadIndex] = newPoint
        else : #grow snake          
            SNAKE_SCORE = SNAKE_SCORE + 1
            snakeHeadIndex = snakeHeadIndex + 1
            snake.insert(snakeHeadIndex, newPoint)
            if (updateSpeed > 1) :
                updateSpeed = updateSpeed*SNAKE_SPEED_INCREASE_RATE
            
        snakeView.end_edit(edit)
        
        sublime.status_message("SNAKE_SCORE: " + str(SNAKE_SCORE))
        sublime.set_timeout(lambda: renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed), int(updateSpeed))
    else :
        # reset arrow key functionality
        SNAKE_ON = False
        SNAKE_DIRECTION = "right"
#	Created by jon finerty - 2013
#	
#

import sublime, sublime_plugin, time  

snakeDirection = 'right'
snakeOn = False
score = 0
startingLength = 10
startingSpeed = 100
speedIncreaseRate = 0.99

# OVERWRITE ARROW KEYS - but pass through to old commands
class set_snake_rightCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global snakeDirection
		if snakeDirection != 'left':
			snakeDirection = 'right'
		if snakeOn == False:
			self.view.run_command("move", {"by": "characters", "forward": True})

class set_snake_leftCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global snakeDirection
		if snakeDirection != 'right':
			snakeDirection = 'left'
		if snakeOn == False:
			self.view.run_command("move", {"by": "characters", "forward": False})

class set_snake_upCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global snakeDirection
		if snakeDirection != 'down':
			snakeDirection = 'up'
		if snakeOn == False:
			self.view.run_command("move", {"by": "lines", "forward": False})

class set_snake_downCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global snakeDirection
		if snakeDirection != 'up':
			snakeDirection = 'down'
		if snakeOn == False:
			self.view.run_command("move", {"by": "lines", "forward": True})

class SnakeCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		global snakeOn
		global score
		score = 0

		if snakeOn == False :

			snakeOn = True

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
			snake = range(snakeStartingPoint, snakeStartingPoint+startingLength+1)
			snakeHeadIndex = startingLength
			updateSpeed = startingSpeed #ms
			# draw initial snake
			edit = snakeView.begin_edit()
			for segment in snake:			
				snakeView.replace(edit,sublime.Region(segment, segment+1), u"\u2588")
			snakeView.end_edit(edit);		
			snakeView.show_at_center(snakeStartingPoint)	
			sublime.set_timeout(lambda: renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed), updateSpeed)
		else :
			snakeOn = False

def renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed):
	global snakeDirection
	global snakeOn
	global score		
	
	if snakeOn:
		score = score + 1
		# 'Render' snake
		edit = snakeView.begin_edit()
		
		# update tail segment to be new head and draw it, no other cells need to be altered		
		newPosX, newPosY = snakeView.rowcol(snake[snakeHeadIndex])
		if snakeDirection == "right" :
			newPosY = newPosY + 1
		elif snakeDirection == "left" :
			newPosY = newPosY - 1
		elif snakeDirection == "up" :
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
				sublime.error_message("Game Over!\nYour score was: " + str(score));
				snakeOn = False

		if eatenChar == " " : # don't grow
			tailIndex = snakeHeadIndex + 1
			if tailIndex >= len(snake) :
				tailIndex = 0			
			snakeView.replace(edit, sublime.Region(snake[tailIndex], snake[tailIndex]+1), " ")			
			snakeHeadIndex = tailIndex
			snake[snakeHeadIndex] = newPoint
		else : #grow snake			
			score = score + 1
			snakeHeadIndex = snakeHeadIndex + 1
			snake.insert(snakeHeadIndex, newPoint)
			if (updateSpeed > 1) :
				updateSpeed = updateSpeed*speedIncreaseRate
			
		snakeView.end_edit(edit)
		
		sublime.status_message("Score: " + str(score))
		sublime.set_timeout(lambda: renderSnake(snakeView, snake, snakeHeadIndex, updateSpeed), int(updateSpeed))
	else :
		# reset arrow key functionality
		snakeOn = False
		snakeDirection = "right"
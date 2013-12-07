#!/usr/bin/python

from time import sleep, localtime, strftime
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import sys
import subprocess
import threading


# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = Adafruit_CharLCDPlate()

def display(text):
	fmtText = text[:16] + "\n" + text[16:]
	lcd.clear()
	lcd.message(fmtText)

# Clear display and show greeting, pause 1 sec
display("Welcome on jotak's LCD Raspyfi!")
sleep(3)

state = "playback"

# Use subprocess.check_output to get list of playlists (mpc lsplaylists)
lists = ["no-list"]
currentList = 0
previousSong = ""

# Buttons
buttons = (lcd.SELECT, lcd.LEFT, lcd.UP, lcd.DOWN, lcd.RIGHT)
curPressed = -1

# Colors
colors = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET)
curColor = lcd.RED

showingTime = False

def fetchLists():
	global lists
	lists = subprocess.check_output(["mpc", "lsplaylists"]).splitlines()
fetchLists()

def showList():
	global lists, currentList
	display(lists[currentList])

def showPlaying():
	if showingTime:
		showTime()
	else:
		curSong = subprocess.check_output(["mpc", "current"])
		if curSong == "":
			display("No song selected")
		else:
			display(curSong)
		global previousSong
		if previousSong != curSong:
			previousSong = curSong
			changeColor()

def showTime():
	display(strftime("%a, %d %b %Y %H:%M:%S", localtime()))

def buttonPressed(i):
	global state
	if state == "menu":
		buttonPressedMenu(i)
	else:
		buttonPressedPlayback(i)

def changeColor():
	global curColor
	curColor += 1
	curColor %= len(colors)
	lcd.backlight(colors[curColor])

def buttonPressedMenu(i):
	global state, currentList, lists, showingTime
	if i == 0:
		state = "playback"
	elif i == 1:
		# prev list
                if currentList == 0:
                        currentList = len(lists) - 1
                else:
                        currentList-=1
                showList()
	elif i == 2:
		showingTime = not showingTime
		if not showingTime:
			showList()
	elif i == 3:
		# play list
                subprocess.call(["mpc", "clear"])
                subprocess.call(["mpc", "load", lists[currentList]])
                subprocess.call(["mpc", "play"])
                state = "playback"
	elif i == 4:
		# next list
                currentList+=1
                if currentList == len(lists):
                        currentList = 0
                showList()

def buttonPressedPlayback(i):
	global state, showingTime
	if i == 0:
		fetchLists()
		state = "menu"
		showList()
	elif i == 1:
		subprocess.call(["mpc", "prev"])
	elif i == 2:
		showingTime = not showingTime
	elif i == 3:
		subprocess.call(["mpc", "toggle"])
	elif i == 4:
		subprocess.call(["mpc", "next"])

class DisplayThread ( threading.Thread ):
	def run ( self ):
		while True:
			global state, showingTime
			if state == "playback" or showingTime:
				showPlaying()
				sleep(1)

DisplayThread().start()

while True:
	sleep(.1)
	nothingPressed = True
	for i in range(5):
		if lcd.buttonPressed(buttons[i]):
			nothingPressed = False
			if i != curPressed:
				buttonPressed(i)
				curPressed = i
				break
	if nothingPressed:
		curPressed = -1


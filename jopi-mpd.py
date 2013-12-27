#!/usr/bin/python

from time import sleep, localtime, strftime
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from cleaner import cleanString
import sys
import subprocess
import threading
import os

welcomeText = "Welcome on jotak's LCD Raspyfi!"
musicAbsPath = "/home/pi/music/"
playlistRelPath = "WEBRADIO/playlists/"

class TextScroller:
	text = ''
	position = 0
	textLength = 0
	step = 0

	def scroll(self):
		nextPos = self.position + self.step
		if nextPos < 0 or nextPos >= self.textLength - 32:
			self.step *= -1
		else:
			self.position = nextPos

		return self.text[self.position:self.textLength]

	def setText(self, newText):
		self.text = newText
		self.textLength = len(newText)
		self.position = 0
		if self.textLength <= 32:
			# Text is small enough => deactivate scrolling
			self.step = 0
		else:
			# 1 means left to right
			self.step = 1

scroller = TextScroller()

# Initialize the LCD plate.  Should auto-detect correct I2C bus.  If not,
# pass '0' for early 256 MB Model B boards or '1' for all later versions
lcd = Adafruit_CharLCDPlate()

def display(text):
	fmtText = cleanString(text[:16] + "\n" + text[16:])
	lcd.clear()
	lcd.message(fmtText)

# Clear display and show greeting, pause 1 sec
display(welcomeText)
sleep(3)

state = "play"

# Use subprocess.check_output to get list of playlists (mpc lsplaylists)
lists = ["no-list"]
currentList = 0
fileListIdx = -1
previousSong = ""

# Buttons
buttons = (lcd.SELECT, lcd.LEFT, lcd.UP, lcd.DOWN, lcd.RIGHT)
curPressed = -1

# Colors
colors = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL, lcd.BLUE, lcd.VIOLET)
curColor = lcd.RED

showingTime = False

def fetchLists():
	global lists, fileListIdx, musicAbsPath, playlistRelPath
	lists = subprocess.check_output(["mpc", "lsplaylists"]).splitlines()
	fileListIdx = len(lists)
	lists.extend(os.listdir(musicAbsPath + playlistRelPath))

fetchLists()

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
		state = "play"
		refreshModePlaying(True)
	elif i == 1:
		# prev list
                if currentList == 0:
                        currentList = len(lists) - 1
                else:
                        currentList -= 1
                refreshModeList()
	elif i == 2:
		showingTime = not showingTime
		if not showingTime:
			refreshModeList()
	elif i == 3:
		# play list
                subprocess.call(["mpc", "clear"])
		if currentList < fileListIdx:
	                subprocess.call(["mpc", "load", lists[currentList]])
		else:
			subprocess.call(["mpc", "load", playlistRelPath + lists[currentList]])
                subprocess.call(["mpc", "play"])
                state = "play"
		refreshModePlaying(True)
	elif i == 4:
		# next list
                currentList += 1
                if currentList == len(lists):
                        currentList = 0
                refreshModeList()

def buttonPressedPlayback(i):
	global state, showingTime
	if i == 0:
		fetchLists()
		refreshModeList()
		state = "menu"
	elif i == 1:
		subprocess.call(["mpc", "prev"])
	elif i == 2:
		showingTime = not showingTime
		refreshModePlaying(True)
	elif i == 3:
		subprocess.call(["mpc", "toggle"])
	elif i == 4:
		subprocess.call(["mpc", "next"])


def refreshModeList():
	global lists, currentList, scroller
	scroller.setText(lists[currentList])


def refreshModePlaying(forceSetText=False):
	global previousSong, scroller
	curSong = subprocess.check_output(["mpc", "current"])
	if previousSong != curSong:
		previousSong = curSong
		changeColor()
		if curSong == "":
			scroller.setText("No song selected")
		else:
			scroller.setText(curSong)
	elif forceSetText:
		scroller.setText(curSong)


def refreshModeTime():
	scroller.setText(strftime("%a, %d %b %Y %H:%M:%S", localtime()))

def checkRun():
	try:
		with open('/var/lock/stop-jopi-mpd'):
			return False
	except IOError:
		return True

class DisplayThread(threading.Thread):
	def run (self):
		while True:
			global state, showingTime, scroller
			if checkRun() == False:
				break
			if showingTime:
				refreshModeTime()
			elif state == "play":
				refreshModePlaying()
			display(scroller.scroll())
			sleep(1)

DisplayThread().start()

while True:
	if checkRun() == False:
		break
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

display("Goodbye!")


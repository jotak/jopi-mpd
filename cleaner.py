
import subprocess

def cleanString(str):
	return str.replace("é","e").replace("è","e").replace("ê","e").replace("ë","e").replace("à","a").replace("ù","u").replace("ô","o").replace("â","a").replace("ï","i").replace("î","i").replace("û","u").replace("ü","u");



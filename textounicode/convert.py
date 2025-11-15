import re
import unicodedata
import os


def convert(s):
	global data_loaded

	if data_loaded == False:
		load_data()
		data_loaded = True

	ss = convert_single_symbol(s)
	if ss != None:
		return ss

	s = apply_aliases(s)
	s = convert_latex_symbols(s)
	s = process_starting_modifiers(s)
	s = apply_all_modifiers(s)

	if s != "":
		s = unicodedata.normalize("NFC",s)
	return s

# If s is just a latex code "alpha" or "beta" it converts it to its
# unicode representation.
def convert_single_symbol(s):
	ss = "\\" + s
	for (code, val) in latex_symbols:
		if code == ss:
			return val
	return None

# Replace each "\alpha", "\beta" and similar latex symbols with
# their unicode representation.
def convert_latex_symbols(s):
	for (code, val) in latex_symbols:
		s=re.sub('\\'+code+'([^A-Za-z]|$)',val+r'\1',s)
	return s

# If s start with "it ", "cal ", etc. then make the whole string
# italic, calligraphic, etc.
def process_starting_modifiers(s):
	s = re.sub("^bb ", r"\\bb{", s)
	s = re.sub("^bf ", r"\\bf{", s)
	s = re.sub("^it ", r"\\it{", s)
	s = re.sub("^cal ", r"\\cal{", s)
	s = re.sub("^frak ", r"\\frak{", s)
	s = re.sub("^mono ", r"\\mono{", s)
	return s

def apply_all_modifiers(s):
	s = apply_modifier(s, "^", superscripts)
	s = apply_modifier(s, "_", subscripts)
	s = apply_modifier(s, "\\bb", textbb)
	s = apply_modifier(s, "\\bf", textbf)
	s = apply_modifier(s, "\\it", textit)
	s = apply_modifier(s, "\\cal", textcal)
	s = apply_modifier(s, "\\frak", textfrak)
	s = apply_modifier(s, "\\mono", textmono)
	s = apply_combinings(s)
	return s

# Example: modifier = "^", D = superscripts
# This will search for the ^ signs and replace the next
# digit or (digits when {} is used) with its/their uppercase representation.
def apply_modifier(text, modifier, D):
	text = text.replace(modifier, "^")
	newtext = ""
	mode_normal, mode_modified, mode_long = range(3)
	mode = mode_normal
	for ch in text:
		if mode == mode_normal and ch == '^':
			mode = mode_modified
			continue
		elif mode == mode_modified and ch == '{':
			mode = mode_long
			continue
		elif mode == mode_modified:
			newtext += D.get(ch, ch)
			mode = mode_normal
			continue
		elif mode == mode_long and ch == '}':
			mode = mode_normal
			continue

		if mode == mode_normal:
			newtext += ch
		else:
			newtext += D.get(ch, ch)
	return newtext

# Applying combinings : \overline{ac} => a U+0305 c U+0305
def apply_combinings(text):
	for (modifier,combining) in combinings:
		text = text.replace(modifier,"^")
		newtext = ""
		mode_normal, mode_modified, mode_long = range(3)
		mode = mode_normal
		level = 0
		for ch in text:
			if mode == mode_normal and ch == '^':
				mode = mode_modified
				continue
			elif mode == mode_modified and ch == '{':
				mode = mode_long
				continue
			elif mode == mode_modified:
				newtext += ch
				newtext += combining
				mode = mode_normal
				continue
			elif mode == mode_long and ch == '}':
				if level==0:
					mode = mode_normal 
				else:
					level -= 1
				continue
			elif mode == mode_long and ch == '{':
				level += 1
				
			if mode == mode_normal:
				newtext += ch
			else:
				newtext += ch
				newtext += combining

		text = newtext
	return text


def apply_aliases(text):
	for (code,val) in aliases:
		splitcode = code.split('{}')
		splitval = val.split('{}')
		text = text.replace(splitcode[0],u'\x7f')
		newtext = ""
		mode_normal, mode_modified, mode_long = range(3)
		mode = mode_normal
		level = 0
		noarg = 0
		for ch in text:
			if mode == mode_normal and ch == u'\x7f':
				newtext += splitval[0]
				if len(splitcode) > 1:
					mode = mode_modified
				continue
			elif mode == mode_modified and ch == '{':
				noarg += 1
				newtext += ch
				mode = mode_long
				continue
			elif mode == mode_long and ch == '}':
				newtext += ch
				newtext += splitval[noarg]
				if level==0:
					if noarg == len(splitcode)-1:
						mode = mode_normal
					else:
						mode = mode_modified
				else:
					level -= 1
				continue
			elif mode == mode_long and ch == '{':
				newtext += ch
				level += 1
			else:
				newtext += ch
				

		text = newtext
	return text


def load_data():
	load_symbols()
	load_dict(BASE_DIR+"data/subscripts", subscripts)
	load_dict(BASE_DIR+"data/superscripts", superscripts)
	load_dict(BASE_DIR+"data/textbb", textbb)
	load_dict(BASE_DIR+"data/textbf", textbf)
	load_dict(BASE_DIR+"data/textit", textit)
	load_dict(BASE_DIR+"data/textcal", textcal)
	load_dict(BASE_DIR+"data/textfrak", textfrak)
	load_dict(BASE_DIR+"data/textmono", textmono)
	load_combinings()
	load_aliases()

def load_dict(filename, D):
	with open(filename, "r", encoding="utf-8") as f:
		line = f.readline()
		while line != "":
			words = line.split()
			code = words[0]
			val = words[1]
			D[code] = val
			line = f.readline()

def load_symbols():
	with open(BASE_DIR+"data/symbols", "r", encoding="utf-8") as f:
		line = f.readline()
		while line != "":
			words = line.split()
			code = words[0]
			val = words[1]
			latex_symbols.append((code, val))
			line = f.readline()

def load_combinings():
	with open(BASE_DIR+"data/combinings","r", encoding="utf-8") as f:
		line = f.readline()
		while line != "":
			words = line.split()
			code = words[0]
			val = words[1]
			combinings.append((code, val))
			line = f.readline()

def load_aliases():
	with open(BASE_DIR+"data/aliases","r", encoding="utf-8") as f:
		line = f.readline()
		while line != "":
			words = line.split()
			code = words[0]
			val = words[1]
			aliases.append((code, val))
			line = f.readline()

data_loaded = False

superscripts = {}
subscripts = {}
textbb = {}
textbf = {}
textit = {}
textcal = {}
textfrak = {}
textmono = {}
latex_symbols = []
combinings = []
aliases = []

if __name__ != "__main__":
        BASE_DIR = "textounicode/"
        load_data()
else:
        print(convert(r"\sum^n_{i=0} x^i  13^{12}"))

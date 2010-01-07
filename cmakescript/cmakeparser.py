#!/usr/bin/env python
"""
Module for parsing a CMake source file

Original Author:
2010 Ryan Pavlik <rpavlik@iastate.edu> <abiryan@ryand.net>
http://academic.cleardefinition.com
Iowa State University HCI Graduate Program/VRAC
"""

###
# standard packages
import re

###
# third-party packages
# - none

###
# internal packages
# - none

def parse_string(instr):
	parser = CMakeParser(ParseInput(instr))
	parser.parse()
	return parser

def parse_file(filename):
	cmakefile = open(filename, 'r')
	instr = cmakefile.read()
	cmakefile.close()
	return parse_string(instr)

class ParseInput():
	"""Class providing an iterable interface to the parser's input"""

	def __init__(self, strdata):
		self._data = strdata.splitlines()
		self._lineindex = 0
		self.alldone = False
		self.gotline = False

	def __iter__(self):
		"""Be usable as an iterator."""
		return self

	def next(self):
		"""Return the current line each time we are iterated.
		We don't go to the next line unless we've been accepted."""

		# Will always hit this condition if all works well
		if self._lineindex == len(self._data):
			self.alldone = True
			raise StopIteration

		# If we break, break big
		assert self._lineindex < len(self._data)

		# OK, we can actually return the data now
		self.gotline = True
		return self._data[self._lineindex]

	def accept(self):
		"""Signal that we've processed this line and should go to the next"""

		# We shouldn't accept a line we haven't even seen
		assert self.gotline

		self._lineindex = self._lineindex + 1
		self.gotline = False

	# """A more intuitive alias for next() - get the current line"""
	line = next

class CMakeParser():

	def __init__(self, parseinput):
		self.input = parseinput
		self.parsetree = None

	def output_as_cmake(self):
		return "\n".join(self.output_block(self.parsetree, 0))

	def output_block(self, block, level):
		lines = []
		if block is None:
			return lines
		for statement in block:
			lines.extend(self.output_statement(statement, level))
		return lines

	def output_statement(self, statement, level):

		func, args, comment, children = statement

		if args is None:
			args = ""

		if func=="" and comment is None:
			thisline = ""
		else:
			thisline = "\t" * level

		if func!="":
			thisline = thisline + func.lower() + "(" + args + ")"
			if comment is not None:
				thisline = thisline + "\t"

		if comment is not None:
			thisline = thisline + comment

		output = [thisline]
		# Recurse into children
		output.extend(self.output_block(children, level + 1))
		return output


	def parse(self):
		self.parsetree = self.parse_block_children(None)
		if self.parsetree is None:
			self.parsetree = []

	def parse_block_children(self, startTag):
		if startTag is None:
			# the block is the entire file.
			isEnder = lambda x: (x is None)
		elif self.reBlockBeginnings.match(startTag):
			# can have children
			endblock = self.dReBlockEndings[startTag.lower()]
			isEnder = endblock.match
		else:
			# Can have no children
			return None

		block = []
		for line in self.input:
			func, args, comment, complete = self.parse_line(line)
			assert complete
			if isEnder(func):
				print block
				return block
			# Not an ender, so we accept this child.
			self.input.accept()
			children = self.parse_block_children(func)
			statement = ( func, args, comment, children)
			block.append( statement )



	def parse_line(self, line):
		if line is not None:
			m = self.reFullLine.match(line)
			func, args, comment, fullLine = m.group("FuncName",
												"Args", # todo change to argsCareful
												"Comment",
												"FullLine")

			hasFullLine = (fullLine is not None)
			if func is None:
				func = ""

			# TODO this is a suboptimal workaround!
			if args == "":
				args = None

		return (func, args, comment, hasFullLine)

	####
	## Strings of sub-regexes to compile later - all are re.VERBOSE

	## all the functions that permit parens in their args
	_reParenArgFuncs = (r"(?ix)" # case-insensitive and verbose
		+ "(?P<parenArgFunc>"
		+ "|".join(
			"""
			if
			else
			elseif
			endif

			while
			endwhile

			math
			""".split())
		+ r")")

	## A possible function name
	_reFuncName = r"(?x) \s* (?P<FuncName> [\w\d]+) \s*"

	## Extremely general "non-empty arguments," no leading or trailing whitespc
	_reArgs = r"(?x) \s* (?P<Args> (\S ((\s)*\S)*)?) \s*"

	## Standard command args: no parens
	#_reArgsStd = r"(?x) \s* (?P<ArgsStd> ([\S-\(\)]([\S-\(\)]|\s[\S-\(\)])* )?) \s*"

	## A comment: everything after # as long as it's not preceded by a \
	# the ?<! is a "negative backward assertion handling "not after a \"
	# (?<!\\)
	_reComment = r"(?x) \s* (?P<Comment> (?<!\\)\#.*)"

	## The start of a command, up until the arguments
	_reCommandStart = _reFuncName + r"\("

	## The end of a command
	_reCommandEnd = r"\s*\)"

	## A full (complete) line
	_reFullLine = ( r"^(?P<FullLine>\s*"	# start the full line bool group
				+ r"("			# start optional func call group
				+ _reCommandStart
				+ _reArgs
				+ _reCommandEnd
				+ r")?"			# end optional func call group
				+ r"("			# start optional comment group
				+ _reComment
				+ r")?" 		# end optional comment group
				+ r")?")		# end the full line bool group
	##
	####

	## Regex matching all the functions that permit parens in their args
	#reParenArgFuncs = re.compile("^" + _parenArgFuncs + "$",
	#	re.IGNORECASE | re.VERBOSE)

	## Regex matching a full line
	reFullLine = re.compile(_reFullLine, re.IGNORECASE | re.VERBOSE)

	## All functions that start a block
	_blockBeginnings = """	foreach
							function
							if
							elseif
							else
							macro
							while	""".split()
	_reBlockBeginnings = (r"(?ix)" +		# case-insensitive and verbose
							r"(?P<BlockBeginnings>" +
							"|".join(_blockBeginnings) +
							r")")

	## A compiled regex that matches exactly the functions that start a block
	reBlockBeginnings = re.compile(_reBlockBeginnings, re.IGNORECASE)

	## A dictionary where blockEndings[blockBeginFunc]=(blockEndFunc1,...),
	## all datatypes are strings.  Size is one more than blockBeginnings
	## because we match the empty string opening function (dummy for start
	## of file) with a dummy EOF string as an end tag
	_blockEndings = {'' : ('_CMAKE_PARSER_EOF_FLAG_',),

					'foreach'	: ('endforeach',),

					'function'	: ('endfunction',),

					'if'		: ('elseif', 'else', 'endif'),
					'elseif'	: ('elseif', 'else', 'endif'),
					'else'		: ('endif',),

					'macro'	: ('endmacro',),

					'while'	: ('endwhile',)}

	# Catch any "developer failed to add new function to both lists" bugs
	assert len(_blockEndings) - 1 == len(_blockBeginnings)

	## A big list comprehension that makes a dictionary with pairs (key, end)
	## where key is a start tag key from blockEndings and end is a
	## compiled regex that only exactly matches any corresponding ending
	dReBlockEndings = dict([  # Make a dict from list comprehension of pairs
		# the dictionary key is just the start tag
		( beginning,
		# the value is a compiled regex matching any of the end tags
		re.compile(	r"(?ix)" + # case insensitive
					r"^(?P<BlockEnding>" +
					r"|".join(ends) +
					r")$", re.IGNORECASE) )

		# for every key-value pair in the non-compiled dictionary
		for beginning, ends in _blockEndings.iteritems() ])
	# end of huge list comprehension

	# sanity check the comprehension above
	assert len(_blockEndings) == len(dReBlockEndings)

#if __name__ == "__main__":
#	pass

#!/usr/bin/env python
"""
CMake source file grammar

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


class IncompleteStatementError(Exception):
	"""Exception raised by parse_line when not given a full valid statement"""
	pass

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
_reFuncName = r"(?x) (?P<FuncName> [\w\d]+)"

## Extremely general "non-empty arguments," no leading or trailing whitespc
_reArgs = r"(?x) (?P<Args> (\S ((\s)*\S)*))"

## A given single valid argument
_reArg = r"""(?x) (
			(?:\\.|[^"'\s])+|	# anything that's a single word
			"(?:\\.|[^"\\])+"|	# anything double-quoted
			'(?:\\.|[^'\\])+')		# anything single-quoted
			"""



## Standard command args: no parens permitted
#_reArgsStd = r"(?x) \s* (?P<ArgsStd> ([\S-\(\)]([\S-\(\)]|\s[\S-\(\)])* )?) \s*"

## A comment: everything after # as long as it's not preceded by a \
# the ?<! is a "negative backward assertion handling "not after a \"
# (?<!\\)
_reComment = r"(?x) (?P<Comment> (?<!\\)\#(\s*\S+)*)"

## The start of a command, up until the arguments
_reCommandStart = _reFuncName + r"\s* \("

## The end of a command
_reCommandEnd = r"\)"

## A full (complete) line
_reFullLine = ( r"^\s*(?P<FullLine>"	# start the full line bool group
			+ r"("			# start optional func call group
			+ _reCommandStart
			+ r"\s*"
			+ r"("			# start optional args group
			+ _reArgs
			+ r")?"			# end optional args group
			+ r"\s*"
			+ _reCommandEnd
			+ r")?"			# end optional func call group
			+ r"\s*"
			+ r"("			# start optional comment group
			+ _reComment
			+ r")?" 		# end optional comment group
			+ r")\s*$")		# end the full line bool group

## The start of a multiline command
_reMLCommandStart = ( r"^\s*(?P<MLStart>"	# start the multi line bool group
			+ _reCommandStart
			+ r"\s*"
			+ r"(?P<MLArgs>"
			+ r"("
			+ _reArg
			+ r")*)"
			+ r"\s*"
			+ r"(?P<MLComment>"			# start optional comment group
			+ _reComment
			+ r")?)\s*$" 		# end optional comment group
			)


## The middle/end of a multiline command
_reMLCommandStart = ( r"^\s*(?P<MLMiddle>"	# start the multi line bool group
			+ r"\s*"
			+ r"(?P<MLArgs>"
			+ r"("
			+ _reArg
			+ r")*)"
			+ r"(?P<MLEndCommand>"
			+ _reCommandEnd
			+ ")?"
			+ r"\s*"
			+ r"(?P<MLComment>"			# start optional comment group
			+ _reComment
			+ r")?)\s*$" 		# end optional comment group
			)

## Regex matching all the functions that permit parens in their args
#reParenArgFuncs = re.compile("^" + _parenArgFuncs + "$",
#	re.IGNORECASE | re.VERBOSE)

## Regex matching a full line
reFullLine = re.compile(_reFullLine, re.IGNORECASE | re.VERBOSE | re.MULTILINE)

## A dictionary where blockEndings[blockBeginFunc]=(blockEndFunc1,...),
## all datatypes are strings.
_blockTagsDict = {'foreach'	: ('endforeach',),

				'function'	: ('endfunction',),

				'if'		: ('elseif', 'else', 'endif'),
				'elseif'	: ('elseif', 'else', 'endif'),
				'else'		: ('endif',),

				'macro'	: ('endmacro',),

				'while'	: ('endwhile',)}

##
_reBlockBeginnings = (r"(?ix)" +		# case-insensitive and verbose
						r"(?P<BlockBeginnings>" +
						"|".join(_blockTagsDict.keys()) +
						r")")

## A compiled regex that matches exactly the functions that start a block
reBlockBeginnings = re.compile(_reBlockBeginnings, re.IGNORECASE)

## A big list comprehension that makes a dictionary with pairs (key, end)
## where key is a start tag key from blockEndings and end is a
## compiled regex that only exactly matches any corresponding ending
dReBlockTagsDict = dict([  # Make a dict from list comprehension of pairs
	# the dictionary key is just the start tag
	( beginning,
	# the value is a compiled regex matching any of the end tags
	re.compile(	r"(?ix)" + # case insensitive
				r"^(?P<BlockEnding>" +
				r"|".join(ends) +
				r")$", re.IGNORECASE) )

	# for every key-value pair in the non-compiled dictionary
	for beginning, ends in _blockTagsDict.iteritems() ])
# end of huge list comprehension

# sanity check the comprehension above
assert len(_blockTagsDict) == len(dReBlockTagsDict)


def parse_line(line):
	if line is None:
		return (None, None, None)

	m = reFullLine.match(line)
	if m is None:
		raise IncompleteStatementError

	FuncName, Args, Comment = m.group("FuncName",
										"Args", # todo change to argsCareful
										"Comment")
	#if re.search(r"\n", Args):
		# This is multiline
	#	pass

	if FuncName is None:
		FuncName = ""

	return (FuncName, Args, Comment)
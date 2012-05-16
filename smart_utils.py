'''
SMART Snippets
Licensed under MIT
Copyright (c) 2012 William Cain
'''

from time import gmtime, strftime

def list_time():
	return [
		[strftime('%B %d, %y'), 'Month Day, Year']
	]
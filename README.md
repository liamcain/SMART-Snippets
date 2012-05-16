SMART Snippets
==============

Important
=========
SMART Snippets is still early in development.  There is *A LOT* left to do.  At the moment, however, it is both functional and bugfree.  This is exciting because now I can finally think seriously about where I see this plugin going in the future.

SMART Snippets is a *new* [Sublime Text](http://sublimetext.com/2) plugin that aims to enhance your overall coding experience.  With SMART Snippets, You can now use Python to *dynamically* create snippets.  Need to quickly timestamp your code?  Unfortunately, ST2's default snippets are static.  So you could spend your time trudging through Sublime Text's API, wasting precious hours to do something so trivial... but that shouldn't be your job.  You have your own work to do.  Instead, let SMART Snippets handle it.  Not only does this plugin let you execute Python code within a snippet, it provides a simpler syntax for gettings things done.

Getting Started
===============
SMART Snippets comes pre-bundled with a few snippets to get you started and demonstrate some of the syntax as well as show of the power you now hold.  To create your own, open the *Command Palette* and type `SMART Snippets: Create new SMART Snippet`.  The template will guide you from there.  *IMPORTANT:* the snippet must be saved within the SMART Snippet folder.  It can be in a subfolder, though, so feel free to organize by language or any other preference.  SMART Snippets makes snippet management as easy and painless as possible.  To view a list of all your snippets, type `SMART Snippets: List SMART Snippets` into the Command Palette.  Selecting the first item from list list will show only the snippets that match the current scope.  Selecting a snippet from the quick panel will open the corresponding snippet file.

Options within the Snippet template:
- ###params (Optional)
  > Available parameters:
   - Regex: specifies that the snippet's trigger will be regex
   - auto_expand: The snippet will expand within the need to press tab
- ###trigger (Required)
  > Indicates what text will expand into the snippet
- ###scope (Optional)
  > Limits the snippet to only expand when within a given scope (eg. source.python or text.html)


What To Do From There
=====================
SMART Snippets is meant to be the missing link between the average user and the ST2 API while bringing more fluidity to the power user.  On that note, here are the available commands so far:

- `$0,$1,$2...$n`: Tabstops.  This syntax is taken from the default snippets.  Pressing tab moves the cursor to the next sequential tabstop.  $0 represents the end position.
- `${0:placeholder}`: Tabstops w/ Placeholder text.  Again taken from the default snippet behavior, pressing tab will select the placeholder text in the next sequential tabstop
- `QP{placeholder:[options]}`: A Quick Panel region.  When the placeholder text is selected in the view, a quick panel will dropdown with a list of options.  Selecting the option will replace the placeholder text with the given option.  *Note* Quickpanel options can include python code when given the following syntax: text\tCODE.  So SMART Snippets will execute anything after \t.
- `AC{placeholder:[options]}`: An Autocomplete Region.  Similar to the QP Region, this region will display a list of options in the autocompletion panel.
- `` ```python code``` ``: Run python code directly within a snippet.  Insert your own raw python code or take use of SMART Snippets awesome custom syntax.  That's right.  SMART Snippets tries to make your python even easier by adding custom functions, syntax variants, and more.

SMART Snippet's Custom Syntax
=============================
The following is a list of functions and additions to the python insertions available at your disposal.

- `insert(string)`: Obviously you'll need some way to insert the text generated within the snippets.  Insert will insert the text at the correct spot for you. (Don't worry about keeping track of the cursor).  For beta testers: I'm considering changing this syntax.  Possible alternatives being insert string or print string.  What do you think?
- `region(placeholder,code [on 'char'])`: Sometimes you don't want to run the python code immediately.  Adding code to the region function means the code will not run until the cursor is within the given region.  Optionally, adding "on 'char'" means that the code will not run until you press a given key why within the code region.  For example print 'Hello World' on 't' means that pressing 't' while the cursor overlaps the code region will active the code. (Use '\n' for enter and '\t' for tab)
- `when name:CODE` : Here comes the interesting part.  The 'when' keyword creates what I call a 'minion region.'  The code will only run when the given name is activated.
- `activate(string_name)`:  To activate a 'minion region,' use this function, passing the corresponding name.  Protip: use activate() within a code region to activate code in an adjacent region when the cursor lands in a specific spot.

Not a Pythonista?
=================
Don't fret.  Not only is Python insanely simple and readable, SMART Snippets keeps everything you need within reach.  With direct access to Python libraries and the Sublime Text API, you'll be manipulating your code ease.

License
=======
Copyright (c) 2012 William Cain

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Getting Started with the Scandroid
==================================

The Scandroid is a program that scans metrical English verse.
If you don't know what that means, you probably don't want to use it.

Under the GNU General Public License, the Scandroid is freely distributable.
You can give it away, use it in class, make it do all your poetry homework,
anything you like. You can also fork a copy of the Scandroid source code
and modify it as you please. Just be sure to give credit where it is due.

Below are brief descriptions of the various Scandroid modules.

Scandroid.py
------------

Main module. Handles the wxPython frame and most of the interface, 
including the menus and button-presses that control everything.
Owns a ScansionMachine that does all the interesting work.

scanfuncs.py
------------

Contains the ScansionMachine class that has the methods called by Scandroid
to do the actual scansion work. It owns a dictionary and instances of a
Syllabizer and a Positioner for some of the grunt work.

syllables.py
------------

Divides a word into syllables, relying on regular expressions.

scanpositions.py
----------------

Positions all of the scansion marks (foot boundaries, stressed syllables,
unstressed syllables, etc.) above any line of poetry selected for scansion.

dictfuncs.py
------------

Holds the class that, rather loosely, contains methods and structures
connected with the dictionary of syllable-and-stress exceptions.

scandictionary.py
-----------------

Has the dictionary intended for use by the Scandroid. The words listed
are exceptions that will not be syllabized correctly by the routine method.

scanutilities.py
----------------

Contains utility classes and out-of-class functions.

scanstrings.py
--------------

Has text, strings, and generally useful globals the Scandroid needs;
Also, contains the Explainer class, which gabs about what we're doing
at every stage. Some non-class utility functions are also included.

scanstc.py
----------

Holds our subclasses of wx.StyledTextCtrl, or wx.STC, and bindings.

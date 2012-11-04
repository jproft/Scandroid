# scanstc.py 1.2
#
# the Scandroid
# Copyright (C) 2005 Charles Hartman
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. See the accompanying file, gpl.txt, for full
# details.
# OSI Certified Open Source Software
#
# This module of the Scandroid contains its STC subclass and  bindings.
# Also we subclass TextCtrl for a generic one-line read-only control, and
# subclass that for our text line and its scansion; want specialized
# methods for each of those. Constrained to non-proportional fonts!

import wx
import wx.stc as stc
from scanstrings import *

NAVKEYS = (wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_UP, wx.WXK_DOWN,
           wx.WXK_HOME, wx.WXK_END, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN,
           wx.WXK_NUMPAD_LEFT, wx.WXK_NUMPAD_RIGHT, wx.WXK_NUMPAD_UP,
           wx.WXK_NUMPAD_DOWN, wx.WXK_NUMPAD_HOME, wx.WXK_NUMPAD_END,
           wx.WXK_NUMPAD_PAGEUP, wx.WXK_NUMPAD_PAGEDOWN)


class MyOneLineTC(wx.TextCtrl):
    def __init__(self, parent, id, fontsize):
        self.fontsize = fontsize
        wx.TextCtrl.__init__(self, parent, id, style=wx.TE_READONLY)
        self.workfont = wx.Font(self.fontsize, wx.MODERN, wx.NORMAL, wx.NORMAL)
        self.SetFont(self.workfont)
        
    def Clear(self):
        wx.TextCtrl.Clear(self)
        self.SetFont(self.workfont)		

    def CopySelection(self): CopySelectedText(self)


class MyScanTC(MyOneLineTC):
    def __init__(self, parent, fontsize):
        MyOneLineTC.__init__(self, parent, -1, fontsize)
        self.AppendText(' (the scansion will go here) ')
        self.SetInsertionPoint(0)

class MyLineTC(MyOneLineTC):
    def __init__(self, parent, fontsize):
        MyOneLineTC.__init__(self, parent, -1, fontsize)
        self.AppendText(' Double-click any text line to bring it up here for scanning')
        self.SetInsertionPoint(0)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_RIGHT_DCLICK, self.OnDoubleClick)

    def OnDoubleClick(self, event):		# only in line, not scansion
        (start, end) = self.GetSelection()		# here (only) we know *where* in word
        wx.CallAfter(self.GetSelectedWord, event, start)	# selection so far 0 length
        event.Skip()
    def GetSelectedWord(self, event, clickpos):
        clicked = self.GetStringSelection()
        clicked = clicked.strip()			# Windows leaves trailing space!
        if not clicked: return
        hyphen = clicked.find('-')
        if hyphen != -1:
            (selstart, selend) = self.GetSelection()
            hyphen += selstart			# within selection
            if clickpos < hyphen:		# user selected first half of compound
                self.SetSelection(selstart, hyphen)
                clicked = clicked[:hyphen-selstart]
            else:
                self.SetSelection(hyphen+1, selend)
                clicked = clicked[hyphen+1-selstart:]
        try:
            result = self.GetParent().SM.SD.EditDict(clicked)
        except: 
            self.GetParent().ErrorMessage(self.GetParent().SM.SD.EditDict, clicked)
            return
        if result:
            self.GetParent().RestartLineAfterCancel()
        else:		# canceled; just un-select
            self.SetSelection(0, 0)


class MyNotesTC(wx.TextCtrl):
    def __init__(self, parent, fontsize):
        self.fontsize = fontsize
        wx.TextCtrl.__init__(self, parent, -1, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.workfont = wx.Font(self.fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.SetFont(self.workfont)
        
    def Clear(self):
        wx.TextCtrl.Clear(self)
        self.SetFont(self.workfont)

    def CopySelection(self): CopySelectedText(self)


class MyTextSTC(stc.StyledTextCtrl):
    def __init__(self, parent, ID):
        stc.StyledTextCtrl.__init__(self, parent, ID)
        # following shd probably have settable fontsize per screen like TCs above
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "size:14,face:Courier")
        self.Bind(stc.EVT_STC_DOUBLECLICK, self.OnDoubleClick)
        wx.EVT_CHAR(self, self.OnKeyDown)

    def GetStringSelection(self): return self.GetSelectedText()

    def OnKeyDown(self, event):
        #import sys
        #ch = event.KeyCode()
        #if ch in NAVKEYS: event.Skip()
        ##elif ((sys.platform == 'darwin' and event.MetaDown()) or (sys.platform
                                ##== 'win32' and event.ControlDown())):
            ##if ch == 'C':
                ##self.CopySelection()
            ##elif ch == 'A':
                ##self.SelectAll()
        self.SetFocus()
        event.Skip()

    def DisplayText(self, text):
        self.SetReadOnly(0)
        self.ClearAll()
        for line in text.splitlines():
            self.AddText(line + '\n')
        if len(self.GetLine(self.GetLineCount())) > 2:	# non-blank last line
            self.AddText('\n')		# make GetNextUnscanned work on last
        self.SetFocus()
        self.GotoPos(0)

    def CopySelection(self): CopySelectedText(self)

    def IsScanLine(self, number):
        """Return True/False for arg line contains scansion marks"""
        line = self.GetLine(number)
        if line.find(STRESS) != -1 or line.find(SYLMARK) != -1: 
            return True			# NOT a sophisticated test
        else: return False
        
    def GetNextUnscannedLine(self):
        """Find next scannable text line at or below cursor.
        
        Our criteria: line contains text, not whitespace, is not a "title"
        (= beginning with a tab), is not itself a scansion, isn't preceded
        by a scansion, and the click wasn't inside a selection (*presume* 
        that the selection is the whole line, because it was clicked!).

        The not-in-a-selection trick is to allow the current line (rather than
        the one following) to be selected, but for an immediately following
        get-next-line command to move forward from it.
        """
        ourpos = self.GetCurrentPos()
        aline = self.LineFromPosition(ourpos)
        last = self.GetLineCount() - 1
        (start, end) = self.GetSelection()
        while aline < last:
            line = self.GetLine(aline)
            if len(line) > 0 and not line.isspace() and line[0] != '\t' and \
                            not self.IsScanLine(aline) and (start == end and \
                            (aline == 0 or not self.IsScanLine(aline - 1))):
                break			# we have our target line
            end = start		# dummy to get next line selected
            aline += 1
            self.GotoLine(aline)
        if aline < last:
            self.SelectTheLine(aline)
            return True		# not used!
        else: return False	# used by testing routine ScanEverything

    def OnDoubleClick(self, evt):
        """Copy double-clicked line into to-be-scanned box"""
        clickline = self.LineFromPosition(self.GetCurrentPos())
        if self.IsScanLine(clickline): clickline += 1
        self.SelectTheLine(clickline)
        
    def SelectTheLine(self, thelinenum):
        """Implement double-click's call to copy line to work box"""
        # rstrip() to remove ugly Windows box; preserve leading whitespace!
        linetext = self.GetLine(thelinenum).rstrip()
        if len(linetext) < 2: return			# blank, or newline only
        if thelinenum > 0: selstart = self.GetLineEndPosition(thelinenum - 1) + 1
        else: selstart = 0
        self.SetSelection(selstart, self.GetLineEndPosition(thelinenum))
        self.GetParent().ShowTextLine(linetext, thelinenum)

    def PutLineBack(self, linenum, thescansion):
        """Place scansion over line it belongs to in Text panel"""
        if linenum > 0 and self.IsScanLine(linenum - 1):	# scan line exists?
            linenum -= 1
            self.GotoLine(linenum)
            pos = self.GetCurrentPos()
            self.SetSelection(self.GetCurrentPos(), self.GetLineEndPosition(linenum))
            self.ReplaceSelection(thescansion)		# substitute newer scansion
        else:
            self.GotoLine(linenum)			# go back where we got it
            pos = self.GetCurrentPos()
            self.AddText(thescansion + '\n')		# insert scansion line
            bottomline = self.GetFirstVisibleLine() + self.LinesOnScreen()
            if linenum > bottomline - 2:
                self.LineScroll(0, 2)


def CopySelectedText(aninstance):
    """Copy-to-clipboard text selected in any text field."""
    if not wx.TheClipboard.Open(): return	    # some error; ignore
    seltxt = aninstance.GetStringSelection()
    if len(seltxt) != 0: wx.TheClipboard.SetData(wx.TextDataObject(seltxt))
    wx.TheClipboard.Close()

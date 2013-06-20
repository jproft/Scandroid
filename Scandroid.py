# scanmain.py 1.5
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
# Main module of the Scandroid, the Python version of the verse scanner.
# This module handles the wxPython frame and most of the interface, 
# including the menus and button-presses that control everything. The Frame 
# owns a ScansionMachine that does all the interesting work.
#
# Version 1.5 (somewhat arbitrarily numbered) is the first revision in about
# seven years.  The occasion was Jim O'Connor's coming on board to fix
# up the old code.



import wx
import string, os, sys, sre
import random
import robIcon
from math import modf
from scanstrings import *			# some global texts & the Explainer
from scanstc import *				# editors for subwindows
from scanfuncs import *				# the Scansion Machine

# global to this module:
FORKSTEP = 3		# in iambics, the step at which the two algorithms divide
dummyevent = wx.MouseEvent(wx.wxEVT_LEFT_UP)	# to call button directly

class ScandroidFrame(wx.Frame):
## - - - - - initializations
    def __init__(self, parent, ID, title):
        wd, ht, fnt = self._setSizes()
        wx.Frame.__init__(self, parent, ID, title, size=(wd, ht))
        # our panels, top to bottom
        self.ScanLine = MyScanTC(self, fnt)
        self.TextLine = MyLineTC(self, fnt)
        self.NotesWindow = MyNotesTC(self, fnt)
        self.WholeText = MyTextSTC(self, -1)
        # line numbers
        self.WholeText.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.WholeText.SetMarginType(1, stc.STC_MARGIN_SYMBOL)
        self.WholeText.SetMarginWidth(0, 1)
        self.WholeText.SetMarginWidth(1, 10)
        self.WholeText.StyleSetBackground(stc.STC_STYLE_LINENUMBER, (246,246,246))
        # initialize our data members and helpers
        self.SM = ScansionMachine()		# central engine of scansion work
        self.E = Explainer(self.NotesWindow)
        self.lineNum = 0			# where to put its scansion when done
        self.loaddir = ''			# where user gets textfiles to Load
        self.Metron = 2				# initial assumption:
        self.LineFeet = 5			#   iambic pentameter
        self.LineFeetSet = True
        self.SM.SetLineFeet(5, True)
        self.SetupGUI()			# buttons, menus . . .
        self.SetupScansionSteps()		# inc some more data items
        self.WholeText.DisplayText(InitialText)		# as a startup . . .
        self.WholeText.SetReadOnly(0)	# but allow editing
        self.EnableScanButtons(False)
        wx.FutureCall(100, self.WholeText.SetFocus)	# Robin Dunn's fix!
        self.leadSpaceRE = sre.compile(r'[ |\t]+')
        # icon
        ico = robIcon.getrobIcon()
        self.SetIcon(ico)	

    def _setSizes(self):
        screensize = wx.GetDisplaySize()
        # set and return width, height, fontsize
        if screensize[1] > 800: return (650, 750, 13)
        else: return (600, 650, 12)

    def SetupGUI(self):
        """Establish all visible elements of the program's main window.

        That's two separate rows of buttons plus menus. The text fields
        have already beeen created in the __init__; here they get put into
        sizers with the rest and displayed.
        """
        self.ScanBtn = wx.Button(self, 1001, label="Scan", size=(-1, -1))
        self.StepBtn = wx.Button(self, 1002, label="Step", size=(-1, -1))
        self.SaveBtn = wx.Button(self, 1003, label="Save", size=(-1, -1))
        self.CancelScanBtn = wx.Button(self, 1008, label="Cancel", size=(-1,-1))
        self.LoadBtn = wx.Button(self, 1004, label="Load New", size=(-1, -1))
        self.TypeBtn = wx.Button(self, 1005, label="Type New", size=(-1, -1))
        self.SaveTxtBtn = wx.Button(self, 1006, label="Save Text", size=(-1, -1))
        self.ReloadBtn = wx.Button(self, 1007, label="Reload Dict", size=(-1, -1))
        self.StatBar = wx.StatusBar(self, -1)
        self.SetStatusBar(self.StatBar)
        self.StatBar.SetFieldsCount(2)
        self.StatBar.SetStatusWidths([-1, -3])
        self.UpdateStatusBar(self.Metron, self.LineFeet, self.LineFeetSet)
                # our sizers
        outersizer = wx.BoxSizer(wx.VERTICAL)
        toplinesizer = wx.BoxSizer(wx.VERTICAL)
        topbtnsizer = wx.BoxSizer(wx.HORIZONTAL)
        logsizer = wx.BoxSizer(wx.VERTICAL)
        stcsizer = wx.BoxSizer(wx.VERTICAL)
        btmbtnsizer = wx.BoxSizer(wx.HORIZONTAL)
            # put stuff in sizers
        toplinesizer.Add(self.ScanLine, 1, wx.EXPAND)
        toplinesizer.Add(self.TextLine, 1, wx.EXPAND)
        topbtnsizer.Add((10, 10), 0); topbtnsizer.Add(self.ScanBtn, 0)
        topbtnsizer.Add((10, 10), 0); topbtnsizer.Add(self.StepBtn, 0)
        topbtnsizer.Add((10,10), 0); topbtnsizer.Add(self.SaveBtn, 0)
        topbtnsizer.Add((10,10), 0); topbtnsizer.Add(self.CancelScanBtn, 0)
        logsizer.Add(self.NotesWindow, 1, wx.EXPAND)
        stcsizer.Add(self.WholeText, 1, wx.EXPAND)
        btmbtnsizer.Add((10,10),0); btmbtnsizer.Add(self.LoadBtn, 0)
        btmbtnsizer.Add((10,10),0); btmbtnsizer.Add(self.TypeBtn, 0)
        btmbtnsizer.Add((10,10),0); btmbtnsizer.Add(self.ReloadBtn, 0)
        btmbtnsizer.Add((10,10),0); btmbtnsizer.Add(self.SaveTxtBtn, 0)
        outersizer.Add((10, 10), 0); outersizer.Add(toplinesizer, 0, wx.EXPAND)
        outersizer.Add((10, 10), 0); outersizer.Add(topbtnsizer, 0, wx.ALIGN_CENTER)
        outersizer.Add((10, 10), 0); outersizer.Add(logsizer, 3, wx.EXPAND)
        outersizer.Add((10, 10), 0); outersizer.Add(stcsizer, 4, wx.EXPAND)
        outersizer.Add((10, 10), 0); outersizer.Add(btmbtnsizer, 0, wx.ALIGN_CENTER)
        outersizer.Add((10,10), 0)
        self.SetSizer(outersizer)
        self.Layout()
            # the Bindings for our buttons, sending the real work out elsewhere
        self.Bind(wx.EVT_BUTTON, self.OnLoadBtn, id=1004)
        self.Bind(wx.EVT_BUTTON, self.OnStepButton, id=1002)
        self.Bind(wx.EVT_BUTTON, self.OnScanButton, id=1001)
        self.Bind(wx.EVT_BUTTON, self.OnSaveButton, id=1003)
        self.Bind(wx.EVT_BUTTON, self.OnCancelBtn, id=1008)
        self.Bind(wx.EVT_BUTTON, self.OnSaveAllBtn, id=1006)
        self.Bind(wx.EVT_BUTTON, self.OnTypeBtn, id=1005)
        self.Bind(wx.EVT_BUTTON, self.OnReloadBtn, id=1007)
            # our menus, mostly to do the same tasks faster
        menuBar = wx.MenuBar()
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(101, "&Load text file\tCtrl+L")
        self.fileMenu.Append(102, "T&ype text\tCtrl+Y")
        self.fileMenu.Append(104, "&Reload dictionary")
        self.fileMenu.Append(103, "&Save scanned text\tCtrl+S")
        # THE FOLLOWING FIXES MAC-SPECIFIC CLOSING BEHAVIOR
        item = self.fileMenu.Append(wx.ID_EXIT,'E&xit','Terminate the program')
        self.Bind(wx.EVT_MENU, self.OnClose, item)
        menuBar.Append(self.fileMenu, "File")
        self.editMenu = wx.Menu()
        self.editMenu.Append(301, "Select &all\tCtrl+A")
        self.editMenu.Append(302, "&Copy to clipboard\tCtrl+C")
        self.editMenu.Append(304, "&Find in text\tCtrl+F")
        self.editMenu.Append(303, "turn ON line numbers")
        self.lineNumsVisible = False
        menuBar.Append(self.editMenu, "Edit")
        self.scanMenu = wx.Menu()
        self.scanMenu.Append(201, "S&tep\tCtrl+T")
        self.scanMenu.Append(202, "Scan\tCtrl+2")
        self.scanMenu.Append(203, "S&ave line\tCtrl+3")
        self.scanMenu.Append(207, "Force anapestics")
        self.scanMenu.Append(208, "Force iambics")
        self.scanMenu.Append(204, "Force iambic alg. 1")
        self.scanMenu.Append(205, "Force iambic alg. 2")
        self.scanMenu.Append(206, "Next unscanned line\tCtrl+1")
        self.scanMenu.Append(220, "(Scan All)")		# FOR TESTING ONLY
        menuBar.Append(self.scanMenu, "Scan")
        # arcane boilerplate for cross-platform Help and About
        HelpMenu = wx.Menu()
        HelpMenu.Append(wx.ID_ABOUT, "About the Scandroid")
        menuBar.Append(HelpMenu, "&Help")
        app.SetMacHelpMenuTitleName("&Help")
        # more help menu stuff goes here, someday; but user needs manual anyway
            # note: bind menu to same as btn; not using evt anyway
            # NB: no menu or key for "cancel"; eventually, Esc?
        self.Bind(wx.EVT_MENU, self.ShowAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnLoadBtn, id=101)
        self.Bind(wx.EVT_MENU, self.OnTypeBtn, id=102)
        self.Bind(wx.EVT_MENU, self.OnReloadBtn, id=104)
        self.Bind(wx.EVT_MENU, self.OnSaveAllBtn, id=103)
        self.Bind(wx.EVT_MENU, self.OnStepButton, id=201)
        self.Bind(wx.EVT_MENU, self.OnScanButton, id=202)
        self.Bind(wx.EVT_MENU, self.OnSaveButton, id=203)
        self.Bind(wx.EVT_MENU, self.ForceAlg, id=204)
        self.Bind(wx.EVT_MENU, self.ForceAlg, id=205)
        self.Bind(wx.EVT_MENU, self.GotoNextUnscannedLine, id=206)
        self.Bind(wx.EVT_MENU, self.ForceMetron, id=207)
        self.Bind(wx.EVT_MENU, self.ForceMetron, id=208)
        self.Bind(wx.EVT_MENU, self.ScanEverything, id=220)	# FOR TESTING
        self.Bind(wx.EVT_MENU, self.SelectAll, id=301)
        self.Bind(wx.EVT_MENU, self.CopyToClipboard, id=302)
        self.Bind(wx.EVT_MENU, self.ShowHideLineNums, id=303)
        self.Bind(wx.EVT_MENU, self.OnFindText, id=304)
        self.Bind(wx.EVT_FIND, self.OnFind)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFind)
        self.SetMenuBar(menuBar)
        self.AboutBox()

    def OnClose(self, item):
        self.Destroy()
#        wx.GetApp().ExitMainLoop()

    def SetupScansionSteps(self, iambic=True, algorithm1=True):
        """Match a sequence of step names with function names.

        By default, initialize the sequence as per iambic Algorithm 1. It can 
        be switched to Algorithm 2 for each iambic line any time before 
        FORKSTEP (caller is responsible for checking this): at random, as 
        forced by the user, or as a switch in desperation when an alg fails.
        Steps after 1 can be switched from iambic to anapestic.
        Switch arguments allow these options.
        """
        self.Steps = [('SYLLABLES', self.SM.ShowSyllables), \
                      ('PRELIMINARY MARKS', self.SM.ShowLexStresses)]
        if iambic:
            self.Steps.append(('CHOOSE ALGORITHM', self.SM.ChooseAlgorithm))
            if algorithm1:
                self.Steps.append(('FIRST TESTS', self.SM.WeirdEnds))
                self.Steps.append(('FOOT DIVISION', self.SM.TestLengthAndDice))
            else:
                self.Steps.append(('LONGEST NORMAL', self.SM.TryREs))
                self.Steps.append(('CLEAN UP ENDS', self.SM.CleanUpRE))
            self.Steps.append(('PROMOTIONS', self.SM.PromotePyrrhics))
            self.Steps.append(('ANALYSIS', self.SM.HowWeDoing))
        else:		# anapestic steps
            self.Steps.append(('ADJUST STRESSES', self.SM.GetBestAnapLexes))
            self.Steps.append(('ANAPESTICS: LINE END', self.SM.AnapEndFoot))
            self.Steps.append(('ANAPESTICS: FOOT DIVISION', self.SM.AnapDivideHead))
            self.Steps.append(('ANAPESTICS: ANALYSIS', self.SM.AnapCleanUpAndReport))

## - - - - - menu and keystroke methods mainly doing simple display stuff
    def ShowAbout(self, evt): self.AboutBox()    
    def AboutBox(self):
        pythonver = 'Python ver %s' % sys.version.split()[0]
        wxversion = 'wxPython ver %s' % wx.__version__
        msg = abouttxt + '\n\n' + pythonver + '\n' +wxversion
        dlg = wx.MessageDialog(self, message=msg, caption="the Scandroid",
                               style=wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def ClearWorkBoxes(self):
        """Clear text and scansion fields, not Notes window; disable buttons.

        Do not clear Notes window; we want it to stay, for example, after a
        scansion has been saved with OnSaveBtn(). We disable the Save button
        for now, because there's nothing yet to save."""
        self.TextLine.Clear()
        self.ScanLine.Clear()
        self.SaveBtn.Disable()

    def EnableScanButtons(self, enable=True):
        """Enable/disable buttons except Save (enabled after there's something to save)"""
        self.ScanBtn.Enable(enable)
        self.StepBtn.Enable(enable)
        self.CancelScanBtn.Enable(enable)
        self.scanMenu.Enable(201, enable)
        self.scanMenu.Enable(202, enable)
        self.scanMenu.Enable(204, enable)
        self.scanMenu.Enable(205, enable)
        if not enable:
            self.SaveBtn.Enable(False)
            self.scanMenu.Enable(203, False)

    def UpdateStatusBar(self, metron=2, linefeet=5, linefeetset=True):
        if metron == 2: mfieldtxt = "metron: IAMBIC"
        else: mfieldtxt = "metron: ANAPESTIC"
        if linefeetset: footfieldtxt = "feet per line: " + lineLengthName[linefeet]
        else: footfieldtxt = "feet per line: VARIABLE"
        self.SetStatusText(mfieldtxt, 0)
        self.SetStatusText(footfieldtxt, 1)

    def ShowHideLineNums(self, evt):
        if self.lineNumsVisible:
            self.WholeText.SetMarginWidth(0,1)
            self.WholeText.SetMarginWidth(1,10)
            self.Refresh()
            self.editMenu.SetLabel(303, "turn ON line numbers")
            self.lineNumsVisible = False
        else:
            totlines = self.WholeText.GetLineCount()
            width = self.WholeText.TextWidth(stc.STC_STYLE_LINENUMBER,
                                             str(totlines) + ' ')
            self.WholeText.SetMarginWidth(0, width)
            self.WholeText.SetMarginWidth(1, 20)
            self.Refresh()
            self.editMenu.SetLabel(303, "turn OFF line numbers")
            self.lineNumsVisible = True

    def CopyToClipboard(self, evt):
        which = self.FindFocus()
        which.CopySelection()
        if which == self.NotesWindow:
            end = self.NotesWindow.GetLastPosition()
            self.NotesWindow.SetSelection(end, end)
        else: which.SetSelection(0, 0)

    def SelectAll(self, evt):
        which = self.FindFocus()
        if which == self.WholeText:
            self.WholeText.SetSelection(0, self.WholeText.GetLength())
        elif which == self.NotesWindow:
            self.NotesWindow.SetSelection(-1, -1)

    def OnFindText(self, evt):
        """Put up Find dialog in response to menu/keystroke command.

        This uses wxPython's default dialog, which is a little ugly (no default
        button! up/down option not supported by STC!).
        """
        data = wx.FindReplaceData()
        dlg = wx.FindReplaceDialog(self, data, "Find")
        dlg.data = data
        dlg.Show(True)
        self.foundTextPos = 0

    def OnFind(self, evt):
        """Implement search in Text panel, from command in Find dialog.

        We set case and whole-word flags for the STC search; nothing in that
        corresponds to the up/down flag of the wxPython Find dialog. We begin
        the search at the current position each new time the dialog is called
        up; within (non-modal) dialog runs, searches are incremental, forward
        throughout the text.
        """
        if evt.GetEventType() in (wx.wxEVT_COMMAND_FIND,
                                  wx.wxEVT_COMMAND_FIND_NEXT):
            fnd = evt.GetFindString()
            flags = evt.GetFlags()
            stcflags = 0
            if flags & wx.FR_MATCHCASE: stcflags |= stc.STC_FIND_MATCHCASE
            if flags & wx.FR_WHOLEWORD: stcflags |= stc.STC_FIND_WHOLEWORD
            if self.foundTextPos: findstart = self.foundTextPos
            else: findstart = self.WholeText.GetCurrentPos()
            self.foundTextPos = self.WholeText.FindText(findstart + 1,
                                                        self.WholeText.GetLength(), fnd, stcflags)
            self.WholeText.SetSelection(self.foundTextPos, self.foundTextPos +
                                        len(fnd))

    def ErrorMessage(self, function, msg=''):	## All-purpose emergency bail-out
        line1 = "the Scandroid has encountered an internal error.\n"
        line2 = "It would be helpful if you reported it to me at \n"
        line3 = "charles.hartman@conncoll.edu.\n\n"
        line4 = "Please include the verse line on which it occurred,\n"
        line5 = "and the following function name:\n\n\t\t"
        line6 = function.__name__
        if not msg: message = ''.join([line1, line2, line3, line4, line5,
                                       function.__name__])
        else: message = ''.join([line1, line2, line3, line4, line5,
                                 function.__name__, '\n\n\t\t', msg])
        dlg = wx.MessageDialog(self, message, "Internal Error", wx.OK |
                               wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()

## - - - - - display routines: scansion is simple; line is big initializer
    def ShowScanLine(self, marks, showAlg=False):
        """Clear scansion field and display a new scansion in it.

        Default-false argument adds a tag to each scansion noting which iambic
        algorithm produced it. Strictly for testing purposes.
        """
        self.ScanLine.Clear()		# get rid of e.g. intermediate results
        if showAlg and self.Metron == 2: 	# meaningless while anapestics
            marks += '[alg ' + `self.whichAlgorithm` + ']'
        self.ScanLine.AppendText(marks)

    def ShowTextLine(self, txt, num): 
        """Initialize conditions for scansion and display selected line.

        This is where news arrives, here at the top level, of a new line to be
        scanned, so quite a lot is initialized, internally and visibly.
        """
        self.ClearWorkBoxes()		# no old lines or previous scansions
        self.NotesWindow.Clear()		# nor old notes
        self.WholeText.SetReadOnly(1)	# no edits while scanning (till Save)
        self.EnableScanButtons()
        self.leadspace = self.leadSpaceRE.match(txt)	# for Save btn
        self.linetext = txt.strip()
        self.TextLine.AppendText(self.linetext)		# put selected line up in the box
        self.lineNum = num			# where to put scansion when done
        self.CurrentStep = 0			# (re)start the procedure
        if self.Metron == 2:			# iambic-only preparations
            if random.randint(0,1): self.whichAlgorithm = 1	# begin at random
            else: self.whichAlgorithm = 2
            self.SetupScansionSteps(iambic=True, algorithm1=(self.whichAlgorithm==1))
            self.OneIambicAlgFailed = False
        #self.E.Explain("Press Step to inch through, Scan to rush")
        self.E.Explain("\n\n\"%s\"" % self.linetext)
        try:
            self.SM.ParseLine(self.linetext)
        except:
            self.ErrorMessage(self.SM.ParseLine, self.linetext)

## - - - - - button & other routines for treatment of individual lines
    def OnStepButton(self, evt):
        """Perform next scansion setp in self.Steps (indexed by self.CurentStep)"""
        if self.CurrentStep == len(self.Steps) - 1:
            self.StepBtn.Disable()
            self.ScanBtn.Disable()
        if self.CurrentStep >= len(self.Steps): 
            return		# end of steps, stop
        self.SaveBtn.Enable(True)			# now there'll be something to save
        self.scanMenu.Enable(203, True)
        #if self.CurrentStep == 0: self.NotesWindow.Clear()
        self.NotesWindow.AppendText('\n\n')
        self.E.Explain(self.Steps[self.CurrentStep][0] + '  ')		# show header
        try:		# this line is THE distributor of work to the SM
            (scanline, result) = self.Steps[self.CurrentStep][1](self.E)
        except:
            self.ErrorMessage(self.Steps[self.CurrentStep][1])
            self.CurrentStep = len(self.Steps)		# bail out!
            return
        # sneaky use of result for iambic ChooseAlgorithm step
        if self.CurrentStep == 2 and self.Metron == 2:
            if result: self.whichAlgorithm = 1			# arbitrary T/F code to put alg.
            else: self.whichAlgorithm = 2			#   into succeed/fail return
            # substitute failure test; only for too-short lines if linefeet not set
            if scanline:
                self.SetupScansionSteps(iambic=True, algorithm1=(self.whichAlgorithm == 1))
                self.ShowScanLine(scanline)
                self.scanMenu.Enable(204, True)
                self.scanMenu.Enable(205, True)
                self.CurrentStep += 1
            else: self.CurrentStep = len(self.Steps)		# stop
        else:				# ALL steps except iambic ChooseAlgorithm
            if scanline: 
#                self.ShowScanLine(scanline, showAlg=True)		# FOR TESTING ONLY!!
                self.ShowScanLine(scanline)
            if not result:		# some step FAILED
                if self.Metron == 2 and self.OneIambicAlgFailed:
                    self.E.Explain("\n\nAbject failure of both iambic methods!\n")
                    self.ShowScanLine(self.SM.P.GetScanString() + '    ***')
                    self.CurrentStep = len(self.Steps)		# quit
                elif self.Metron == 3:
                    self.ShowScanLine(self.SM.P.GetScanString() + '    ***')
                    self.CurrentStep = len(self.Steps)		# quit
                else:
                    self.OneIambicAlgFailed = True	# orig. set in ShowTextLine
                    scanline = self.SM.RestartNewIambicAlg(self.E, self.whichAlgorithm,
                                                           scanline)
                    self.ShowScanLine(scanline)
                    if self.whichAlgorithm == 1: self.whichAlgorithm = 2
                    else: self.whichAlgorithm = 1
                    self.SetupScansionSteps(iambic=True, algorithm1=(self.whichAlgorithm == 1))
                    self.CurrentStep = FORKSTEP
            else:
                self.scanMenu.Enable(204, False)
                self.scanMenu.Enable(205, False)
                self.CurrentStep += 1

    def OnScanButton(self, evt):
        """Perform all remaining steps in scansion without intervention"""
        laststep = len(self.Steps)		# tricky; we may restart if an algorithm fails
        step = self.CurrentStep		# so can't use
        while step < laststep:		#  'for step in range(len(self.Steps))'
            self.OnStepButton(evt)
            step = self.CurrentStep

    def GotoNextUnscannedLine(self, evt):
        if self.WholeText.GetNextUnscannedLine(): return True	# not used!
        else: return False			# for test routine ScanEverything only

    def OnSaveButton(self, evt):
        """Insert currrent-stage scansion into Text panel above line it belongs to"""
        currentscansion = self.ScanLine.GetValue()
        self.WholeText.SetReadOnly(0)	# allow editing till ShowTextLine
        self.WholeText.SetFocus()		# and even encourage it
        if self.leadspace:
            currentscansion = self.leadspace.group() + currentscansion
        self.WholeText.PutLineBack(self.lineNum, currentscansion)	# make it so
        self.ClearWorkBoxes()		# clarify status, flag to allow editing
        self.EnableScanButtons(False)

    def ScanEverything(self, evt):
        while 1:
            if not self.GotoNextUnscannedLine(evt): 
                break
            self.OnScanButton(evt)
            self.OnSaveButton(evt)

    def OnCancelBtn(self, evt):
        """Return all to condition before line was selected"""
        self.ClearWorkBoxes()
        self.WholeText.SetReadOnly(0)		# allow editing again
        p = self.WholeText.GetCurrentPos()
        self.WholeText.SetSelection(p, p)
        self.EnableScanButtons(False)
        self.NotesWindow.Clear()			# unlike save!

    def RestartLineAfterCancel(self):
        """Zero the conditions for scansion of same line as was in process

        This is in response to need to rebegin after a dict word has been edited
        (don't know if it will be needed anywhere else--modular design is falling
        apart!). Assume that self.lineNum and self.linetext are current; don't
        change the algorithm, however it was chosen.
        """
        self.ClearWorkBoxes()
        self.NotesWindow.Clear()
        self.TextLine.AppendText(self.linetext)
        self.WholeText.SetReadOnly(1)
        self.EnableScanButtons()
        self.CurrentStep = 0
        # let's leave the Algorithm alone
        self.OneIambicAlgFailed = False
        self.SM.ParseLine(self.linetext)

## - - - - - button routines for handling text (files etc)
    def OnLoadBtn(self, evt):
#        wildcard = 'All files (*.*) | *.*' WHY DOESN'T THIS WORK ANY MORE??
        wildcard = '*.*'
        if not self.loaddir: defDir = os.getcwd()
        else: defDir = self.loaddir
        dlg = wx.FileDialog(self, message="Choose a plain text file",
                            defaultDir=defDir, defaultFile="",
                            wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.ClearWorkBoxes()
            self.NotesWindow.Clear()
            f = open(dlg.GetPath(), 'rU')
            self.loaddir = dlg.GetPath()
            # retain line-numbering status, but refigure width of margin
            if self.lineNumsVisible:
                self.ShowHideLineNums(dummyevent)
                resetnums = True
            else: resetnums = False
            self.WholeText.DisplayText(f.read())
            if resetnums: self.ShowHideLineNums(dummyevent)
            f.close()
            dlg.Destroy()
            self.DeduceParameters()		# sets self.LineFeet, .Metron, .LineFeetSet (T/F)
        else: dlg.Destroy()

    def OnSaveAllBtn(self, evt):
        dlg = wx.FileDialog(self, message="File to save scanned text",
                            defaultDir=os.getcwd(), defaultFile='scansion', wildcard="*.txt",
                            style=wx.SAVE | wx.CHANGE_DIR | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            defenc = wx.GetDefaultPyEncoding()
            f = open(dlg.GetPath(), 'w')
#            f = open(dlg.GetPath(), 'wU')

            textToWrite = self.WholeText.GetText()
            textToWrite = textToWrite.encode(defenc)
            f.write(textToWrite)
            #for c in range(self.WholeText.GetLineCount()):
                #f.write(self.WholeText.GetLine(c))
            f.close()
        dlg.Destroy()

    def OnTypeBtn(self, evt):
        # safety check, if any scansions?? ("do you want to save...")
        self.ClearWorkBoxes()
        self.WholeText.ClearAll()
        self.WholeText.SetFocus()
        self.NotesWindow.Clear()
        s1 = 'Type lines of verse into the main text window,'
        s2 = '\nor press Load button to open a file of text'
        self.E.Explain(''.join([s1, s2]))
        self.Metron = 2
        self.LineFeetSet = False
        self.LineFeet = 5
        self.UpdateStatusBar(self.Metron, self.LineFeet, self.LineFeetSet)
        self.SM.SetLineFeet(5, False)
        self.SetupScansionSteps()		# restore iambic steps

    def OnReloadBtn(self, evt):
        del(self.SM.SD.Dict)
        self.SM.SD.Dict = {}
        self.SM.SD.LoadDictionary()
        self.E.Explain("\n\n(default dictionary reloaded)\n")

## - - - - - establish major context for scansion work
    def DeduceParameters(self, forceiamb=False, forceanap=False):
        """When text is loaded, read multiple lines; find metron and linelength.

        Read all lines (up to a dozen); call SM to try a quick scansion of each as 
        iambic (both algorithms, but without stress-resolution options) and as 
        anapestic to decide consistent metron (2 or 3). Guess line-length in feet 
        under each assumption; if close average, declare constant length. 
        Set three flags as distributable globals: Metron, LineFeet, and 
        LineFeetSet (True *or* False). Metron is always set (for better or worse).

        Added "force" flags so this will be callable from ForceMetron. With one
        or the other set, skip non-pertinent parts.
        """
        textlines = self.WholeText.GetLineCount()
        iambLens = []
        anapLens = []
        iambCompTotal = anapCompTotal = 0
        linesToSample = 12
        theLengths = 0  #initialize the length variable
        i = 0		# sample min of all lines (textlines) or linesToSample (break)
        self.SM.SetLineFeet(5, False)		# unset "linefeetset" for tests
        for linex in range(textlines):	# parse each line, try various scansions
            if i >= linesToSample: break
            line = self.WholeText.GetLine(linex)
            if len(line) < 5 or line[:1] == '\t': 		# can't use line[0] with or!
                continue	# skip a title or other non-verse
            i += 1	# count of "real" lines
            self.SM.ParseLine(line)
            if not forceanap:
                try:
                    (score, length) = self.SM.ChooseAlgorithm(self.E, deducingParams=True)
                except: self.ErrorMessage(self.SM.ChooseAlgorithm, self.SM.P.GetMarks())
                iambCompTotal += score
                if score < 100: iambLens.append(length)
            if not forceiamb:
                try:
                    (score, length) = self.SM.GetBestAnapLexes(self.E, deducingParams=True)
                except: self.ErrorMessage(self.SM.GetBestAnapLexes, self.SM.P.GetMarks())
                anapCompTotal += score
                if score < 100: anapLens.append(length)
        if not forceiamb and not forceanap:
            if iambCompTotal < anapCompTotal:
                self.Metron = 2
                theLengths = iambLens
                self._setLineLengthIfPossible(theLengths) # The LineLength function was being called prior
            else:                                         # to theLengths being initialized,
                self.Metron = 3                           # which broke the force iamb as well as LineLength
                theLengths = anapLens
                self._setLineLengthIfPossible(theLengths)
            self.SetupScansionSteps(iambic=(self.Metron==2))
        if not forceiamb and not forceanap:
            self.E.ExpDeduceParams(self.Metron, self.LineFeet, self.LineFeetSet)
        self.SM.SetLineFeet(self.LineFeet, self.LineFeetSet)
        self.UpdateStatusBar(self.Metron, self.LineFeet, self.LineFeetSet)

    def _setLineLengthIfPossible(self, theLengths):
        """If there's a clear average, set length and lengthset"""
        total = sum(theLengths)
        if not total or not theLengths:
            self.E.Explain("\nFAILED to determine verse parameters\n\n")
            return
        (frac, integ) = modf(float(total) / len(theLengths))
        if frac > 0.8:				# probably about right
            self.LineFeet = int(integ) + 1
            self.LineFeetSet = True
        elif frac < 0.2:
            self.LineFeet = int(integ)
            self.LineFeetSet = True
        else: self.LineFeetSet = False

    def ForceAlg(self, evt):
        """Menu-choice to override automatic choice of algorithm for iambics.

        This would have no effect (be cancelled out) if chosen before the Choose
        Algorithm step. After just past that step it would produce chaos because
        of conflicting work on the line. To enforce this narrow window, the menu item
        and keypress are disabled except at the end of that crucial step.
        """
        which = evt.GetId()
        if which == 204:
            self.whichAlgorithm = 1
            self.E.Explain("\n\nAlgorithm 1 forced")
        else: 
            self.whichAlgorithm = 2
            self.E.Explain("\n\nAlgorithm 2 forced")
        self.SetupScansionSteps(iambic=True, algorithm1=(self.whichAlgorithm == 1))

    def ForceMetron(self, evt):
        """Menu-only choice to force scansion iambic/anapestic till next Load."""
        self.OnCancelBtn(dummyevent)	# before msg or will be erased
        which = evt.GetId()
        if which == 207:
            self.Metron = 3
            self.E.Explain("\nForced switch to anapestic scansion\n")
            self.SetupScansionSteps(iambic=False)
            self.DeduceParameters(forceanap=True)
        else:
            self.Metron = 2
            self.E.Explain("\nForced switch to iambic scansion\n")
            self.SetupScansionSteps(iambic=True)
            self.DeduceParameters(forceiamb=True)
        if self.LineFeetSet:
            self.E.Explain("Implied line length is %s feet\n\n" % self.LineFeet)
        else: self.Explain("Implied line length is variable\n\n")

# - - - - - - - - - - - end of ScandroidFrame class - - - - - - - - - - - - - - - - - - - - - -

profiling = False
if profiling: import profile

# app = wx.PySimpleApp()
app = wx.App(False)
appframe = ScandroidFrame(None, -1, "the Scandroid")
appframe.Center()
appframe.Show()
if profiling:
    profile.run('app.MainLoop()', 'ScandroidProf')
else:
    app.MainLoop()
# Scandroid.py 1.5
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
# including the menus and button-presses that control everything.
# The Frame owns a ScansionMachine that does all the interesting work.

# Version 1.5 (somewhat arbitrarily numbered) is the first revision in about
# seven years.  The occasion was Jim O'Connor's coming on board to fix
# up the old code. 

import wx
import string, os, sys, sre
import random
import robIcon
from math import modf
from scanstrings import *		# some global texts & the Explainer
from scanstc import *			# editors for subwindows
from scanfuncs import *			# the Scansion Machine
from datetime import *          # used for saving scansions

import traceback

# global to this module:
FORKSTEP = 3		# in iambics, the step at which the two algorithms divide
dummyevent = wx.MouseEvent(wx.wxEVT_LEFT_UP)		# to call button directly

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
        self.WholeText.StyleSetBackground(stc.STC_STYLE_LINENUMBER,
                                                      (246,246,246))
        # initialize our data members and helpers
        self.SM = ScansionMachine()		# central engine of scansion work
        self.E = Explainer(self.NotesWindow)
        self.lineNum = 0			# where to put its scansion when done
        self.Metron = 2				# initial assumption:
        self.LineFeet = 5			#   iambic pentameter
        self.LineFeetSet = True
        self.SM.SetLineFeet(5, True)
        self.forceiamb, self.forceanap = False, False
        self.SetupGUI()			# buttons, menus . . .
        self.SetupScansionSteps()		# inc some more data items
        self.WholeText.DisplayText(InitialText)		# as a startup . . .
        self.loadedtext = True
        self.WholeText.SetReadOnly(0)	# but allow editing
        self.DisableAllScanButtons()
        self.loadPath, self.savePath = '', ''
        wx.FutureCall(100, self.WholeText.SetFocus)	# Robin Dunn's fix!
        self.leadSpaceRE = sre.compile(r'[ |\t]+')
        self.newFindDialog, self.oldFindDialog = [None for i in range(2)]
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
        
        # -- CONSTANTS --
        SIZE = wx.Size(10, 10)
        BTNSIZE = wx.Size(-1, -1)
        
        # -- CREATION OF BUTTONS --
        lbls = ['Scan', 'Step', 'Store', 'Cancel',
                'Load New', 'Type New', 'Save Text', 'Save Scansion']
                
        tips = ['Perform all scansion steps on the selected line.',
                'Go to the next stage in the scanning process.',
                'Store the current scansion into the text panel.',
                'Cancel the scansion of the current line.',
                'Load a new plain text file into the Scandroid.',
                'Clear current text and type new text into the Scandroid.',
                'Save typed text to a new plain text file.',
                'Save line scansion and notes to a generated file.']
                
        self.btns = []
        for i, lbl in enumerate(lbls):
           button = wx.Button(self, i + 1001, label = lbl, size = BTNSIZE)
           button.SetToolTipString(tips[i])
           self.btns.append(button)
        
        # -- CREATION OF BUTTON NAME & ID DICTIONARY --
        self.btnIDs = {}
        for btn in self.btns:
            self.btnIDs[btn.GetLabel()] = btn.GetId()
        
        # -- CREATION OF STATUS BAR --
        sb = wx.StatusBar(self, -1)
        sb.SetFieldsCount(3)             # initial dummy field prevents
        sb.SetStatusWidths([0, -1, -3])  # metron from being overwritten
        
        # -- SETTING OF STATUS BAR --
        self.SetStatusBar(sb)
        self.UpdateStatusBar(self.Metron, self.LineFeet, self.LineFeetSet)

        # -- CREATION OF MAIN SIZERS (outer, top line, log, and stc sizers) --
        mainSizers = [wx.BoxSizer(wx.VERTICAL) for i in range(4)]
        initItems = [self.ScanLine, self.TextLine,
                     self.NotesWindow, self.WholeText]
        for i, item in enumerate(initItems):
            if not i: i = 1
            mainSizers[i].Add(item, 1, wx.EXPAND)             
        
        # -- CREATION OF BUTTON SIZERS (top row and bottom row)
        btnSizers = [wx.BoxSizer(wx.HORIZONTAL) for i in range(2)]
        for i in range(len(self.btns)):
            if i < len(self.btns) / 2:
                btnSizers[0].Add(SIZE, 0)
                btnSizers[0].Add(self.btns[i])
            else:
                btnSizers[1].Add(SIZE, 0)
                btnSizers[1].Add(self.btns[i])
        
        # -- ADDING OF ALL INNER SIZERS TO SINGLE OUTER SIZER --
        innerSizers = [[mainSizers[1], 0, wx.EXPAND],
                       [btnSizers[0], 0, wx.ALIGN_CENTER],
                       [mainSizers[2], 3, wx.EXPAND],
                       [mainSizers[3], 4, wx.EXPAND],
                       [btnSizers[1], 0, wx.ALIGN_CENTER]]
        for i, s in enumerate(innerSizers):
            mainSizers[0].Add(SIZE, 0)
            mainSizers[0].Add(s[0], s[1], s[2])
        mainSizers[0].Add(SIZE, 0)
        
        # -- SETTING OF FRAME SIZER AND LAYOUT --
        self.SetSizer(mainSizers[0])
        self.Layout()
        
        # -- BINDING OF BUTTON HANDLERS --
        btnHandlers = [self.OnScanBtn, self.OnStepBtn,
                       self.OnStoreBtn, self.OnCancelBtn,
                       self.OnLoadBtn, self.OnTypeBtn,
                       self.OnSaveTextBtn, self.OnSaveScanBtn]
        for i, h in enumerate(btnHandlers):
            self.Bind(wx.EVT_BUTTON, btnHandlers[i], id = i + 1001)
        
        # -- CREATION OF MENU BAR AND MENUS (FILE, EDIT, and SCAN) --
        menuBar = wx.MenuBar()
        menuTitles = ['&File', '&Edit', '&Scan']
        menuItems = [['L&oad text file\tCtrl+O',
                      'Type &new\tCtrl+N',
                      '&Save typed text\tCtrl+S',
                      'Save scansion and notes\tCtrl+4'],
                     ['Select &all\tCtrl+A', '&Copy\tCtrl+C',
                      'Cut\tCtrl+X', 'Paste\tCtrl+V',
                      '&Find in text\tCtrl+F',
                      'Toggle &line numbers\tCtrl+L'],
                     ['Scan\tCtrl+2', 'S&tep\tCtrl+T',
                      'Store\tCtrl+3', 'Canc&el\tCtrl+E',
                      'Force anapestics', 'Force iambics',
                      'Force iambic alg. 1', 'Force iambic alg. 2',
                      'Next unscanned line\tCtrl+1', '(Scan All)']]
                       # (Scan All) is for testing only!
                      
        self.menus = []
        for i, title in enumerate(menuTitles):
            self.menus.append(wx.Menu())
            for j, item in enumerate(menuItems[i]):
                self.menus[i].Append((i + 1) * 100 + (j + 1), item)
            menuBar.Append(self.menus[i], title)
        
        # -- CREATION OF MENU ITEM NAME & ID DICTIONARY --
        self.menuItemIDs = {}
        for menu in self.menus:
            for item in menu.GetMenuItems():
                self.menuItemIDs[item.GetLabel()] = item.GetId()

        # -- CREATION OF HELP MENU --
        HelpMenu = wx.Menu()
        HelpMenu.Append(wx.ID_ABOUT, "About the Scandroid", ' ')
        menuBar.Append(HelpMenu, "&Help")
        app.SetMacHelpMenuTitleName("&Help")

        # -- BINDING OF MENU HANDLERS --  
        menuHandlers = [[self.OnLoadBtn, self.OnTypeBtn,
                         self.OnSaveTextBtn, self.OnSaveScanBtn],
                        [self.SelectAll, self.CopyToClipboard,
                         self.CutToClipboard, self.PasteFromClipboard,
                        self.OnFindText, self.ShowHideLineNums],
                        [self.OnScanBtn, self.OnStepBtn,
                         self.OnStoreBtn, self.OnCancelBtn,
                         self.ForceMetron, self.ForceMetron,
                         self.ForceAlg, self.ForceAlg,
                         self.GotoNextUnscannedLine,
                         self.ScanEverything]] # <-- ALSO FOR TESTING      
        for i, menu in enumerate(menuHandlers):
            for j, item in enumerate(menu):
                self.Bind(wx.EVT_MENU, item, id = (i + 1) * 100 + (j + 1))
        self.Bind(wx.EVT_MENU, self.ShowAboutBox, id = wx.ID_ABOUT)
        self.Bind(wx.EVT_FIND, self.OnFind)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFind)
        # THE FOLLOWING FIXES MAC-SPECIFIC CLOSING BEHAVIOR
        ex = self.menus[0].Append(wx.ID_EXIT,'&Quit\tCtrl+Q', ' ')
        self.Bind(wx.EVT_MENU, self.OnClose, ex) 
        
        # -- SETTING OF MENU BAR --
        self.SetMenuBar(menuBar)
    
        # -- DISPLAYING OF ABOUT BOX --
        self.ShowAboutBox()
    
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
        self.Steps = [('SYLLABLES', self.SM.ShowSyllables),
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
            self.Steps.append(('ANAPESTICS: FOOT DIVISION',
                                    self.SM.AnapDivideHead))
            self.Steps.append(('ANAPESTICS: ANALYSIS',
                              self.SM.AnapCleanUpAndReport))

## - - - - - menu and keystroke methods mainly doing simple display stuff      
    def ShowAboutBox(self, evt = None):
        pythonver = 'Python ver %s' % sys.version.split()[0]
        wxversion = 'wxPython ver %s' % wx.__version__
        msg = abouttxt + '\n\n' + pythonver + '\n' +wxversion
        dlg = wx.MessageDialog(self, message=msg, caption="the Scandroid",
                               style=wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def GetButton(self, label):
        for btn in self.btns:
            if btn.GetId() == self.btnIDs[label]:
                return btn
                
    def GetMenuItem(self, label):
        for menu in self.menus:
            for item in menu.GetMenuItems():
                if item.GetId() == self.menuItemIDs[label]:
                    return item
 
    def DisableAllScanButtons(self):
        self.EnableScanButtons(False)
        self.EnableScansionSaving(False)
        self.EnableIambicAlgForcing(False)
 
    def EnableScanButtons(self, enable=True, ignoreCancel=False):
        """Enable/disable buttons except Store
        (enabled after there's something to store)"""
        self.GetButton('Scan').Enable(enable)
        self.GetButton('Step').Enable(enable)
        self.GetMenuItem('Step').Enable(enable)
        self.GetMenuItem('Scan').Enable(enable)
        if not ignoreCancel:
            self.GetButton('Cancel').Enable(enable)
            self.GetMenuItem('Cancel').Enable(enable)
        
    def EnableScansionSaving(self, enable=True):
        self.GetButton('Store').Enable(enable)
        self.GetButton('Save Scansion').Enable(enable)
        self.GetMenuItem('Store').Enable(enable)
        self.GetMenuItem('Save scansion and notes').Enable(enable)

    def EnableNonScanMenuOptions(self, enable=True):
        self.GetMenuItem('Force anapestics').Enable(enable)
        self.GetMenuItem('Force iambics').Enable(enable)
        self.GetMenuItem('Next unscanned line').Enable(enable)
        
    def EnableIambicAlgForcing(self, enable=True):
        self.GetMenuItem('Force iambic alg. 1').Enable(enable)
        self.GetMenuItem('Force iambic alg. 2').Enable(enable)
        
    def ClearWorkBoxes(self):
        """Clear text and scansion fields, not Notes window; disable buttons.

        Do not clear Notes window; we want it to stay, for example, after a
        scansion has been stored with OnStoreBtn(). We disable scansion
        saving because there is nothing to store or save yet."""
        self.TextLine.Clear()
        self.ScanLine.Clear()
        self.EnableScansionSaving(False)

    def UpdateStatusBar(self, metron=2, linefeet=5, linefeetset=True):
        if metron == 2: mfieldtxt = "metron: IAMBIC"
        else: mfieldtxt = "metron: ANAPESTIC"
        if linefeetset and len(lineLengthName) > linefeet:
            footfieldtxt = "feet per line: " + lineLengthName[linefeet]
        else: footfieldtxt = "feet per line: VARIABLE"
        self.SetStatusText(mfieldtxt, 1)
        self.SetStatusText(footfieldtxt, 2)
        
    def ShowHideLineNums(self, evt):
        self.WholeText.lineNumsVisible = not self.WholeText.lineNumsVisible
        self.WholeText.ToggleLineNumbers()

    def SelectAll(self, evt):
        try: self.FindFocus().SelectAll()
        except: return
        
    def CopyToClipboard(self, evt):
        try: self.FindFocus().Copy()
        except: return
        
    def CutToClipboard(self, evt):
        try: self.FindFocus().Cut()
        except: return
        
    def PasteFromClipboard(self, evt):
        try: self.FindFocus().Paste()
        except: return
            
    def CreateFindDialog(self):
        data = wx.FindReplaceData()
        self.oldFindDialog = self.newFindDialog
        self.newFindDialog = wx.FindReplaceDialog(self, data, "Find")
        self.newFindDialog.data = data
        self.foundTextPos = 0
    
    def OnFindText(self, evt):
        """Put up Find dialog in response to menu/keystroke command.
        
        This uses wxPython's default dialog, which is a little ugly
        (no default button! up/down option not supported by STC!).
        """
        if self.oldFindDialog:
            self.oldFindDialog.Close(True)
        self.CreateFindDialog()
        try: self.newFindDialog.Show()
        except: self.oldFindDialog.Close(True)
        
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
        
    def ErrorMessage(self, function, msg=''): # All-purpose emergency bail-out
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
        self.linetext = txt.strip()
        # If someone pastes a huge block of text that is all one line,
        # the Scandroid will most likely crash. Here, I've imposed a
        # limit of 450 characters, which is about six sentences or
        # a small paragraph. The Scandroid can't handle much more.
        if (len(self.linetext)) > 450:
            self.E.Explain("\n\nERROR: The line you are attempting to scan " +
                           "is too long for the Scandroid. Please divide " +
                           "your text into smaller lines and try again.")
            self.DisableAllScanButtons(); return
        #self.WholeText.SetReadOnly(1)	# no edits while scanning (till Store)
        self.EnableScanButtons()
        self.leadspace = self.leadSpaceRE.match(txt)	# for Store btn
        self.TextLine.AppendText(self.linetext)	# put selected line in the box
        self.lineNum = num			# where to put scansion when done
        self.CurrentStep = 0			# (re)start the procedure
        # iambic-only preparations
        if self.Metron == 2:
            self.whichAlgorithm = random.randint(1, 2) # begin at random
            self.SetupScansionSteps(iambic=True,
                                    algorithm1=(self.whichAlgorithm==1))
            self.OneIambicAlgFailed = False
        #self.E.Explain("Press Step to inch through, Scan to rush")
        self.E.Explain("\n\n\"%s\"" % self.linetext)
        self.SM.ParseLine(self.linetext)
        # If the text was loaded, the parameters have already been deduced.
        if self.loadedtext: return
        # Otherwise, if it's being typed, we want to figure out the params.
        # The feet per line will stay as variable.
        try:
            #self.SM.SetLineFeet(5, False); theLengths = 0
            if not self.forceanap:
                (score, length) = self.SM.ChooseAlgorithm(self.E,
                                              deducingParams=True)
                iambCompTotal = score
            if not self.forceiamb:
                (score, length) = self.SM.GetBestAnapLexes(self.E,
                                               deducingParams=True)
                anapCompTotal = score
            if not self.forceiamb and not self.forceanap:
                if iambCompTotal < anapCompTotal:
                    self.Metron = 2
                else:
                    self.Metron = 3
                self.SetupScansionSteps(iambic=(self.Metron==2))
            #self.SM.SetLineFeet(self.LineFeet, self.LineFeetSet)
            self.UpdateStatusBar(self.Metron, self.LineFeet, self.LineFeetSet)
        except:
            traceback.print_exc()

## - - - - - button & other routines for treatment of individual lines
    def OnStepBtn(self, evt):
        """Perform next scansion step in self.Steps
        (indexed by self.CurrentStep)"""
        self.EnableScansionSaving()
        if not self.CurrentStep:
            self.EnableNonScanMenuOptions(False)
        if self.CurrentStep == len(self.Steps) - 1:
            self.EnableNonScanMenuOptions()
            self.EnableScanButtons(False, ignoreCancel=True)
        if self.CurrentStep >= len(self.Steps):
            return	 # end of steps, stop
        #if self.CurrentStep == 0: self.NotesWindow.Clear()
        self.NotesWindow.AppendText('\n\n')
        self.E.Explain(self.Steps[self.CurrentStep][0] + '  ')	# show header
        try:		# this line is THE distributor of work to the SM
            (scanline, result) = self.Steps[self.CurrentStep][1](self.E)
        except:
            #self.ErrorMessage(self.Steps[self.CurrentStep][1])
            traceback.print_exc()
            self.AbortScansion(); return # bail out!
        # sneaky use of result for iambic ChooseAlgorithm step
        if self.CurrentStep == 2 and self.Metron == 2:
            if result: self.whichAlgorithm = 1 # arbitrary T/F code to put
            else: self.whichAlgorithm = 2	   # alg. into succeed/fail return
            # substitute failure test only
            # for too-short lines if linefeet not set
            if scanline:
                self.SetupScansionSteps(iambic=True,
                                        algorithm1=(self.whichAlgorithm == 1))
                self.ShowScanLine(scanline)
                self.EnableIambicAlgForcing()
                self.CurrentStep += 1
            else: self.AbortScansion() # stop
        else:	         # ALL steps except iambic ChooseAlgorithm
            if scanline: 
#		        self.ShowScanLine(scanline, showAlg=True) # FOR TESTING ONLY
                self.ShowScanLine(scanline)
            if not result:		# some step FAILED
                if self.Metron == 2 and not self.OneIambicAlgFailed:
                    self.OneIambicAlgFailed = True # orig. set in ShowTextLine
                    scanline = self.SM.RestartNewIambicAlg(self.E,
                                                           self.whichAlgorithm,
                                                           scanline)
                    self.ShowScanLine(scanline)
                    self.SwitchIambicAlg()
                    self.SetupScansionSteps(iambic=True,
                                         algorithm1=(self.whichAlgorithm == 1))
                    self.CurrentStep = FORKSTEP
                else:
                    if self.Metron == 2:
                        self.E.Explain("\n\nAbject failure of both "
                                       + "iambic methods!")
                    self.ShowScanLine(self.SM.P.GetScanString() + '   **** ')
                    self.TextLine.AppendText('   (FAIL)')
                    self.AbortScansion() # quit
            else:
                self.EnableIambicAlgForcing(False)
                self.CurrentStep += 1

    def OnScanBtn(self, evt):
        """Perform all remaining steps in scansion without intervention"""
        laststep = len(self.Steps)	# tricky; we may restart if algorithm fails
        step = self.CurrentStep		# so can't use
        while step < laststep:		#  'for step in range(len(self.Steps))'
            self.OnStepBtn(evt)
            step = self.CurrentStep
            
    def AbortScansion(self):
        self.EnableScanButtons(False, ignoreCancel=True)
        self.EnableNonScanMenuOptions()
        self.CurrentStep = len(self.Steps)
    
    def GotoNextUnscannedLine(self, evt):
        if self.WholeText.GetNextUnscannedLine(): return True	# not used!
        else: return False			# for test routine ScanEverything only

    def OnStoreBtn(self, evt):
        """Insert currrent-stage scansion into
        Text panel above line it belongs to"""
        currentscansion = self.ScanLine.GetValue()
        self.WholeText.SetReadOnly(0)	# allow editing till ShowTextLine
        self.WholeText.SetFocus()		# and even encourage it
        if self.leadspace:
            currentscansion = self.leadspace.group() + currentscansion
        self.WholeText.PutLineBack(self.lineNum, currentscansion) # make it so
        self.GetButton('Store').Enable(False)
        self.GetMenuItem('Store').Enable(False)
    
    def ScanEverything(self, evt):
        while 1:
            if not self.GotoNextUnscannedLine(evt): 
                break
            self.OnScanBtn(evt)
            self.OnStoreBtn(evt)

    def OnCancelBtn(self, evt):
        """Return all to condition before line was selected"""
        self.ClearWorkBoxes()
        self.WholeText.SetReadOnly(0)		# allow editing again
        p = self.WholeText.GetCurrentPos()
        self.WholeText.SetSelection(p, p)
        self.DisableAllScanButtons()
        self.NotesWindow.Clear()			# unlike store!
    
    def RestartLineAfterCancel(self):
        """Zero the conditions for scansion of same line as was in process
        
        This is in response to need to rebegin after a dict word has been
        edited (don't know if it will be needed anywhere else--modular design
        is falling apart!). Assume that self.lineNum and self.linetext are
        current; don't change the algorithm, however it was chosen.
        """
        # Prevents an error if user changes dictionary
        # syllabification for a word in default text.
        if not hasattr(self, 'linetext'): return
        # If self.linetext exists, continue as normal.
        self.ClearWorkBoxes()
        self.NotesWindow.Clear()
        self.TextLine.AppendText(self.linetext)
        #self.WholeText.SetReadOnly(1)
        self.EnableScanButtons()
        self.CurrentStep = 0
        # let's leave the Algorithm alone
        self.OneIambicAlgFailed = False
        self.SM.ParseLine(self.linetext)

## - - - - - button routines for handling text (files etc)
    def OnLoadBtn(self, evt):
        if not self.loadPath: dir = os.getcwd()
        else: dir = self.loadPath
        dlg = wx.FileDialog(self, message="Choose a plain text file",
                            defaultDir=dir, defaultFile="", wildcard="*.*",
                            style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.ClearWorkBoxes()
            self.NotesWindow.Clear()
            self.loadPath = dlg.GetPath()
            try:
                with open(self.loadPath, 'rU') as f:
                    self.WholeText.DisplayText(f.read())
                self.loadedtext = True
                self.forceiamb, self.forceAnap = False, False
                self.DeduceParameters()	# sets LineFeet, Metron, & LineFeetSet
            except:
                self.WholeText.DisplayText('')
                self.E.Explain("\n\nERROR: The Scandroid could not load the"
                               + " text from the file you have specified. You"
                               + " may need to copy the text from the file"
                               + " and paste it into the Scandroid.\n")
        dlg.Destroy()
        
    def OnSaveTextBtn(self, evt):
        if not self.savePath: dir = os.getcwd()
        else: dir = self.savePath
        dlg = wx.FileDialog(self, message="File to save scanned text",
                    defaultDir=dir, defaultFile='*.txt', wildcard="*.txt",
                    style=wx.SAVE | wx.CHANGE_DIR | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            defenc = wx.GetDefaultPyEncoding()
            textToWrite = self.WholeText.GetText().encode(defenc)
            self.savePath = dlg.GetPath()
            try:
                with open(self.savePath, 'w') as f:
                    f.write(textToWrite)
                    self.E.Explain("\n\nTyped text written to "
                                   + self.savePath + "\n")
            except:
                self.E.Explain("\n\nERROR: The Scandroid could not save the"
                               + " text to the file you have specified. You"
                               + " may need to manually copy the information"
                               + " and save it to a file.\n")
        dlg.Destroy()
        
    def OnSaveScanBtn(self, evt):
        defenc = wx.GetDefaultPyEncoding()
        # Get values of ScanLine, TextLine, and NotesWindow.
        scansion = self.ScanLine.GetValue()
        textline = self.TextLine.GetValue()
        scanNotes = self.NotesWindow.GetValue()
        # Make a divider for the scanned line based on line length.
        divider = max(len(scansion), len(textline)) * '-'
        # Sandwich the scansion and textline between two dividers.
        scannedLine = '\n'.join([divider, scansion, textline, divider])
        # Concatenate everything to form one string that will be written.
        textToWrite = (scannedLine + scanNotes + '\n\n').encode(defenc)
        filename = str(datetime.now().date()) + '-Scansions.txt'
        pathname = os.path.join(os.getcwd(), filename)
        try:
            with open(pathname, 'a') as f:
                f.write(textToWrite)
                self.E.Explain("\n\nScansion and notes " +
                               "written to " + pathname + "\n")
        except:
            self.E.Explain("\n\nERROR: The Scandroid could not automatically"
                           + " save the scansion and notes. You will need to"
                           + " to manually copy the information and save"
                           + " it to a file.\n")
        self.GetButton('Save Scansion').Enable(False)
        self.GetMenuItem('Save scansion and notes').Enable(False)

    def OnTypeBtn(self, evt):
        # safety check, if any scansions?? ("do you want to save...")
        self.loadedtext = False
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

## - - - - - establish major context for scansion work
    def DeduceParameters(self):
        """When text is loaded, read multiple lines;
        find metron and linelength.
        
        Read all lines (up to a dozen); call SM to try a quick scansion
        of each as iambic (both algorithms, but without stress-resolution
        options) and as anapestic to decide consistent metron (2 or 3).
        Guess line-length in feet under each assumption; if close average,
        declare constant length. Set three flags as distributable globals:
        Metron, LineFeet, and LineFeetSet (True *or* False). Metron is
        always set (for better or worse).
        
        Added "force" flags so this will be callable from ForceMetron.
        With one or the other set, skip non-pertinent parts.
        """
        textlines = self.WholeText.GetLineCount()
        iambLens, anapLens = [], []
        iambCompTotal = anapCompTotal = 0
        linesToSample = 12
        theLengths = 0 # initialize the length variable
        i = 0 # sample min of all lines (textlines) or linesToSample (break)
        self.SM.SetLineFeet(5, False) # unset "linefeetset" for tests
        for linex in range(textlines):	# parse lines, try various scansions
            if i >= linesToSample: break
            line = self.WholeText.GetLine(linex)
            if len(line) < 5 or line[:1] == '\t': # can't use line[0] with or!
                continue	# skip a title or other non-verse
            i += 1	# count of "real" lines
            self.SM.ParseLine(line)
            if not self.forceanap:
                try:
                    (score, length) = self.SM.ChooseAlgorithm(self.E,
                                                          deducingParams=True)
                #except: self.ErrorMessage(self.SM.ChooseAlgorithm,
                #                              self.SM.P.GetMarks())
                except: traceback.print_exc()
                iambCompTotal += score
                if score < 100: iambLens.append(length)
            if not self.forceiamb:
                try:
                    (score, length) = self.SM.GetBestAnapLexes(self.E,
                                                          deducingParams=True)
                #except: self.ErrorMessage(self.SM.GetBestAnapLexes,
                #                               self.SM.P.GetMarks())
                except: traceback.print_exc()
                anapCompTotal += score
                if score < 100: anapLens.append(length)
        if not self.forceiamb and not self.forceanap:
            if iambCompTotal < anapCompTotal:
                self.Metron = 2
                theLengths = iambLens
                self._setLineLengthIfPossible(theLengths)
            else:
                self.Metron = 3
                theLengths = anapLens
                self._setLineLengthIfPossible(theLengths)
            self.SetupScansionSteps(iambic=(self.Metron==2))
        if not self.forceiamb and not self.forceanap:
            self.E.ExpDeduceParams(self.Metron, self.LineFeet,
                                              self.LineFeetSet)
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

    def ForceMetron(self, evt):
        """Menu-only choice to force scansion
        iambic/anapestic till next Load."""
        self.OnCancelBtn(dummyevent)	# before msg or will be erased
        which = evt.GetId()
        if which == self.menuItemIDs['Force anapestics']:
            self.Metron = 3
            self.forceanap = True; self.forceiamb = False
            self.E.Explain("\nForced switch to anapestic scansion\n")
            self.SetupScansionSteps(iambic=False)
            self.DeduceParameters()
        elif which == self.menuItemIDs['Force iambics']:
            self.Metron = 2
            self.forceiamb = True; self.forceanap = False
            self.E.Explain("\nForced switch to iambic scansion\n")
            self.SetupScansionSteps(iambic=True)
            self.DeduceParameters()
        else: return
        if self.LineFeetSet:
            self.E.Explain("implied line length is %s feet\n\n"
                                                % self.LineFeet)
        else: self.E.Explain("implied line length is variable\n\n")
        
    def ForceAlg(self, evt):
        """Menu-choice to override automatic choice of algorithm for iambics.
        
        This would have no effect (be cancelled out) if chosen before the
        Choose Algorithm step. After just past that step it would produce
        chaos because of conflicting work on the line. To enforce this
        narrow window, the menu item and keypress are disabled except
        at the end of that crucial step.
        """
        which = evt.GetId()
        if which == self.menuItemIDs['Force iambic alg. 1']:
            self.whichAlgorithm = 1
            self.E.Explain("\n\nAlgorithm 1 forced")
        elif which == self.menuItemIDs['Force iambic alg. 2']:
            self.whichAlgorithm = 2
            self.E.Explain("\n\nAlgorithm 2 forced")
        else: return
        self.SetupScansionSteps(iambic=True,
                                algorithm1=(self.whichAlgorithm == 1))
                                
    def SwitchIambicAlg(self):
        if self.whichAlgorithm == 1:
            self.whichAlgorithm = 2
        else: self.whichAlgorithm = 1

# - - - - - - - - - - - end of ScandroidFrame class - - - - - - - - - - - -

profiling = False
if profiling: import profile

#app = wx.PySimpleApp()
app = wx.App(False)
appframe = ScandroidFrame(None, -1, "the Scandroid")
appframe.Center()
appframe.Show()
if profiling:
    profile.run('app.MainLoop()', 'ScandroidProf')
else:
    app.MainLoop()
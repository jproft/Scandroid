# dictfuncs.py 1.5
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
# This module holds the class that, rather loosely, contains methods and
# structures connected with the dictionary of syllable-and-stress exceptions.

import wx

# Grabs the dictionary from scandictionary.py
from scandictionary import scandict

class ScanDict:

    def __init__(self, parent):
        self.Dict = {}
        self.mom = parent
        self.Dict = scandict

    def EditDict(self, selstring):
        """Show how dict or calculation treats a word, get user's correction.
        
        If user enters new syllabification and stress for word, enter the word
        (if it wasn't in the dictionary) or the corrected syl-list (if it was).
        Otherwise leave it alone. Called by mouse-drive function in the
        StyledTextCtrl in scanstc.py.
        """
        word = selstring.lower()  # stripped in scanstc.py before it gets here
        if self.Dict.has_key(word): syls = self.Dict[word]
        else: syls = self.mom.S.Syllabize(word)
        s = ''
        for syl in syls: s += syl + ' '
        dlg = DictEditDialog(self, -1, s)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            newsyls = dlg.CorrectedWord
            # should undoubtedly do some very careful checking of this!
            if newsyls:
                syls = newsyls
                self.Dict[word] = syls.split() # change dict but
            dlg.Destroy()                      # NOT SAVED TO FILE
            return True
        else:
            dlg.Destroy()
            return False
        

class DictEditDialog(wx.Dialog):
    def __init__(self, parent, id, syls):
        wx.Dialog.__init__(self, None, id,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        instructions = ("The Scandroid thinks the word",
                        "has this pattern of syllables",
                        "and stress:\n",
                        "Type in the corrected form,",
                        "separating syllables with spaces,",
                        "the stressed one ALL CAPS:\n")
        textlines = []
        for line in instructions:
            text = wx.StaticText(self, -1, line)
            textlines.append((text, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3))
            
        self.wordAsKnown = wx.TextCtrl(self, -1, syls)
        self.wordCorrected = wx.TextCtrl(self, -1, "")
 
        self.OKbutton = wx.Button(self, wx.ID_OK, " OK ")
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, " Cancel ")
 
        items = ((self.wordAsKnown, 3, wx.EXPAND),
                 (self.wordCorrected, 3, wx.EXPAND),
                 (self.OKbutton, 0, wx.ALIGN_LEFT),
                 (self.CancelButton, 0, wx.ALIGN_RIGHT))
                 
        spacers = (((40, 20), 0), ((30, 30), 0), ((20, 20), 0))
 
        fieldsizers = []
        for item in items[:2]:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(*spacers[0])
            sizer.Add(*item)
            sizer.Add(*spacers[0])
            fieldsizers.append((sizer, 0, wx.EXPAND, 3))
        
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(*spacers[1])
        for item in items[2:]:
            buttonsizer.Add(*item)
            buttonsizer.Add(*spacers[1])
        buttonsizer = (buttonsizer, 0, wx.EXPAND, 3)
        
        components = (textlines[0], textlines[1], textlines[2],
                      fieldsizers[0], textlines[3], textlines[4],
                      textlines[5], fieldsizers[1], buttonsizer)
        
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(*spacers[2])
        for cmpnt in components:
            mainsizer.Add(*cmpnt)
            if cmpnt not in textlines:
                mainsizer.Add(*spacers[2])
        
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.OKbutton)
        self.SetSizer(mainsizer); self.SetAutoLayout(True)
        mainsizer.Fit(self)
        
        self.wordAsKnown.SetEditable(0)
        self.wordCorrected.SetFocus()
        self.OKbutton.SetDefault()
        
    def OnOK(self, event):
        """When DictEditDialog's OK button is pressed,
        save the selected word."""
        self.CorrectedWord = self.wordCorrected.GetValue()
        event.Skip()


if __name__ == '__main__':
    app = wx.PySimpleApp()
    appframe = wx.Frame(None, -1, "the Scandroid")
    appframe.Show()
    sd = ScanDict(None)
    sd.EditDict('inane')

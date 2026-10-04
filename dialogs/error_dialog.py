# ***********************************************************************
"""
Module Name : error_dialog.py
Author      : Chris Anderson
Create Date : 2026-10-04
Description : Simple reusable error dialog.
"""
# ***********************************************************************

import wx


class ErrorDialog(wx.MessageDialog):
    @staticmethod
    def show(parent, title, message):
        dlg = wx.MessageDialog(
            parent,
            message,
            title,
            style=wx.OK | wx.ICON_ERROR
        )
        dlg.ShowModal()
        dlg.Destroy()

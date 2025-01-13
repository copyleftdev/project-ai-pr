#------------------------------------------------------------------------------
#  SyCheck.py
#
#  - Ensure correct configuration of controllers on the network
#  - written for Python v3.9
#
#  Symbrosia
#  Copyright 2024, all rights reserved
#
# 23Oct2024 A. Cooper v0.1
# - initial version
# 23Oct2024 A. Cooper v0.2
# - test version released to cultivation
#
#------------------------------------------------------------------------------
verStr = 'SyCheck v0.2'

#-- constants -----------------------------------------------------------------
cfgFileName = 'configuration.xml'
cfgFilePath = 'cfg'
rptFilePath = 'rpt'
refFilePath = 'ref'
libFilePath = 'lib'
colBack = '#BBBBBB'
colDev  = '#999999'
colOn   = '#ADFF8C'
colOff  = '#FFADAD'

verbose = False

#-- library -------------------------------------------------------------------
import string
import sys
import os
import time
import urllib.request
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils
import xml.etree.ElementTree as xml

#-- globals -------------------------------------------------------------------
localDir = os.path.dirname(os.path.realpath(__file__))
rptPath  = os.path.join(localDir, rptFilePath)
cfgPath  = os.path.join(localDir, cfgFilePath)
refPath  = os.path.join(localDir, refFilePath)
libPath  = os.path.join(localDir, libFilePath)
sys.path.append(libPath)

#-- local library (dummy) -----------------------------------------------------
import symbCtrlModbus

#------------------------------------------------------------------------------
#  SyCheck GUI
#
#  - setup the GUI
#
#------------------------------------------------------------------------------
class Application(tk.Frame):
    units = {}
    refs  = {}
    report = []
    lastLog = dt.datetime.now()
    eventNow = dt.datetime.min

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        root.resizable(width=False, height=False)
        root.protocol("WM_DELETE_WINDOW", self.done)

        # Create controller object
        self.controller = symbCtrlModbus.SymbCtrl()

        # load units and refs
        if not self.loadConfig(cfgPath, cfgFileName):
            sys.exit()
        if not self.loadRefs(refPath):
            sys.exit()

        self.createUnitMenu()
        # finish
        self.logEvent('{} started'.format(verStr), True)
        self.device = ModbusClient()
        print('{} running...'.format(verStr))

    #-------------------------------------------------------------------------- 
    #  CREATE TKINTER WIDGETS
    #-------------------------------------------------------------------------- 
    def createWidgets(self):
        spaceX = 5
        spaceY = 1

        # Dropdown for unit selection
        self.ctrlStr = tk.StringVar()
        self.ctrlMenu = tk.OptionMenu(self, self.ctrlStr, ())
        self.ctrlMenu.config(width=14, font=('Helvetica','10'))
        self.ctrlMenu.grid(column=1, row=1, padx=spaceX, pady=spaceY, sticky=tk.W)

        # Buttons
        self.scanButton = tk.Button(self, text="Scan", width=10,
                                    command=self.scan, font=("Helvetica", "12"))
        self.scanButton.grid(column=1, row=2, padx=spaceX, pady=spaceY)

        self.scanAllButton = tk.Button(self, text="Scan All", width=10,
                                       command=self.scanAll, font=("Helvetica", "12"))
        self.scanAllButton.grid(column=1, row=3, padx=spaceX, pady=spaceY)

        self.saveButton = tk.Button(self, text="Save", width=10,
                                    command=self.saveReport, font=("Helvetica", "12"))
        self.saveButton.grid(column=1, row=4, padx=spaceX, pady=spaceY)

        self.quitButton = tk.Button(self, text="Quit", width=10,
                                    command=self.done, font=("Helvetica", "12"))
        self.quitButton.grid(column=1, row=5, padx=spaceX, pady=spaceY)

        # Log window
        self.eventLog = tk.Text(self, width=80, height=16, bg=colBack)
        self.eventLog.grid(column=3, row=1, rowspan=5, padx=0, pady=spaceY, sticky=tk.E+tk.W)

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.config(command=self.eventLog.yview)
        self.eventLog.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(column=4, row=1, rowspan=5,
                            padx=0, pady=spaceY, sticky=tk.N+tk.S+tk.W)

        # Spacers
        self.spacer1 = tk.Label(self, text=' ')
        self.spacer1.grid(column=0, row=0)
        self.spacer2 = tk.Label(self, text=' ')
        self.spacer2.grid(column=5, row=6)

    #--------------------------------------------------------------------------
    #  CREATE THE DROPDOWN MENU FOR UNITS
    #--------------------------------------------------------------------------
    def createUnitMenu(self):
        if not self.units:
            return
        self.ctrlList = [ctrl['name'] for ctrl in self.units]
        if self.ctrlList:
            self.ctrlStr.set(self.ctrlList[0])

        # Recreate OptionMenu to reflect the newly loaded controllers
        menu = self.ctrlMenu["menu"]
        menu.delete(0, "end")
        for item in self.ctrlList:
            menu.add_command(label=item, command=lambda value=item: self.ctrlStr.set(value))

    #--------------------------------------------------------------------------
    #  LOAD CONFIGURATION FILE (configuration.xml)
    #--------------------------------------------------------------------------
    def loadConfig(self, configPath, configFile):
        fullPath = os.path.join(configPath, configFile)
        if not os.path.exists(fullPath):
            messagebox.showerror(
                title='Startup error...',
                message=f'Unable to locate configuration file {fullPath}'
            )
            return False

        try:
            tree = xml.parse(fullPath)
        except Exception as ex:
            messagebox.showerror(
                title='Startup error...',
                message=f'Error parsing configuration file {fullPath}: {ex}'
            )
            return False

        root = tree.getroot()
        self.units = []
        for ctrl in root:
            if ctrl.tag == 'ctrl':
                new = {'name': ctrl.attrib['name']}
                for item in ctrl:
                    new[item.tag] = item.text
                self.units.append(new)
        self.logEvent('Controllers loaded', True)
        return True

    #--------------------------------------------------------------------------
    #  LOAD REFERENCE FILES
    #--------------------------------------------------------------------------
    def loadRefs(self, refPath):
        self.refs = {}
        for unit in self.units:
            refName = unit.get('ref')
            if not refName:
                continue

            if refName not in self.refs:
                fullRefPath = os.path.join(refPath, refName)
                if not os.path.exists(fullRefPath):
                    messagebox.showerror(
                        title='Startup error...',
                        message=f'Unable to load reference file {fullRefPath}'
                    )
                    return False

                try:
                    tree = xml.parse(fullRefPath)
                except Exception as ex:
                    messagebox.showerror(
                        title='Startup error...',
                        message=f'Error parsing reference file {fullRefPath}: {ex}'
                    )
                    return False

                newRegList = []
                rootRef = tree.getroot()
                for reg in rootRef:
                    if reg.tag == 'register':
                        # The type is determined later by the controller,
                        # but we store "raw" info here
                        newRegList.append({
                            'reg': reg.attrib['name'],
                            'value': reg.text.strip() if reg.text else '',
                        })
                self.refs[refName] = newRegList
                self.logEvent(f'Reference file {refName} loaded', True)
        return True

    #--------------------------------------------------------------------------
    #  SCAN BUTTON (SCAN SINGLE CONTROLLER)
    #--------------------------------------------------------------------------
    def scan(self):
        if not self.units:
            self.logEvent('No controllers configured.', True)
            return

        selection = self.ctrlStr.get()
        if not selection:
            self.logEvent('No controller selected.', True)
            return

        self.report = []
        self.report.append('SyCheck Report')
        self.report.append('  {:%Y-%m-%d %H:%M:%S}'.format(dt.datetime.now()))
        self.report.append('')

        for unit in self.units:
            if unit['name'] == selection:
                self.scanUnit(unit)
                break
        self.logEvent(f'Scan {selection} complete', True)

    #--------------------------------------------------------------------------
    #  SCAN ALL BUTTON
    #--------------------------------------------------------------------------
    def scanAll(self):
        if not self.units:
            self.logEvent('No controllers configured.', True)
            return

        self.report = []
        self.report.append('SyCheck Report')
        self.report.append('  {:%Y-%m-%d %H:%M:%S}'.format(dt.datetime.now()))
        self.report.append('')

        for unit in self.units:
            self.scanUnit(unit)
        self.logEvent('Scan all complete', True)

    #--------------------------------------------------------------------------
    #  SCAN A SINGLE CONTROLLER
    #--------------------------------------------------------------------------
    def scanUnit(self, unit):
        refName = unit.get('ref')
        if not refName:
            self.report.append(f"Controller {unit['name']} has no 'ref' file specified.")
            return

        if refName not in self.refs:
            self.logEvent(f"Reference {refName} not loaded for {unit['name']}", True)
            return

        header = '  Register               Controller   Reference        Description'
        headline = '  -------------------------------------------------------------------------------------------'
        self.logEvent(f"Check config for {unit['name']} against {refName}...", True)
        self.report.append(f"Check config for {unit['name']} against {refName}...")
        diffs = 0

        address = unit.get('address', '127.0.0.1')
        port = 502
        try:
            port = int(unit.get('port', '502'))
        except:
            port = 502

        # Start communication
        if self.controller.start(address, port):
            self.controller.service()
            if self.controller.error():
                self.logEvent(f"  Communications error with {unit['name']}", True)
                self.report.append(f"  Communications error with {unit['name']}")
            else:
                self.logEvent(f"  {unit['name']} configuration read", True)
                firstErr = True
                for reg in self.refs[refName]:
                    regName = reg['reg']
                    regValue = self.controller.value(regName)
                    refValue = self.controller.convert(regName, reg['value'])
                    regType  = self.controller.type(regName)

                    # Compare the two
                    mismatch = False
                    if regType == 'str':
                        mismatch = (regValue != refValue)
                    elif regType == 'int' or regType == 'uint':
                        mismatch = (regValue != refValue)
                    elif regType == 'float':
                        mismatch = (round(regValue, 4) != round(refValue, 4))
                    elif regType == 'bool':
                        mismatch = (regValue != refValue)
                    else:
                        # treat as string
                        mismatch = (str(regValue) != str(refValue))

                    if mismatch:
                        if firstErr:
                            self.report.append(header)
                            self.report.append(headline)
                            firstErr = False
                        if regType == 'bool':
                            ctrlStr = 'On' if regValue else 'Off'
                            refStr  = 'On' if refValue else 'Off'
                            self.report.append(
                                f"  {regName:<16} {ctrlStr:>16} ≠ {refStr:<16} {self.controller.description(regName)}"
                            )
                            self.logEvent(f"  {regName}:{ctrlStr} ≠ {refStr} in reference", True)
                        elif regType == 'int' or regType == 'uint':
                            self.report.append(
                                f"  {regName:<16} {regValue:>16d} ≠ {refValue:<16d} {self.controller.description(regName)}"
                            )
                            self.logEvent(f"  {regName}:{regValue} ≠ {refValue} in reference", True)
                        elif regType == 'float':
                            self.report.append(
                                f"  {regName:<16} {regValue:>16.2f} ≠ {refValue:<16.2f} {self.controller.description(regName)}"
                            )
                            self.logEvent(f"  {regName}:{regValue:.2f} ≠ {refValue:.2f} in reference", True)
                        else:
                            # treat as str
                            self.report.append(
                                f"  {regName:<16} {regValue:>16} ≠ {refValue:<16} {self.controller.description(regName)}"
                            )
                            self.logEvent(f"  {regName}:'{regValue}' ≠ '{refValue}' in reference", True)
                        diffs += 1

                if diffs == 0:
                    self.logEvent('  No differences found', True)
                    self.report.append('  No differences found')
                elif diffs == 1:
                    self.logEvent(f'  {diffs} difference found', True)
                    self.report.append(f'  {diffs} difference found')
                else:
                    self.logEvent(f'  {diffs} differences found', True)
                    self.report.append(f'  {diffs} differences found')
                self.report.append('')
        else:
            self.logEvent(f"  Error!! Unable to open {unit['name']}", True)
            self.report.append(f"  Error!! Unable to open {unit['name']}")

    #--------------------------------------------------------------------------
    #  SAVE REPORT BUTTON
    #--------------------------------------------------------------------------
    def saveReport(self):
        if not self.report:
            messagebox.showinfo("No Data", "No report data to save.")
            return

        typ = [('Text', '*.txt')]
        name = 'SyCheck{:%Y%m%d}'.format(dt.datetime.now())
        file = filedialog.asksaveasfilename(
            title='Save report...',
            initialfile=name,
            filetypes=typ,
            defaultextension=typ,
            initialdir=localDir
        )
        if not file:
            return

        try:
            with open(file, 'w', encoding="utf-8") as reportFile:
                for line in self.report:
                    reportFile.write(line + '\n')
            self.logEvent(f'Report {os.path.basename(file)} saved', True)
        except Exception as ex:
            messagebox.showwarning(
                title='File error...',
                message=f'Unable to open file {file}: {ex}'
            )
            return

    #--------------------------------------------------------------------------
    #  QUIT / CLOSE WINDOW
    #--------------------------------------------------------------------------
    def done(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.quit()

    #--------------------------------------------------------------------------
    #  LOG EVENT
    #--------------------------------------------------------------------------
    def logEvent(self, event, incDate):
        self.eventLast = self.eventNow
        self.eventNow = dt.datetime.now()
        # Avoid date spam if logs occur in < 3 seconds
        if (self.eventNow - self.eventLast) < dt.timedelta(seconds=3):
            incDate = False

        if incDate:
            self.eventLog.insert(tk.END, '{:%Y-%m-%d %H:%M:%S} '.format(self.eventNow))
        else:
            self.eventLog.insert(tk.END, '                    ')
        self.eventLog.insert(tk.END, event+'\n')
        self.eventLog.see(tk.END)

    #--------------------------------------------------------------------------
    #  CLEAR THE TEXT LOG (not used here, but could be helpful)
    #--------------------------------------------------------------------------
    def clearEvents(self):
        self.eventLog.delete('1.0', tk.END)

#------------------------------------------------------------------------------
#  GUI Main
#------------------------------------------------------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.master.title(verStr)
    root.protocol("WM_DELETE_WINDOW", app.done)
    app.mainloop()
    root.destroy()

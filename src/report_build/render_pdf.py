#!/usr/bin/env python3
"""Open a .docx in headless LibreOffice, update fields and indexes (ToC, lists), export PDF.
Usage: render_pdf.py in.docx out.pdf"""
import os, subprocess, sys, time
import uno
from com.sun.star.beans import PropertyValue

def prop(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p

src, dst = map(os.path.abspath, sys.argv[1:3])
proc = subprocess.Popen(['soffice', '--headless', '--invisible', '--norestore',
                         '--accept=socket,host=localhost,port=2002;urp;'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
ctx = None
for _ in range(60):
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        ctx = resolver.resolve('uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext')
        break
    except Exception:
        time.sleep(1)
smgr = ctx.ServiceManager
desktop = smgr.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.loadComponentFromURL('file://' + src, '_blank', 0, (prop('Hidden', True),))
for _ in range(2):
    doc.getTextFields().refresh()
    idx = doc.getDocumentIndexes()
    for i in range(idx.getCount()):
        idx.getByIndex(i).update()
doc.storeToURL('file://' + dst, (prop('FilterName', 'writer_pdf_Export'),))
doc.close(True)
try:
    desktop.terminate()
except Exception:
    pass
proc.wait(timeout=30)
print('PDF', dst)

import urwid

class TlmRow():
    def __init__(self):
        self.time = urwid.Text("-",'left','ellipsis')
        self.id = urwid.Text("-",'right','ellipsis')
        self.name = urwid.Text("-",'left','ellipsis')
        self.severity = urwid.Text("-",'left','ellipsis')
        self.text = urwid.Text("-",'left','ellipsis')
        self.sep = urwid.Text("|",'center')
        self.columns = urwid.Columns(
            (
                (1,self.sep),
                self.time,
                (1,self.sep),
                self.id,
                (1,self.sep),
                self.name,
                (1,self.sep),
                self.severity,
                (1,self.sep),
                self.text,
                (1,self.sep),
            ),
            1,0,1)

    def getColumns(self):
        return self.columns
    
    def set(self, time,id,name,severity,text):
        self.time.set_text(time)
        self.id.set_text(id)
        self.name.set_text(name)
        self.severity.set_text(severity)
        self.text.set_text(text)

class TlmTable():
    def __init__(self):
        self.table_hdr = TlmRow()
        self.table_hdr.set(
            "Time",
            "ID",
            "Name",
            "Severity",
            "Text",
        )
        self.table = urwid.Pile(
            (
                urwid.Divider('-'),
                self.table_hdr.getColumns(),
                urwid.Divider('-')
            )
        )

        for row in range(1,21):
            entry = TlmRow()
            entry.set(
                "%d"%row,
                "%d"%row,
                "%d"%row,
                "%d"%row,
                "%d"%row,
            )
            self.table.contents.append(
                (entry.getColumns(),('pack',None))
                 )

    def getTable(self):
        return self.table
    
    def update(temp, newVals):
        pass

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    # else:
    #     row.set("12","34","56","78","90")
        


if __name__ == "__main__":
    # row = TlmRow()
    # frame = urwid.Frame(urwid.Filler(row.getColumns()))
    table = TlmTable()
    frame = urwid.Frame(
        urwid.ScrollBar(
            urwid.Scrollable(
                urwid.Filler(
                    table.getTable(), 'top'
                )
            )
        )
    )

    loop = urwid.MainLoop(frame, unhandled_input=show_or_exit)
    loop.run()




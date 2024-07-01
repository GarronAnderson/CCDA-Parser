from guizero import *
import parser

patient = None


def open_ccda():
    global patient
    filename = app.select_file(
        title="Pick A CCDA", folder=".", filetypes=[["CCDA Files (xml)", "*.xml"]]
    )
    patient = parser.Parser(filename)
    name.value = patient.name
    dob.value = patient.dob


app = App(title="CCDA Parser", layout="grid")

menubar = MenuBar(
    app,
    toplevel=["File"],
    options=[
        [["Open CCDA", open_ccda]],
    ],
)

name_label = Text(app, text="Name:", grid=[0, 0])
name = Text(app, text="No CCDA Loaded", grid=[1, 0])

dob_label = Text(app, text="DOB:", grid=[0, 2])
dob = Text(app, text="", grid=[1, 2])

app.display()

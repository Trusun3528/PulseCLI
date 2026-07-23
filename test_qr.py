import segno
qr = segno.make("https://google.com")
for row in qr.matrix:
    line = ""
    for col in row:
        if col: # dark
            line += "██"
        else:
            line += "  "
    print(line)

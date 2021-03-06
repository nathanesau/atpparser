from atpparser import downloadArchive, downloadDraw, \
    parseDraw, parseArchive

def test_downloadArchive():
    out = downloadArchive(2019)
    f = open(out, 'r')
    data = f.read()
    assert(data != None)

def test_parseArchive2019():
    out = downloadArchive(2019)
    data = parseArchive(out)
    assert(data != None)

def test_parseArchive2020():
    out = downloadArchive(2020)
    data = parseArchive(out) # < 1s
    assert(data != None)

def test_downloadDraw():
    out = downloadDraw("rotterdam",
        "/en/scores/archive/rotterdam/407/2019/draws?matchtype=singles", 2019)
    f = open(out, 'r')
    data = f.read()
    assert(data != None)

def test_parseDraw():
    out = downloadDraw("rotterdam",
        "/en/scores/archive/rotterdam/407/2019/draws?matchtype=singles", 2019)
    data = parseDraw(out)
    assert(data != None)
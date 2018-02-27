import os
import re
import argparse
import sys
import shutil
import ntpath

# USAGE: python3 gutenberg_file_finder.py <command> <file-type> <gutenberg-dir> <target-path>
# Commands: ls mv cp
# File types: all txt pdf audio video
# Examples:
# python3 gutenberg_file_finder.py ls all /corpora/proj-gutenberg/gutenberg.readingroo.ms/gutenberg gutenberg.info

command = ""
file_type = ""
gutenberg_dir = ""
target_path = ""

argParser = argparse.ArgumentParser("Finds text files in the project Gutenberg corpus by language")
argParser.add_argument("command", choices=['list','move','copy'], help="enter 'list' to list the proposed file organization; enter 'move' to move files into organized directories; enter 'copy' to copy files instead")
argParser.add_argument("gutenberg_dir", help="the directory where project gutenberg files are found. e.g. gutenberg.readingroo.ms/gutenberg. If a file (from 'list') is entered instead of a directory, the file is used instead of searching the gutenberg directories")
argParser.add_argument("target_path", help="the directory where the files are placed; if 'list' is chosen, the name of the file to write the listed files")
args = argParser.parse_args()


def eprint(text):
    print(text, file=sys.stderr)


if not os.path.isdir(args.gutenberg_dir):
    if args.command == 'list':
        eprint("gutenberg_dir needs to be a directory for the list command")
        exit()
    elif not os.path.isfile(args.gutenberg_dir):
        eprint("Couldn't find gutenberg_dir: "+args.gutenberg_dir)
        exit()

if os.path.isfile(args.target_path):
    if args.command != 'list':
        eprint("target_path needs to be a directory for the "+args.command+" command")
        exit()
elif args.command == 'list':
    eprint("target_path needs to be a file (not a directory) for the 'list' command")
    exit()

gutIndexName = "GUTINDEX.ALL"
TEXTEXTS = ["txt","utf8"]
DEFAULT_LANGUAGE = "English"


# def getBookStats(books):
#     numBooks = len(books)
#     filetypes = {}


class Gutenberg:
    def __init__(self, gutenberg_dir):
        self.dir = gutenberg_dir
        self.cacheDir = os.path.join(self.dir,"cache","generated")
        self.filetypes = []
        self.dirBooks = {}
        self.books = {}
        self.cacheBooks = {}
        self.languages = {}
        self.lastIndex = 0
        self.lineRegex = re.compile('[\w\p{P}]\s\s+\d*(\d|C)')
        self.langSecRegex = re.compile("<dcterms:language>.{1,100}<rdf:value.{1,100}>(\w{1,100})<\/rdf:value>.{1,100}</dcterms:language>") # Grab language code in RDF file
        # self.textLangRegex = re.compile("\nLanguage: ([a-zA-Z]+)\n")
        self.unlisted = []
        self.noLangBooks = {}
        self.pdfs = {}
        self.epubs = {}
        self.txts = {}

    # Return the language of the book and the index of the line after the last line of attributes
    def parseBookAttributes(self, lines, lineI):
        language = DEFAULT_LANGUAGE
        # while
        return language, lineI

    def getRDFLangs(self, rdfFilepath):
        with open(rdfFilepath, 'r') as rdfFile:
            fileStr = rdfFile.read().replace("\n","")
            langStrs = self.langSecRegex.findall(fileStr)
            if not langStrs or not len(langStrs):
                print("Could not find lang in "+rdfFilepath)
            return langStrs

    def getLangsFromText(self, textPath):
        with open(textPath, 'r') as textFile:
            for line in textFile:
                line = line.strip()
                if line.startswith("Language:"):
                    langs = re.split(",|&|and|with|\s|/",line.split(":")[1].strip().lower())
                    langStrs = []
                    for lang in langs:
                        if lang:
                            lang = re.sub(r'[^a-zA-Z]+','',lang)
                            if len(lang):
                                langStrs.append(lang)
                    return langStrs
                if line.startswith("***"):
                    break
        return False

    def addBookLang(self, lang, book, fileFormat):
        langFormats = None
        if lang not in self.languages:
            langFormats = {}
        else:
            langFormats = self.languages[lang]
        if fileFormat not in langFormats:
            langFormats[fileFormat] = []
        langFormats[fileFormat].append(book)
        self.languages[lang] = langFormats

    def getIndexPath(self, index):
        indexStr = str(index)
        lastDigitI = len(indexStr)-1
        path = self.dir
        offset = 0
        if index < 10:
            path = os.path.join(path,"0")
        while offset < lastDigitI:
            path = os.path.join(path,indexStr[offset])
            offset += 1
        path = os.path.join(path, indexStr)
        return self.findFile(index, path)

    def getIndexDir(self, index):
        indexStr = str(index)
        lastDigitI = len(indexStr)-1
        path = self.dir
        offset = 0
        if index < 10:
            path = os.path.join(path,"0")
        while offset < lastDigitI:
            path = os.path.join(path,indexStr[offset])
            offset += 1
        path = os.path.join(path, indexStr)
        if os.path.isdir(path):
            return path
        return False

    def containsAlpha(self, text):
        for char in text:
            if char.isalpha():
                return True
        return False

    def findFile(self, index, dirPath):
        if os.path.isdir(dirPath):
            bookFiles = os.listdir(dirPath)
            textPath = ""
            epubPath = ""
            pdfPath = ""
            rdfPath = ""
            indexStr = str(index)
            for file in bookFiles:
                if "readme" in file or indexStr not in file:
                    continue
                if file.endswith(".txt"):
                    filename, file_extension = os.path.splitext(file)
                    if self.containsAlpha(filename): # This check is debatable
                        continue
                    textPath = os.path.join(dirPath, file)
                elif file.endswith(str(index)+".epub"):
                    epubPath = os.path.join(dirPath, file)
                elif file.endswith(".pdf"):
                    pdfPath = os.path.join(dirPath, file)
                elif file.endswith(".rdf"):
                    rdfPath = os.path.join(dirPath, file)
            # print("zip path:" +os.path.join(path,indexStr+".zip"))
            langs = None
            if not len(rdfPath):
                rdfPath = self.getCacheRDFPath(index) # Cache consistently contains the rdf files
            if len(textPath) or len(epubPath) or len(pdfPath):
                if len(rdfPath):
                    langs = self.getRDFLangs(rdfPath)
                if not langs and len(textPath):
                    langs = self.getLangsFromText(textPath)
                if not langs or not len(langs):
                    langs = ["en"]
                    self.noLangBooks[index] = True

            book = False
            fileFormat = ""
            if len(textPath):
                book = Book(index, textPath, languages=langs)
                if index not in self.books or not self.books[index].path.endswith(".txt"):
                    self.books[index] = book
                    if index in self.epubs:
                        del self.epubs[index]
                    if index in self.pdfs:
                        del self.pdfs[index]
                fileFormat = "txt"
            elif len(epubPath):
                book = Book(index, epubPath, languages=langs)
                if index not in self.books:
                    self.books[index] = book
                    self.epubs[index] = book
                else:
                    bookPath = self.books[index].path
                    if not bookPath.endswith(".txt") and not bookPath.endswith(".epub"):
                        self.books[index] = book
                        self.epubs[index] = book
                fileFormat = "epub"
            elif len(pdfPath):
                book = Book(index, pdfPath, languages=langs)
                if index not in self.books:
                    self.books[index] = book
                    self.pdfs[index] = book
                else:
                    bookPath = self.books[index].path
                    if not bookPath.endswith(".txt") and not bookPath.endswith(".epub"):
                        self.books[index] = book
                        self.pdfs[index] = book
                fileFormat = "pdf"
            else:
                return False
            self.dirBooks[index] = book
            return book
            # txtPath = os.path.join(self.cacheDir,indexStr,"pg"+indexStr+".txt.utf8.gzip")
            # txtPath = os.path.join(bookDir,"pg"+indexStr+".txt.utf8")
            # print("txtPath: "+txtPath)
        return False

    def getCachePath(self, index):
        indexStr = str(index)
        bookPath = os.path.join(self.cacheDir,indexStr)
        return self.findFile(index, bookPath)

    def getCacheRDFPath(self, index):
        cacheDir = self.getCacheDir(index)
        rdfPath = ""
        if cacheDir:
            rdfPath = os.path.join(cacheDir,"pg"+str(index)+".rdf") # Trusting that the format pg<index>.rdf won't change
            if os.path.isfile(rdfPath):
                return rdfPath
        return rdfPath

    def getCacheDir(self, index):
        indexStr = str(index)
        cacheDir = os.path.join(self.cacheDir,indexStr)
        if os.path.isdir(cacheDir):
            return cacheDir
        else:
            return False

    def isBookIndexLine(self, listingLine, bookIndex):
        if listingLine.startswith("<==End of GUTINDEX.ALL==>") or listingLine.startswith("GUTINDEX"):
            return -1
        if str(bookIndex-1) in listingLine or self.lineRegex.match(listingLine):
        # if str(bookIndex-1) in listingLine:
            print("listing line book index: "+listingLine)
            return 1
        return 0

    # Get the information already available in GUTINDEX.ALL, such as the last index.
    def parseIndex(self):
        gutIndexLines = open(os.path.join(self.dir,gutIndexName), 'r').readlines()
        gutIndexLines = list(line for line in gutIndexLines if len(line.strip()))

        lineI = 0
        while "<==LISTINGS==>" not in gutIndexLines[lineI]: # Make sure we're in the listings parts of the index.
            lineI += 1

        while "ETEXT NO." not in gutIndexLines[lineI]: # This is the last non-empty line before the actual listings.
            lineI += 1
        lineI += 1

        # Now with confidence, find the number that ends the current line.
        listingLine = gutIndexLines[lineI].strip()
        numIndex = len(listingLine)-1
        foundC = False
        if listingLine[numIndex] == "C": # Sometimes there's a C following the index number, for "copyright".
            numIndex -= 1
            foundC = True

        while listingLine[numIndex].isdigit() or listingLine[numIndex]=="C":
            numIndex -= 1

        if foundC:
            self.lastIndex = int(listingLine[numIndex:-1])
        else:
            self.lastIndex = int(listingLine[numIndex:]) # This is the number of the last (and highest) book index.
        print("Number of books listed in Gutenberg index: "+str(self.lastIndex))

        self.unlisted = [] # e.g. "42850 Not in the Posted Archives"
        for i in range(self.lastIndex+1):
            self.dirBooks.append(None)
        title = ""
        language = DEFAULT_LANGUAGE
        bookIndex = self.lastIndex
        while not listingLine.startswith("<==End of GUTINDEX.ALL==>"):
            # listingLine = gutIndexLines[lineI].strip()
            while not self.isBookIndexLine(listingLine, bookIndex):
                lineI += 1
                listingLine = gutIndexLines[lineI].strip()
            print("listingLine: "+listingLine)
            numIndex = len(listingLine)-1
            foundC = False
            if listingLine[numIndex] == "C": # Sometimes there's a C following the index number, for "copyright".
                numIndex -= 1
                foundC = True

            if not listingLine[numIndex].isdigit(): # e.g. "42850 Not in the Posted Archives"
                endNumIndex = 0
                while not listingLine[numIndex].isdigit(): # Find the last index of the book index
                    numIndex -= 1
                endNumIndex = numIndex
                while numIndex > -1 and listingLine[numIndex].isdigit(): # Find the first index of the book index
                    numIndex -= 1

                print("unlisted book index:"+str(listingLine[numIndex+1:endNumIndex+1]))
                bookIndex = int(listingLine[numIndex+1:endNumIndex+1])
                # self.unlisted.append(bookIndex)
                lineI += 1
                listingLine = gutIndexLines[lineI].strip()
                continue

            while listingLine[numIndex].isdigit(): # Find the first index of the book index
                numIndex -= 1

            if foundC:
                bookIndex = int(listingLine[numIndex+1:-1])
                foundC = False
            else:
                bookIndex = int(listingLine[numIndex+1:]) # This is the number of the last (and highest) book index.
            # print("bookIndex: "+str(bookIndex))
            title = listingLine[:numIndex].strip()
            # print("title: "+title)
            # If language is identified, parse the language name
            lineI += 1
            listingLine = gutIndexLines[lineI].strip()
            while not self.isBookIndexLine(listingLine, bookIndex):
                if listingLine.startswith("[Language:"):
                    language = listingLine.split()[1][:-1] # -1 to remove the ending bracket
                    # print("found language: "+language)
                lineI += 1
                listingLine = gutIndexLines[lineI].strip()

            self.dirBooks[bookIndex] = Book(bookIndex, language, title)
            language = "English" # Reset to default language
            listingLine = gutIndexLines[lineI].strip()
            if listingLine.startswith("GUTINDEX"): # Found new GUTINDEX section
                while not listingLine.endswith("ETEXT NO."):
                    lineI += 1
                    listingLine = gutIndexLines[lineI].strip()
            if listingLine.endswith("ETEXT NO."): # Found posting dates section
                lineI += 1
                listingLine = gutIndexLines[lineI].strip()

            if bookIndex < 50000:
                break

    def loadList(self):
        self.languages = {}
        with open(self.dir, 'r') as listFile:
            lang = "en"
            fileFormat = "txt"
            for line in listFile:
                line = line.strip()
                if len(line):
                    splitLine = line.split()
                    if len(splitLine) > 2 and splitLine[1] == "FORMAT":
                        fileFormat = splitLine[2][:-1] # Don't include the colon
                        self.languages[lang][fileFormat] = []
                        continue
                    elif len(splitLine) > 1 and splitLine[0] == "LANGUAGE":
                        lang = splitLine[1][:-1] # Don't include the colon
                        self.languages[lang] = {}
                        continue
                    else:
                        path = line
                        self.languages[lang][fileFormat].append(Book(path=path))

    def loadCorpus(self):
        # self.parseIndex()
        # for bookI in range(self.lastIndex+1):
        #     if not self.dirBooks[bookI]:
        #         self.unlisted.append(bookI)
        if os.path.isfile(self.dir):
            self.loadList()
            return
        bookI = 1
        numMissing = 0
        missingThreshold = 100
        tempUnlisted = []
        # Search Gutenberg directory structure
        while 1: # We don't know yet how many books there are (the index may not be up to date)
            book = self.getIndexPath(bookI)
            # print("Book path for "+str(bookI)+": "+str(bookPath))
            if not book:
                numMissing += 1
                if numMissing > missingThreshold:
                    break
                else:
                    tempUnlisted.append(bookI)
                    bookI += 1
                    continue
            bookPath = book.path
            if len(tempUnlisted):
                self.unlisted.extend(tempUnlisted)
                tempUnlisted = []
            numMissing = 0

            newBook = Book(bookI, bookPath)
            self.dirBooks[bookI] = newBook
            bookI += 1
        print("Number of books found in Gutenberg directories: "+str(len(self.dirBooks)))
        print("Number of book indices skipped: "+str(len(self.unlisted)))
        self.cacheBooks = {}
        cacheUnlisted = []
        # Search cache
        bookI = 1
        numMissing = 0
        tempUnlisted = []
        while 1: # We don't know yet how many books there are (the index may not be up to date)
            book = self.getCachePath(bookI)
            # print("Book path for "+str(bookI)+": "+str(txtPath))
            if not book:
                numMissing += 1
                if numMissing > missingThreshold:
                    break
                else:
                    tempUnlisted.append(bookI)
                    bookI += 1
                    continue

            bookPath = book.path
            if len(tempUnlisted):
                cacheUnlisted.extend(tempUnlisted)
                tempUnlisted = []
            numMissing = 0

            newBook = Book(bookI, bookPath)
            self.cacheBooks[bookI] = newBook
            bookI += 1
        print("Number of text books found in cache: "+str(len(self.cacheBooks)))
        print("Number of book indices not found as text books in cache: "+str(len(cacheUnlisted)))
        foundStr = "Indices in cache but not in directory structure:\n"
        notFoundStr = "Indices not in either cache or directory structure:\n"
        foundCount = 0
        dirFoundCount = 0
        notFoundCount = 0
        notFoundList = []
        cacheOnlyList = []
        dirOnlyList = []
        dirFoundStr = ""
        # dirFoundStr += "Indices in directory structure but not in cache:\n"
        for bookI in self.unlisted:
            if bookI in self.cacheBooks:
                foundStr += str(bookI)+", "
                cacheOnlyList.append(bookI)
                foundCount += 1
            else:
                notFoundStr += str(bookI)+", "
                notFoundList.append(bookI)
                notFoundCount += 1
        foundStr += "\n"
        foundStr += "Total books found only in cache: "+str(foundCount)+"\n"
        print(foundStr)
        for bookI in cacheUnlisted:
            if bookI in self.dirBooks:
                # dirFoundStr += str(bookI)+", "
                dirOnlyList.append(bookI)
                dirFoundCount += 1
        # dirFoundStr += "\n"
        dirFoundStr += "Total books found only in directory structure: "+str(dirFoundCount)+"\n"
        print(dirFoundStr)
        print("Books found as epubs but not txt: "+str(len(self.epubs)))
        for bookI in self.epubs:
            print(self.epubs[bookI])
        print("\nBooks found as pdfs but not txt: "+str(len(self.pdfs)))
        for bookI in self.pdfs:
            print(self.pdfs[bookI])
        print("Total books not found in either cache or directory structure: "+str(notFoundCount)+"\n")
        print(notFoundStr+"\n")
        # Print all files in cache directories of unfound books
        for bookI in notFoundList:
            cacheDir = self.getCacheDir(bookI)
            if cacheDir:
                print("Cache files for "+str(bookI)+": "+str(os.listdir(cacheDir)))
            else:
                print("No cache directory found for "+str(bookI))
            dirDir = self.getIndexDir(bookI)
            if dirDir:
                print("Directory structure files for "+str(bookI)+": "+str(os.listdir(dirDir)))
            else:
                print("No directory files for "+str(bookI))
            print("")
        for index, book in self.books.items():
            langs = book.languages
            filename, file_extension = os.path.splitext(book.path)
            for lang in langs:
                self.addBookLang(lang, book, file_extension[1:]) # Don't include dot in file extension
        print("\n== Languages: ==")
        for lang, formats in self.languages.items():
            totalLang = 0
            for fileFormat, books in formats.items():
                totalLang += len(books)
                print(lang+": "+fileFormat+": "+str(len(books)))
            print("Total for "+lang+": "+str(totalLang)+"\n")
        print("Books for which no language was found (defaulted to "+DEFAULT_LANGUAGE+"): "+str(len(self.noLangBooks)))
        for book in self.noLangBooks:
            print(book, end='')
        print("")

    def list(self):
        listStr = ""
        for lang, fileFormats in self.languages.items():
            listStr += "\n LANGUAGE "+lang+":\n"
            for fileFormat, books in fileFormats.items():
                listStr += "\n FILE FORMAT "+fileFormat+":\n"
                for book in books:
                    listStr += book.path+"\n"
        return listStr

    def placeFile(self, command, bookPath, targetPath):
        bookTarget = ""
        if "/" in bookPath:
            bookTarget = os.path.join(targetPath, ntpath.basename(bookPath))
        else:
            bookTarget = os.path.join(targetPath, bookTarget)
        if command == "move":
            shutil.move(bookPath, bookTarget)
        elif command == "copy":
            shutil.copy(bookPath, bookTarget)

    def organizeFiles(self, command, target_path):
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        for lang, fileFormats in self.languages.items():
            langPath = os.path.join(target_path, lang)
            if not os.path.exists(langPath):
                os.makedirs(langPath)
            for fileFormat, books in fileFormats.items():
                formatPath = os.path.join(langPath, fileFormat)
                if not os.path.exists(formatPath):
                    os.makedirs(formatPath)
                for book in books:
                    self.placeFile(command, book.path, formatPath)


class Book:
    def __init__(self, index=-1, path="", languages=["en"], title=""):
        self.index = index
        self.languages = languages
        self.filetypes = []
        self.title = title
        self.path = path

    def __str__(self):
        return "Book index: "+str(self.index)+" path: "+str(self.path)


class Language:
    def __init__(self, name):
        self.name = name
        self.dirBooks = []
        self.filetypes = []

    def addBook(self, book):
        self.dirBooks.append(book)


gutenberg = Gutenberg(args.gutenberg_dir)
gutenberg.loadCorpus()

if args.command == 'list':
    outStr = gutenberg.list()

    targetFile = open(args.target_path, 'w')
    targetFile.write(outStr)
elif args.command == 'move' or args.command == 'copy':
    gutenberg.organizeFiles(args.command, args.target_path)

# gutenberg-file-manager
File manager for Gutenberg directory structure on local machine.  
Performs a fairly comprehensive search on the files within the Gutenberg directories on a local machine, finds all text files (alternatively epubs and then pdfs if no txt file is found), and organizes them first by language and then by file format (txt, epub, pdf).  
After performing list, you can use list's output file for move and copy, and you can edit list's file as you please for this purpose. An example list file is provided (gutenberg.list) for your convenience (with absolute paths removed), as well as an example output file with statistics about the corpus.  

## Example commands
python3 gutenberg-file-manager/gutenberg_file_finder.py list gutenberg.readingroo.ms/gutenberg gutenberg.list > gutenberg.out  
python3 gutenberg-file-manager/gutenberg_file_finder.py copy gutenberg.list gutenberg_organized

Note: I recommend redirecting standard out to a file when running 'list', as it outputs quite a lot.

usage: Finds text files in the project Gutenberg corpus by language  
       [-h] {list,move,copy} gutenberg_dir target_path  

positional arguments:  
  {list,move,copy}  enter 'list' to list the proposed file organization; enter  
                    'move' to move files into organized directories; enter  
                    'copy' to copy files instead  
  gutenberg_dir     the directory where project gutenberg files are found.  
                    e.g. gutenberg.readingroo.ms/gutenberg. If a file (from  
                    'list') is entered instead of a directory, the file is  
                    used instead of searching the gutenberg directories  
  target_path       the directory where the files are placed; if 'list' is  
                    chosen, the name of the file to write the listed files  

Developed using a copy of Gutenberg's corpus pulled from the mirror ftp://gutenberg.readingroo.ms/gutenberg/  
For University of Washington CLMS students.

## Known Issues
The list functionality is not built for efficiency (takes a couple minutes on a very fast machine), because many repetitive dictionary calls are made, instead of using indices or choosing not to gather statistics about the corpus.

This program could be added upon to allow specifying specific file extensions or searching for audio files instead (there are many).

There appear to be 10 books that have a pdf folder containing multiple (or at least one) pdf files. For example, one contains sheet music for different instrumental parts. Another contains different separate parts of a book. Currently these books are ignored.

Another funtionality to add is converting epub and pdf files to text automatically.

Note that some files starts with "pg" (those from cache), particularly the epub files. It may be worth normalizing moved or copied file names in the future.

Books with multiple languages are added to each language. Languages for each book are taken from the book's respective rdf file. If no rdf file or language is found for a book, the book's text is parsed to find the languages (indicated by "Language: language1, language2").
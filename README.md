# wikipedia-chronam

Compile a number of statistics on how Chronicling America is used by Wikipedia editors

[Linkypedia](http://linkypedia.inkdroid.org/websites/4/) was first used to obtain a list of Wikipedia pages containing (or having every contained) [Chronicling America](http://chroniclingamerica.loc.gov/) links.  Then we export a complete page revision history from Wikipedia as XML and finally extract the desired statistics into CSV files.


## Files

[pages.txt](pages.txt) - list of matching Wikipedia pages from Linkypedia

[export.py](export.py) - export page revision history from Wikipedia using 

[parse.py](parse.py) - extract revision statistics per page (edits.csv and editors.csv)

## License

[CC0](http://creativecommons.org/publicdomain/zero/1.0/)

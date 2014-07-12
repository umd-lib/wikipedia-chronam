import os
import re
import sys
import httplib, urllib

# http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
def slugify(value):
    """
    Normalizes string, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip())
    re.sub('[-\s]+', '-', value)
    return str(value)

# Create base directory for exported pages
PAGES='pages'
if not os.path.isdir(PAGES):
    os.mkdir(PAGES)

# Process each page, one per line, from the input file
count = 0
with open('pages.txt') as f:
    for page in f:
        count += 1
        page = page.rstrip('\r\n')
        print count, page

        # Create file name from page name
        filename = slugify(page) + '.xml'

        # create target directory
        initial = filename[0]
        
        dir = os.path.join(PAGES, initial)
        if not os.path.isdir(dir):
            os.mkdir(dir)

        outfile = os.path.join(dir, filename)

        if not os.path.exists(outfile):
            try:
                # Export the page from Wikipedia
                params = urllib.urlencode({'catname': '', 'pages': page})
                headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
                conn = httplib.HTTPConnection("en.wikipedia.org")
                conn.request("POST", "/w/index.php?title=Special:Export&action=submit", params, headers)
                response = conn.getresponse()
                print 'Return: ', response.status, response.reason
                data = response.read()
                conn.close()
            except:
                print 'Error exporting ', page, ': ', sys.exc_info()[0]
                continue

            # Write out to file
            with open(outfile, 'w') as out:
                out.write(data)

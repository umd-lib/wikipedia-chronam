import xml.etree.ElementTree as ET
import re
import sys
import os
import csv
from urllib.parse import quote

if sys.version_info[0] < 3:
    raise Exception("This script requires Python 3")
    
def main():
    filenameParam = sys.argv[1]
    
    with open('edits.csv', 'w') as csvfileEdits:
        csvEdits = csv.writer(csvfileEdits, quoting=csv.QUOTE_ALL)
        csvEdits.writerow(['Page','Page Link','Revision ID','Editor','Timestamp','Comment','#Additions',' #Deletions', 'URLs','Categories'])

        # single file
        if os.path.isfile(filenameParam):
            parse(filenameParam, csvEdits)
            
        # directory to be traversed
        elif os.path.isdir(filenameParam):
            for (dirpath, dirnames, filenames) in os.walk(filenameParam):
                for name in filenames:
                    filename = os.path.join(dirpath, name)
                    parse(filename, csvEdits)
    
def parse(filename=None, csvEdits=None):
    tree = ET.parse(filename)
    root = tree.getroot()

    page = root.find('./{http://www.mediawiki.org/xml/export-0.8/}page')
    
    if page:
        title = page.find('./{http://www.mediawiki.org/xml/export-0.8/}title').text
        print("Parsing '{0}'".format(title))
      
        # setup the previous revision (there is none at this point)
        revParsedPrev = {'url' : set()}
        
        for revision in page.findall('./{http://www.mediawiki.org/xml/export-0.8/}revision'):
            # Extract desired elements from a single revision
            revParsed = parseRevision(revision)
    
            # Check for URL changes
            if revParsedPrev['url'] != revParsed['url']:
                additions = revParsed['url'] - revParsedPrev['url']
                deletions = revParsedPrev['url'] - revParsed['url']
    
                if 'username' in revParsed:
                    editor = revParsed['username']
                elif 'ip' in revParsed:
                    editor = revParsed['ip']
                else:
                    editor = '?'

                if csvEdits:
                    row = [                    
                           title,
                           'http://en.wikipedia.org/wiki/' + quote(title.replace(' ','_')),
                           revParsed['revid'],
                           editor,
                           revParsed['timestamp'],
                           revParsed['comment'],
                           str(len(additions)),
                           str(len(deletions)),
                           " | ".join(revParsed['url']),
                           " | ".join(revParsed['category']),
                           ]
                    csvEdits.writerow(row)
                    
            revParsedPrev = revParsed

def parseRevision(revision):
    '''Parse a single revision for the desired elements'''
    ret = {
           'revid' : None,
           'timestamp' : None,
           'comment' : None,
           'text' : None,
           'url' : set(),
           'category' : [],
           }

    for child in revision:
        # revision id
        if (child.tag == '{http://www.mediawiki.org/xml/export-0.8/}id'):
            ret['revid'] = child.text

        # timestamp            
        elif (child.tag == '{http://www.mediawiki.org/xml/export-0.8/}timestamp'):
            ret['timestamp'] = child.text

        # contributor - username or ip
        elif (child.tag == '{http://www.mediawiki.org/xml/export-0.8/}contributor'):
            for e in child:
                if (e.tag == '{http://www.mediawiki.org/xml/export-0.8/}username'):
                    ret['username'] = e.text
                elif (e.tag == '{http://www.mediawiki.org/xml/export-0.8/}ip'):
                    ret['ip'] = e.text
                
        # comment                
        elif (child.tag == '{http://www.mediawiki.org/xml/export-0.8/}comment'):
            ret['comment'] = child.text
            
        # page text
        elif (child.tag == '{http://www.mediawiki.org/xml/export-0.8/}text'):
            text = child.text

            if text:
                # Extract Chronicling America URLs and Page Categories           
                for match in re.findall("(http://chroniclingamerica.loc.gov/[^\s\|]+)|(?:\[\[Category:(.*?)\]\])", text,re.MULTILINE):
                    if match[0]:
                        ret['url'].add(match[0])
                    elif match[1]:
                        ret['category'].append(match[1])
    
    return(ret)
    
main()
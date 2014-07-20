import xml.etree.ElementTree as ET
import re
import sys
import os
import csv
from urllib.parse import quote
import difflib
from collections import defaultdict

if sys.version_info[0] < 3:
    raise Exception("This script requires Python 3")
    
def main():
    filenameParam = sys.argv[1]
    
    with open('edits.csv', 'w', 1) as csvfileEdits:
        csvEdits = csv.writer(csvfileEdits, quoting=csv.QUOTE_ALL)
        csvEdits.writerow(['Page','Page Link','Revision ID','Editor','Timestamp','Comment','#Additions',' #Deletions', 'URLs','Categories'])

        with open('editors.csv', 'w', 1) as csvfileEditors:
            csvEditors = csv.writer(csvfileEditors, quoting=csv.QUOTE_ALL)
            csvEditors.writerow(['Page','Page Link','Editor','Additions', 'Deletions', 'Total Additions', 'Total Deletions', 'Percent Contribution'])

            # single file
            if os.path.isfile(filenameParam):
                parse(filenameParam, csvEdits, csvEditors)
       
            # directory to be traversed
            elif os.path.isdir(filenameParam):
                for (dirpath, dirnames, filenames) in os.walk(filenameParam):
                    for name in filenames:
                        filename = os.path.join(dirpath, name)
                        parse(filename, csvEdits, csvEditors)
    
def parse(filename=None, csvEdits=None, csvEditors=None):
    '''Parse a single file, which is a single Wikipedia Page'''
    tree = ET.parse(filename)
    root = tree.getroot()

    page = root.find('./{http://www.mediawiki.org/xml/export-0.8/}page')
    
    if page:
        # Track Editors - all edit counts
        diffs = defaultdict(lambda: defaultdict(int))
        
        # Track Editors - editors which make a matching URL change
        editors = set()

        title = page.find('./{http://www.mediawiki.org/xml/export-0.8/}title').text
        print("Parsing '{0}'".format(title))
      
        pageUrl = 'http://en.wikipedia.org/wiki/' + quote(title.replace(' ','_'))

        # setup the previous revision (there is none at this point)
        revParsedPrev = {'url' : set(), 'text' : ''}
        
        for revision in page.findall('./{http://www.mediawiki.org/xml/export-0.8/}revision'):
            # Extract desired elements from a single revision
            revParsed = parseRevision(revision)

            # Determine the editor
            if 'username' in revParsed:
                editor = revParsed['username']
            elif 'ip' in revParsed:
                editor = revParsed['ip']
            else:
                editor = '?'

            # Compute character diffs (additions and deletions) for this edit
            (additionsChar, deletionsChar) = diff(revParsedPrev['text'], revParsed['text'])
            
            # Accumulate diffs for each editor
            diffs[editor]['add'] += additionsChar
            diffs[editor]['del'] += deletionsChar
            
            # Check for URL changes
            if revParsedPrev['url'] != revParsed['url']:
                
                # This edit made a Chronicling America URL change
                additionsUrl = revParsed['url'] - revParsedPrev['url']
                deletionsUrl = revParsedPrev['url'] - revParsed['url']

                # Track the editor
                editors.add(editor)
                    
                if csvEdits:
                    row = [                    
                           title,
                           pageUrl,
                           revParsed['revid'],
                           editor,
                           revParsed['timestamp'],
                           revParsed['comment'],
                           str(len(additionsUrl)),
                           str(len(deletionsUrl)),
                           " | ".join(revParsed['url']),
                           " | ".join(revParsed['category']),
                           ]
                    csvEdits.writerow(row)
                    
            revParsedPrev = revParsed
    
        # Report contributing editors
        if csvEditors:
            addTotal = sum([diffs[editor]['add'] for editor in diffs.keys()])
            delTotal = sum([diffs[editor]['del'] for editor in diffs.keys()])
             
            for editor in editors:
                addEditor = diffs[editor]['add']
                delEditor = diffs[editor]['del']
                
                row = [                    
                       title,
                       pageUrl,
                       editor,
                       addEditor,
                       delEditor,
                       addTotal,
                       delTotal,
                       "{:.2%}".format((addEditor + delEditor) / (addTotal + delTotal))
                       ]
                csvEditors.writerow(row)

                
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
                
                ret['text'] = text
                
    return(ret)

def diff(a, b):
    '''Compute count of character additions and deletions between two strings'''

    s = difflib.SequenceMatcher(None, a, b, autojunk=False)

    aLength = len(a)
    bLength = len(b)

    # Get count of characters the same in each string
    countSame = sum([block[2] for block in s.get_matching_blocks()]) 

    return (bLength - countSame, aLength - countSame)

main()
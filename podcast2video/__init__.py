import re
import sys
from podcast2video import process_feed

URL_REGEX = re.compile(
        r'^https?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

HELP_MESSAGE = '''Usage: podcast2video [options ...] feedURL [ [options ...]

Options:
  --all   Grabs all of the podcasts in the feed, rather than just
          the first one
  --help  Shows this helpful message

This downloads the most recent podcast in the podcast feed, as well as its
poster image, and creates a video of the podcast, with the poster image as every
frame of the video. 'feedURL' must be the valid URL of a valid podcast RSS feed.
'''

def main():
    """Entry point for the application script"""
    # process all the command line parameters
    process_all = False
    feed_url = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--all':
                process_all = True
            elif arg == '--help':
                print HELP_MESSAGE
                sys.exit()
            elif URL_REGEX.match(arg):
                feed_url = arg
            else:
                print 'Invalid argument "%s". Type "%s --help" for info.' % (arg, sys.argv[0])
                sys.exit()

    if feed_url == False:
        print 'No feed URL specified. Type "%s --help" for info.' % sys.argv[0]
    else:
        process_feed( feed_url, process_all )

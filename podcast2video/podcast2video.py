#!/usr/bin/python
"""This module illustrates how to write your docstring in OpenAlea
and other projects related to OpenAlea."""

__license__   = 'LGPLv3'
__docformat__ = 'reStructuredText'

import feedparser
import os
import re
import shutil
import sys
from bs4 import BeautifulSoup
from urllib2 import urlopen, URLError, HTTPError, Request
from urlparse import urlparse

TEMP_DIR = '/tmp/podcast2video/'

IMAGE_REGEX = re.compile('https?:\/\/.*?\.(png|jpg)')

# Expand image canvas to 1920x1080 with a black background.
#   convert PODCAST_ART.png -background black -gravity center -extent 1920x1080 RESIZED_PODCAST_ART.png
CMD_RESIZE_IMAGE = 'convert %s -background black -gravity center -extent 1920x1080 %s'

# Make a silent video out of the PNG that is the length of the podcast audio:
#    ffmpeg -loop 1 -i PODCAST_ART.png -c:v libx264 -t PODCAST_LENGTH_SECONDS -pix_fmt yuv420p SILENT.mp4
CMD_CREATE_VIDEO = 'ffmpeg -loop 1 -i %s -c:v libx264 -t %s -pix_fmt yuv420p %s'

# Add the podcast audio to the video we just created:
#    ffmpeg -i SILENT.mp4 -i PODCAST_AUDIO.mp3 -c:v copy -c:a aac -strict experimental PODCAST_VIDEO.mp4
CMD_ADD_AUDIO = 'ffmpeg -i %s -i %s -c:v copy -c:a aac -strict experimental %s'

def download_file(url, path):
    """Download a file and save it to a specific path.
    :param url: URL of the file to download
    :param path: path to save the file to
    """
    path = path.replace('%20', '_')
    if not os.path.exists(path):
        try:
            req = Request(url, headers={'User-Agent' : 'podcast2video'})
            f = urlopen(req)

            # Open our local file for writing
            with open(path, "wb") as local_file:
                local_file.write(f.read())

        except HTTPError, e:
            print "HTTP Error:", e.code, url
        except URLError, e:
            print "URL Error:", e.reason, url
    else:
        print "Already downloaded %s" % path

def convert_podcast(podcast_url, podcast_image_url, podcast_length, output_dir):
    """Convert a podcast from a given URL to a video file
    :param podcast_url: URL of the podcast file to download
    :param podcast_image_url: URL of the podcast image to download
    :param podcast_length: length of the podcast in seconds
    """
    if podcast_image_url == '':
        podcast_image_url = 'http://www.onepeterfive.com/wp-content/uploads/2016/10/E38-2.png'

    podcast_file_name = podcast_url.split('/')[-1]
    podcast_image_file_name = podcast_image_url.split('/')[-1]
    video_file_name = podcast_file_name.split('.mp3')[0] + '.mp4'

    # if the video doesn't already exist, download the files and convert
    if not os.path.exists(output_dir + video_file_name):

        img_download_path = TEMP_DIR + podcast_image_file_name
        img_resized_path = TEMP_DIR + 'resized_' + podcast_image_file_name
        print 'Downloading podcast artwork "%s"' % (podcast_image_url)
        download_file( podcast_image_url, img_download_path )

        # Up-size the image to 1080p by expanding the canvas and filling with white
        os.system(CMD_RESIZE_IMAGE % (img_download_path, img_resized_path))

        print 'Downloading podcast "%s"' % (podcast_url)
        download_file( podcast_url, TEMP_DIR + podcast_file_name )

        # If the silent video has not already been created, render it
        if not os.path.exists(TEMP_DIR + video_file_name):
            command = CMD_CREATE_VIDEO % (img_resized_path, podcast_length, TEMP_DIR + video_file_name)
            print(command)
            os.system(command)

        # Add audio to silent video
        command = CMD_ADD_AUDIO % (TEMP_DIR + video_file_name, TEMP_DIR + podcast_file_name, output_dir + video_file_name)
        print(command)
        os.system(command)

def process_entry(entry, output_dir):
    """process an entry fromt he feed. We're extracting the podcast URL, podcast
    image URL, and length of the podcast
    :param entry: entry in a podcast RSS feed
    """
    # Time format of <itunes:duration> may be in either hh:mm:ss format,
    # or an integer containing seconds. So we convert everything to seconds.
    l = map(int, entry.itunes_duration.split(':'))
    podcast_length = sum(n * sec for n, sec in zip(l[::-1], (1, 60, 3600)))

    # grab podcast URL
    podcast_url = ''
    for link in entry.links:
        if link.rel == 'enclosure':
            podcast_url = link.href

    # check for podcast image. If entry.image exists, get its value.
    # as a fall back, parse the content for image URLs.
    podcast_image_url = ''
    if entry.has_key('image'):
        podcast_image_url = entry.image.href
    else:
        for content in entry.content:
            soup = BeautifulSoup(content.value, 'html.parser')
            img = soup.find('img')
            if(img):
                podcast_image_url = img['src'];

    if podcast_image_url == '':
        for content in entry.content:
            imgs = IMAGE_REGEX.search( content.value )
            if imgs:
                podcast_image_url = imgs.group()

    convert_podcast(podcast_url, podcast_image_url, podcast_length, output_dir)

def process_feed(feed_url, process_all):
    # parse feed
    parsed = feedparser.parse(feed_url)

    # Create output directory from feed name.
    feed_name = parsed['feed']['title'].replace(' ', '_')
    output_dir = './' + feed_name + '/'
    for create_dir in [TEMP_DIR, output_dir]:
        if not os.path.exists(create_dir):
            os.makedirs(create_dir)

    # grab entries from feed and process them
    if process_all == True:
        print 'Processing all podcasts from feed'
        for entry in parsed.entries:
            process_entry(entry, output_dir)
    else:
        print 'Processing latest podcast from feed'
        process_entry(parsed.entries[0], output_dir)

    # delete temp directory when we're done. Cleaning up is a good thing.
    shutil.rmtree(TEMP_DIR)

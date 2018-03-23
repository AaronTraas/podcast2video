#!/usr/bin/python
"""Utilities to convert a podcast given an RSS feed from MP3 to video."""

__license__   = 'LGPLv3'
__docformat__ = 'reStructuredText'

import feedparser
import os
import shutil
import sys
import tempfile
from bs4 import BeautifulSoup
from urllib2 import urlopen, URLError, HTTPError, Request
from urlparse import urlparse

# If larger than 1280x720, resize down to fit in 1280x720, and fill background
# with black if aspect ratio is different
#   convert 1P5-PODCAST_ART.png -resize 1280x720\> -background black -gravity center -extent 1280x720 RESIZED_PODCAST_ART.png
CMD_RESIZE_IMAGE = 'convert %s -resize 1280x720\> -background black -gravity center -extent 1280x720 %s'

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

def convert_podcast(podcast_name, podcast_url, podcast_image_url, podcast_length, output_dir):
    """Convert a podcast from a given URL to a video file
    :param podcast_name: Name of the podast (human readable string from feed)
    :param podcast_url: URL of the podcast file to download
    :param podcast_image_url: URL of the podcast image to download
    :param podcast_length: length of the podcast in seconds
    :param output_dir: Where we're storing the final video that we render
    """

    # figure out what we're naming the video rendering of the podcast
    podcast_file_name = podcast_url.split('/')[-1]
    video_file_name = podcast_file_name.split('.mp3')[0] + '.mp4'

    # if the video doesn't already exist, download the files and convert
    if not os.path.exists(output_dir + video_file_name):
        try:
            # Create temporary directory. All file writes, until the very end,
            # will happen in this directory, so that no matter what we do, it
            # won't hose existing stuff.
            temp_dir = tempfile.mkdtemp("podcast2video") + '/'

            # download image
            podcast_image_file_name = podcast_image_url.split('/')[-1]
            img_download_path = temp_dir + podcast_image_file_name
            img_resized_path = temp_dir + 'resized_' + podcast_image_file_name
            print 'Downloading podcast artwork "%s"' % (podcast_image_url)
            download_file(podcast_image_url, img_download_path)

            # Up-size the image to 1080p by expanding the canvas and filling with white
            os.system(CMD_RESIZE_IMAGE % (img_download_path, img_resized_path))

            # download podcast
            print 'Downloading podcast "%s"' % (podcast_url)
            download_file(podcast_url, temp_dir + podcast_file_name)

            # If the silent video has not already been created, render it
            if not os.path.exists(temp_dir + video_file_name):
                command = CMD_CREATE_VIDEO % (img_resized_path, podcast_length, temp_dir + video_file_name)
                print(command)
                os.system(command)

            # Add audio to silent video
            command = CMD_ADD_AUDIO % (temp_dir + video_file_name, temp_dir + podcast_file_name, output_dir + video_file_name)
            print(command)
            os.system(command)
        finally:
            # Ensure that temporary directory gets deleted no matter what
            shutil.rmtree(temp_dir)

def process_entry(podcast_name, podcast_image_url, entry, output_dir):
    """process an entry from the feed. We're extracting the podcast URL, podcast
    image URL, and length of the podcast
    :param podcast_name: Name of the podast (human readable string from feed)
    :param podcast_image_url: Image representing the podcast
    :param entry: entry in a podcast RSS feed
    :param output_dir: Where we're storing the final video that we render
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

    # check for podcast image. Otherwise fall back on feed image
    if entry.has_key('image'):
        podcast_image_url = entry.image.href

    # if there's no feed image or episode image, scrape the content for an
    # image. Gettin' to the bottom of the barrel here!
    if podcast_image_url == '':
        for content in entry.content:
            soup = BeautifulSoup(content.value, 'html.parser')
            img = soup.find('img')
            if(img):
                podcast_image_url = img['src'];

    # if we still got nothin, generate an image.
    if podcast_image_url == '':
        podcast_image_url = 'http://fpoimg.com/1920x1080?text=' + podcast_name

    convert_podcast(podcast_name, podcast_url, podcast_image_url, podcast_length, output_dir)

def process_feed(feed_url, process_all):
    """process an RSS feed, converting podcasts in the feed from audio to video
    :param feed_url: URL of the RSS feed
    :param process_all: if true, process entire feed. Otherwise,
                        only process the latest entry in the feed.
    """

    # parse feed
    parsed = feedparser.parse(feed_url)
    if 'media_thumbnail' in parsed['channel']:
        podcast_image = parsed['channel']['media_thumbnail'][0]['url'];
    elif 'image' in parsed['channel']:
        podcast_image = parsed['channel']['image']['href'];
    else:
        podcast_image = ''

    # Create output directory from feed name.
    podcast_name = parsed['feed']['title'].replace(' ', '_')
    output_dir = './' + podcast_name + '/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # grab entries from feed and process them
    if process_all == True:
        print 'Processing all podcasts from feed'
        for entry in parsed.entries:
            process_entry(podcast_name, podcast_image, entry, output_dir)
    else:
        print 'Processing latest podcast from feed'
        process_entry(podcast_name, podcast_image, parsed.entries[0], output_dir)

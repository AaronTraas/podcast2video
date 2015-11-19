==================================================
podcast2video -- audio to video conversion utility
==================================================

This is a utility to convert one or more episodes from a podcast, given an RSS
feed as an input, to .mp4 video files for upload to YouTube.

This was inspired by listening to an episode of Cortex_, where Myke mentioned
that he purchased a copy of Logic Pro just to encode podcasts, with a static
repeated for every frame of the video, for uploading the podcast to YouTube. My
first thought was "I bet I could do that on the command line with `ffmpeg`".

So with a little bit of web searching, I came to the following solution::

    ffmpeg -loop 1 -i PODCAST_ART.png -c:v libx264 -t PODCAST_LENGTH_SECONDS -pix_fmt yuv420p SILENT.mp4
    ffmpeg -i SILENT.mp4 -i PODCAST_AUDIO.mp3 -c:v copy -c:a aac -strict experimental PODCAST_VIDEO.mp4

Then a friend asked me to help him convert his podcast to a bunch of video
files, so I wrapped a python script around those commands that parsed his RSS
feed, grabbed the audio and the show title image, and rendered all the videos.
This worked great, but it was messy, a pain to use for non-developers, required
the installation of both ImageMagick and `ffmpeg` via Homebrew or similar, etc.

So I decided to make a more generic version. I aim to make this PyPi compatible,
as my first somewhat serious python project. I've eliminated the need to install
ImageMagick, but not `ffmpeg`. I'm currently evaluating various ffmpeg-like
Python packages, but I'm not there yet.

This is very early software. Use with caution. This has only ever been tested on
MacOS 10.9. Test this on your local machine  by first installing `ffmpeg` with
homebrew::

    brew install ffmpeg

Then checking out this repo, and installing through pip locally::

    sudo pip install -e .

Then try grabbing the latest episode of a podcast::

    podcast2video http://feeds.theincomparable.com/robot

Robot Or Not chosen because it's really short, so the encoding is fast.

.. _Cortex: https://www.relay.fm/cortex

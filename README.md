# Shark Scraper
The idea is to download videos where drones took footage of sharks. This info
can be obtained from YouTube or other sources, but the first one is the easiest one.

While making a search by myself, I found out there are some channels where the 
videos are filmed by drones and most of them are about sharks. But neither the 
title nor the description had the word "drone", so, they are in a separated 
category called approved videos. They will be scraped only with the word "shark" 
or "great white", and those videos are safe. They are some small exceptions which 
will be in the disapproved titles' category. On the other hand, there are some 
channels that have the words drone and shark but the videos are about how to use a 
drone, they do not have actual footage of sharks.

### Approved Channels:
* SouthForkSalt
* GreatWhiteDronE
* theroguedroner
* DroneSharkApp
* TheMalibuArtist
* hydrophilik6666

### Disapproved Channels:
* UltimateDroneFishing

There are 3 ways to get the info:
* YouTube API
* Selenium library
* Pytube

The first one won't be used since it has a limit. The second one has the problem
with speed, since you are imitating a human being. And the third one is the
current choice for finishing the program.

There are already some csv files with the information of each video:
* notSafeVideo: are videos from unknown channels (in other words they are
not part of the approved channels), so there are some problems, like they might
be repeated or from other things such as Shark Tank.

* otherVideos: this info was obtained by the API, and well do not use it

* safeVideos info from the approved channels. Those videos are safe, but
some have other info (like people talking), so not sure if that is a problem

To download the videos just write the path of the csv file here:
` df = pd.read_csv('lib/safeVideos.csv')`
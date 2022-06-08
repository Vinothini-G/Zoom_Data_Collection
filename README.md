# Zoom_Data_Collection
<!-- Algorithm : Initial Implementation Plan using Salsify
• Log into Zoom from master
• Join Zoom meeting from master and minion
• Create a 1s video with 30fps where each frame is a
number between 1-30 using ffmpeg. Loop the same
1s video multiple times to create a longer video. This
is similar to the Salsify approach where a QR code
is placed on each frame to uniquely identify it. Pipe
the numbers video in the Zoom call at the master
• Capture the frames received in the Zoom call at the
minion each second. Possibility to either: utilize
Salsify take screenshots of each frame
• Record the received video and process it offline to
find different frames
• Capture the network packets at the minion during
the zoom call using tshark
• Calculate FPS QoE metric for at a “one second”
granularity for the zoom call
• Create dataset across several zoom calls with FPS
and network packet information -->

Step 1: Use Irene's base code and write Zoom data handling script
Step 2: Write a script to automate Zoom login
Step 3: Update - Since automated login is not possible in Zoom, can't proceed this algorithm.
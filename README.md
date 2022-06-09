# Zoom_Data_Collection

Algorithm :
• Start Zoom meeting from the local machine
• Master will join the meeting using automated script
• Create a 1 sec video with 30 fps where each frame
is a number between 1-30 using FFMPEG. Loop the
same video multiple times to create a longer video
stream.
• Use the Zoom’s in-built statistics to capture the re-
ceived video’s FPS at “one second” granularity. Take
screenshots of FPS for every second and record it
for corresponding timestamp.
• Capture the network packets at the local machine
during the zoom call using TShark
• Calculate FPS QoE metric at a ’one second’ granu-
larity
• Create dataset across several zoom calls with FPS
and network packet information
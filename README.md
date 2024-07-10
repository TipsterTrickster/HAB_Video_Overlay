Get the flight data as a csv file and put the file into the data directory
Truncate the data


## Settings:

### General:
DataPath: Name of .csv file in the data directory
VideoInputName: Name of input video in video_in directory
VideoOutputName: What you want the output video to be named and put in video_out directory
DatetimeFormat: Datetime format if the data doesn't contain seconds since startup
Resolution: resolution of the input video
VideoFPS: Frames per second of input video
VideoSpeed: How much the video is sped up by

### Minimap
MinimapScale (float): How muc the minimap will be scaled down by from the originial video
MinimapZoom (int): How much the minimap should be zoomed in 
MinimapOpacity (float 0-1): How transparent the minimap should be
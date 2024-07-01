#!/usr/bin/python3

import csv
import numpy as np
from datetime import datetime
import math

def convert_datetime(dts):
    datetime_format = "%Y-%m-%dT%H:%M:%SZ"
    times = []

    for dt in dts:
        datetime_obj1 = datetime.strptime(dts[0], datetime_format)
        datetime_obj2 = datetime.strptime(dt, datetime_format)
        time_difference = datetime_obj2 - datetime_obj1

        # Convert the difference to seconds
        times.append(time_difference.total_seconds())
    return times


def read_csv_NEBP(file_path):
    datetimes = []
    times = []
    altitudes = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            datetimes.append(row['datetime'])
            altitudes.append(float(row['altitude']))
    
    times = convert_datetime(datetimes)
    
    return times, altitudes

# launch row & burst row
def read_csv_loonatec(file_path, launch, burst):
    times = []
    altitudes = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            times.append(float(row['MET']))
            altitudes.append(float(row['Altitude (m)']))
    
    times = [time - launch for time in times]

    return times[launch:burst], altitudes[launch:burst]

def interpolate_altitude(times, altitudes, fps, speed):
    times = [x / speed for x in times]
    total_seconds = times[-1]
    total_frames = math.ceil(fps * total_seconds)
    frame_times = np.linspace(0, total_seconds, total_frames)
    interpolated_altitudes = np.interp(frame_times, times, altitudes)
    return interpolated_altitudes


def generate_ffmpeg_command(interpolated_altitudes, fps):
    drawtext_filters = []
    for frame, altitude in enumerate(interpolated_altitudes):
        drawtext_filters.append(f"{frame / fps}-{(frame + 1) / fps} [enter] drawtext reinit text='Altitude\\: {altitude:.2f}m':x=(w-text_w)/2:y=H-th-10:fontsize=48:fontcolor=white:box=1:boxborderw=10:boxcolor=black@0.5")
    
    filter_complex = ";\n".join(drawtext_filters)
    return filter_complex

def main():
    # data_path = input("csv file path: ")
    data_path = "./data/umhab-147.csv"

    time_data, alt_data = read_csv_loonatec(data_path, 2780, 9345)
    interpolated_altitudes = interpolate_altitude(time_data, alt_data, 30, 64)
    ffmpeg_script = generate_ffmpeg_command(interpolated_altitudes, 30)

    with open("./altitude.cmd", "w") as f:
        f.write(ffmpeg_script)



# ffmpeg -i video_in/umhab-140.mp4 -vf "sendcmd=f=altitude.cmd,drawtext=text=''" -preset veryfast ./video_out/umhab-140.mp4

if __name__ == "__main__":
    main()

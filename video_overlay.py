import folium
from datetime import datetime
import csv
import math
import numpy as np
import cv2
import os
import subprocess
import imgkit
import configparser
import subprocess

class Minimap_Generator():
    def __init__(self, data_path, resolution, dt_format, vid_fps, vid_speed, mmap_scale, mmap_zoom, alt_units, use_dt, dt_name, seconds_name, alt_name, lat_name, lon_name):
        self.resolution = resolution
        self.minimap_resolution = int(self.resolution / mmap_scale)
        self.data_path = data_path
        self.dt_format = dt_format
        self.vid_fps = vid_fps
        self.vid_speed = vid_speed
        self.mmap_zoon = mmap_zoom
        self.alt_units = alt_units

        if use_dt == "True":
            self.time_data, self.lat_data, self.lon_data, self.altitude_data = self.read_csv_NEBP(data_path, dt_name, alt_name, lat_name, lon_name)
        else:
            self.time_data, self.lat_data, self.lon_data, self.altitude_data = self.read_csv_loonatec(data_path, seconds_name, alt_name, lat_name, lon_name)


        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                #map {{
                    width: {mmap_res}px;
                    height: {mmap_res}px;
                }}
                .leaflet-container {{
                    width: {mmap_res}px !important;
                    height: {mmap_res}px !important;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                {map_script}
            </script>
        </body>
        </html>
        """

        self.options = {
            'format': 'png',
            'width': self.minimap_resolution,
            'height': self.minimap_resolution,
            'crop-x': 60,
            'crop-w': self.minimap_resolution - 60,
            'crop-h': self.minimap_resolution - 20,
            'quality': 100
        }


    def convert_datetime(self, dts):
        datetime_format = self.dt_format
        times = []

        for dt in dts:
            datetime_obj1 = datetime.strptime(dts[0], datetime_format)
            datetime_obj2 = datetime.strptime(dt, datetime_format)
            time_difference = datetime_obj2 - datetime_obj1

            # Convert the difference to seconds
            times.append(time_difference.total_seconds())
        return times
    
    def read_csv_NEBP(self, file_path, dt_name, alt_name, lat_name, lon_name):
        datetimes = []
        times = []
        lats = []
        lons = []
        altitudes = []
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                datetimes.append(row[dt_name])
                lats.append(float(row[lat_name]))
                lons.append(float(row[lon_name]))
                altitudes.append(float(row[alt_name]))
        
        times = self.convert_datetime(datetimes)
        return times, lats, lons, altitudes

    def read_csv_loonatec(self, file_path, seconds_name, alt_name, lat_name, lon_name):
        times = []
        lats = []
        lons = []
        altitudes = []
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                times.append(float(row[seconds_name]))
                lats.append(float(row[lat_name]))
                lons.append(float(row[lon_name]))
                altitudes.append(float(row[alt_name]))
        
        start = times[0]
        times = [time - start for time in times]

        return times, lats, lons, altitudes

    def interpolate_location(self, times, lats, lons, fps, speed):
        times = [x / speed for x in times]
        total_seconds = times[-1]
        total_frames = math.ceil(fps * total_seconds)
        frame_times = np.linspace(0, total_seconds, total_frames)
        interpolated_lats = np.interp(frame_times, times, lats)
        interpolated_lons = np.interp(frame_times, times, lons)
        return interpolated_lats, interpolated_lons

    def interpolate_altitude(self, times, altitudes, fps, speed):
        times = [x / speed for x in times]
        total_seconds = times[-1]
        total_frames = math.ceil(fps * total_seconds)
        frame_times = np.linspace(0, total_seconds, total_frames)
        interpolated_altitudes = np.interp(frame_times, times, altitudes)
        return interpolated_altitudes

    def convert_html(self, path):
        html_files = [f for f in os.listdir(path) if f.endswith('.html')]

        for html_file in html_files:
            png_file = html_file.replace('.html', '.png')
            command = ['wkhtmltoimage', f'map_images/{html_file}', f'map_images/{png_file}']
            subprocess.run(command)

    def generate_video(self):
        lat_data, lon_data = self.interpolate_location(self.time_data, self.lat_data, self.lon_data, 1, self.vid_speed)

        coords = list(zip(lat_data, lon_data))

        for i, loc in enumerate(coords):
            m = folium.Map(location=loc, zoom_start=self.mmap_zoon)
            folium.Marker(location=loc).add_to(m)
            if i > 0:
                folium.PolyLine(coords[:i+1]).add_to(m)
            
            # Get the HTML representation of the map
            map_html = m.get_root().render()

            # Combine with the template
            full_html = self.html_template.format(map_script=map_html, mmap_res=self.minimap_resolution)
            
            # Save the combined HTML to a file
            html_file = f'minimap/map_{i}.html'
            with open(html_file, 'w') as file:
                file.write(full_html)

            # m.save(f"minimap/map_{i}.html")

            imgkit.from_file(f"./minimap/map_{i}.html", f"./minimap/map_{i}.png", self.options)
        

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter('minimap.mp4', fourcc, 1, (self.minimap_resolution, self.minimap_resolution))

        png_files = sorted([f.removesuffix(".png") for f in os.listdir('./minimap') if f.endswith('.png')], key=lambda name: int(name.split("_")[1]))[:len(coords)]
        
        for png_file in png_files:
            img = cv2.imread(f'minimap/{png_file}.png')
            img = cv2.resize(img, (self.minimap_resolution, self.minimap_resolution))
            video.write(img)

        # Release resources
        video.release()

    def generate_ffmpeg_command(self):

        # time_data, alt_data = self.read_csv_loonatec_Altitude(self.data_path, 2780, 9345)
        interpolated_altitudes = self.interpolate_altitude(self.time_data, self.altitude_data, self.vid_fps, self.vid_speed)

        drawtext_filters = []
        for frame, altitude in enumerate(interpolated_altitudes):
            drawtext_filters.append(f"{frame / self.vid_fps}-{(frame + 1) / self.vid_fps} [enter] drawtext reinit text='Altitude\\: {altitude:.2f}{self.alt_units}':x=(w-text_w)/2:y=H-th-10:fontsize={self.resolution / 22.5}:fontcolor=white:box=1:boxborderw=10:boxcolor=black@0.5")
        
        filter_complex = ";\n".join(drawtext_filters)

        with open("./altitude.cmd", "w") as f:
            f.write(filter_complex)
        return

def main():
    conf = configparser.RawConfigParser()
    conf.read("settings.ini")

    video_input_name = conf.get("General", "VideoInputName")
    video_output_name = conf.get("General", "VideoOutputName")
    data_path = conf.get("Data", "DataPath")
    resolution = int(conf.get("General", "Resolution"))
    datetime_format = conf.get("General", "DatetimeFormat")
    video_fps = int(conf.get("General", "VideoFPS"))
    video_speed = float(conf.get("General", "VideoSpeed"))
    mmap_scale = float(conf.get("Minimap", "MinimapScale"))
    mmap_opacity = float(conf.get("Minimap", "MinimapOpacity"))
    mmap_zoom = int(conf.get("Minimap", "MinimapZoom"))
    alt_units = conf.get("Altitude", "AltitudeUnits")
    use_dt = conf.get("Data", "UseDatetime")
    dt_name = conf.get("Data", "DatetimeColumn")
    seconds_name = conf.get("Data", "SecondsColumn")
    alt_name = conf.get("Data", "AltitudeColumn")
    lat_name = conf.get("Data", "LatitudeColumn")
    lon_name = conf.get("Data", "LongitudeColumn")

    mmap = Minimap_Generator(data_path, resolution, datetime_format, video_fps, video_speed, mmap_scale, mmap_zoom, alt_units, use_dt, dt_name, seconds_name, alt_name, lat_name, lon_name)
    
    mmap.generate_video()
    mmap.generate_ffmpeg_command()

    # command = [
    # 'ffmpeg', '-i', f'video_in/{video_input_name}', '-vf',
    # 'movie=minimap.mp4 [over]; [in][over] overlay=main_w-overlay_w:0, sendcmd=f=altitude.cmd,drawtext=text=\'\'',
    # '-preset', 'veryfast', f'video_out/{video_output_name}'
    # ]
    command = [
    'ffmpeg', '-i', f'video_in/{video_input_name}', '-i', 'minimap.mp4', '-filter_complex',
    f'[1]format=rgba,colorchannelmixer=aa={mmap_opacity}[over];[0][over]overlay=main_w-overlay_w:0,sendcmd=f=altitude.cmd,drawtext=text=\'\'',
    '-preset', 'veryfast', f'video_out/{video_output_name}'
    ]
    subprocess.run(command)

if __name__ == "__main__":
    main()

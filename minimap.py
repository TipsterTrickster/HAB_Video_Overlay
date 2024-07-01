import folium
from datetime import datetime
import csv
import math
import numpy as np
import cv2
import os
import subprocess
import imgkit

# resolution = 1080
# mmap_res = 540

# html_template = """
# <!DOCTYPE html>
# <html>
# <head>
#     <meta charset="utf-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <style>
#         #map {{
#             width: 540px;
#             height: 540px;
#         }}
#         .leaflet-container {{
#             width: 540px !important;
#             height: 540px !important;
#         }}
#     </style>
# </head>
# <body>
#     <div id="map"></div>
#     <script>
#         {map_script}
#     </script>
# </body>
# </html>
# """

# options = {
#     'format': 'png',
#     'width': 540,
#     'height': 540,
#     'crop-x': 60,
#     'crop-w': 740,
#     'crop-h': 580,
#     'quality': 100
# }


# def convert_datetime(dts):
#     datetime_format = "%Y-%m-%dT%H:%M:%SZ"
#     times = []

#     for dt in dts:
#         datetime_obj1 = datetime.strptime(dts[0], datetime_format)
#         datetime_obj2 = datetime.strptime(dt, datetime_format)
#         time_difference = datetime_obj2 - datetime_obj1

#         # Convert the difference to seconds
#         times.append(time_difference.total_seconds())
#     return times


# def read_csv_NEBP(file_path, start, end):
#     datetimes = []
#     times = []
#     lats = []
#     lons = []
#     with open(file_path, 'r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             datetimes.append(row['datetime'])
#             lats.append(float(row['latitude']))
#             lons.append(float(row['longitude']))
    
#     times = convert_datetime(datetimes)

    
#     return times[start:end], lats[start:end], lons[start:end]

# def read_csv_loonatec(file_path, start, end):
#     times = []
#     lats = []
#     lons = []
#     with open(file_path, 'r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             times.append(float(row['MET']))
#             lats.append(float(row['Latitude (deg)']))
#             lons.append(float(row['Longitude (deg)']))
    
#     times = [time - start for time in times]
#     return times[start:end], lats[start:end], lons[start:end]


# def interpolate_location(times, lats, lons, fps, speed):
#     times = [x / speed for x in times]
#     total_seconds = times[-1]
#     total_frames = math.ceil(fps * total_seconds)
#     frame_times = np.linspace(0, total_seconds, total_frames)
#     interpolated_lats = np.interp(frame_times, times, lats)
#     interpolated_lons = np.interp(frame_times, times, lons)
#     return interpolated_lats, interpolated_lons


# def convert_html(path):
#     html_files = [f for f in os.listdir(path) if f.endswith('.html')]

#     for html_file in html_files:
#         png_file = html_file.replace('.html', '.png')
#         command = ['wkhtmltoimage', f'map_images/{html_file}', f'map_images/{png_file}']
#         subprocess.run(command)





class Minimap_Generator():
    def __init__(self, video_path, data_path, resolution):
        self.resolution = resolution
        self.minimap_resolution = int(self.resolution / 2)
        self.data_path = data_path
        self.video_path = video_path
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                #map {{
                    width: 540px;
                    height: 540px;
                }}
                .leaflet-container {{
                    width: 540px !important;
                    height: 540px !important;
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
            'width': 540,
            'height': 540,
            'crop-x': 60,
            'crop-w': 740,
            'crop-h': 580,
            'quality': 100
        }


    def convert_datetime(self, dts, dt_format):
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        times = []

        for dt in dts:
            datetime_obj1 = datetime.strptime(dts[0], datetime_format)
            datetime_obj2 = datetime.strptime(dt, datetime_format)
            time_difference = datetime_obj2 - datetime_obj1

            # Convert the difference to seconds
            times.append(time_difference.total_seconds())
        return times


    def read_csv_NEBP(self, file_path, start, end):
        datetimes = []
        times = []
        lats = []
        lons = []
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                datetimes.append(row['datetime'])
                lats.append(float(row['latitude']))
                lons.append(float(row['longitude']))
        
        times = self.convert_datetime(datetimes)

        
        return times[start:end], lats[start:end], lons[start:end]

    def read_csv_loonatec(self, file_path, start, end):
        times = []
        lats = []
        lons = []
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                times.append(float(row['MET']))
                lats.append(float(row['Latitude (deg)']))
                lons.append(float(row['Longitude (deg)']))
        
        times = [time - start for time in times]
        return times[start:end], lats[start:end], lons[start:end]


    def interpolate_location(self, times, lats, lons, fps, speed):
        times = [x / speed for x in times]
        total_seconds = times[-1]
        total_frames = math.ceil(fps * total_seconds)
        frame_times = np.linspace(0, total_seconds, total_frames)
        interpolated_lats = np.interp(frame_times, times, lats)
        interpolated_lons = np.interp(frame_times, times, lons)
        return interpolated_lats, interpolated_lons


    def convert_html(self, path):
        html_files = [f for f in os.listdir(path) if f.endswith('.html')]

        for html_file in html_files:
            png_file = html_file.replace('.html', '.png')
            command = ['wkhtmltoimage', f'map_images/{html_file}', f'map_images/{png_file}']
            subprocess.run(command)

    def generate_video(self):
        # data_path = input("csv file path: ")
        data_path = "./data/umhab-147.csv"

        time_data, lat_data, lon_data = self.read_csv_loonatec(data_path, 2780, 9345)

        lat_data, lon_data = self.interpolate_location(time_data, lat_data, lon_data, 1, 64)

        coords = list(zip(lat_data, lon_data))

        for i, loc in enumerate(coords):
            m = folium.Map(location=loc, zoom_start=12)
            folium.Marker(location=loc).add_to(m)
            if i > 0:
                folium.PolyLine(coords[:i+1]).add_to(m)
            
            # Get the HTML representation of the map
            map_html = m.get_root().render()

            # Combine with the template
            full_html = self.html_template.format(map_script=map_html)

            # Save the combined HTML to a file
            html_file = f'minimap/map_{i}.html'
            with open(html_file, 'w') as file:
                file.write(full_html)

            # m.save(f"minimap/map_{i}.html")

            imgkit.from_file(f"./minimap/map_{i}.html", f"./minimap/map_{i}.png", self.options)
        

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter('minimap.mp4', fourcc, 1, (self.minimap_resolution, self.minimap_resolution))

        png_files = sorted([f.removesuffix(".png") for f in os.listdir('./minimap') if f.endswith('.png')], key=lambda name: int(name.split("_")[1]))
        
        for png_file in png_files:
            img = cv2.imread(f'minimap/{png_file}.png')
            img = cv2.resize(img, (self.minimap_resolution, self.minimap_resolution))
            video.write(img)

        # Release resources
        video.release()


def main():
    mmap = Minimap_Generator("", "", 1080)
    mmap.generate_video()
    # # data_path = input("csv file path: ")
    # data_path = "./data/umhab-147.csv"

    # time_data, lat_data, lon_data = read_csv_loonatec(data_path, 2780, 9345)

    # lat_data, lon_data = interpolate_location(time_data, lat_data, lon_data, 1, 64)

    # coords = list(zip(lat_data, lon_data))

    # for i, loc in enumerate(coords):
    #     m = folium.Map(location=loc, zoom_start=12)
    #     folium.Marker(location=loc).add_to(m)
    #     if i > 0:
    #         folium.PolyLine(coords[:i+1]).add_to(m)
        
    #     # Get the HTML representation of the map
    #     map_html = m.get_root().render()

    #     # Combine with the template
    #     full_html = html_template.format(map_script=map_html)

    #     # Save the combined HTML to a file
    #     html_file = f'minimap/map_{i}.html'
    #     with open(html_file, 'w') as file:
    #         file.write(full_html)

    #     # m.save(f"minimap/map_{i}.html")

    #     imgkit.from_file(f"./minimap/map_{i}.html", f"./minimap/map_{i}.png", options)
    

    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # video = cv2.VideoWriter('minimap.mp4', fourcc, 1, (mmap_res, mmap_res))

    # png_files = sorted([f.removesuffix(".png") for f in os.listdir('./minimap') if f.endswith('.png')], key=lambda name: int(name.split("_")[1]))
    
    # for png_file in png_files:
    #     img = cv2.imread(f'minimap/{png_file}.png')
    #     img = cv2.resize(img, (mmap_res, mmap_res))
    #     video.write(img)

    # # Release resources
    # video.release()

# ffmpeg -i umhab-147.mp4 -vf "movie=../minimap.mp4 [over]; [in][over] overlay" -preset veryfast umhab-147-2.mp4
# ffmpeg -i umhab-147.mp4 -vf "movie=../minimap.mp4 [over]; [in][over] overlay=0:main_h-overlay_h" -preset veryfast umhab-147-2.mp4

if __name__ == "__main__":
    main()

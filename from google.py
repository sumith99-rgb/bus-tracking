from google.transit import gtfs_realtime_pb2
import requests
import folium
from geopy.geocoders import Nominatim
import json
import time
import datetime
import os
from html2image import Html2Image
import cv2

def get_map(time_stamp):
    feed = gtfs_realtime_pb2.FeedMessage()
    
    # Use your real API key here
    api_key = "your_api_key_here"  # Replace with your actual API key
    api_url = f"https://opendata.iiitd.edu.in/api/realtime/VehiclePositions.pb?key={api_key}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad status codes
        feed.ParseFromString(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return

    from google.protobuf.json_format import MessageToJson
    json_string = MessageToJson(feed)
    data = json.loads(json_string)

    # Extract latitude and longitude for each bus position
    locations = []
    for entity in data["entity"]:
        latitude = entity["vehicle"]["position"]["latitude"]
        longitude = entity["vehicle"]["position"]["longitude"]
        locations.append([latitude, longitude])

    # Geolocate "New Delhi"
    geolocator = Nominatim(user_agent="location_details")
    try:
        location = geolocator.geocode("New Delhi")
        latitude = location.latitude
        longitude = location.longitude
    except Exception as e:
        print(f"Error geocoding New Delhi: {e}")
        latitude, longitude = 28.6139, 77.2090  # Default to New Delhi coordinates

    # Create the map centered around New Delhi
    map_new = folium.Map(location=[latitude, longitude], zoom_start=10.5, width=1920, height=1080)

    # Add circle markers for each bus location
    for loc in locations:
        folium.CircleMarker(
            location=loc,
            radius=5,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=1
        ).add_to(map_new)

    # Save map as HTML
    os.makedirs("htmlfiles", exist_ok=True)  # Ensure directory exists
    map_filename = f'htmlfiles/map_{time_stamp}.html'
    map_new.save(map_filename)

def generate_screenshots_from_html():
    # Path to HTML files
    html_files_path = 'htmlfiles'

    # Initialize Html2Image instance
    hti = Html2Image()

    # Iterate over each HTML file and convert it to an image
    cnt = 1
    for html_file in os.listdir(html_files_path):
        html_path = os.path.join(html_files_path, html_file)
        
        # Read HTML content and convert to PNG
        try:
            with open(html_path, 'r') as f:
                html_str = f.read()
            
            screenshot_filename = f"time_{cnt}.png"
            hti.screenshot(html_str=html_str, save_as=screenshot_filename)
            cnt += 1
        except Exception as e:
            print(f"Error converting {html_file} to image: {e}")

def create_video_from_images(image_directory):
    # Get sorted list of image files in directory
    image_files = [f for f in os.listdir(image_directory) if os.path.isfile(os.path.join(image_directory, f))]
    image_files.sort()

    # Set video dimensions and frame rate
    width, height = 1920, 1080
    fps = 28

    # Create a VideoWriter object
    video_writer = cv2.VideoWriter('output_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # Write each image to the video
    for image_file in image_files:
        image_path = os.path.join(image_directory, image_file)
        try:
            image = cv2.imread(image_path)
            if image is not None:
                image = cv2.resize(image, (width, height))
                video_writer.write(image)
            else:
                print(f"Error reading image: {image_file}")
        except Exception as e:
            print(f"Error processing {image_file}: {e}")

    # Release the video writer object
    video_writer.release()

def main():
    max_iterations = 10  # Set a limit for the number of iterations (optional)
    iteration = 0

    while iteration < max_iterations:
        try:
            # Generate map and save as HTML file
            get_map(time.time())
            iteration += 1
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        # Wait for 30 seconds before next update
        time.sleep(30)

    # After the map updates are done, generate screenshots from HTML files
    generate_screenshots_from_html()

    # Path to image files
    image_directory = 'htmlfiles'  # The directory with saved PNGs
    create_video_from_images(image_directory)

if __name__ == "__main__":
    main()
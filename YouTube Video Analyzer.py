# by - ADITYA SINGH

import requests
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import ttk  
from tkinter import filedialog
import re
from PIL import Image, ImageTk
import io
import threading
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import asyncio
import html

# Define the global API key
API_KEY = ""  # Replace with your YouTube DATA API key

progress_bar = None
original_comments = []
filter_keywords = []  

# Define global variables for widgets
video_url_entry = None
result_text = None
video_details_text = None
thumbnail_label = None

def get_video_id(video_url):
    video_id = None

    try:
        parsed_url = urlparse(video_url)
        if parsed_url.netloc == "youtu.be":
            video_id = parsed_url.path[1:]
        else:
            query_params = parse_qs(parsed_url.query)
            if "v" in query_params:
                video_id = query_params["v"][0]
    except Exception as e:
        print("Error extracting video ID:", e)

    return video_id


# Function to get video details
def get_video_details(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?key={API_KEY}&part=snippet,contentDetails,statistics&id={video_id}"
    response = requests.get(url)
    data = response.json()

    if "items" in data:
        video_info = data["items"][0]
        snippet = video_info["snippet"]
        content_details = video_info["contentDetails"]
        statistics = video_info["statistics"]

        video_title = snippet["title"]
        video_description = snippet["description"]
        published_date = snippet["publishedAt"]
        channel_name = snippet["channelTitle"]
        channel_id = snippet["channelId"]

        # Extract ISO 8601 formatted duration and convert to HH:MM:SS format
        duration_ISO8601 = content_details["duration"]
        duration = re.search(r'PT(\d+H)?(\d+M)?(\d+S)?', duration_ISO8601).groups()
        hours = int(duration[0][:-1]) if duration[0] else 0
        minutes = int(duration[1][:-1]) if duration[1] else 0
        seconds = int(duration[2][:-1]) if duration[2] else 0
        video_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        view_count = statistics.get("viewCount", "N/A")
        like_count = statistics.get("likeCount", "N/A")
        dislike_count = statistics.get("dislikeCount", "N/A")
        comment_count = statistics.get("commentCount", "N/A")
        video_tags = snippet.get("tags", [])
        video_category = snippet.get("categoryId", "")

        video_details = {
            "Title": video_title,
            "Description": video_description,
            "Published Date": published_date,
            "Channel Name": channel_name,
            "Channel ID": channel_id,
            "Duration": video_duration,
            "View Count": view_count,
            "Like Count": like_count,
            "Dislike Count": dislike_count,
            "Comment Count": comment_count,
            "Tags": ", ".join(video_tags),
            "Category": video_category
        }

        return video_details
    else:
        return None



def get_video_statistics(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?key={API_KEY}&part=statistics&id={video_id}"
    response = requests.get(url)
    data = response.json()

    if "items" in data:
        statistics = data["items"][0]["statistics"]
        return statistics
    else:
        return None
    

# Function to update video details in the GUI
def update_video_details(details):
    video_details_text.config(state=tk.NORMAL)
    video_details_text.delete(1.0, tk.END)
    video_details_text.insert(tk.END, "Video Details:\n")
    video_details_text.insert(tk.END, f"Channel ID: {details['Channel ID']}\n")
    video_details_text.insert(tk.END, f"Channel Name: {details['Channel Name']}\n")
    video_details_text.insert(tk.END, f"Published Date: {details['Published Date']}\n")
    video_details_text.insert(tk.END, f"Title: {details['Title']}\n")
    video_details_text.insert(tk.END, f"Description: {details['Description']}\n")
    video_details_text.insert(tk.END, f"Duration: {details['Duration']}\n")
    video_details_text.insert(tk.END, f"View Count: {details['View Count']}\n")
    video_details_text.insert(tk.END, f"Like Count: {details['Like Count']}\n")
    video_details_text.insert(tk.END, f"Dislike Count: {details['Dislike Count']}\n")
    video_details_text.insert(tk.END, f"Comment Count: {details['Comment Count']}\n")
    video_details_text.insert(tk.END, f"Tags: {details['Tags']}\n")  # Include tags here
    video_details_text.insert(tk.END, f"Category: {details['Category']}\n")
    video_details_text.config(state=tk.DISABLED)
    
    # Clear existing content in fetched_comments_text
    fetched_comments_text.config(state=tk.NORMAL)
    fetched_comments_text.delete(1.0, tk.END)
    
    # Display fetched comments in fetched_comments_text
    for index, comment in enumerate(original_comments, start=1):
        fetched_comments_text.insert(tk.END, f"Comment {index}: {comment}\n")
    fetched_comments_text.config(state=tk.DISABLED)



        
def extract_comments_and_details():
    try:
        global progress_bar  # Reference the global progress_bar variable
        # Show the progress bar
        progress_bar.start()

        video_url = video_url_entry.get()
        print("Video URL:", video_url)  # Print the video URL for debugging purposes
        video_id = get_video_id(video_url)

        if video_id:
            print("Video ID:", video_id)  # Print the video ID for debugging purposes
            video_details = get_video_details(video_id)
            if video_details:
                print("Video Details:", video_details)  # Print video details for debugging purposes
                update_video_details(video_details)
                statistics = get_video_statistics(video_id)
                if statistics:
                    print("Video Statistics:", statistics)  # Print video statistics for debugging purposes
                    update_video_statistics(statistics, video_details)
                retrieve_and_display_thumbnail(video_id)
                fetch_comments_in_background(video_id)  # Fetch comments in the background
        else:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "Invalid YouTube video URL.")
            result_text.config(state=tk.DISABLED)

    except Exception as e:
        # Handle exceptions if needed
        print("Exception:", e)  # Print the exception for debugging purposes
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Failed To Fetch Details")
        result_text.config(state=tk.DISABLED)

    finally:
        # After fetching details or error, stop the progress bar
        if progress_bar:
            progress_bar.stop()


def update_gui_widget(new_text):
    fetched_comments_text.config(state=tk.NORMAL)
    fetched_comments_text.delete(1.0, tk.END)
    fetched_comments_text.insert(tk.END, new_text)
    fetched_comments_text.config(state=tk.DISABLED)

def fetch_comments_in_background(video_id):
    comments_thread = threading.Thread(target=fetch_comments, args=(video_id,))
    comments_thread.start()

def fetch_comments(video_id):
    comments = get_comments(video_id)
    original_comments.clear()
    original_comments.extend(comments)
    
    # Create a new string containing the fetched comments
    comments_text = ""
    for index, comment in enumerate(original_comments, start=1):
        comments_text += f"Comment {index}: {comment}\n"
    
    # Update the GUI widget in the main thread
    root.after(0, update_gui_widget, comments_text)
    

def fetch_comments_in_background(video_id):
    comments_thread = threading.Thread(target=fetch_comments, args=(video_id,))
    comments_thread.start()

def fetch_comments(video_id):
    comments = get_comments(video_id)
    original_comments.clear()  # Clear previous comments
    original_comments.extend(comments)  # Update comments list
    
    # Clear existing content in fetched_comments_text
    fetched_comments_text.config(state=tk.NORMAL)
    fetched_comments_text.delete(1.0, tk.END)
    
    # Display fetched comments in fetched_comments_text
    for index, comment in enumerate(original_comments, start=1):
        fetched_comments_text.insert(tk.END, f"Comment {index}: {comment}\n")
    fetched_comments_text.config(state=tk.DISABLED)

def refresh_comments():
    video_url = video_url_entry.get()
    video_id = get_video_id(video_url)
    
    if video_id:
        fetch_comments_in_background(video_id)
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Invalid YouTube video URL.")
        result_text.config(state=tk.DISABLED)

def update_video_statistics(statistics, details):
    video_statistics_text.config(state=tk.NORMAL)
    video_statistics_text.delete(1.0, tk.END)
    video_statistics_text.insert(tk.END, "Video Statistics:\n")
    video_statistics_text.insert(tk.END, f"View Count: {statistics.get('viewCount', 'N/A')}\n")
    video_statistics_text.insert(tk.END, f"Like Count: {statistics.get('likeCount', 'N/A')}\n")
    video_statistics_text.insert(tk.END, f"Dislike Count: {statistics.get('dislikeCount', 'N/A')}\n")
    video_statistics_text.insert(tk.END, f"Comment Count: {details.get('Comment Count', 'N/A')}\n")
    # Add more statistics as needed
    video_statistics_text.config(state=tk.DISABLED)
    
    # Calculate percentage values
    view_percentage = (int(details.get('View Count', 0)) / (int(details.get('View Count', 0)) + int(statistics.get('likeCount', 0)) + int(statistics.get('dislikeCount', 0)) + int(details.get('Comment Count', 0)))) * 100
    like_percentage = (int(statistics.get('likeCount', 0)) / (int(details.get('View Count', 0)) + int(statistics.get('likeCount', 0)) + int(statistics.get('dislikeCount', 0)) + int(details.get('Comment Count', 0)))) * 100
    dislike_percentage = (int(statistics.get('dislikeCount', 0)) / (int(details.get('View Count', 0)) + int(statistics.get('likeCount', 0)) + int(statistics.get('dislikeCount', 0)) + int(details.get('Comment Count', 0)))) * 100
    comment_percentage = (int(details.get('Comment Count', 0)) / (int(details.get('View Count', 0)) + int(statistics.get('likeCount', 0)) + int(statistics.get('dislikeCount', 0)) + int(details.get('Comment Count', 0)))) * 100

    # Create a bar chart for view counts, like counts, dislike counts, and comment counts
    videos = ["View Count", "Like Count", "Dislike Count", "Comment Count"]
    counts = [int(details.get('View Count', 0)), int(statistics.get('likeCount', 0)), int(statistics.get('dislikeCount', 0)), int(details.get('Comment Count', 0))]
    percentages = [f"{view_percentage:.2f}%", f"{like_percentage:.2f}%", f"{dislike_percentage:.2f}%", f"{comment_percentage:.2f}%"]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(videos, counts, color=['blue', 'green', 'red', 'purple'])

    # Add percentage labels above the bars
    for bar, label, count in zip(bars, percentages, counts):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{label}\n({count})", ha='center', va='bottom', color='black', fontweight='bold')
    plt.xlabel('Statistic')
    plt.ylabel('Count')
    plt.title('Video Statistics Comparison')
    plt.show()



def get_comments(video_id):
    comments = []

    url = f"https://www.googleapis.com/youtube/v3/commentThreads?key={API_KEY}&videoId={video_id}&part=snippet&maxResults=100"
    
    while url:
        response = requests.get(url)
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                if "<a href=\"https://www.youtube.com/watch?v=" not in comment_text:
                    comments.append(comment_text)

        if "nextPageToken" in data:
            next_page_token = data["nextPageToken"]
            url = f"{url}&pageToken={next_page_token}"
        else:
            url = None

    return comments


        
def apply_comment_filtration():
    global filter_keywords  # Use the global filter_keywords variable

    filter_keywords = filter_keywords_entry.get()
    filter_keywords = [keyword.strip() for keyword in filter_keywords.split(',') if keyword.strip()]
    
    if filter_keywords:
        filtered_comments = get_filtered_comments(data["items"], filter_keywords)
        if filtered_comments:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"Filtered Comments (using keywords: {', '.join(filter_keywords)}):\n")
            for index, comment in enumerate(filtered_comments, start=1):
                result_text.insert(tk.END, f"Filtered Comment {index}: {comment}\n")
            result_text.config(state=tk.DISABLED)
        else:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, "No comments matching the filter criteria.")
            result_text.config(state=tk.DISABLED)
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Please enter filter keywords.")
        result_text.config(state=tk.DISABLED)
        
        # Disable the filter button if no keywords are entered
        filter_button.config(state=tk.DISABLED)

def extract_comments():
    result_text.config(state=tk.NORMAL)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Extracting comments...\n")
    result_text.config(state=tk.DISABLED)
    get_comments()

def export_comments():
    comments = fetched_comments_text.get("1.0", tk.END)
    if not comments.strip():
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(comments)
        comments_export_message.config(text="Comments exported to file.", fg="green")
        root.after(2000, clear_comments_export_message)


def clear_comments_export_message():
    comments_export_message.config(text="", fg="black")


def retrieve_and_display_thumbnail(video_id):
    thumbnail_data = retrieve_thumbnail_data(video_id, quality="maxresdefault")
    
    if thumbnail_data:
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        thumbnail_image = thumbnail_image.resize((200, 150), Image.LANCZOS)
        thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
        thumbnail_label.config(image=thumbnail_photo)
        thumbnail_label.image = thumbnail_photo
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Thumbnail data could not be retrieved.")
        result_text.config(state=tk.DISABLED)    

def update_thumbnail_label(video_id):
    thumbnail_data = retrieve_thumbnail_data(video_id, quality="maxresdefault")

    if thumbnail_data:
        thumbnail_image = Image.open(io.BytesIO(thumbnail_data))
        thumbnail_image = thumbnail_image.resize((200, 150), Image.LANCZOS)
        thumbnail_photo = ImageTk.PhotoImage(thumbnail_image)
        thumbnail_label.config(image=thumbnail_photo)
        thumbnail_label.image = thumbnail_photo
    else:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Thumbnail data could not be retrieved.")
        result_text.config(state=tk.DISABLED)
        
# Function to retrieve thumbnail data using the requests library
def retrieve_thumbnail_data(video_id, quality="maxresdefault"):
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        return response.content
    return None
        
def export_thumbnail():
    video_url = video_url_entry.get()
    video_id = get_video_id(video_url)
    
    if not video_id:
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Please enter a valid YouTube video URL.")
        result_text.config(state=tk.DISABLED)
        return

    thumbnail_data = retrieve_thumbnail_data(video_id)

    if thumbnail_data:
        thumbnail_path = filedialog.asksaveasfilename(defaultextension=".jpeg", filetypes=[("JPEG Files", "*.jpeg")])
        if thumbnail_path:
            with open(thumbnail_path, "wb") as file:
                file.write(thumbnail_data)
            thumbnail_export_message.config(text="Thumbnail exported to file.", fg="green")
            root.after(2000, clear_thumbnail_export_message)
    else:
        thumbnail_export_message.config(text="No thumbnail available to export.", fg="red")
        root.after(2000, clear_thumbnail_export_message)
        

def clear_thumbnail_export_message():
    thumbnail_export_message.config(text="", fg="black")


def filter_comments():
    global original_comments
    
    filtered_comments_text.config(state=tk.NORMAL)
    
    # Clear the text widget
    filtered_comments_text.delete("1.0", tk.END)
    
    # Fetch video ID
    video_url = video_url_entry.get()
    video_id = get_video_id(video_url)
    
    if not video_id:
        filtered_comments_text.insert(tk.END, "Invalid YouTube video URL.")
        filtered_comments_text.config(state=tk.DISABLED)
        return

    # Fetch comments
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?key={API_KEY}&videoId={video_id}&part=snippet&maxResults=100"
    response = requests.get(url)
    data = response.json()

    if "items" in data:
        comments = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in data["items"]]
        original_comments = comments  # Store the fetched comments
        
        # Retrieve filter keywords
        filter_keywords_str = filter_keywords_entry.get()
        filter_keywords = [keyword.strip().lower() for keyword in filter_keywords_str.split(",")] if filter_keywords_str else []

        if filter_keywords:
            filtered_comments = []

            for comment in comments:
                if any(keyword in comment.lower() for keyword in filter_keywords):
                    filtered_comments.append(comment)

            if filtered_comments:
                for index, comment in enumerate(filtered_comments, start=1):
                    # Parse and extract text from HTML using BeautifulSoup
                    comment_text = BeautifulSoup(comment, "html.parser").get_text()
                    filtered_comments_text.insert(tk.END, f"Filtered Comment {index}: {comment_text}\n")
            else:
                filtered_comments_text.insert(tk.END, "No comments matching the filter criteria.")
        else:
            filtered_comments_text.insert(tk.END, "No filter keywords provided.")

    else:
        filtered_comments_text.insert(tk.END, "No comments found for this video.")
    
    filtered_comments_text.config(state=tk.DISABLED)



root = tk.Tk()
root.title("YouTube Video Analyzer (Aditya)")

# Configure the main window to open in fullscreen
root.state('zoomed')  # Opens the window in fullscreen mode

# Create a style for the main window
style = ttk.Style()
style.theme_use("clam")  # Choose a theme for the interface


fetched_comments_text = tk.Text(root)
original_comments = []        


# Initialize the progress bar
progress_bar = ttk.Progressbar(root, mode="indeterminate")

# Configure the main frame
frame = tk.Frame(root, bg="#f0f0f0")  # Light gray background
frame.pack(padx=20, pady=20)

# Create and place widgets
video_url_label = tk.Label(frame, text="Enter YouTube Video URL:")
video_url_label.grid(row=0, column=0, columnspan=2, sticky="w")

video_url_entry = tk.Entry(frame, width=50)
video_url_entry.grid(row=1, column=0, columnspan=2, sticky="w")

# Create and place widgets for comment filtration
filter_keywords_label = tk.Label(frame, text="Enter Filter Keywords (comma-separated):")
filter_keywords_label.grid(row=2, column=0, columnspan=2, sticky="w")

filter_keywords_entry = tk.Entry(frame, width=50)
filter_keywords_entry.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")


# Create the "Extract Comments" button
extract_button = ttk.Button(frame, text="Fetch Details", command=extract_comments_and_details)
extract_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")

# Create the "Filter Comments" button
filter_button = ttk.Button(frame, text="Filter Comments", command=filter_comments)
filter_button.grid(row=4, column=1, padx=5, pady=5, sticky="e")

# Create the "Export Comments" button
export_button = ttk.Button(frame, text="Export Comments", command=export_comments)
export_button.grid(row=5, column=0, padx=5, pady=5, sticky="w")

# Create the "Refresh Comments" button
refresh_button = ttk.Button(frame, text="Refresh Comments", command=refresh_comments)
refresh_button.grid(row=4, column=10, padx=5, pady=5, sticky="w")  # Place below the "Export Comments" button

# Create the "Export Thumbnail" button
thumbnail_button = ttk.Button(frame, text="Export Thumbnail", command=export_thumbnail)
thumbnail_button.grid(row=5, column=1, padx=5, pady=5, sticky="e")

thumbnail_export_message = tk.Label(frame, text="", fg="green")
thumbnail_export_message.grid(row=6, column=0, columnspan=2, sticky="w")



# Create a frame for fetched and filtered comments
comments_frame = tk.Frame(root)
comments_frame.pack(fill=tk.BOTH, expand=True)

# Create scrollbars for fetched and filtered comments
fetched_comments_scrollbar = tk.Scrollbar(comments_frame)
fetched_comments_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

filtered_comments_scrollbar = tk.Scrollbar(comments_frame)
filtered_comments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Create a scrollable text widget for fetched comments
fetched_comments_text = tk.Text(comments_frame, wrap=tk.WORD, yscrollcommand=fetched_comments_scrollbar.set, height=20, state=tk.DISABLED)
fetched_comments_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
fetched_comments_scrollbar.config(command=fetched_comments_text.yview)

# Create a scrollable text widget for filtered comments
filtered_comments_text = tk.Text(comments_frame, wrap=tk.WORD, yscrollcommand=filtered_comments_scrollbar.set, height=20, state=tk.DISABLED)
filtered_comments_text.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
filtered_comments_scrollbar.config(command=filtered_comments_text.yview)


scrollbar = tk.Scrollbar(comments_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

result_text = tk.Text(comments_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=20, state=tk.DISABLED)
result_text.pack(fill=tk.BOTH, expand=True)
scrollbar.config(command=result_text.yview)


comments_export_message = tk.Label(comments_frame, text="", fg="green")
comments_export_message.pack()

# Create a frame for video details and statistics
details_and_statistics_frame = tk.Frame(root)
details_and_statistics_frame.pack(side=tk.LEFT, padx=20, pady=10)

# Create a frame for the thumbnail
thumbnail_frame = tk.Frame(details_and_statistics_frame)
thumbnail_frame.pack(side=tk.TOP)

# Create a label to display the thumbnail image
thumbnail_label = tk.Label(thumbnail_frame)
thumbnail_label.pack()

# Create a frame for video details and statistics
details_and_statistics_frame = tk.Frame(root)
details_and_statistics_frame.pack(side=tk.RIGHT, padx=20, pady=10)

# Create a frame for the thumbnail
thumbnail_frame = tk.Frame(details_and_statistics_frame)
thumbnail_frame.pack(side=tk.LEFT)

# Create a label to display the thumbnail image
thumbnail_label = tk.Label(thumbnail_frame)
thumbnail_label.pack()

# Create a frame for video statistics
video_statistics_frame = tk.Frame(details_and_statistics_frame)
video_statistics_frame.pack(side=tk.RIGHT, padx=20)

video_statistics_label = tk.Label(video_statistics_frame, text="Video Statistics:")
video_statistics_label.pack()

video_statistics_text = tk.Text(video_statistics_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
video_statistics_text.pack(fill=tk.BOTH, expand=True)

# Create a frame for video details
video_details_frame = tk.Frame(details_and_statistics_frame)
video_details_frame.pack(side=tk.RIGHT, padx=20)

video_details_label = tk.Label(video_details_frame, text="Video Details:")
video_details_label.pack()

video_details_text = tk.Text(video_details_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
video_details_text.pack(fill=tk.BOTH, expand=True)


# Create a frame for the thumbnail
thumbnail_frame = tk.Frame(details_and_statistics_frame)
thumbnail_frame.pack(side=tk.TOP)

# Create a label to display the thumbnail image
thumbnail_label = tk.Label(thumbnail_frame)
thumbnail_label.pack()



root.mainloop()

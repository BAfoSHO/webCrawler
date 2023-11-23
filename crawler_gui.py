import tkinter as tk
from tkinter import ttk
import threading
from PIL import Image, ImageTk  # Import from Pillow for image handling
from config import DATABASE_PATH  # Import database path
from crawler import Crawler  # Import your crawler class


app = tk.Tk() # Initialize the app


# Function to update the status label
def update_status(status_label, message):
    status_label.config(text=message)
    app.update_idletasks()


# Function to run the crawler in a separate thread
# Define the status label
status_label = ttk.Label(app)

# Define the progress bar
progress_bar = ttk.Progressbar(app, mode='determinate')


# Function to update the progress bar
def update_progress(current, total):
    progress_bar['value'] = (current / total) * 100  
    app.update_idletasks()


def run_crawler_thread(urls, mode):
    crawler = Crawler(headless=True)  # Adjust as needed
    total_urls = len(urls)
    
    status_label.pack(pady=10)
    progress_bar.pack(pady=10)
    
    for i, url in enumerate(urls, start=1):
        update_status(status_label, f"Processing {i}/{total_urls}...")  # Pass status_label as an argument
        update_progress(i, total_urls)
        # Your crawler logic here

    update_status(status_label, "Crawl complete.")  # Pass status_label as an argument
    progress_bar.pack_forget()  # Hide the progress bar
    app.config(cursor="")


# Function to start the crawler
def run_crawler():
    selected_mode = mode_var.get()
    urls = url_entry.get().split(';')
    app.config(cursor="watch")
    threading.Thread(target=run_crawler_thread, args=(urls, selected_mode)).start()


# Function to update the placeholder text based on mode selection
# Define placeholder text for different modes
placeholder_text = {
    'dark': 'Enter URL(s) separated by semicolon (;)',
    'light': 'Enter URL(s) separated by semicolon (;)'
}


# Create the URL entry field
url_entry = ttk.Entry(app)
# Function to clear the placeholder text in URL entry field
def on_entry_click(event):
    if event.widget.get() in placeholder_text.values():
        event.widget.delete(0, tk.END)
        event.widget.config(foreground='black')


# Bind events to the URL entry field
url_entry.bind('<FocusIn>', on_entry_click)


# Function to add placeholder text if the field is empty
def on_focus_out(event):
    if event.widget.get().strip() == '':
        update_placeholder()


# Define mode_var as a global variable
mode_var = tk.StringVar()


# Function to update the placeholder text
def update_placeholder():
    mode = mode_var.get()
    mode = mode if mode in placeholder_text else 'dark'
    placeholder = placeholder_text[mode]
    url_entry.delete(0, tk.END)
    url_entry.insert(0, placeholder)
    url_entry.config(foreground='grey')


url_entry.bind('<FocusOut>', on_focus_out)


# Set the initial placeholder text
update_placeholder()


# Define the dark and light color schemes
dark_mode_style = {
    'background': '#2D2D2D',
    'foreground': '#EAEAEA',
    'button': 'DarkButton.TButton',
    'entry': 'DarkEntry.TEntry',
    'text': '#EAEAEA'
}

light_mode_style = {
    'background': '#FFFFFF',
    'foreground': '#000000',
    'button': 'LightButton.TButton',
    'entry': 'LightEntry.TEntry',
    'text': '#000000'
}


# Initialize mode to dark
current_mode = 'dark'
style = ttk.Style()


# Define dark mode styles
style.configure('DarkButton.TButton', background='#2D2D2D', foreground='#EAEAEA')
style.configure('DarkEntry.TEntry', fieldbackground='#2D2D2D', foreground='#EAEAEA')


# Define light mode styles
style.configure('LightButton.TButton', background='#FFFFFF', foreground='#000000')
style.configure('LightEntry.TEntry', fieldbackground='#FFFFFF', foreground='#000000')


# Function to toggle between dark and light mode
def toggle_mode():
    global current_mode
    if current_mode == 'dark':
        current_mode = 'light'
        mode = light_mode_style
        toggle_button.config(text="Toggle Dark Mode", style=mode['button'])
        app.config(background=mode['background'])
        url_entry.config(style='LightEntry.TEntry')
        # Update any other widgets that need to change style
    else:
        current_mode = 'dark'
        mode = dark_mode_style
        toggle_button.config(text="Toggle Light Mode", style=mode['button'])
        app.config(background=mode['background'])
        url_entry.config(style='DarkEntry.TEntry')
        # Update any other widgets that need to change style

# Initialize mode to dark
current_mode = 'dark'

# Set up the window icon and logo
try:
    icon_path = 'images/crawlerLogo.png'  # Make sure the path is correct
    window_icon = Image.open(icon_path)
    photo_icon = ImageTk.PhotoImage(window_icon)
    app.iconphoto(False, photo_icon)

    logo_path = 'images/crawlerLogo.png'  # Make sure the path is correct
    window_logo = Image.open(logo_path)
    photo_logo = ImageTk.PhotoImage(window_logo)

    window_width = photo_logo.width() + 20
    window_height = photo_logo.height() + 60
    app.geometry(f"{window_width}x{window_height}")

    # Calculate the position to center the logo
    x_position = (window_width - photo_logo.width()) // 2
    y_position = 20  # 20 pixels from the top for padding

    # Place the logo at the calculated position
    logo_label = tk.Label(app, image=photo_logo)
    logo_label.image = photo_logo  # Keep a reference
    logo_label.place(x=x_position, y=y_position)
except Exception as e:
    print(f"An error occurred: {e}")


# Function to configure the styles based on the selected mode
mode_var = tk.StringVar()  # Define the mode_var variable

def configure_styles(mode, style):
    if mode == 'dark':
        style.configure('TLabel', background='black', foreground='white')
        style.configure('TButton', background='black', foreground='white')
        style.configure('TEntry', background='black', foreground='white')
    else:
        style.configure('TLabel', background='white', foreground='black')
        style.configure('TButton', background='white', foreground='black')
        style.configure('TEntry', background='white', foreground='black')


mode_dropdown = ttk.Combobox(app, textvariable=mode_var, values=["scrape", "research"], state='readonly')
mode_dropdown.pack()


# URL Input Field
url_entry = ttk.Entry(app, width=50)
url_entry.pack(pady=10)


# Run Button
run_button = ttk.Button(app, text="Run Crawler", command=lambda: threading.Thread(target=run_crawler).start())
run_button.pack(pady=10)


# Status Label
status_label = ttk.Label(app, text="")
status_label.pack(pady=10)


# Toggle Dark/Light Mode Button
toggle_button = ttk.Button(app, text="Toggle Light Mode", command=lambda: toggle_mode())
toggle_button.pack(side='bottom', anchor='se', padx=10, pady=10)


app.mainloop()


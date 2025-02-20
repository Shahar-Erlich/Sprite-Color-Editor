import tkinter as tk #tkinter for all GUI
from tkinter import filedialog #file browser
import os #os to get file paths
import colorsys #colorsys to convert and sort hex colors

from numpy.f2py.capi_maps import f2cmap_all
from tkcolorpicker import askcolor #color picker
from PIL import Image, ImageTk #Python image library to load and handle images

# Create the main window
root = tk.Tk() #create tkinter root
root.title("Pixel Art Color Editor") #window title
root.state("zoomed")
root.resizable(False,False)

# Global variables
photo = None #The photo showing
image_label = None #the image holder
swatch_frame = None #the swatch holder
image_path = None #the image path
num_colors = tk.IntVar(value=10) #number of colors to show
update_task = None #current task to update swatches
modified_image = None #modified image after changing colors
image_button_frame = None #frame to hold the image and button
original_image =None #the original image for size reference
swatch_container = None #container for the swatch to scroll



def filechoose():
    global photo, image_label, swatch_frame, image_path, modified_image, image_button_frame, original_image

    currdir = os.getcwd()  # Get current working directory
    file_path = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select an image')  # Open file browser

    if file_path and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):  # If file is an image
        image_path = file_path  # Store image path

        image = Image.open(file_path).convert("RGBA")  # Open image in RGBA mode
        original_image = image.copy()  # Store original size image

        #  Define fixed display size
        DISPLAY_WIDTH = 500
        DISPLAY_HEIGHT = 500

        #  Maintain aspect ratio while fitting inside the defined box
        img_aspect = image.width / image.height
        display_aspect = DISPLAY_WIDTH / DISPLAY_HEIGHT

        if img_aspect > display_aspect:
            # Wider image: fit to width
            new_width = DISPLAY_WIDTH
            new_height = int(DISPLAY_WIDTH / img_aspect)
        else:
            # Taller image: fit to height
            new_width = int(DISPLAY_HEIGHT * img_aspect)
            new_height = DISPLAY_HEIGHT

        # Resize while keeping aspect ratio
        image = image.resize((new_width, new_height), Image.Resampling.NEAREST)

        # Create a new blank image with the exact display size
        final_image = Image.new("RGBA", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 0, 0))
        final_image.paste(image, ((DISPLAY_WIDTH - new_width) // 2, (DISPLAY_HEIGHT - new_height) // 2))

        photo = ImageTk.PhotoImage(final_image)  # Convert to Tkinter-compatible format
        modified_image = final_image.copy()  # Store working copy

        image_label.config(image=photo)  # Update image display
        image_label.image = photo  # Prevent garbage collection

        print(f"Image loaded! Resized to: {final_image.size}")

        update_color_swatches()  # Update colors


def get_exact_palette(image_path):
    image = Image.open(image_path).convert("RGBA") #open image in RGB format
    pixels = list(image.getdata()) #get a list of all pixels in the image

    unique_colors = sorted(set(pixels)) # sort
    color_counts = {color: pixels.count(color) for color in unique_colors} #count all appearances of each color in the image

    total_pixels = len(pixels) #get total amount of pixels
    dominant_colors = [(color, round((count / total_pixels) * 100, 2)) for color, count in color_counts.items()]

    return dominant_colors


def is_color_too_light(r, g, b):
    # Convert RGB to relative luminance (perceived brightness)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    return luminance > 0.6  # Returns True if the color is too light
def display_color_swatches(dominant_colors):
    global swatch_frame,swatch_container

    if swatch_frame:  # If a swatch set exists, destroy it so a new one can be created
        swatch_frame.destroy()

    # Create a frame to hold the canvas and scrollbar
    if swatch_container:# Destroy previous swatch container if it exists
        swatch_container.destroy()

    swatch_container = tk.Frame(root)# Create a new container to hold everything
    swatch_container.pack(side='left', expand=True, fill='both', padx=10)

    canvas = tk.Canvas(swatch_container)# Create a canvas inside the container
    canvas.pack(side='left', fill='both', expand=True)

    scrollbar = tk.Scrollbar(swatch_container, orient='vertical', command=canvas.yview)# Add a scrollbar to the right side of the canvas for vertical scrolling
    scrollbar.pack(side='right', fill='y')

    # Configure canvas scrolling
    canvas.configure(yscrollcommand=scrollbar.set)# Configure the canvas to update the scrollbar dynamically

    # Create a frame inside the canvas for swatches
    swatch_frame = tk.Frame(canvas)

    swatch_window = canvas.create_window((0, 0), window=swatch_frame, anchor='nw')# Create a frame inside the canvas that will hold all the color swatches

    max_per_row = 15  # Max colors per row

    # Get the hue and lightness value of the image
    def get_hue_lightness(rgb):
        r, g, b, a = rgb  # Get RGB values
        hue, _, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)  # Convert RGB to hue and value
        return value, hue

    sorted_colors = sorted(dominant_colors, key=lambda x: get_hue_lightness(x[0]))  # Sort colors

    # Creating the swatches
    for index, (rgb, percentage) in enumerate(sorted_colors):
        if isinstance(rgb, tuple) and len(rgb) == 1:  # Flatten nested tuples
            rgb = rgb[0]
        if not (isinstance(rgb, tuple) and len(rgb) == 4):  # Validate RGB values
            print(f"Skipping invalid color: {rgb}")
            continue

        color_hex = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"  # Convert RGB to hex
        h,l,s = rgb_2_hsl(rgb)
        # color_label = tk.Label(swatch_frame, bg=color_hex, width=10, height=5, text=f"{color_hex}",   fg="white")  # Swatch
        color_label = tk.Label(swatch_frame, bg=color_hex, width=10, height=5, text=f"H:{h}\nS:{s}\nL:{l}",  fg= "black" if is_color_too_light(rgb[0],rgb[1],rgb[2]) else "white")  # Swatch
        row = index // max_per_row  # Get number of rows
        col = index % max_per_row  # Get number of columns

        color_label.bind("<Button-1>", lambda event, label=color_label: update_swatch(label))  # Click event

        color_label.grid(row=row, column=col, padx=5, pady=5)

    # Update scroll region after widgets are placed
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    swatch_frame.bind("<Configure>", update_scroll_region)

    # Enable mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    canvas.bind_all("<MouseWheel>", on_mousewheel)

def rgb_2_hsl(rgb):
    r, g, b = r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # Scale values to standard HLS ranges
    h = round(h * 360, 1)  # Hue: 0-360 degrees
    l = round(l * 100, 1)  # Lightness: 0-100%
    s = round(s * 100, 1)  # Saturation: 0-100%
    return h,l,s

def update_color_swatches_delayed():
    global update_task
    if update_task:#cancel previous tasks to not overload the thread
        root.after_cancel(update_task)
    update_task = root.after(300, update_color_swatches)  # Wait 300ms before calling the swatch updates to avoid lags when switching fast


def update_swatch(color_label):
    global photo, modified_image

    original_color = color_label.cget("bg")  # Get the current color of the swatch clicked
    new_color = askcolor(original_color)[1]  # Open color picker to choose a new color

    if new_color:  # If a color has been selected
        # Convert HEX to RGB (Ignoring Alpha)
        original_rgb = tuple(int(original_color[i:i + 2], 16) for i in (1, 3, 5))
        new_rgb = tuple(int(new_color[i:i + 2], 16) for i in (1, 3, 5))
        h,l,s = rgb_2_hsl(new_rgb)
        color_label.config(bg=new_color,text=f"H:{h}\nL:{l}\nS:{s}", fg= "black" if is_color_too_light(new_rgb[0],new_rgb[1],new_rgb[2]) else "white")  # Change current swatch BG to new color

        pixels = modified_image.load()  # Get all pixels of the modified image
        width, height = modified_image.size  # Get width and height

        for x in range(width):
            for y in range(height):
                current_pixel = pixels[x, y]

                # Handle RGBA images (ignore alpha when checking colors)
                if len(current_pixel) == 4:  # (R, G, B, A)
                    if current_pixel[:3] == original_rgb:  # Compare only R, G, B
                        pixels[x, y] = new_rgb + (current_pixel[3],)  # Preserve alpha
                else:  # If RGB image
                    if current_pixel == original_rgb:
                        pixels[x, y] = new_rgb

        updated_photo = modified_image
        photo = ImageTk.PhotoImage(updated_photo)
        image_label.config(image=photo)
        image_label.image = photo  # Prevent garbage collection


def update_color_swatches():
    if image_path:# if image path isnt null
        print("Extracting colors")
        dominant_colors = get_exact_palette(image_path) # get colors
        display_color_swatches(dominant_colors) #display swatches

def save_image():
    global modified_image

    if modified_image is None: #if no image was selected at first
        print("No modified image to save.")
        return

    # Open file dialog to choose save location
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG file", "*.png")],
        title="Save Image As"
    )

    if file_path:  # Ensure a file was selected
        try:
            image_to_save = modified_image.resize(original_image.size) #create a new image from the modified image with the original size
            image_to_save.convert("RGBA").save(file_path, "PNG") #save it as a png
            print(f"Image saved successfully: {file_path}")
        except Exception as e:
            print(f"Error saving image: {e}")


def initStuff():
    global photo, image_label, swatch_frame,image_button_frame #Global variables

    menubar = tk.Menu(root)
    save_menu = tk.Menu(menubar,tearoff=False)
    save_menu.add_command(
        label='Save Image',
        command=save_image,
    )
    menubar.add_cascade(
        label="File",
        menu=save_menu,
        underline=0
    )
    root.config(menu=menubar)

    image_button_frame = tk.Frame(root)
    image_button_frame.pack(side = 'right',pady=10)

    image_label = tk.Label(image_button_frame) #Create the image holder
    image_label.pack(pady=20)

    button = tk.Button(image_button_frame, text="Choose an image", command=filechoose, font=("Arial", 14)) #Create the button
    button.pack(pady=10)

    num_colors.trace_add("write", lambda *args: update_color_swatches_delayed()) # Add call to update swatches when number of colors changes

    swatch_frame = tk.Frame(root) #create holder for swatches
    swatch_frame.pack(side = 'left',pady=10)

    root.mainloop()



if __name__ == "__main__":
    initStuff() #Start initialization

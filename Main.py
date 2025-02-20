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
root.geometry("1000x1500")  # create a window

# Global variables
photo = None #The photo showing
image_label = None #the image holder
swatch_frame = None #the swatch holder
image_path = None #the image path
num_colors = tk.IntVar(value=10) #number of colors to show
update_task = None #current task to update swatches
modified_image = None #modified image after changing colors


def filechoose():
    global photo, image_label, swatch_frame, image_path, modified_image

    currdir = os.getcwd() #get current working directory
    file_path = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select an image') #open a file browser

    if file_path and file_path.lower().endswith(('.png', '.jpg', '.jpeg')): #if file is an image
        image_path = file_path #get image path

        image = Image.open(file_path).convert("RGB") #open image convert to RGB

        photo = ImageTk.PhotoImage(image)#load image

        modified_image = image.copy()

        image_label.config(image=photo)
        image_label.image = photo

        print("Image loaded!")

        update_color_swatches() #update colors


def get_exact_palette(image_path):
    image = Image.open(image_path).convert("RGB") #open image in RGB format
    pixels = list(image.getdata()) #get a list of all pixels in the image

    unique_colors = sorted(set(pixels)) # sort
    color_counts = {color: pixels.count(color) for color in unique_colors} #count all appearances of each color in the image

    total_pixels = len(pixels) #get total amount of pixels
    dominant_colors = [(color, round((count / total_pixels) * 100, 2)) for color, count in color_counts.items()]

    return dominant_colors


def display_color_swatches(dominant_colors):
    global swatch_frame

    if swatch_frame: # if a switch set exists, destroy so a new one can be created
        swatch_frame.destroy()

    swatch_frame = tk.Frame(root) #recreate swatch holder
    swatch_frame.pack(pady=10)

    max_per_row = 6 #max colors per row

    ## Get the hue and lightness value of the image
    def get_hue_lightness(rgb):
        r, g, b = rgb #get RGB values
        hue, _, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0) #convert RGB to hue and value
        return value, hue

    sorted_colors = sorted(dominant_colors, key=lambda x: get_hue_lightness(x[0])) #sort

    #Creating the swatches
    for index, (rgb,percentage) in enumerate(sorted_colors):
        if isinstance(rgb, tuple) and len(rgb) == 1: #check if the color is nested tuple i.e: ((R,G,B),a)) and flatten it
            rgb = rgb[0]
        if not (isinstance(rgb, tuple) and len(rgb) == 3): #check if color has valid R,G,B values
            print(f"Skipping invalid color: {rgb}")
            continue

        color_hex = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}" #convert rgb values to hex

        row = index // max_per_row #get amount of rows that need to be added
        col = index % max_per_row #get amount of cols that need to be added

        color_label = tk.Label(swatch_frame, bg=color_hex, width=10, height=5, text=f"{color_hex}", fg="white") #set up the swatch with correct color background and hex value printed
        color_label.bind("<Button-1>", lambda event, label=color_label: update_swatch(label))#add an event to open a color picker and change color on click

        color_label.grid(row=row, column=col, padx=5, pady=5)


def update_color_swatches_delayed():
    global update_task
    if update_task:#cancel previous tasks to not overload the thread
        root.after_cancel(update_task)
    update_task = root.after(300, update_color_swatches)  # Wait 300ms before calling the swatch updates to avoid lags when switching fast


def update_swatch(color_label):
    global photo, modified_image

    original_color = color_label.cget("bg") #get the current color of the swatch clicked
    new_color = askcolor(original_color)[1] #open color picker to choose a new color

    if new_color: #if a color has been selected
        color_label.config(bg=new_color) #change current swatch BG to new color
        original_rgb = tuple(int(original_color[i:i + 2], 16) for i in (1, 3, 5))#converts RGB to tuple, for each i - i+2 convert to base 16
        new_rgb = tuple(int(new_color[i:i + 2], 16) for i in (1, 3, 5))#converts RGB to tuple, for each i - i+2 convert to base 16

        pixels = modified_image.load() #get all the pixels of the current image
        width, height = modified_image.size #get width and height of current image

        for x in range(width):
            for y in range(height):
                if pixels[x, y] == original_rgb: #for every pixel if it matches the old color
                    pixels[x, y] = new_rgb #change it to new color

        photo = ImageTk.PhotoImage(modified_image) #change photo to the new modified photo
        image_label.config(image=photo)#change label image
        image_label.image = photo


def update_color_swatches():
    if image_path:# if image path isnt null
        print("Extracting colors")
        dominant_colors = get_exact_palette(image_path) # get colors
        display_color_swatches(dominant_colors) #display swatches

def save_image():
    """Saves the modified image to a user-selected location."""
    global modified_image

    if modified_image is None:
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
            # Ensure image is in RGB mode before saving
            modified_image.convert("RGB").save(file_path, "PNG")
            print(f"Image saved successfully: {file_path}")
        except Exception as e:
            print(f"Error saving image: {e}")


def initStuff():
    global photo, image_label, swatch_frame #Global variables

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


    image_label = tk.Label(root) #Create the image holder
    image_label.pack(pady=20)

    button = tk.Button(root, text="Choose an image", command=filechoose, font=("Arial", 14)) #Create the button
    button.pack(pady=10)

    slider_frame = tk.Frame(root) #Create color amount slider
    slider_frame.pack(pady=10)
    tk.Label(slider_frame, text="Number of Colors:").pack(side=tk.LEFT)
    cluster_slider = tk.Scale(slider_frame, from_=2, to=50, orient=tk.HORIZONTAL, variable=num_colors)
    cluster_slider.pack(side=tk.LEFT)

    num_colors.trace_add("write", lambda *args: update_color_swatches_delayed()) # Add call to update swatches when number of colors changes

    swatch_frame = tk.Frame(root) #create holder for swatches
    swatch_frame.pack(pady=10)

    root.mainloop()



if __name__ == "__main__":
    initStuff() #Start initialization

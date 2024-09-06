import os
import re
import webbrowser
import configparser
from tkinter import Tk, filedialog, Button, Canvas, messagebox, Frame, Menu, Scrollbar, Toplevel, Label, Entry
from PIL import Image, ImageTk, ImageFont, ImageDraw

SETTINGS_FILE = "settings.ini"

def natural_sort_key(s):
    """Split string into a list of integers and text for natural sorting."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

class ImageCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Linx Bulk Image Cropper')

        self.load_settings()

        self.menubar = Menu(root)
        root.config(menu=self.menubar)

        self.menubar.add_command(label="Select Folder", command=self.load_folder)

        settings_menu = Menu(self.menubar, tearoff=0)
        settings_menu.add_command(label="Configure Shortcuts", command=self.open_settings_dialog)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)

        self.main_frame = Frame(root, width=1280)
        self.main_frame.pack()

        self.left_nav_button = Button(self.main_frame, text="◀", command=self.show_previous_image, width=5)
        self.left_nav_button.grid(row=0, column=0, sticky="ns")

        self.canvas = Canvas(self.main_frame, width=800, height=600)
        self.canvas.grid(row=0, column=1)

        self.right_nav_button = Button(self.main_frame, text="▶", command=self.show_next_image, width=5)
        self.right_nav_button.grid(row=0, column=2, sticky="ns")

        self.preview_frame = Frame(self.main_frame)
        self.preview_frame.grid(row=1, column=0, columnspan=3, sticky="we")

        self.scrollbar = Scrollbar(self.preview_frame, orient='horizontal')
        self.scrollbar.pack(side='bottom', fill='x')

        self.preview_canvas = Canvas(self.preview_frame, height=100, width=800, scrollregion=(0, 0, 1000, 100))
        self.preview_canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar.config(command=self.preview_canvas.xview)
        self.preview_canvas.config(xscrollcommand=self.scrollbar.set)

        self.preview_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        self.preview_canvas.bind("<Button-4>", self.on_mouse_wheel_linux)
        self.preview_canvas.bind("<Button-5>", self.on_mouse_wheel_linux)

        self.font_path = "resources/fa-solid-900.ttf"

        self.confirm_crop_icon = self.create_icon('\uf0c7', (30, 30))
        self.duplicate_icon = self.create_icon('\uf0c5', (30, 30))

        self.confirm_crop_button = Button(self.canvas, image=self.confirm_crop_icon, command=self.confirm_crop, state="disabled")
        self.duplicate_button = Button(self.canvas, image=self.duplicate_icon, command=self.duplicate_crop, state="disabled")
        self.confirm_crop_button_id = None
        self.duplicate_button_id = None

        self.images = []
        self.current_image_index = 0
        self.crop_box = None
        self.rect = None
        self.overlay = None
        self.crop_count = 0
        self.current_image = None
        self.display_image = None
        self.cropped_thumbnails = []
        self.thumbnail_paths = []

        self.bind_shortcuts()

    def create_icon(self, icon_unicode, size):
        """Create an icon using FontAwesome TTF and Pillow."""
        icon_img = Image.new('RGBA', size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(icon_img)

        font = ImageFont.truetype(self.font_path, size=size[0])

        draw.text((0, 0), icon_unicode, font=font, fill='black')

        return ImageTk.PhotoImage(icon_img)

    def on_mouse_wheel(self, event):
        """Translate vertical mouse wheel scroll to horizontal scroll."""
        if event.delta:
            self.preview_canvas.xview_scroll(-1 * (event.delta // 120), "units")

    def on_mouse_wheel_linux(self, event):
        """Handle scrolling for Linux/macOS."""
        if event.num == 4:  
            self.preview_canvas.xview_scroll(-1, "units")
        elif event.num == 5:  
            self.preview_canvas.xview_scroll(1, "units")

    def load_folder(self):
        """Select a folder and automatically start the cropping process."""
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.images = sorted(
                [os.path.join(self.folder_path, file) for file in os.listdir(self.folder_path) if file.endswith(('.png', '.jpg', '.jpeg'))],
                key=lambda x: natural_sort_key(os.path.basename(x))
            )
            if self.images:
                self.start_cropping()
            else:
                messagebox.showerror("Error", "No images found in the folder.")

    def start_cropping(self):
        """Begin the cropping process."""
        if self.images:
            self.show_next_image()

    def show_next_image(self):
        """Show the next image in the sequence."""
        if self.current_image_index < len(self.images):
            self.current_image = Image.open(self.images[self.current_image_index])

            self.display_image = self.current_image.copy()
            self.display_image.thumbnail((800, 600))

            self.img_display = ImageTk.PhotoImage(self.display_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor='nw', image=self.img_display)

            self.canvas.config(height=self.display_image.height)

            self.crop_count = 0
            self.current_image_index += 1
            self.setup_crop_selection()
        else:
            messagebox.showinfo("Info", "All images have been processed.")

    def show_previous_image(self):
        """Show the previous image in the sequence."""
        if self.current_image_index > 1:
            self.current_image_index -= 2
            self.show_next_image()
        else:
            messagebox.showinfo("Info", "No previous images.")

    def setup_crop_selection(self):
        """Set up the crop selection mechanism on the canvas."""
        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.perform_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)
        self.crop_box = None
        self.overlay = None
        if self.confirm_crop_button_id:
            self.canvas.delete(self.confirm_crop_button_id)
        if self.duplicate_button_id:
            self.canvas.delete(self.duplicate_button_id)

    def start_crop(self, event):
        """Begin drawing the crop rectangle."""
        self.start_x = max(0, min(event.x, self.display_image.width))
        self.start_y = max(0, min(event.y, self.display_image.height))
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = None
        if self.overlay:
            self.canvas.delete(self.overlay)
        self.overlay = None

    def perform_crop(self, event):
        """Update the crop rectangle as the mouse is dragged."""
        self.end_x = max(0, min(event.x, self.display_image.width))
        self.end_y = max(0, min(event.y, self.display_image.height))

        self.canvas.delete("overlay")
        self.canvas.delete(self.rect)

        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline='red', width=2)

        self.canvas.delete("overlay")
        left, right = min(self.start_x, self.end_x), max(self.start_x, self.end_x)
        top, bottom = min(self.start_y, self.end_y), max(self.start_y, self.end_y)
        self.canvas.create_rectangle(0, 0, 800, top, fill='black', stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(0, bottom, 800, self.display_image.height, fill='black', stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(0, top, left, bottom, fill='black', stipple="gray50", tags="overlay")
        self.canvas.create_rectangle(right, top, 800, bottom, fill='black', stipple="gray50", tags="overlay")

    def end_crop(self, event):
        """Finalize the crop rectangle."""
        left = min(self.start_x, self.end_x)
        right = max(self.start_x, self.end_x)
        top = min(self.start_y, self.end_y)
        bottom = max(self.start_y, self.end_y)
        self.crop_box = (left, top, right, bottom)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        button_width = 30
        button_height = 30
        total_button_width = button_width * 2 + 20
        padding = 10

        button_x = min(right, canvas_width - total_button_width - padding)
        button_y = min(bottom + padding, canvas_height - button_height - padding)

        if self.confirm_crop_button_id:
            self.canvas.delete(self.confirm_crop_button_id)
        if self.duplicate_button_id:
            self.canvas.delete(self.duplicate_button_id)

        self.confirm_crop_button.config(state="normal")
        self.duplicate_button.config(state="normal")
        self.confirm_crop_button_id = self.canvas.create_window(button_x, button_y, window=self.confirm_crop_button, anchor="nw")
        self.duplicate_button_id = self.canvas.create_window(button_x + button_width + padding, button_y, window=self.duplicate_button, anchor="nw")

    def save_crop(self, is_duplicate=False):
        """Save the cropped portion of the image."""
        if self.crop_box:
            display_width, display_height = self.display_image.size
            original_width, original_height = self.current_image.size

            scale_x = original_width / display_width
            scale_y = original_height / display_height

            scaled_crop_box = (
                int(self.crop_box[0] * scale_x),
                int(self.crop_box[1] * scale_y),
                int(self.crop_box[2] * scale_x),
                int(self.crop_box[3] * scale_y)
            )

            if scaled_crop_box[2] <= scaled_crop_box[0] or scaled_crop_box[3] <= scaled_crop_box[1]:
                messagebox.showerror("Error", "Invalid crop area. Please try again.")
                return

            cropped_image = self.current_image.crop(scaled_crop_box)
            result_folder = os.path.join(self.folder_path, 'result')
            os.makedirs(result_folder, exist_ok=True)

            self.crop_count += 1
            cropped_image_path = os.path.join(result_folder, f'cropped_{self.current_image_index}_{self.crop_count}.jpg')
            cropped_image.save(cropped_image_path, quality=100)

            self.add_thumbnail_to_preview(cropped_image, cropped_image_path)

    def add_thumbnail_to_preview(self, cropped_image, image_path):
        """Add a cropped image to the preview area with the correct aspect ratio and centered in a square."""
        max_thumb_width, max_thumb_height = 100, 100

        thumbnail = cropped_image.copy()
        thumbnail.thumbnail((max_thumb_width, max_thumb_height), Image.Resampling.LANCZOS)

        thumb_canvas = Image.new('RGBA', (max_thumb_width, max_thumb_height), (255, 255, 255, 0))

        thumb_x = (max_thumb_width - thumbnail.width) // 2
        thumb_y = (max_thumb_height - thumbnail.height) // 2

        thumb_canvas.paste(thumbnail, (thumb_x, thumb_y))

        thumbnail_tk = ImageTk.PhotoImage(thumb_canvas)

        self.cropped_thumbnails.insert(0, thumbnail_tk)
        self.thumbnail_paths.insert(0, image_path)

        self.preview_canvas.delete("all")
        for i, thumbnail in enumerate(self.cropped_thumbnails):
            x_position = i * (max_thumb_width + 10)
            thumbnail_id = self.preview_canvas.create_image(x_position, 0, anchor="nw", image=thumbnail)
            self.preview_canvas.tag_bind(thumbnail_id, "<Button-1>", lambda e, path=self.thumbnail_paths[i]: self.open_image(path))

        new_width = len(self.cropped_thumbnails) * (max_thumb_width + 10)
        self.preview_canvas.config(scrollregion=(0, 0, new_width, 100))

    def open_image(self, image_path):
        """Open the image using the default image viewer."""
        if os.name == 'nt':
            os.startfile(image_path)
        else:
            webbrowser.open(image_path)

    def confirm_crop(self):
        """Save the current crop and proceed to the next image."""
        self.save_crop(is_duplicate=False)

        if self.confirm_crop_button_id:
            self.canvas.delete(self.confirm_crop_button_id)
        if self.duplicate_button_id:
            self.canvas.delete(self.duplicate_button_id)

        self.show_next_image()

    def duplicate_crop(self):
        """Save the current crop as a duplicate and allow further cropping on the same image."""
        self.save_crop(is_duplicate=True)
        self.setup_crop_selection()

    def load_settings(self):
        """Load settings from the settings.ini file or set defaults."""
        self.config = configparser.ConfigParser()
        self.shortcuts = {
            'save': 's',
            'duplicate': 'd',
            'next_image': 'Right',
            'previous_image': 'Left'
        }

        if os.path.exists(SETTINGS_FILE):
            self.config.read(SETTINGS_FILE)
            if 'SHORTCUTS' in self.config:
                for key in self.shortcuts:
                    self.shortcuts[key] = self.config['SHORTCUTS'].get(key, self.shortcuts[key])
        else:
            self.config['SHORTCUTS'] = self.shortcuts
            with open(SETTINGS_FILE, 'w') as configfile:
                self.config.write(configfile)

        self.previous_shortcuts = self.shortcuts.copy()

    def bind_shortcuts(self):
        """Unbind old shortcuts and bind new ones to their respective functions."""
        try:
            self.root.unbind(f"<{self.previous_shortcuts['save']}>")
            self.root.unbind(f"<{self.previous_shortcuts['duplicate']}>")
            self.root.unbind(f"<{self.previous_shortcuts['next_image']}>")
            self.root.unbind(f"<{self.previous_shortcuts['previous_image']}>")
        except AttributeError:
            pass

        self.root.bind(f"<{self.shortcuts['save']}>", lambda event: self.confirm_crop())
        self.root.bind(f"<{self.shortcuts['duplicate']}>", lambda event: self.duplicate_crop())
        self.root.bind(f"<{self.shortcuts['next_image']}>", lambda event: self.show_next_image())
        self.root.bind(f"<{self.shortcuts['previous_image']}>", lambda event: self.show_previous_image())

        self.previous_shortcuts = self.shortcuts.copy()

    def open_settings_dialog(self):
        """Open a dialog to modify shortcuts."""
        dialog = Toplevel(self.root)
        dialog.title("Configure Shortcuts")

        def on_key_press(event, entry_widget):
            """Handles key press event and updates entry widget with the correct key."""
            key = event.keysym

            if len(key) == 1 or key in ('Left', 'Right', 'Up', 'Down', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'):
                entry_widget.delete(0, 'end')  # Clear the entry field
                entry_widget.insert(0, key)  # Insert the detected key

            return "break"

        Label(dialog, text="Save Crop:").grid(row=0, column=0)
        save_entry = Entry(dialog)
        save_entry.grid(row=0, column=1)
        save_entry.insert(0, self.shortcuts['save'])
        save_entry.bind("<KeyPress>", lambda event: on_key_press(event, save_entry))

        Label(dialog, text="Duplicate Crop:").grid(row=1, column=0)
        duplicate_entry = Entry(dialog)
        duplicate_entry.grid(row=1, column=1)
        duplicate_entry.insert(0, self.shortcuts['duplicate'])
        duplicate_entry.bind("<KeyPress>", lambda event: on_key_press(event, duplicate_entry))

        Label(dialog, text="Next Image:").grid(row=2, column=0)
        next_image_entry = Entry(dialog)
        next_image_entry.grid(row=2, column=1)
        next_image_entry.insert(0, self.shortcuts['next_image'])
        next_image_entry.bind("<KeyPress>", lambda event: on_key_press(event, next_image_entry))

        Label(dialog, text="Previous Image:").grid(row=3, column=0)
        previous_image_entry = Entry(dialog)
        previous_image_entry.grid(row=3, column=1)
        previous_image_entry.insert(0, self.shortcuts['previous_image'])
        previous_image_entry.bind("<KeyPress>", lambda event: on_key_press(event, previous_image_entry))

        def save_shortcuts():
            """Save the shortcuts to the settings.ini file."""
            self.shortcuts['save'] = save_entry.get()
            self.shortcuts['duplicate'] = duplicate_entry.get()
            self.shortcuts['next_image'] = next_image_entry.get()
            self.shortcuts['previous_image'] = previous_image_entry.get()

            self.config['SHORTCUTS'] = self.shortcuts
            with open(SETTINGS_FILE, 'w') as configfile:
                self.config.write(configfile)

            self.bind_shortcuts()
            dialog.destroy()

        Button(dialog, text="Save", command=save_shortcuts).grid(row=4, column=0, columnspan=2)



if __name__ == '__main__':
    root = Tk()
    app = ImageCropperApp(root)
    root.mainloop()

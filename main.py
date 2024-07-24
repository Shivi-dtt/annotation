import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageOps
import numpy as np

class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")

        # Create canvas and scrollbars
        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_x = tk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.scroll_y = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<B1-Motion>", self.on_freehand_draw, add="+")
        self.canvas.bind("<MouseWheel>", self.on_zoom)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.drawing = False
        self.freehand_id = None
        self.image = None
        self.tk_image = None
        self.original_image = None
        self.labels = []
        self.freehand_labels = []
        self.font_color = "black"
        self.rect_color = "red"
        self.freehand_color = "blue"
        self.scale = 1.0
        self.rotation = 0  # Rotation angle in degrees

        # Create menus
        self.menubar = tk.Menu(root)
        self.root.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_image)
        self.file_menu.add_command(label="Save Annotations", command=self.save_annotations)
        self.file_menu.add_command(label="Save Image", command=self.save_image)
        self.file_menu.add_command(label="Exit", command=root.quit)

        # Color selection buttons
        self.color_frame = tk.Frame(root)
        self.color_frame.pack(side=tk.BOTTOM, pady=5)
        self.font_color_button = tk.Button(self.color_frame, text="Font Color", command=self.choose_font_color)
        self.font_color_button.pack(side=tk.LEFT, padx=5)
        self.rect_color_button = tk.Button(self.color_frame, text="Rect Color", command=self.choose_rect_color)
        self.rect_color_button.pack(side=tk.LEFT, padx=5)
        self.freehand_color_button = tk.Button(self.color_frame, text="Freehand Color", command=self.choose_freehand_color)
        self.freehand_color_button.pack(side=tk.LEFT, padx=5)

        # Label entry and add button
        self.label_entry = tk.Entry(root, width=20)
        self.label_entry.pack(side=tk.BOTTOM, pady=5)
        self.label_button = tk.Button(root, text="Add Label", command=self.add_label)
        self.label_button.pack(side=tk.BOTTOM, pady=5)

        # Toggle for freehand drawing
        self.freehand_mode = False
        self.freehand_button = tk.Button(root, text="Toggle Freehand Mode", command=self.toggle_freehand_mode)
        self.freehand_button.pack(side=tk.BOTTOM, pady=5)

        # Store freehand drawings separately
        self.freehand_drawings = []

        # Zoom and Rotate buttons
        self.zoom_in_button = tk.Button(root, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.zoom_out_button = tk.Button(root, text="Zoom Out", command=self.zoom_out)
        self.zoom_out_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.rotate_button = tk.Button(root, text="Rotate 90°", command=self.rotate_image)
        self.rotate_button.pack(side=tk.LEFT, padx=5, pady=5)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if not file_path:
            return
        self.image = Image.open(file_path)
        self.original_image = self.image.copy()  # Keep a copy of the original image
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.rect = None
        self.labels = []
        self.freehand_drawings = []
        self.freehand_labels = []  # Clear previous freehand labels

    def on_click(self, event):
        if self.freehand_mode:
            return
        if self.rect:
            self.canvas.delete(self.rect)
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                   outline=self.rect_color)

    def on_drag(self, event):
        if self.freehand_mode:
            return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_freehand_draw(self, event):
        if not self.freehand_mode:
            return
        if not self.drawing:
            self.drawing = True
            self.prev_x = self.canvas.canvasx(event.x)
            self.prev_y = self.canvas.canvasy(event.y)
        else:
            cur_x = self.canvas.canvasx(event.x)
            cur_y = self.canvas.canvasy(event.y)
            line_id = self.canvas.create_line(self.prev_x, self.prev_y, cur_x, cur_y, fill=self.freehand_color, width=2)
            self.freehand_drawings.append(line_id)
            self.prev_x = cur_x
            self.prev_y = cur_y

    def on_freehand_draw_release(self, event):
        self.drawing = False

    def add_label(self):
        if not self.freehand_mode and self.rect_id:
            label = self.label_entry.get()
            if label:
                self.labels.append((self.rect_id, label))
                self.label_entry.delete(0, tk.END)
                self.canvas.create_text(self.start_x, self.start_y - 10, text=label, fill=self.font_color)
            else:
                messagebox.showwarning("Warning", "Please enter a label.")
        elif self.freehand_mode:
            # Optionally handle labeling freehand drawings
            label = self.label_entry.get()
            if label:
                self.freehand_labels.append((self.freehand_drawings[-1], label))  # Label the last freehand drawing
                self.label_entry.delete(0, tk.END)
                # Create label for the last freehand drawing (simplified approach)
                x, y = self.canvas.coords(self.freehand_drawings[-1])[0:2]
                self.canvas.create_text(x, y - 10, text=label, fill=self.font_color)
            else:
                messagebox.showwarning("Warning", "Please enter a label.")

    def save_annotations(self):
        if not self.image:
            messagebox.showwarning("Warning", "No image to save annotations.")
            return
        annotations = []
        for rect_id, label in self.labels:
            coords = self.canvas.coords(rect_id)
            annotations.append({
                'label': label,
                'bbox': (coords[0], coords[1], coords[2], coords[3])
            })
        for line_id, label in self.freehand_labels:
            coords = self.canvas.coords(line_id)
            annotations.append({
                'label': label,
                'freehand': coords
            })
        # Save annotations (e.g., to a file)
        with open("annotations.txt", "w") as f:
            for ann in annotations:
                if 'bbox' in ann:
                    f.write(f"{ann['label']} {ann['bbox']}\n")
                else:
                    f.write(f"{ann['label']} {ann['freehand']}\n")
        messagebox.showinfo("Info", "Annotations saved.")

    def save_image(self):
        if not self.image:
            messagebox.showwarning("Warning", "No image to save.")
            return

        # Draw annotations on the image
        draw = ImageDraw.Draw(self.image)
        for rect_id, label in self.labels:
            coords = self.canvas.coords(rect_id)
            draw.rectangle(coords, outline=self.rect_color, width=2)
            draw.text((coords[0], coords[1] - 10), label, fill=self.font_color)

        # Draw freehand drawings
        for line_id, label in self.freehand_labels:
            coords = self.canvas.coords(line_id)
            draw.line(coords, fill=self.freehand_color, width=2)
            x, y = coords[0:2]
            draw.text((x, y - 10), label, fill=self.font_color)

        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                               filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if not file_path:
            return
        self.image.save(file_path)
        messagebox.showinfo("Info", "Image saved with annotations.")

    def choose_font_color(self):
        color = colorchooser.askcolor(title="Choose Font Color")[1]
        if color:
            self.font_color = color

    def choose_rect_color(self):
        color = colorchooser.askcolor(title="Choose Rectangle Color")[1]
        if color:
            self.rect_color = color

    def choose_freehand_color(self):
        color = colorchooser.askcolor(title="Choose Freehand Color")[1]
        if color:
            self.freehand_color = color

    def toggle_freehand_mode(self):
        self.freehand_mode = not self.freehand_mode
        self.canvas.config(cursor="cross" if self.freehand_mode else "arrow")

    def on_zoom(self, event):
        factor = 1.1
        if event.delta < 0:
            factor = 1 / factor
        self.scale *= factor
        self.zoom_image(factor)
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_in(self):
        self.scale *= 1.1
        self.zoom_image(1.1)
        self.canvas.scale("all", 0, 0, 1.1, 1.1)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_out(self):
        self.scale *= 0.9
        self.zoom_image(0.9)
        self.canvas.scale("all", 0, 0, 0.9, 0.9)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_image(self, factor):
        if not self.image:
            return
        new_size = (int(self.image.width * factor), int(self.image.height * factor))
        self.image = self.original_image.resize(new_size, Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def rotate_image(self):
        if not self.image:
            messagebox.showwarning("Warning", "No image to rotate.")
            return
        self.rotation = (self.rotation + 90) % 360
        self.image = self.original_image.rotate(self.rotation, expand=True)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()

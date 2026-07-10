import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2

from test import predict_liver_condition  # your existing function, class-only version


class LiverScanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Liver Ultrasound Classifier")
        self.root.geometry("420x520")
        self.root.resizable(False, False)

        self.image_path = None

        # Title
        tk.Label(root, text="Liver Ultrasound Classifier",
                 font=("Segoe UI", 16, "bold")).pack(pady=15)

        # Image preview area
        self.image_label = tk.Label(root, text="No image selected",
                                     width=40, height=15, bg="#f0f0f0",
                                     relief="groove")
        self.image_label.pack(pady=10)

        # Upload button
        self.upload_btn = tk.Button(root, text="Upload Image",
                                     font=("Segoe UI", 11),
                                     command=self.upload_image,
                                     bg="#4a90d9", fg="white",
                                     padx=10, pady=5)
        self.upload_btn.pack(pady=10)

        # Predict button
        self.predict_btn = tk.Button(root, text="Run Prediction",
                                      font=("Segoe UI", 11),
                                      command=self.run_prediction,
                                      bg="#2e7d32", fg="white",
                                      padx=10, pady=5, state="disabled")
        self.predict_btn.pack(pady=5)

        # Result display
        self.result_label = tk.Label(root, text="",
                                      font=("Segoe UI", 14, "bold"),
                                      fg="#333")
        self.result_label.pack(pady=20)

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select an ultrasound image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not file_path:
            return

        self.image_path = file_path
        self.result_label.config(text="")  # clear old result

        # Show preview
        img = Image.open(file_path)
        img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk, text="")
        self.image_label.image = img_tk  # keep a reference so it doesn't get garbage-collected

        self.predict_btn.config(state="normal")

    def run_prediction(self):
        if not self.image_path:
            messagebox.showwarning("No image", "Please upload an image first.")
            return

        self.result_label.config(text="Predicting...", fg="#888")
        self.root.update_idletasks()  # force UI to refresh before the (blocking) predict call

        try:
            predicted_class = predict_liver_condition(self.image_path)
            self.result_label.config(text=f"Prediction: {predicted_class}", fg="#1b5e20")
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed:\n{e}")
            self.result_label.config(text="")


def main():
    root = tk.Tk()
    app = LiverScanApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
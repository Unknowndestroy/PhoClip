import sys
import os
import ctypes
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import win32clipboard
import io
import hashlib

son_hash_img = None
son_hash_text = None
last_img_popup = None
last_text_popup = None

def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    params = ' '.join([f'"{x}"' for x in sys.argv])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        return False
    except:
        return False

def clipboard_hash_img():
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            win32clipboard.CloseClipboard()
            if data:
                img = Image.open(io.BytesIO(data))
                return hashlib.md5(img.tobytes()).hexdigest()
        win32clipboard.CloseClipboard()
    except:
        try: win32clipboard.CloseClipboard()
        except: pass
    return None

def clipboard_get_text():
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return data
        win32clipboard.CloseClipboard()
    except:
        try: win32clipboard.CloseClipboard()
        except: pass
    return None

def slide_in(window, w, h, x, y_start, y_end):
    def _in():
        nonlocal y_start
        if y_start > y_end:
            y_start -= 10
            window.geometry(f"{w}x{h}+{x}+{y_start}")
            window.after(10, _in)
        else:
            window.geometry(f"{w}x{h}+{x}+{y_end}")
    _in()

def slide_out(window, w, h, x, y_limit):
    def _out():
        geom = window.geometry().split('+')
        curr_y = int(geom[2])
        if curr_y < y_limit:
            curr_y += 10
            window.geometry(f"{w}x{h}+{x}+{curr_y}")
            window.after(10, _out)
        else:
            window.destroy()
    _out()

def show_image_popup(img):
    global last_img_popup
    if last_img_popup and last_img_popup.winfo_exists():
        slide_out(last_img_popup, *last_img_popup._geom)
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.wm_attributes("-topmost", True)
    p.wm_attributes("-alpha", 0.95)

    sw, sh = p.winfo_screenwidth(), p.winfo_screenheight()
    iw, ih = img.size
    max_w, max_h = int(sw * 0.6), int(sh * 0.6)
    if iw > max_w or ih > max_h:
        scale = min(max_w / iw, max_h / ih)
        iw, ih = int(iw * scale), int(ih * scale)
        img = img.resize((iw, ih))

    btn_size = 25
    total_w, total_h = iw + btn_size, ih
    x0, y_start, y_end, y_limit = 20, sh, sh - ih - 50, sh
    p.geometry(f"{total_w}x{total_h}+{x0}+{y_start}")
    p._geom = (total_w, total_h, x0, y_limit)

    photo = ImageTk.PhotoImage(img)
    label = tk.Label(p, image=photo, bd=0)
    label.image = photo
    label.place(x=0, y=0)

    btn = tk.Button(p, text="✖", bg="red", fg="white", bd=0, highlightthickness=0,
                    command=lambda: slide_out(p, total_w, total_h, x0, y_limit))
    btn.place(x=iw, y=0, width=btn_size, height=btn_size)
    p.bind("<KeyPress-x>", lambda e: slide_out(p, total_w, total_h, x0, y_limit))
    slide_in(p, total_w, total_h, x0, y_start, y_end)
    last_img_popup = p

def show_text_popup(text):
    global last_text_popup
    if last_text_popup and last_text_popup.winfo_exists():
        slide_out(last_text_popup, *last_text_popup._geom)
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.wm_attributes("-topmost", True)
    p.wm_attributes("-alpha", 0.95)

    sw, sh = p.winfo_screenwidth(), p.winfo_screenheight()
    w, h = 300, 100
    x_end, y0, y_end, y_limit = sw - w - 20, sh, sh - h - 50, sh
    p.geometry(f"{w}x{h}+{x_end}+{y0}")
    p._geom = (w, h, x_end, y_limit)

    txt_widget = scrolledtext.ScrolledText(p, wrap=tk.WORD, bd=1, relief="solid")
    txt_widget.insert(tk.END, text)
    txt_widget.configure(state="normal")
    txt_widget.place(x=0, y=0, width=w-35, height=h)

    btn = tk.Button(p, text="✖", bg="red", fg="white", bd=0, highlightthickness=0,
                    command=lambda: slide_out(p, w, h, x_end, y_limit))
    btn.place(x=w-35, y=0, width=35, height=35)
    p.bind("<KeyPress-x>", lambda e: slide_out(p, w, h, x_end, y_limit))
    slide_in(p, w, h, x_end, y0, y_end)
    last_text_popup = p

def poll_clipboard():
    global son_hash_img, son_hash_text

    img_hash = clipboard_hash_img()
    if img_hash and img_hash != son_hash_img:
        son_hash_img = img_hash
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            win32clipboard.CloseClipboard()
            img = Image.open(io.BytesIO(data))
            show_image_popup(img)
        except:
            try: win32clipboard.CloseClipboard()
            except: pass

    txt = clipboard_get_text()
    if txt and txt != son_hash_text:
        son_hash_text = txt
        show_text_popup(txt)
    root.after(500, poll_clipboard)

if __name__ == "__main__":
    if not run_as_admin():
        sys.exit(0)

    root = tk.Tk()
    root.withdraw()

    root.after(500, poll_clipboard)
    root.mainloop()

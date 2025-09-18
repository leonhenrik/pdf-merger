#!/usr/bin/env python3
import os
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image, ImageTk

# Note: Requires poppler installed and in PATH; pip install pdf2image pillow

class PDFEditorApp:
    def __init__(self):
        self.root = tb.Window(
            title="📄 PDF Editor",
            themename="flatly",
            size=(900, 600)
        )
        self.page_entries = []  # list of (file_path, page_index)
        self.selected = set()   # indices of selected pages
        self.thumb_images = []  # keep references to PhotoImage
        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        top = tb.Frame(self.root, padding=10)
        top.pack(fill=X)
        tb.Button(top, text="Open PDFs", bootstyle="primary", command=self._open_files).pack(side=LEFT)
        tb.Button(top, text="Clear All", bootstyle="warning", command=self._clear_all).pack(side=LEFT, padx=5)

        mid = tb.Frame(self.root)
        mid.pack(fill=BOTH, expand=True)

        # Scrollable thumbnail area
        lb_frame = tb.LabelFrame(mid, text="Pages Preview (click to select)", padding=10)
        lb_frame.pack(fill=BOTH, expand=True, side=LEFT)

        canvas = tk.Canvas(lb_frame)
        scrollbar_v = tb.Scrollbar(lb_frame, orient='vertical', command=canvas.yview)
        scrollbar_h = tb.Scrollbar(lb_frame, orient='horizontal', command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')
        canvas.pack(side='left', fill='both', expand=True)

        self.thumb_frame = tk.Frame(canvas)
        canvas.create_window((0,0), window=self.thumb_frame, anchor='nw')
        self.thumb_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Actions panel
        btn_frame = tb.Frame(mid, padding=10)
        btn_frame.pack(side=LEFT, fill=Y)
        tb.Button(btn_frame, text="Delete", width=12, bootstyle="danger", command=self._delete_pages).pack(pady=5)
        tb.Separator(btn_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
        tb.Button(btn_frame, text="↑ Move Up", width=12, bootstyle="secondary", command=lambda: self._move(-1)).pack(pady=5)
        tb.Button(btn_frame, text="↓ Move Down", width=12, bootstyle="secondary", command=lambda: self._move(1)).pack(pady=5)

        bot = tb.Frame(self.root, padding=10)
        bot.pack(fill=X)
        tb.Button(bot, text="Save PDF", bootstyle="success", command=self._save_pdf).pack(side=RIGHT)

    def _open_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files","*.pdf")])
        if not paths:
            return
        self.page_entries.clear()
        self.selected.clear()
        for p in paths:
            reader = PdfReader(p)
            for i in range(len(reader.pages)):
                self.page_entries.append((p, i))
        self._refresh_thumbnails()

    def _refresh_thumbnails(self):
        # Clear previous
        for w in self.thumb_frame.winfo_children(): w.destroy()
        self.thumb_images.clear()
        # Generate and display thumbs
        for idx, (file, page_idx) in enumerate(self.page_entries):
            try:
                # Render page to image
                pil_img = convert_from_path(file, dpi=50, first_page=page_idx+1, last_page=page_idx+1)[0]
                pil_img.thumbnail((100, 140))
                img = ImageTk.PhotoImage(pil_img)
                self.thumb_images.append(img)
                # Button with image
                btn = tk.Button(self.thumb_frame, image=img, relief='flat', bd=1,
                                command=lambda i=idx: self._toggle_select(i))
                btn.grid(row=idx//5, column=idx%5, padx=5, pady=5)
                # border highlight if selected
                if idx in self.selected:
                    btn.config(relief='solid', bd=2)
            except Exception as e:
                # fallback: text label
                lbl = tk.Label(self.thumb_frame, text=f"Page {page_idx+1}\nError", bg='#f8d7da')
                lbl.grid(row=idx//5, column=idx%5, padx=5, pady=5)
        self.thumb_frame.update_idletasks()

    def _toggle_select(self, idx):
        if idx in self.selected:
            self.selected.remove(idx)
        else:
            self.selected.add(idx)
        self._refresh_thumbnails()

    def _delete_pages(self):
        if not self.selected:
            return
        for i in sorted(self.selected, reverse=True):
            del self.page_entries[i]
        self.selected.clear()
        self._refresh_thumbnails()

    def _move(self, delta):
        sel = sorted(self.selected)
        if not sel:
            return
        for i in (sel if delta<0 else reversed(sel)):
            j = i + delta
            if 0 <= j < len(self.page_entries):
                self.page_entries[i], self.page_entries[j] = self.page_entries[j], self.page_entries[i]
        # update selection indices
        self.selected = {i+delta for i in sel}
        self._refresh_thumbnails()

    def _clear_all(self):
        self.page_entries.clear()
        self.selected.clear()
        self._refresh_thumbnails()

    def _save_pdf(self):
        if not self.page_entries:
            messagebox.showerror("No Pages","Nothing to save.")
            return
        out = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[("PDF Files","*.pdf")])
        if not out:
            return
        writer = PdfWriter()
        for file, pidx in self.page_entries:
            reader = PdfReader(file)
            writer.add_page(reader.pages[pidx])
        with open(out,'wb') as f:
            writer.write(f)
        messagebox.showinfo("Saved", f"PDF saved to:\n{out}")

if __name__ == '__main__':
    PDFEditorApp()

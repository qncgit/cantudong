# gui/set_password_dialog.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import tkinter as tk # Thêm import tk để dùng END

class SetPasswordDialog(ttk.Toplevel):
    """Hộp thoại để Admin nhập mật khẩu mới cho người dùng."""
    def __init__(self, parent, username_to_set):
        # ---- SỬA DÒNG NÀY ----
        super().__init__(master=parent, title="Đặt mật khẩu mới") # Sử dụng master=parent
        # ---- KẾT THÚC SỬA ĐỔI ----
        self.parent = parent
        self.username_to_set = username_to_set
        self.new_password = None # Lưu mật khẩu mới nếu hợp lệ

        # --- Cấu hình cửa sổ dialog ---
        self.geometry("400x250") # Kích thước phù hợp cho dialog
        self.transient(parent) # Đặt dialog lên trên parent
        self.grab_set() # Chặn tương tác với cửa sổ parent
        self.protocol("WM_DELETE_WINDOW", self.on_cancel) # Xử lý khi nhấn nút X

        # --- Nội dung dialog ---
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        info_label = ttk.Label(main_frame, text=f"Đặt mật khẩu mới cho: {self.username_to_set}", font="-weight bold")
        info_label.pack(pady=(0, 15))

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(pady=5)

        new_pass_label = ttk.Label(form_frame, text="Mật khẩu mới:")
        new_pass_label.grid(row=0, column=0, padx=5, pady=8, sticky=tk.W) # Sử dụng tk.W
        self.new_pass_entry = ttk.Entry(form_frame, show="*", width=30)
        self.new_pass_entry.grid(row=0, column=1, padx=5, pady=8)
        self.new_pass_entry.focus_set() # Focus vào ô nhập đầu tiên

        confirm_pass_label = ttk.Label(form_frame, text="Xác nhận MK:")
        confirm_pass_label.grid(row=1, column=0, padx=5, pady=8, sticky=tk.W) # Sử dụng tk.W
        self.confirm_pass_entry = ttk.Entry(form_frame, show="*", width=30)
        self.confirm_pass_entry.grid(row=1, column=1, padx=5, pady=8)
        # Nhấn Enter ở ô xác nhận cũng tương đương nhấn OK
        self.confirm_pass_entry.bind("<Return>", self.on_ok)

        # --- Nút bấm ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))

        ok_button = ttk.Button(button_frame, text="Đặt mật khẩu", command=self.on_ok, bootstyle=SUCCESS)
        ok_button.pack(side=tk.LEFT, padx=10) # Sử dụng tk.LEFT

        cancel_button = ttk.Button(button_frame, text="Hủy bỏ", command=self.on_cancel, bootstyle=SECONDARY)
        cancel_button.pack(side=tk.LEFT, padx=10) # Sử dụng tk.LEFT

        # Căn giữa dialog trên cửa sổ cha (AdminWindow)
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        # Đảm bảo x, y không âm (trường hợp dialog lớn hơn màn hình)
        x = max(0, x)
        y = max(0, y)
        self.geometry(f"+{x}+{y}")

        # Chờ dialog đóng
        self.wait_window(self)

    def on_ok(self, event=None):
        """Xử lý khi nhấn nút OK hoặc Enter."""
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()

        if not new_pass or not confirm_pass:
            Messagebox.show_warning("Vui lòng nhập đầy đủ mật khẩu mới và xác nhận.", "Thiếu thông tin", parent=self)
            return

        if len(new_pass) < 6:
            Messagebox.show_warning("Mật khẩu mới phải có ít nhất 6 ký tự.", "Mật khẩu quá ngắn", parent=self)
            return

        if new_pass != confirm_pass:
            Messagebox.show_error("Mật khẩu mới và xác nhận không khớp.", "Lỗi nhập liệu", parent=self)
            self.confirm_pass_entry.delete(0, tk.END) # Sử dụng tk.END
            self.confirm_pass_entry.focus()
            return

        # Nếu hợp lệ, lưu lại mật khẩu và đóng dialog
        self.new_password = new_pass
        self.destroy()

    def on_cancel(self):
        """Xử lý khi nhấn nút Cancel hoặc nút X."""
        self.new_password = None # Đảm bảo không trả về gì
        self.destroy()

# --- Hàm tiện ích để gọi dialog (giữ nguyên) ---
def ask_new_password(parent, username):
    """Hiển thị dialog và trả về mật khẩu mới hoặc None."""
    dialog = SetPasswordDialog(parent, username)
    return dialog.new_password # Trả về giá trị đã lưu
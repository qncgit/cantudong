# gui/login.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from database.db_manager import verify_user
from utils.session import set_current_user
import tkinter as tk

class LoginWindow(ttk.Frame):
    def __init__(self, master, login_success_callback):
        """
        Khởi tạo cửa sổ đăng nhập và đặt kích thước cho cửa sổ chứa nó.
        Args:
            master: Cửa sổ Toplevel cha chứa Frame này.
            login_success_callback: Hàm sẽ được gọi khi đăng nhập thành công.
        """
        super().__init__(master, padding=0)
        self.pack(fill=BOTH, expand=YES) # Frame này sẽ fill Toplevel
        self.master = master # Lưu lại tham chiếu đến Toplevel cha
        self.login_success_callback = login_success_callback

        # ---- ĐẶT TIÊU ĐỀ VÀ KÍCH THƯỚC CHO MASTER (TOPLEVEL) TỪ ĐÂY ----
        self.master.title("Đăng nhập Hệ thống Cân")
        self.master.geometry("800x480")
        # ---- KẾT THÚC ĐẶT TIÊU ĐỀ VÀ KÍCH THƯỚC ----
        # Lưu ý: Việc Frame con đặt geometry cho Toplevel cha không phải là cách thực hành tốt nhất
        # về mặt đóng gói, nhưng nó đáp ứng yêu cầu đặt code tại đây.

        # ---- Frame chính để căn giữa nội dung ----
        center_frame = ttk.Frame(self, padding=(20, 20))
        center_frame.pack(expand=True) # Căn giữa frame này

        # ----- Các thành phần giao diện (đặt trong center_frame) -----
        header = ttk.Label(center_frame, text="ĐĂNG NHẬP HỆ THỐNG", font="-size 20 -weight bold")
        header.pack(pady=(0, 30))

        form_frame = ttk.Frame(center_frame)
        form_frame.pack(pady=10, padx=10)

        username_label = ttk.Label(form_frame, text="Tên đăng nhập:", font="-size 12")
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.username_entry = ttk.Entry(form_frame, width=40, font="-size 12")
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        self.username_entry.focus_set()

        password_label = ttk.Label(form_frame, text="Mật khẩu:", font="-size 12")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.password_entry = ttk.Entry(form_frame, show="*", width=40, font="-size 12")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        self.password_entry.bind("<Return>", self.handle_login)

        self.error_label = ttk.Label(center_frame, text="", bootstyle=DANGER, font="-size 10")
        self.error_label.pack(pady=(5, 15))

        login_button = ttk.Button(center_frame, text="Đăng nhập", command=self.handle_login, bootstyle=SUCCESS, width=20, padding=(10, 8))
        login_button.pack(pady=(10, 0))

    def handle_login(self, event=None):
        """Xử lý sự kiện nhấn nút Đăng nhập."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            self.show_error("Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        user_info = verify_user(username, password)

        if user_info:
            db_username, role = user_info
            set_current_user(db_username, role)
            self.show_error("")
            if self.login_success_callback:
                self.login_success_callback()
            self.destroy() # Hủy Frame này
        else:
            self.show_error("Tên đăng nhập hoặc mật khẩu không đúng.")
            self.password_entry.delete(0, END)
            self.password_entry.focus()

    def show_error(self, message):
        """Hiển thị thông báo lỗi."""
        if hasattr(self, 'error_label') and self.error_label.winfo_exists():
            self.error_label.config(text=message)
# gui/admin_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.session import get_current_username, clear_current_user
# Import các thành phần cần thiết cho đổi mật khẩu
from database.db_manager import get_user_password_hash, update_user_password
from models.user_model import verify_password
import tkinter as tk

class AdminWindow(ttk.Toplevel):
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Admin")
        self.geometry("800x480") # Kích thước đã đặt
        self.logout_callback = logout_callback
        self.username = get_current_username()

        # Ngăn chặn đóng cửa sổ bằng nút 'X' mặc định nếu cần xử lý đặc biệt
        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header -----
        # Giữ nguyên header, fill=X đảm bảo nó chiếm đủ chiều rộng
        header_frame = ttk.Frame(self, padding=(10, 5)) # Giảm padding dưới một chút
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))

        welcome_label = ttk.Label(header_frame, text=f"Tài khoản đăng nhập: {self.username}", font="-size 12 -weight bold")
        welcome_label.pack(side=LEFT, padx=10)

        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(DANGER))
        logout_button.pack(side=RIGHT, padx=10)

        # ----- Tạo Notebook (Tabs) -----
        # fill=BOTH, expand=YES là tốt, giúp notebook lấp đầy không gian
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=5, padx=10, fill=BOTH, expand=YES) # Giảm pady trên/dưới notebook

        # --- Tab 1: Chức năng chính ---
        admin_main_tab = ttk.Frame(self.notebook, padding=15) # Giảm padding trong tab một chút
        self.notebook.add(admin_main_tab, text=' Chức năng chính ')

        # Căn giữa các widget trong tab này
        label = ttk.Label(admin_main_tab, text="Khu vực quản trị và cấu hình hệ thống.", font="-size 14")
        label.pack(pady=(15, 10)) # Điều chỉnh pady

        manage_users_button = ttk.Button(admin_main_tab, text="Quản lý Người dùng", bootstyle=PRIMARY, width=25) # Tăng nhẹ width
        manage_users_button.pack(pady=8) # Giảm pady

        system_config_button = ttk.Button(admin_main_tab, text="Cấu hình Hệ thống", bootstyle=PRIMARY, width=25) # Tăng nhẹ width
        system_config_button.pack(pady=8) # Giảm pady

        # --- Tab 2: Tài khoản ---
        account_tab = ttk.Frame(self.notebook, padding=15) # Giảm padding trong tab một chút
        self.notebook.add(account_tab, text=' Quản lý Tài khoản ')
        self.setup_account_tab(account_tab)


    def setup_account_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Tài khoản (điều chỉnh padding)."""
        # Frame con để nhóm các widget đổi mật khẩu và căn giữa chúng theo chiều dọc (tùy chọn)
        center_frame = ttk.Frame(tab_frame)
        center_frame.pack(expand=True) # Cho phép frame này căn giữa

        account_label = ttk.Label(center_frame, text="Đổi mật khẩu", font="-size 14 -weight bold")
        # Giảm pady, dùng grid trong center_frame
        account_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Mật khẩu hiện tại
        current_pass_label = ttk.Label(center_frame, text="Mật khẩu hiện tại:")
        current_pass_label.grid(row=1, column=0, padx=5, pady=8, sticky=tk.W) # Giảm pady
        self.current_pass_entry = ttk.Entry(center_frame, show="*", width=35) # Tăng width một chút
        self.current_pass_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.W)

        # Mật khẩu mới
        new_pass_label = ttk.Label(center_frame, text="Mật khẩu mới:")
        new_pass_label.grid(row=2, column=0, padx=5, pady=8, sticky=tk.W) # Giảm pady
        self.new_pass_entry = ttk.Entry(center_frame, show="*", width=35)
        self.new_pass_entry.grid(row=2, column=1, padx=5, pady=8, sticky=tk.W)

        # Xác nhận mật khẩu mới
        confirm_pass_label = ttk.Label(center_frame, text="Xác nhận mật khẩu mới:")
        confirm_pass_label.grid(row=3, column=0, padx=5, pady=8, sticky=tk.W) # Giảm pady
        self.confirm_pass_entry = ttk.Entry(center_frame, show="*", width=35)
        self.confirm_pass_entry.grid(row=3, column=1, padx=5, pady=8, sticky=tk.W)

        # Nút đổi mật khẩu
        change_pass_button = ttk.Button(center_frame, text="Đổi mật khẩu",
                                        command=self.handle_change_password, bootstyle=SUCCESS, width=20) # Tăng width
        change_pass_button.grid(row=4, column=0, columnspan=2, pady=15) # Giảm pady

        # Nhãn thông báo trạng thái
        # Tăng wraplength để phù hợp hơn với chiều rộng 800
        self.password_status_label = ttk.Label(center_frame, text="", wraplength=450, justify=tk.CENTER)
        self.password_status_label.grid(row=5, column=0, columnspan=2, pady=(5, 0)) # Giảm pady

        # Cấu hình grid layout cho center_frame
        center_frame.columnconfigure(0, weight=0) # Cột label không co giãn
        center_frame.columnconfigure(1, weight=1) # Cột entry co giãn nhẹ


    def handle_change_password(self):
        """Xử lý logic khi nhấn nút Đổi mật khẩu."""
        current_pass = self.current_pass_entry.get()
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()

        self.password_status_label.config(text="")

        if not current_pass or not new_pass or not confirm_pass:
            self.show_password_status("Vui lòng nhập đầy đủ thông tin.", DANGER)
            return

        if len(new_pass) < 6:
             self.show_password_status("Mật khẩu mới phải có ít nhất 6 ký tự.", DANGER)
             return

        if new_pass != confirm_pass:
            self.show_password_status("Mật khẩu mới và xác nhận không khớp.", DANGER)
            self.confirm_pass_entry.delete(0, END)
            self.confirm_pass_entry.focus()
            return

        current_hash = get_user_password_hash(self.username)
        if not current_hash or not verify_password(current_hash, current_pass):
            self.show_password_status("Mật khẩu hiện tại không đúng.", DANGER)
            self.current_pass_entry.delete(0, END)
            self.current_pass_entry.focus()
            return

        if update_user_password(self.username, new_pass):
            self.show_password_status("Đổi mật khẩu thành công!", SUCCESS)
            self.current_pass_entry.delete(0, END)
            self.new_pass_entry.delete(0, END)
            self.confirm_pass_entry.delete(0, END)
        else:
            self.show_password_status("Lỗi hệ thống: Không thể cập nhật mật khẩu.", DANGER)

    def show_password_status(self, message, style=DEFAULT):
        """Hiển thị thông báo trạng thái đổi mật khẩu."""
        # Đảm bảo widget còn tồn tại trước khi config
        if self.winfo_exists():
            self.password_status_label.config(text=message, bootstyle=style)
            # Tự động xóa thông báo sau 5 giây, cũng kiểm tra widget tồn tại
            self.after(5000, lambda: self.password_status_label.config(text="") if self.winfo_exists() else None)


    def handle_logout(self):
        """Xử lý sự kiện nhấn nút Đăng xuất."""
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        """Xử lý khi người dùng đóng cửa sổ bằng nút X."""
        print("Người dùng cố gắng đóng cửa sổ Admin bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout()
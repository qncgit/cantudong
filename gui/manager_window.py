# gui/manager_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.session import get_current_username, clear_current_user
# Import các thành phần cần thiết cho đổi mật khẩu
from database.db_manager import get_user_password_hash, update_user_password
from models.user_model import verify_password
import tkinter as tk

class ManagerWindow(ttk.Toplevel):
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Quản lý (Manager)")
        self.geometry("800x480")
        self.logout_callback = logout_callback
        self.username = get_current_username()

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header -----
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))

        welcome_label = ttk.Label(header_frame, text=f"Chào mừng Manager: {self.username}", font="-size 12 -weight bold")
        welcome_label.pack(side=LEFT, padx=10)

        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)

        # ----- Tạo Notebook (Tabs) -----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill=BOTH, expand=YES)

        # --- Tab 1: Chức năng chính (Quản lý lệnh cân) ---
        manager_main_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(manager_main_tab, text=' Quản lý Lệnh cân ')

        label = ttk.Label(manager_main_tab, text="Khu vực tạo và quản lý lệnh cân.", font="-size 14")
        label.pack(pady=20)

        create_order_button = ttk.Button(manager_main_tab, text="Tạo Lệnh Cân Mới", bootstyle=SUCCESS)
        create_order_button.pack(pady=10)
        # TODO: Thêm command

        view_orders_button = ttk.Button(manager_main_tab, text="Xem Danh Sách Lệnh Cân", bootstyle=PRIMARY)
        view_orders_button.pack(pady=10)
        # TODO: Thêm command

        # --- Tab 2: Tài khoản ---
        account_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(account_tab, text=' Quản lý Tài khoản ')
        self.setup_account_tab(account_tab) # Gọi hàm thiết lập tab tài khoản

    # --- Các hàm setup_account_tab, handle_change_password, show_password_status ---
    # --- Copy y hệt từ AdminWindow vào đây ---
    def setup_account_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Tài khoản."""
        account_label = ttk.Label(tab_frame, text="Đổi mật khẩu", font="-size 14 -weight bold")
        account_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Mật khẩu hiện tại
        current_pass_label = ttk.Label(tab_frame, text="Mật khẩu hiện tại:")
        current_pass_label.grid(row=1, column=0, padx=5, pady=10, sticky=W)
        self.current_pass_entry = ttk.Entry(tab_frame, show="*", width=30)
        self.current_pass_entry.grid(row=1, column=1, padx=5, pady=10, sticky=W)

        # Mật khẩu mới
        new_pass_label = ttk.Label(tab_frame, text="Mật khẩu mới:")
        new_pass_label.grid(row=2, column=0, padx=5, pady=10, sticky=W)
        self.new_pass_entry = ttk.Entry(tab_frame, show="*", width=30)
        self.new_pass_entry.grid(row=2, column=1, padx=5, pady=10, sticky=W)

        # Xác nhận mật khẩu mới
        confirm_pass_label = ttk.Label(tab_frame, text="Xác nhận mật khẩu mới:")
        confirm_pass_label.grid(row=3, column=0, padx=5, pady=10, sticky=W)
        self.confirm_pass_entry = ttk.Entry(tab_frame, show="*", width=30)
        self.confirm_pass_entry.grid(row=3, column=1, padx=5, pady=10, sticky=W)

        # Nút đổi mật khẩu
        change_pass_button = ttk.Button(tab_frame, text="Đổi mật khẩu",
                                        command=self.handle_change_password, bootstyle=SUCCESS)
        change_pass_button.grid(row=4, column=0, columnspan=2, pady=20)

        # Nhãn thông báo trạng thái
        self.password_status_label = ttk.Label(tab_frame, text="", wraplength=350) # wraplength để tự xuống dòng
        self.password_status_label.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        # Cấu hình grid layout
        tab_frame.columnconfigure(1, weight=1) # Cho phép cột entry mở rộng


    def handle_change_password(self):
        """Xử lý logic khi nhấn nút Đổi mật khẩu."""
        current_pass = self.current_pass_entry.get()
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()

        self.password_status_label.config(text="") # Xóa thông báo cũ

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
        self.password_status_label.config(text=message, bootstyle=style)
        self.after(5000, lambda: self.password_status_label.config(text=""))
    # --- Kết thúc phần copy ---

    def handle_logout(self):
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        print("Người dùng cố gắng đóng cửa sổ Manager bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout()
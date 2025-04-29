# gui/manager_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.session import get_current_username, clear_current_user
# --- XÓA CÁC IMPORT LIÊN QUAN ĐỔI MK ---
# from database.db_manager import get_user_password_hash, update_user_password
# from models.user_model import verify_password
# --- KẾT THÚC XÓA IMPORT ---
import tkinter as tk # Giữ lại nếu cần

class ManagerWindow(ttk.Toplevel):
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Quản lý (Manager)")
        self.geometry("800x480")
        self.logout_callback = logout_callback
        self.username = get_current_username()

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header -----
        header_frame = ttk.Frame(self, padding=10, bootstyle=INFO)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))

        welcome_label = ttk.Label(header_frame, text=f"Chào mừng Manager: {self.username}", font="-size 12 -weight bold")
        welcome_label.pack(side=LEFT, padx=10)

        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)

        # ----- Chỉ còn nội dung chính -----
        # --- KHÔNG DÙNG NOTEBOOK NỮA ---
        # self.notebook = ttk.Notebook(self)
        # self.notebook.pack(pady=10, padx=10, fill=BOTH, expand=YES)
        # --- KẾT THÚC KHÔNG DÙNG NOTEBOOK ---

        # --- Frame chứa nội dung chính ---
        manager_main_frame = ttk.Frame(self, padding=20)
        # self.notebook.add(manager_main_frame, text=' Quản lý Lệnh cân ') # Dòng này không cần nữa
        manager_main_frame.pack(pady=10, padx=10, fill=BOTH, expand=YES) # Pack frame chính vào window

        label = ttk.Label(manager_main_frame, text="Khu vực tạo và quản lý lệnh cân.", font="-size 14")
        label.pack(pady=20)

        create_order_button = ttk.Button(manager_main_frame, text="Tạo Lệnh Cân Mới", bootstyle=SUCCESS, width=25)
        create_order_button.pack(pady=10)
        # TODO: Thêm command

        view_orders_button = ttk.Button(manager_main_frame, text="Xem Danh Sách Lệnh Cân", bootstyle=PRIMARY, width=25)
        view_orders_button.pack(pady=10)
        # TODO: Thêm command

        # --- XÓA TOÀN BỘ PHẦN TẠO TAB TÀI KHOẢN VÀ CÁC HÀM LIÊN QUAN ---
        # account_tab = ttk.Frame(self.notebook, padding=20)
        # self.notebook.add(account_tab, text=' Quản lý Tài khoản ')
        # self.setup_account_tab(account_tab)
        # def setup_account_tab(...): ...
        # def handle_change_password(...): ...
        # def show_password_status(...): ...
        # --- KẾT THÚC XÓA ---

    # ----- CÁC HÀM CÒN LẠI GIỮ NGUYÊN -----
    def handle_logout(self):
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        print("Người dùng cố gắng đóng cửa sổ Manager bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout()
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----
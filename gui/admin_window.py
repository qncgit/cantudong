# gui/admin_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
# Bỏ các import không dùng trong file này nữa
# from ttkbootstrap.widgets import DateEntry
# from tkinter import filedialog
# import os
# import datetime
from utils.session import get_current_username, clear_current_user
from database.db_manager import (
    get_user_password_hash, update_user_password,
    get_all_users, add_user, delete_user, set_user_password_by_admin,
    # Giữ các hàm quản lý nhân sự
    add_nhan_su, get_all_nhan_su, get_nhan_su_by_id, update_nhan_su, delete_nhan_su
)
from models.user_model import verify_password, ADMIN, MANAGER, USER, ROLES
from gui.set_password_dialog import ask_new_password
# --- THÊM IMPORT DIALOG LÁI XE ---
from gui.driver_info_dialog import DriverInfoDialog
# --- KẾT THÚC THÊM IMPORT ---
import tkinter as tk


class AdminWindow(ttk.Toplevel):
    # ----- __init__ (Giữ nguyên) -----
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Admin")
        self.geometry("800x480") # Kích thước cửa sổ chính
        self.logout_callback = logout_callback
        self.username = get_current_username()
        self.selected_driver_id = None # ID lái xe đang chọn trong Treeview

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header (Giữ nguyên) -----
        header_frame = ttk.Frame(self, padding=(10, 5), bootstyle=INFO)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))
        welcome_label = ttk.Label(header_frame, text=f"Chào mừng Admin: {self.username}", font="-size 12 -weight bold", bootstyle=INFO)
        welcome_label.pack(side=LEFT, padx=10)
        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)
        # ----- Kết thúc Header -----

        # ----- Tạo Notebook (Tabs) (Giữ nguyên) -----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=5, padx=10, fill=BOTH, expand=YES)

        # --- Tab 1: Quản lý Người dùng (Giữ nguyên) ---
        user_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(user_management_tab, text=' Quản lý Người dùng ')
        self.setup_user_management_tab(user_management_tab)

        # --- Tab 2: Quản lý Lái xe (Gọi hàm đã sửa) ---
        driver_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(driver_management_tab, text=' Quản lý Lái xe ')
        self.setup_driver_management_tab(driver_management_tab) # Gọi hàm đã sửa

        # --- Tab 3: Tài khoản Admin (Giữ nguyên) ---
        account_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(account_tab, text=' Tài khoản Admin ')
        self.setup_account_tab(account_tab)
    # ----- Kết thúc __init__ -----


    # ----- setup_user_management_tab và các hàm liên quan (Giữ nguyên) -----
    # ... (Toàn bộ code cho Tab Quản lý Người dùng giữ nguyên ở đây) ...
    def setup_user_management_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Quản lý Người dùng."""
        tab_frame.columnconfigure(0, weight=1) # Cho phép Treeview mở rộng
        tab_frame.rowconfigure(1, weight=1)    # Cho phép Treeview mở rộng theo chiều dọc

        # ----- Phần Thêm người dùng -----
        add_user_frame = ttk.Labelframe(tab_frame, text="Thêm người dùng mới", padding=10)
        add_user_frame.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="ew")
        # Cấu hình cột cho frame thêm người dùng để các entry/combobox co giãn hợp lý
        add_user_frame.columnconfigure(1, weight=2) # Cột username
        add_user_frame.columnconfigure(3, weight=2) # Cột password
        add_user_frame.columnconfigure(5, weight=1) # Cột role
        add_user_frame.columnconfigure(6, weight=0) # Cột nút thêm

        ttk.Label(add_user_frame, text="Tên đăng nhập:").grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")
        self.new_username_entry = ttk.Entry(add_user_frame, width=20)
        self.new_username_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(add_user_frame, text="Mật khẩu:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.new_password_entry = ttk.Entry(add_user_frame, width=20)
        self.new_password_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        self.new_password_entry.insert(0, "123456") # Gợi ý mật khẩu mặc định

        ttk.Label(add_user_frame, text="Vai trò:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        # Chỉ cho phép thêm Manager hoặc User từ giao diện Admin
        self.new_role_combobox = ttk.Combobox(add_user_frame, values=[MANAGER, USER], state="readonly", width=10)
        self.new_role_combobox.set(USER) # Mặc định là User
        self.new_role_combobox.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        add_button = ttk.Button(add_user_frame, text="Thêm", command=self.handle_add_user, bootstyle=SUCCESS, width=8)
        add_button.grid(row=0, column=6, padx=(10, 0), pady=5)

        # Label trạng thái cho việc quản lý user
        self.user_manage_status_label = ttk.Label(add_user_frame, text="", bootstyle=INFO, anchor="w")
        self.user_manage_status_label.grid(row=1, column=0, columnspan=7, pady=(5,0), sticky="ew")


        # ----- Phần Danh sách người dùng -----
        user_list_frame = ttk.Frame(tab_frame)
        user_list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        user_list_frame.rowconfigure(0, weight=1) # Cho Treeview fill theo chiều dọc
        user_list_frame.columnconfigure(0, weight=1) # Cho Treeview fill theo chiều ngang

        # Tạo Treeview
        columns = ("id", "username", "role")
        self.user_tree = ttk.Treeview(user_list_frame, columns=columns, show="headings", bootstyle=PRIMARY, height=10) # Đặt chiều cao cố định

        # Định nghĩa headings
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="Tên đăng nhập")
        self.user_tree.heading("role", text="Vai trò")

        # Định nghĩa cột (điều chỉnh width)
        self.user_tree.column("id", width=60, anchor=tk.CENTER, stretch=False) # Không cho co giãn cột ID
        self.user_tree.column("username", width=300, stretch=True)
        self.user_tree.column("role", width=150, stretch=True)

        # Thêm Scrollbar
        scrollbar = ttk.Scrollbar(user_list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)

        # Đặt Treeview và Scrollbar vào frame
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # ----- Các nút thao tác với danh sách -----
        action_frame = ttk.Frame(tab_frame)
        action_frame.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="ew")

        # Đặt các nút cách đều nhau (dùng pack với fill=X và expand=True cho frame chứa nút)
        button_container = ttk.Frame(action_frame)
        button_container.pack(expand=True, fill=X) # Cho container căn giữa và fill

        refresh_button = ttk.Button(button_container, text="Làm mới DS", command=self.refresh_user_list, bootstyle=INFO, width=18)
        refresh_button.pack(side=tk.LEFT, padx=(0, 5), pady=5, expand=True) # expand=True để các nút cách đều

        set_pass_button = ttk.Button(button_container, text="Đặt mật khẩu mới", command=self.handle_set_password, bootstyle=WARNING, width=18) # Đổi text và command
        set_pass_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True)

        delete_button = ttk.Button(button_container, text="Xóa người dùng", command=self.handle_delete_user, bootstyle=DANGER, width=18)
        delete_button.pack(side=tk.LEFT, padx=(5, 0), pady=5, expand=True)

        # Load danh sách người dùng ban đầu
        self.refresh_user_list()
    # ----- Kết thúc setup_user_management_tab -----


    # ----- SỬA HÀM setup_driver_management_tab -----
    def setup_driver_management_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Quản lý Lái xe (Popup mode)."""
        tab_frame.columnconfigure(0, weight=1) # Cột chính
        tab_frame.rowconfigure(0, weight=1)    # Hàng cho danh sách
        tab_frame.rowconfigure(1, weight=0)    # Hàng cho nút
        tab_frame.rowconfigure(2, weight=0)    # Hàng cho status label

        # ----- Frame chứa Danh sách Lái xe -----
        driver_list_frame = ttk.Labelframe(tab_frame, text="Danh sách Lái xe", padding=10)
        driver_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew") # Hàng 0
        driver_list_frame.rowconfigure(0, weight=1)
        driver_list_frame.columnconfigure(0, weight=1)

        # Treeview (Giữ nguyên cấu trúc, có thể tăng height)
        driver_cols = ("id", "maNhanVien", "maThe", "tenNhanVien", "trangThai") # Thêm các cột nếu muốn
        self.driver_tree = ttk.Treeview(driver_list_frame, columns=driver_cols, show="headings", bootstyle=INFO, height=15)
        self.driver_tree.heading("id", text="ID")
        self.driver_tree.heading("maNhanVien", text="Mã NV")
        self.driver_tree.heading("maThe", text="Mã Thẻ")
        self.driver_tree.heading("tenNhanVien", text="Tên Lái xe")
        self.driver_tree.heading("trangThai", text="Trạng thái")
        self.driver_tree.column("id", width=40, anchor=tk.CENTER, stretch=False)
        self.driver_tree.column("maNhanVien", width=100, stretch=False)
        self.driver_tree.column("maThe", width=120, stretch=False)
        self.driver_tree.column("tenNhanVien", width=300, stretch=True) # Tăng width
        self.driver_tree.column("trangThai", width=100, stretch=False)
        # Scrollbar (Giữ nguyên)
        driver_scrollbar = ttk.Scrollbar(driver_list_frame, orient=tk.VERTICAL, command=self.driver_tree.yview)
        self.driver_tree.configure(yscrollcommand=driver_scrollbar.set)
        self.driver_tree.grid(row=0, column=0, sticky="nsew")
        driver_scrollbar.grid(row=0, column=1, sticky="ns")
        # Gắn sự kiện chọn item (Giữ nguyên)
        self.driver_tree.bind("<<TreeviewSelect>>", self.on_driver_select)

        # ----- Frame chứa các nút thao tác -----
        driver_action_frame = ttk.Frame(tab_frame, padding=(0, 10))
        driver_action_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew") # Hàng 1

        # Đặt các nút vào frame này
        button_container_driver = ttk.Frame(driver_action_frame)
        button_container_driver.pack(expand=True) # Căn giữa

        add_driver_button = ttk.Button(button_container_driver, text="Thêm lái xe mới", command=self.handle_add_new_driver, bootstyle=PRIMARY, width=18)
        add_driver_button.pack(side=tk.LEFT, padx=10, pady=5)

        edit_driver_button = ttk.Button(button_container_driver, text="Sửa thông tin", command=self.handle_edit_driver, bootstyle=SUCCESS, width=18, state="disabled") # Bắt đầu bị vô hiệu hóa
        edit_driver_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.edit_driver_button = edit_driver_button # Lưu lại để bật/tắt

        delete_driver_button = ttk.Button(button_container_driver, text="Xóa lái xe", command=self.handle_delete_driver_from_tab, bootstyle=DANGER, width=18, state="disabled") # Bắt đầu bị vô hiệu hóa
        delete_driver_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.delete_driver_button = delete_driver_button # Lưu lại để bật/tắt

        refresh_driver_button_tab = ttk.Button(button_container_driver, text="Làm mới DS", command=self.refresh_driver_list, bootstyle=INFO, width=18)
        refresh_driver_button_tab.pack(side=tk.LEFT, padx=10, pady=5)

        # Label trạng thái chung cho tab này
        self.driver_tab_status_label = ttk.Label(tab_frame, text="Chọn một lái xe để sửa hoặc xóa.", bootstyle=INFO, anchor="w")
        self.driver_tab_status_label.grid(row=2, column=0, padx=5, pady=(0,5), sticky="ew") # Hàng 2


        # Load danh sách lái xe ban đầu
        self.refresh_driver_list()
    # ----- KẾT THÚC SỬA HÀM -----

    # ----- CÁC HÀM QUẢN LÝ LÁI XE (Sửa đổi/Thêm mới) -----
    def refresh_driver_list(self):
        """Làm mới danh sách lái xe trong Treeview."""
        try:
            # Bỏ chọn và vô hiệu hóa nút Sửa/Xóa trước khi làm mới
            self.selected_driver_id = None
            # Kiểm tra sự tồn tại của nút trước khi config
            if hasattr(self, 'edit_driver_button') and self.edit_driver_button.winfo_exists():
                self.edit_driver_button.config(state="disabled")
            if hasattr(self, 'delete_driver_button') and self.delete_driver_button.winfo_exists():
                self.delete_driver_button.config(state="disabled")
            selection = self.driver_tree.selection()
            if selection:
                self.driver_tree.selection_remove(selection)


            # Xóa dữ liệu cũ trong Treeview
            for item in self.driver_tree.get_children():
                self.driver_tree.delete(item)

            # Lấy dữ liệu mới
            drivers = get_all_nhan_su()
            # Thêm dữ liệu mới vào Treeview
            for driver in drivers:
                values = (
                    driver.get('id', ''),
                    driver.get('maNhanVien', ''),
                    driver.get('maThe', ''),
                    driver.get('tenNhanVien', ''),
                    driver.get('trangThai', '')
                )
                self.driver_tree.insert("", tk.END, values=values)

            self.show_driver_tab_status("Đã tải danh sách lái xe.", INFO)
        except Exception as e:
             self.show_driver_tab_status(f"Lỗi tải danh sách lái xe: {e}", DANGER)

    def on_driver_select(self, event=None):
        """Xử lý khi chọn một lái xe từ Treeview."""
        selected_items = self.driver_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            try:
                # Lấy ID từ cột đầu tiên (index 0)
                driver_id = int(self.driver_tree.item(selected_item, 'values')[0])
                self.selected_driver_id = driver_id
                # Kích hoạt nút Sửa và Xóa
                if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="normal")
                if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="normal")
                self.show_driver_tab_status(f"Đã chọn lái xe ID: {driver_id}. Nhấn 'Sửa' hoặc 'Xóa'.", INFO)
            except (ValueError, IndexError, TypeError) as e: # Bắt thêm TypeError
                print(f"Lỗi khi lấy driver ID từ treeview: {e}") # In lỗi ra console
                self.selected_driver_id = None
                if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="disabled")
                if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="disabled")
                self.show_driver_tab_status("Lỗi khi lấy thông tin lựa chọn.", WARNING)
        else:
            # Nếu không có gì được chọn (ví dụ: click vào khoảng trống)
            self.selected_driver_id = None
            if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="disabled")
            if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="disabled")
            self.show_driver_tab_status("Chọn một lái xe để sửa hoặc xóa.", INFO)

    def handle_add_new_driver(self):
        """Mở dialog để thêm lái xe mới."""
        db_funcs = {
            'add': add_nhan_su
        }
        dialog = DriverInfoDialog(self, db_functions=db_funcs, driver_id=None)
        if dialog.success:
            self.refresh_driver_list()
            self.show_driver_tab_status("Thêm lái xe mới thành công.", SUCCESS)
        # else: # Có thể thêm thông báo hủy bỏ nếu cần
        #     self.show_driver_tab_status("Đã hủy thêm lái xe mới.", INFO)

    def handle_edit_driver(self):
        """Mở dialog để sửa thông tin lái xe đã chọn."""
        if self.selected_driver_id is None:
            # Messagebox.show_warning("Vui lòng chọn một lái xe từ danh sách để sửa.", parent=self)
            self.show_driver_tab_status("Vui lòng chọn một lái xe từ danh sách để sửa.", WARNING)
            return

        db_funcs = {
            'get_by_id': get_nhan_su_by_id,
            'update': update_nhan_su
        }
        dialog = DriverInfoDialog(self, db_functions=db_funcs, driver_id=self.selected_driver_id)
        if dialog.success:
            self.refresh_driver_list() # Tự động bỏ chọn và disable nút khi refresh
            self.show_driver_tab_status(f"Cập nhật thông tin lái xe ID {self.selected_driver_id} thành công.", SUCCESS)
        # else:
        #      self.show_driver_tab_status("Đã hủy sửa thông tin lái xe.", INFO)


    def handle_delete_driver_from_tab(self):
        """Xóa lái xe được chọn từ Treeview."""
        if self.selected_driver_id is None:
            # Messagebox.show_warning("Vui lòng chọn một lái xe từ danh sách để xóa.", parent=self)
            self.show_driver_tab_status("Vui lòng chọn một lái xe từ danh sách để xóa.", WARNING)
            return

        # Lấy tên để hiển thị xác nhận
        driver_name = ""
        selected_items = self.driver_tree.selection()
        if selected_items:
             try:
                 driver_name = self.driver_tree.item(selected_items[0], 'values')[3] # Index của tenNhanVien
             except IndexError: pass

        confirm = Messagebox.show_question(
            f"Bạn có chắc muốn xóa lái xe '{driver_name}' (ID: {self.selected_driver_id}) không?",
            "Xác nhận xóa lái xe",
            buttons=['No:secondary', 'Yes:danger'],
            parent=self
        )

        if confirm == "Yes":
            success, message = delete_nhan_su(self.selected_driver_id)
            if success:
                self.show_driver_tab_status(message, SUCCESS)
                self.refresh_driver_list() # Tự động làm mới và bỏ chọn/disable nút
            else:
                self.show_driver_tab_status(message, DANGER)

    def show_driver_tab_status(self, message, style=INFO):
        """Hiển thị thông báo trạng thái trên tab quản lý lái xe."""
        if hasattr(self, 'driver_tab_status_label') and self.driver_tab_status_label.winfo_exists():
            self.driver_tab_status_label.config(text=message, bootstyle=style)
            # Đặt lại trạng thái mặc định sau một thời gian
            self.after(6000, lambda: self.driver_tab_status_label.config(text="Chọn một lái xe để sửa hoặc xóa.", bootstyle=INFO) if self.winfo_exists() else None)
        else:
            print(f"Status (Driver Tab): {message}")
    # ----- KẾT THÚC CÁC HÀM QUẢN LÝ LÁI XE -----


    # ----- CÁC HÀM QUẢN LÝ USER (users table) GIỮ NGUYÊN -----
    # ... (refresh_user_list, handle_add_user, get_selected_user, handle_set_password, handle_delete_user, show_user_manage_status) ...
    def refresh_user_list(self):
        """Lấy dữ liệu người dùng từ DB và cập nhật Treeview."""
        try:
            # Bỏ chọn nút liên quan đến user nếu có
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            users = get_all_users()
            for user in users:
                self.user_tree.insert("", tk.END, values=(user['id'], user['username'], user['role']))
            self.show_user_manage_status("Đã tải danh sách người dùng.", INFO)
        except Exception as e:
            self.show_user_manage_status(f"Lỗi tải danh sách: {e}", DANGER)

    def handle_add_user(self):
        """Xử lý thêm người dùng mới."""
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()
        role = self.new_role_combobox.get()

        if not username or not password or not role:
            self.show_user_manage_status("Vui lòng nhập đầy đủ thông tin.", WARNING)
            return

        if len(password) < 6:
             self.show_user_manage_status("Mật khẩu phải có ít nhất 6 ký tự.", WARNING)
             return

        success, message = add_user(username, password, role)
        if success:
            self.show_user_manage_status(message, SUCCESS)
            self.refresh_user_list()
            self.new_username_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.new_password_entry.insert(0, "123456")
            self.new_role_combobox.set(USER)
        else:
            self.show_user_manage_status(message, DANGER)

    def get_selected_user(self):
        """Lấy thông tin người dùng đang được chọn trong Treeview."""
        selected_item = self.user_tree.focus()
        if not selected_item:
            self.show_user_manage_status("Vui lòng chọn một người dùng trong danh sách.", WARNING)
            return None, None
        user_data = self.user_tree.item(selected_item, 'values')
        if user_data and len(user_data) >= 3:
            return user_data[1], user_data[2] # username, role
        return None, None

    def handle_set_password(self):
        """Xử lý đặt mật khẩu mới cho người dùng được chọn."""
        selected_username, selected_role = self.get_selected_user()
        if not selected_username:
            return

        if selected_username == self.username:
             self.show_user_manage_status("Sử dụng tab 'Tài khoản Admin' để đổi mật khẩu của bạn.", WARNING)
             return

        new_password = ask_new_password(self, selected_username)

        if new_password is not None:
            confirm = Messagebox.show_question(
                f"Bạn có chắc muốn đặt mật khẩu mới cho '{selected_username}' không?",
                "Xác nhận đặt mật khẩu",
                buttons=['No:secondary', 'Yes:primary'],
                parent=self
            )
            if confirm == "Yes":
                success, message = set_user_password_by_admin(selected_username, new_password)
                if success:
                    self.show_user_manage_status(message, SUCCESS)
                else:
                    self.show_user_manage_status(message, DANGER)
        else:
            self.show_user_manage_status("Hủy bỏ thao tác đặt mật khẩu mới.", INFO)


    def handle_delete_user(self):
        """Xử lý xóa người dùng được chọn."""
        selected_username, selected_role = self.get_selected_user()
        if not selected_username:
            return

        if selected_username == self.username:
             self.show_user_manage_status("Không thể xóa tài khoản Admin đang đăng nhập.", DANGER)
             return

        confirm = Messagebox.show_question(
            f"Bạn có chắc muốn XÓA vĩnh viễn người dùng '{selected_username}' không?\nHành động này không thể hoàn tác.",
            "Xác nhận xóa người dùng",
            buttons=['Cancel:secondary', 'Delete:danger'],
            parent=self
        )

        if confirm == "Delete":
            success, message = delete_user(selected_username)
            if success:
                self.show_user_manage_status(message, SUCCESS)
                self.refresh_user_list()
            else:
                self.show_user_manage_status(message, DANGER)


    def show_user_manage_status(self, message, style=INFO):
         """Hiển thị thông báo trạng thái quản lý người dùng."""
         if hasattr(self, 'user_manage_status_label') and self.user_manage_status_label.winfo_exists():
             self.user_manage_status_label.config(text=message, bootstyle=style)
             self.after(5000, lambda: self.user_manage_status_label.config(text="") if self.winfo_exists() else None)
         else:
             print(f"Status (User Manage): {message}")
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----


    # ----- CÁC HÀM CỦA TAB TÀI KHOẢN ADMIN GIỮ NGUYÊN -----
    # ... (setup_account_tab, handle_change_password, show_password_status) ...
    def setup_account_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Tài khoản Admin (Đổi MK của chính Admin)."""
        center_frame = ttk.Frame(tab_frame)
        center_frame.pack(expand=True)
        account_label = ttk.Label(center_frame, text="Đổi mật khẩu của bạn", font="-size 14 -weight bold")
        account_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        current_pass_label = ttk.Label(center_frame, text="Mật khẩu hiện tại:")
        current_pass_label.grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.current_pass_entry = ttk.Entry(center_frame, show="*", width=35)
        self.current_pass_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.W)
        new_pass_label = ttk.Label(center_frame, text="Mật khẩu mới:")
        new_pass_label.grid(row=2, column=0, padx=5, pady=8, sticky=tk.W)
        self.new_pass_entry = ttk.Entry(center_frame, show="*", width=35)
        self.new_pass_entry.grid(row=2, column=1, padx=5, pady=8, sticky=tk.W)
        confirm_pass_label = ttk.Label(center_frame, text="Xác nhận mật khẩu mới:")
        confirm_pass_label.grid(row=3, column=0, padx=5, pady=8, sticky=tk.W)
        self.confirm_pass_entry = ttk.Entry(center_frame, show="*", width=35)
        self.confirm_pass_entry.grid(row=3, column=1, padx=5, pady=8, sticky=tk.W)
        change_pass_button = ttk.Button(center_frame, text="Đổi mật khẩu",
                                        command=self.handle_change_password, bootstyle=SUCCESS, width=20)
        change_pass_button.grid(row=4, column=0, columnspan=2, pady=15)
        self.password_status_label = ttk.Label(center_frame, text="", wraplength=450, justify=tk.CENTER)
        self.password_status_label.grid(row=5, column=0, columnspan=2, pady=(5, 0))
        center_frame.columnconfigure(0, weight=0)
        center_frame.columnconfigure(1, weight=1)

    def handle_change_password(self):
        """Xử lý logic khi Admin nhấn nút Đổi mật khẩu (cho chính mình)."""
        current_pass = self.current_pass_entry.get()
        new_pass = self.new_pass_entry.get()
        confirm_pass = self.confirm_pass_entry.get()
        if hasattr(self, 'password_status_label') and self.password_status_label.winfo_exists():
            self.password_status_label.config(text="")
        else:
             print("Cảnh báo: password_status_label không tồn tại.")
             return
        if not current_pass or not new_pass or not confirm_pass:
            self.show_password_status("Vui lòng nhập đầy đủ thông tin.", DANGER)
            return
        if len(new_pass) < 6:
             self.show_password_status("Mật khẩu mới phải có ít nhất 6 ký tự.", DANGER)
             return
        if new_pass != confirm_pass:
            self.show_password_status("Mật khẩu mới và xác nhận không khớp.", DANGER)
            self.confirm_pass_entry.delete(0, tk.END)
            self.confirm_pass_entry.focus()
            return
        current_hash = get_user_password_hash(self.username)
        if not current_hash or not verify_password(current_hash, current_pass):
            self.show_password_status("Mật khẩu hiện tại không đúng.", DANGER)
            self.current_pass_entry.delete(0, tk.END)
            self.current_pass_entry.focus()
            return
        if update_user_password(self.username, new_pass):
            self.show_password_status("Đổi mật khẩu thành công!", SUCCESS)
            self.current_pass_entry.delete(0, tk.END)
            self.new_pass_entry.delete(0, tk.END)
            self.confirm_pass_entry.delete(0, tk.END)
        else:
            self.show_password_status("Lỗi hệ thống: Không thể cập nhật mật khẩu.", DANGER)

    def show_password_status(self, message, style=DEFAULT):
        """Hiển thị thông báo trạng thái đổi mật khẩu của Admin."""
        if hasattr(self, 'password_status_label') and self.password_status_label.winfo_exists():
            self.password_status_label.config(text=message, bootstyle=style)
            self.after(5000, lambda: self.password_status_label.config(text="") if self.winfo_exists() else None)
        else:
            print(f"Status (Admin PW Change): {message}")
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----


    # ----- CÁC HÀM handle_logout, handle_close GIỮ NGUYÊN -----
    def handle_logout(self):
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        print("Người dùng cố gắng đóng cửa sổ Admin bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout()
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----
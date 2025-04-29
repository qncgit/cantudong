# gui/admin_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from utils.session import get_current_username, clear_current_user
from database.db_manager import (
    get_user_password_hash, update_user_password,
    get_all_users, add_user, delete_user, set_user_password_by_admin,
    # Thêm các hàm DB User mới
    get_user_by_id, update_user_info,
    # Các hàm nhân sự
    add_nhan_su, get_all_nhan_su, get_nhan_su_by_id, update_nhan_su, delete_nhan_su
)
from models.user_model import verify_password, ADMIN, MANAGER, USER, ROLES
from gui.set_password_dialog import ask_new_password
from gui.driver_info_dialog import DriverInfoDialog
# --- THÊM IMPORT USER DIALOG ---
from gui.user_info_dialog import UserInfoDialog
# --- KẾT THÚC THÊM IMPORT ---
import tkinter as tk

class AdminWindow(ttk.Toplevel):
    # ----- __init__ (Giữ nguyên) -----
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Admin")
        self.geometry("800x480")
        self.logout_callback = logout_callback
        self.username = get_current_username() # Username của Admin đang đăng nhập
        self.selected_user_id = None # ID user đang chọn trong Treeview
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

        # --- Tab 1: Quản lý Người dùng (Gọi hàm đã sửa) ---
        user_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(user_management_tab, text=' Quản lý Người dùng ')
        self.setup_user_management_tab(user_management_tab) # Gọi hàm đã sửa

        # --- Tab 2: Quản lý Lái xe (Giữ nguyên cấu trúc Popup) ---
        driver_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(driver_management_tab, text=' Quản lý Lái xe ')
        self.setup_driver_management_tab(driver_management_tab)

        # --- Tab 3: Tài khoản Admin (Giữ nguyên) ---
        account_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(account_tab, text=' Tài khoản Admin ')
        self.setup_account_tab(account_tab)
    # ----- Kết thúc __init__ -----


    # ----- SỬA HÀM setup_user_management_tab -----
    def setup_user_management_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Quản lý Người dùng (Popup mode)."""
        tab_frame.columnconfigure(0, weight=1) # Cột chính
        tab_frame.rowconfigure(0, weight=1)    # Hàng cho danh sách
        tab_frame.rowconfigure(1, weight=0)    # Hàng cho nút
        tab_frame.rowconfigure(2, weight=0)    # Hàng cho status label

        # ----- Frame chứa Danh sách người dùng -----
        user_list_frame = ttk.Labelframe(tab_frame, text="Danh sách Người dùng", padding=10)
        user_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew") # Hàng 0
        user_list_frame.rowconfigure(0, weight=1)
        user_list_frame.columnconfigure(0, weight=1)

        # Treeview (Giữ nguyên cấu trúc)
        columns = ("id", "username", "role")
        self.user_tree = ttk.Treeview(user_list_frame, columns=columns, show="headings", bootstyle=PRIMARY, height=10)
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="Tên đăng nhập")
        self.user_tree.heading("role", text="Vai trò")
        self.user_tree.column("id", width=60, anchor=tk.CENTER, stretch=False)
        self.user_tree.column("username", width=300, stretch=True)
        self.user_tree.column("role", width=150, stretch=True)
        # Scrollbar (Giữ nguyên)
        scrollbar = ttk.Scrollbar(user_list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        self.user_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        # Gắn sự kiện chọn item
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select) # Đổi tên hàm xử lý

        # ----- Frame chứa các nút thao tác -----
        user_action_frame = ttk.Frame(tab_frame, padding=(0, 5))
        user_action_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew") # Hàng 1

        button_container_user = ttk.Frame(user_action_frame)
        button_container_user.pack(expand=True) # Căn giữa

        add_user_button = ttk.Button(button_container_user, text="Thêm người dùng", command=self.handle_add_new_user, bootstyle=PRIMARY, width=18)
        add_user_button.pack(side=tk.LEFT, padx=5, pady=5)

        edit_user_button = ttk.Button(button_container_user, text="Sửa thông tin", command=self.handle_edit_user, bootstyle=SUCCESS, width=18, state="disabled")
        edit_user_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.edit_user_button = edit_user_button # Lưu tham chiếu

        delete_user_button = ttk.Button(button_container_user, text="Xóa người dùng", command=self.handle_delete_user_from_tab, bootstyle=DANGER, width=18, state="disabled")
        delete_user_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_user_button = delete_user_button # Lưu tham chiếu

        reset_password_button = ttk.Button(button_container_user, text="Đặt mật khẩu mới", command=self.handle_reset_user_password, bootstyle=WARNING, width=18, state="disabled")
        reset_password_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.reset_password_button = reset_password_button # Lưu tham chiếu

        refresh_user_button_tab = ttk.Button(button_container_user, text="Làm mới DS", command=self.refresh_user_list, bootstyle=INFO, width=18)
        refresh_user_button_tab.pack(side=tk.LEFT, padx=5, pady=5)

        # Label trạng thái chung cho tab này
        self.user_tab_status_label = ttk.Label(tab_frame, text="Chọn một người dùng để sửa, xóa hoặc đặt lại mật khẩu.", bootstyle=INFO, anchor="w")
        self.user_tab_status_label.grid(row=2, column=0, padx=5, pady=(0,5), sticky="ew") # Hàng 2

        # Load danh sách người dùng ban đầu
        self.refresh_user_list()
    # ----- KẾT THÚC SỬA HÀM -----

    # ----- CÁC HÀM QUẢN LÝ USER (Sửa đổi/Thêm mới) -----
    def refresh_user_list(self):
        """Làm mới danh sách người dùng trong Treeview."""
        try:
            # Bỏ chọn và vô hiệu hóa nút
            self.selected_user_id = None
            if hasattr(self, 'edit_user_button'): self.edit_user_button.config(state="disabled")
            if hasattr(self, 'delete_user_button'): self.delete_user_button.config(state="disabled")
            if hasattr(self, 'reset_password_button'): self.reset_password_button.config(state="disabled")
            selection = self.user_tree.selection()
            if selection:
                self.user_tree.selection_remove(selection)

            for item in self.user_tree.get_children():
                self.user_tree.delete(item)
            users = get_all_users()
            for user in users:
                self.user_tree.insert("", tk.END, values=(user['id'], user['username'], user['role']))
            self.show_user_tab_status("Đã tải danh sách người dùng.", INFO)
        except Exception as e:
            self.show_user_tab_status(f"Lỗi tải danh sách người dùng: {e}", DANGER)


    def on_user_select(self, event=None):
        """Xử lý khi chọn một người dùng từ Treeview."""
        selected_items = self.user_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            try:
                values = self.user_tree.item(selected_item, 'values')
                user_id = int(values[0])
                username = values[1] # Lấy username để kiểm tra
                self.selected_user_id = user_id

                # Chỉ bật nút nếu không phải là admin đang đăng nhập
                is_current_admin = (username == self.username)
                new_state = "disabled" if is_current_admin else "normal"

                if hasattr(self, 'edit_user_button'): self.edit_user_button.config(state=new_state)
                if hasattr(self, 'delete_user_button'): self.delete_user_button.config(state=new_state)
                if hasattr(self, 'reset_password_button'): self.reset_password_button.config(state=new_state)

                status_msg = f"Đã chọn User ID: {user_id}."
                if is_current_admin:
                    status_msg += " (Không thể sửa/xóa/reset chính mình)"
                self.show_user_tab_status(status_msg, INFO)

            except (ValueError, IndexError, TypeError) as e:
                print(f"Lỗi khi lấy user ID/username từ treeview: {e}")
                self.selected_user_id = None
                if hasattr(self, 'edit_user_button'): self.edit_user_button.config(state="disabled")
                if hasattr(self, 'delete_user_button'): self.delete_user_button.config(state="disabled")
                if hasattr(self, 'reset_password_button'): self.reset_password_button.config(state="disabled")
                self.show_user_tab_status("Lỗi khi lấy thông tin lựa chọn.", WARNING)
        else:
            self.selected_user_id = None
            if hasattr(self, 'edit_user_button'): self.edit_user_button.config(state="disabled")
            if hasattr(self, 'delete_user_button'): self.delete_user_button.config(state="disabled")
            if hasattr(self, 'reset_password_button'): self.reset_password_button.config(state="disabled")
            self.show_user_tab_status("Chọn một người dùng để thao tác.", INFO)

    def handle_add_new_user(self):
        """Mở dialog để thêm người dùng mới."""
        # Không cần truyền hàm DB vào dialog khi thêm mới
        dialog = UserInfoDialog(self, db_functions={}, user_id=None, current_admin_username=self.username)

        if dialog.success and dialog.result_data:
            username = dialog.result_data['username']
            role = dialog.result_data['role']
            default_password = "123456" # Mật khẩu mặc định khi thêm mới

            # Gọi hàm add_user từ db_manager
            success, message = add_user(username, default_password, role)
            if success:
                self.show_user_tab_status(message, SUCCESS)
                self.refresh_user_list()
            else:
                self.show_user_tab_status(message, DANGER) # Hiển thị lỗi (ví dụ: trùng username)
        # else: # Có thể thêm thông báo hủy bỏ
        #     self.show_user_tab_status("Đã hủy thêm người dùng.", INFO)


    def handle_edit_user(self):
        """Mở dialog để sửa thông tin người dùng đã chọn."""
        if self.selected_user_id is None:
            self.show_user_tab_status("Vui lòng chọn một người dùng từ danh sách để sửa.", WARNING)
            return

        # Kiểm tra lại có phải admin không (dù nút đã disable nhưng chắc chắn hơn)
        selected_item = self.user_tree.focus()
        if selected_item:
            try:
                if self.user_tree.item(selected_item, 'values')[1] == self.username:
                     self.show_user_tab_status("Không thể sửa thông tin của chính bạn tại đây.", WARNING)
                     return
            except (IndexError, TypeError): pass # Bỏ qua nếu lỗi lấy dữ liệu

        db_funcs = {
            'get_by_id': get_user_by_id,
            'update': update_user_info # Dùng hàm update mới
        }
        dialog = UserInfoDialog(self, db_functions=db_funcs, user_id=self.selected_user_id, current_admin_username=self.username)
        if dialog.success:
            self.refresh_user_list()
            self.show_user_tab_status(f"Cập nhật thông tin user ID {self.selected_user_id} thành công.", SUCCESS)
        # else:
        #     self.show_user_tab_status("Đã hủy sửa thông tin người dùng.", INFO)


    def handle_delete_user_from_tab(self): # Đổi tên để phân biệt với hàm DB
        """Xóa người dùng được chọn từ Treeview."""
        if self.selected_user_id is None:
            self.show_user_tab_status("Vui lòng chọn một người dùng từ danh sách để xóa.", WARNING)
            return

        # Lấy username để hiển thị và kiểm tra
        username_to_delete = ""
        selected_item = self.user_tree.focus()
        if selected_item:
             try:
                 username_to_delete = self.user_tree.item(selected_item, 'values')[1]
             except IndexError: pass

        if not username_to_delete: # Không lấy được username
             self.show_user_tab_status("Không thể xác định người dùng cần xóa.", DANGER)
             return

        if username_to_delete == self.username: # Kiểm tra lại lần nữa
             self.show_user_tab_status("Không thể xóa chính mình.", DANGER)
             return

        confirm = Messagebox.show_question(
            f"Bạn có chắc muốn xóa người dùng '{username_to_delete}' (ID: {self.selected_user_id}) không?",
            "Xác nhận xóa người dùng",
            buttons=['No:secondary', 'Yes:danger'],
            parent=self
        )

        if confirm == "Yes":
            # Gọi hàm delete_user với username
            success, message = delete_user(username_to_delete)
            if success:
                self.show_user_tab_status(message, SUCCESS)
                self.refresh_user_list() # Tự động làm mới và bỏ chọn
            else:
                self.show_user_tab_status(message, DANGER)


    def handle_reset_user_password(self): # Đổi tên từ handle_set_password
        """Đặt lại mật khẩu cho người dùng được chọn."""
        if self.selected_user_id is None:
            self.show_user_tab_status("Vui lòng chọn người dùng cần đặt lại mật khẩu.", WARNING)
            return

        # Lấy username để hiển thị và kiểm tra
        username_to_reset = ""
        selected_item = self.user_tree.focus()
        if selected_item:
             try:
                 username_to_reset = self.user_tree.item(selected_item, 'values')[1]
             except IndexError: pass

        if not username_to_reset:
             self.show_user_tab_status("Không thể xác định người dùng.", DANGER)
             return

        if username_to_reset == self.username:
             self.show_user_tab_status("Sử dụng tab 'Tài khoản Admin' để đổi mật khẩu của bạn.", WARNING)
             return

        # Gọi dialog hỏi mật khẩu mới
        new_password = ask_new_password(self, username_to_reset)

        if new_password is not None:
            confirm = Messagebox.show_question(
                f"Bạn có chắc muốn đặt mật khẩu mới cho '{username_to_reset}' không?",
                "Xác nhận đặt mật khẩu",
                buttons=['No:secondary', 'Yes:primary'],
                parent=self
            )
            if confirm == "Yes":
                # Gọi hàm set password của DB
                success, message = set_user_password_by_admin(username_to_reset, new_password)
                self.show_user_tab_status(message, SUCCESS if success else DANGER)
        # else:
        #     self.show_user_tab_status("Đã hủy đặt mật khẩu mới.", INFO)


    def show_user_tab_status(self, message, style=INFO):
         """Hiển thị thông báo trạng thái trên tab quản lý người dùng."""
         if hasattr(self, 'user_tab_status_label') and self.user_tab_status_label.winfo_exists():
             self.user_tab_status_label.config(text=message, bootstyle=style)
             self.after(5000, lambda: self.user_tab_status_label.config(text="Chọn một người dùng để thao tác.", bootstyle=INFO) if self.winfo_exists() else None)
         else:
             print(f"Status (User Tab): {message}")
    # ----- KẾT THÚC CÁC HÀM QUẢN LÝ USER -----


    # ----- CÁC HÀM QUẢN LÝ LÁI XE (Popup mode - Giữ nguyên) -----
    def setup_driver_management_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Quản lý Lái xe (Popup mode)."""
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.rowconfigure(0, weight=1)
        tab_frame.rowconfigure(1, weight=0)
        tab_frame.rowconfigure(2, weight=0)

        driver_list_frame = ttk.Labelframe(tab_frame, text="Danh sách Lái xe", padding=10)
        driver_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        driver_list_frame.rowconfigure(0, weight=1)
        driver_list_frame.columnconfigure(0, weight=1)

        driver_cols = ("id", "maNhanVien", "maThe", "tenNhanVien", "trangThai")
        self.driver_tree = ttk.Treeview(driver_list_frame, columns=driver_cols, show="headings", bootstyle=INFO, height=15)
        self.driver_tree.heading("id", text="ID")
        self.driver_tree.heading("maNhanVien", text="Mã NV")
        self.driver_tree.heading("maThe", text="Mã Thẻ")
        self.driver_tree.heading("tenNhanVien", text="Tên Lái xe")
        self.driver_tree.heading("trangThai", text="Trạng thái")
        self.driver_tree.column("id", width=40, anchor=tk.CENTER, stretch=False)
        self.driver_tree.column("maNhanVien", width=100, stretch=False)
        self.driver_tree.column("maThe", width=120, stretch=False)
        self.driver_tree.column("tenNhanVien", width=300, stretch=True)
        self.driver_tree.column("trangThai", width=100, stretch=False)
        driver_scrollbar = ttk.Scrollbar(driver_list_frame, orient=tk.VERTICAL, command=self.driver_tree.yview)
        self.driver_tree.configure(yscrollcommand=driver_scrollbar.set)
        self.driver_tree.grid(row=0, column=0, sticky="nsew")
        driver_scrollbar.grid(row=0, column=1, sticky="ns")
        self.driver_tree.bind("<<TreeviewSelect>>", self.on_driver_select)

        driver_action_frame = ttk.Frame(tab_frame, padding=(0, 10))
        driver_action_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        button_container_driver = ttk.Frame(driver_action_frame)
        button_container_driver.pack(expand=True)
        add_driver_button = ttk.Button(button_container_driver, text="Thêm lái xe mới", command=self.handle_add_new_driver, bootstyle=PRIMARY, width=18)
        add_driver_button.pack(side=tk.LEFT, padx=10, pady=5)
        edit_driver_button = ttk.Button(button_container_driver, text="Sửa thông tin", command=self.handle_edit_driver, bootstyle=SUCCESS, width=18, state="disabled")
        edit_driver_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.edit_driver_button = edit_driver_button
        delete_driver_button = ttk.Button(button_container_driver, text="Xóa lái xe", command=self.handle_delete_driver_from_tab, bootstyle=DANGER, width=18, state="disabled")
        delete_driver_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.delete_driver_button = delete_driver_button
        refresh_driver_button_tab = ttk.Button(button_container_driver, text="Làm mới DS", command=self.refresh_driver_list, bootstyle=INFO, width=18)
        refresh_driver_button_tab.pack(side=tk.LEFT, padx=10, pady=5)

        self.driver_tab_status_label = ttk.Label(tab_frame, text="Chọn một lái xe để sửa hoặc xóa.", bootstyle=INFO, anchor="w")
        self.driver_tab_status_label.grid(row=2, column=0, padx=5, pady=(0,5), sticky="ew")
        self.refresh_driver_list()

    def on_driver_select(self, event=None):
        """Xử lý khi chọn một lái xe từ Treeview."""
        selected_items = self.driver_tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            try:
                driver_id = int(self.driver_tree.item(selected_item, 'values')[0])
                self.selected_driver_id = driver_id
                if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="normal")
                if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="normal")
                self.show_driver_tab_status(f"Đã chọn lái xe ID: {driver_id}. Nhấn 'Sửa' hoặc 'Xóa'.", INFO)
            except (ValueError, IndexError, TypeError) as e:
                print(f"Lỗi khi lấy driver ID từ treeview: {e}")
                self.selected_driver_id = None
                if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="disabled")
                if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="disabled")
                self.show_driver_tab_status("Lỗi khi lấy thông tin lựa chọn.", WARNING)
        else:
            self.selected_driver_id = None
            if hasattr(self, 'edit_driver_button'): self.edit_driver_button.config(state="disabled")
            if hasattr(self, 'delete_driver_button'): self.delete_driver_button.config(state="disabled")
            self.show_driver_tab_status("Chọn một lái xe để sửa hoặc xóa.", INFO)

    def handle_add_new_driver(self):
        """Mở dialog để thêm lái xe mới."""
        db_funcs = {'add': add_nhan_su}
        dialog = DriverInfoDialog(self, db_functions=db_funcs, driver_id=None)
        if dialog.success:
            self.refresh_driver_list()
            self.show_driver_tab_status("Thêm lái xe mới thành công.", SUCCESS)

    def handle_edit_driver(self):
        """Mở dialog để sửa thông tin lái xe đã chọn."""
        if self.selected_driver_id is None:
            self.show_driver_tab_status("Vui lòng chọn một lái xe từ danh sách để sửa.", WARNING)
            return
        db_funcs = {'get_by_id': get_nhan_su_by_id, 'update': update_nhan_su}
        dialog = DriverInfoDialog(self, db_functions=db_funcs, driver_id=self.selected_driver_id)
        if dialog.success:
            self.refresh_driver_list()
            self.show_driver_tab_status(f"Cập nhật thông tin lái xe ID {self.selected_driver_id} thành công.", SUCCESS)

    def handle_delete_driver_from_tab(self):
        """Xóa lái xe được chọn từ Treeview."""
        if self.selected_driver_id is None:
            self.show_driver_tab_status("Vui lòng chọn một lái xe từ danh sách để xóa.", WARNING)
            return
        driver_name = ""
        selected_items = self.driver_tree.selection()
        if selected_items:
             try: driver_name = self.driver_tree.item(selected_items[0], 'values')[3]
             except IndexError: pass
        confirm = Messagebox.show_question(
            f"Bạn có chắc muốn xóa lái xe '{driver_name}' (ID: {self.selected_driver_id}) không?",
            "Xác nhận xóa lái xe", buttons=['No:secondary', 'Yes:danger'], parent=self )
        if confirm == "Yes":
            success, message = delete_nhan_su(self.selected_driver_id)
            if success:
                self.show_driver_tab_status(message, SUCCESS)
                self.refresh_driver_list()
            else: self.show_driver_tab_status(message, DANGER)

    def show_driver_tab_status(self, message, style=INFO):
        """Hiển thị thông báo trạng thái trên tab quản lý lái xe."""
        if hasattr(self, 'driver_tab_status_label') and self.driver_tab_status_label.winfo_exists():
            self.driver_tab_status_label.config(text=message, bootstyle=style)
            self.after(6000, lambda: self.driver_tab_status_label.config(text="Chọn một lái xe để sửa hoặc xóa.", bootstyle=INFO) if self.winfo_exists() else None)
        else: print(f"Status (Driver Tab): {message}")

    def refresh_driver_list(self):
        """Làm mới danh sách lái xe trong Treeview."""
        try:
            # Bỏ chọn và vô hiệu hóa nút
            self.selected_driver_id = None
            if hasattr(self, 'edit_driver_button'):
                self.edit_driver_button.config(state="disabled")
            if hasattr(self, 'delete_driver_button'):
                self.delete_driver_button.config(state="disabled")
            selection = self.driver_tree.selection()
            if selection:
                self.driver_tree.selection_remove(selection)

            for item in self.driver_tree.get_children():
                self.driver_tree.delete(item)
            drivers = get_all_nhan_su()
            for driver in drivers:
                self.driver_tree.insert("", tk.END, values=(
                    driver['id'], driver['maNhanVien'], driver['maThe'],
                    driver['tenNhanVien'], driver['trangThai']
                ))
            self.show_driver_tab_status("Đã tải danh sách lái xe.", INFO)
        except Exception as e:
            self.show_driver_tab_status(f"Lỗi tải danh sách lái xe: {e}", DANGER)
    # ----- KẾT THÚC CÁC HÀM QUẢN LÝ LÁI XE -----


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
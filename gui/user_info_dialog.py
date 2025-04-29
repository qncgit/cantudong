# gui/user_info_dialog.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import tkinter as tk
from models.user_model import ADMIN, MANAGER, USER # Import các vai trò

class UserInfoDialog(ttk.Toplevel):
    """Popup Dialog để thêm hoặc sửa thông tin người dùng (username, role)."""

    def __init__(self, parent, db_functions, user_id=None, current_admin_username=None):
        """
        Khởi tạo Dialog.
        Args:
            parent: Cửa sổ cha (AdminWindow).
            db_functions (dict): {'get_by_id': func, 'update': func}
            user_id (int, optional): ID của user cần sửa. None nếu là thêm mới.
            current_admin_username (str): Username của admin đang đăng nhập.
        """
        mode_title = "Sửa thông tin Người dùng" if user_id else "Thêm Người dùng mới"
        super().__init__(master=parent, title=mode_title)
        self.parent = parent
        self.db = db_functions
        self.user_id = user_id
        self.current_admin_username = current_admin_username
        self.success = False
        self.result_data = None # Lưu kết quả {username, role} cho chế độ Add

        # --- Cấu hình dialog ---
        self.geometry("450x250") # Kích thước nhỏ hơn User Dialog
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # --- Form nhập liệu ---
        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)
        form_frame.columnconfigure(1, weight=1)

        # Username
        ttk.Label(form_frame, text="Tên đăng nhập (*):").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Role
        ttk.Label(form_frame, text="Vai trò (*):").grid(row=1, column=0, padx=5, pady=10, sticky="w")
        # Chỉ cho phép chọn Manager hoặc User khi thêm/sửa
        allowed_roles = [MANAGER, USER]
        self.role_combobox = ttk.Combobox(form_frame, values=allowed_roles, state="readonly", width=28)
        self.role_combobox.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # Lưu ý: Không có trường mật khẩu ở đây.
        # Mật khẩu được đặt mặc định khi thêm mới hoặc reset riêng.

        # --- Nút bấm ---
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        save_button = ttk.Button(button_frame, text="Lưu", command=self.on_save, bootstyle=SUCCESS)
        save_button.pack(side=tk.LEFT, padx=15)

        cancel_button = ttk.Button(button_frame, text="Hủy bỏ", command=self.on_cancel, bootstyle=SECONDARY)
        cancel_button.pack(side=tk.LEFT, padx=15)

        # Load data nếu là sửa
        if self.user_id:
            self._load_data()
        else:
            # Đặt giá trị mặc định cho Thêm mới
            self.role_combobox.set(USER)

        # Căn giữa
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        x = max(0, x)
        y = max(0, y)
        self.geometry(f"+{x}+{y}")

        self.username_entry.focus_set()
        if self.user_id:
            self.username_entry.select_range(0, tk.END)


        self.wait_window(self)

    def _load_data(self):
        """Tải dữ liệu user vào form (chế độ sửa)."""
        if 'get_by_id' not in self.db:
            Messagebox.show_error("Lỗi cấu hình: Thiếu hàm 'get_by_id'.", parent=self)
            self.on_cancel()
            return

        user_data = self.db['get_by_id'](self.user_id)
        if not user_data:
            Messagebox.show_error(f"Không tìm thấy dữ liệu cho user ID {self.user_id}.", parent=self)
            self.on_cancel()
            return

        self.username_entry.insert(0, user_data.get('username', ''))
        # Đảm bảo vai trò lấy được nằm trong danh sách cho phép
        role = user_data.get('role', '')
        if role in [MANAGER, USER]:
            self.role_combobox.set(role)
        else:
            # Nếu vai trò là Admin hoặc không hợp lệ, không cho sửa vai trò
            self.role_combobox.set('') # Hoặc đặt về User nếu muốn
            # Có thể vô hiệu hóa combobox nếu sửa Admin
            if role == ADMIN:
                self.role_combobox.config(state="disabled")
                self.username_entry.config(state="readonly") # Không cho sửa username Admin

        # Không cho sửa username của chính Admin đang đăng nhập
        if user_data.get('username') == self.current_admin_username:
            self.username_entry.config(state="readonly")
            self.role_combobox.config(state="disabled") # Không cho tự đổi vai trò


    def on_save(self):
        """Xử lý khi nhấn Lưu."""
        username = self.username_entry.get().strip()
        role = self.role_combobox.get()

        # Validation
        if not username:
            Messagebox.show_warning("Tên đăng nhập không được để trống.", "Thiếu thông tin", parent=self)
            return
        if not role:
            Messagebox.show_warning("Vui lòng chọn vai trò.", "Thiếu thông tin", parent=self)
            return

        if self.user_id is None: # Chế độ Thêm mới
            # Chỉ lưu lại dữ liệu để AdminWindow xử lý tiếp (thêm mật khẩu)
            self.result_data = {'username': username, 'role': role}
            self.success = True
            self.destroy()
        else: # Chế độ Cập nhật
            if 'update' not in self.db:
                 Messagebox.show_error("Lỗi cấu hình: Thiếu hàm 'update'.", parent=self)
                 return
            # Không cho sửa username của chính admin
            if self.username_entry.cget('state') == 'readonly' and role != self.role_combobox['values'][0 if self.role_combobox.current() < 0 else self.role_combobox.current()]:
                 # Nếu username readonly và role bị thay đổi (ví dụ từ Admin) -> không cho phép
                  Messagebox.show_error("Không thể thay đổi vai trò của tài khoản này.", "Hành động bị chặn", parent=self)
                  return

            success, message = self.db['update'](self.user_id, username, role)
            if success:
                self.success = True
                self.destroy()
            else:
                Messagebox.show_error(message, "Lỗi cập nhật", parent=self)

    def on_cancel(self):
        self.success = False
        self.destroy()
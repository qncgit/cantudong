# gui/admin_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
# --- THÊM IMPORT DATEENTRY ---
from ttkbootstrap.widgets import DateEntry
# --- KẾT THÚC THÊM IMPORT ---
from utils.session import get_current_username, clear_current_user
# --- SỬA IMPORT DB MANAGER ---
from database.db_manager import (
    get_user_password_hash, update_user_password,
    get_all_users, add_user, delete_user, set_user_password_by_admin,
    # Thêm các hàm quản lý nhân sự
    add_nhan_su, get_all_nhan_su, get_nhan_su_by_id, update_nhan_su, delete_nhan_su
)
# --- KẾT THÚC SỬA IMPORT DB MANAGER ---
from models.user_model import verify_password, ADMIN, MANAGER, USER, ROLES
from gui.set_password_dialog import ask_new_password
import tkinter as tk
from tkinter import filedialog # Để chọn hình ảnh (nếu cần)
import os # Để xử lý đường dẫn file ảnh (nếu cần)

class AdminWindow(ttk.Toplevel):
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Admin")
        self.geometry("800x480") # Có thể cần tăng kích thước nếu có nhiều tab
        # self.geometry("1000x600") # Thử kích thước lớn hơn
        self.logout_callback = logout_callback
        self.username = get_current_username()
        self.selected_driver_id = None # Theo dõi ID nhân sự đang được chọn/sửa
        self.driver_image_path = None # Lưu đường dẫn ảnh đã chọn

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header (Giữ nguyên) -----
        header_frame = ttk.Frame(self, padding=(10, 5), bootstyle=INFO)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))
        welcome_label = ttk.Label(header_frame, text=f"Chào mừng Admin: {self.username}", font="-size 12 -weight bold", bootstyle=INFO)
        welcome_label.pack(side=LEFT, padx=10)
        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)
        # ----- Kết thúc Header -----

        # ----- Tạo Notebook (Tabs) -----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=5, padx=10, fill=BOTH, expand=YES)

        # --- Tab 1: Quản lý Người dùng (Giữ nguyên) ---
        user_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(user_management_tab, text=' Quản lý Người dùng ')
        self.setup_user_management_tab(user_management_tab)

        # --- Tab 2: Quản lý Lái xe (Mới) ---
        driver_management_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(driver_management_tab, text=' Quản lý Lái xe ')
        self.setup_driver_management_tab(driver_management_tab) # Gọi hàm mới

        # --- Tab 3: Tài khoản Admin (Giữ nguyên) ---
        account_tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(account_tab, text=' Tài khoản Admin ')
        self.setup_account_tab(account_tab)

    # ----- setup_user_management_tab và các hàm liên quan (Giữ nguyên) -----
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

    # ----- Hàm MỚI: setup_driver_management_tab -----
    def setup_driver_management_tab(self, tab_frame):
        """Thiết lập giao diện cho Tab Quản lý Lái xe."""
        tab_frame.columnconfigure(0, weight=1) # Cột chứa danh sách
        tab_frame.columnconfigure(1, weight=1) # Cột chứa form nhập liệu
        tab_frame.rowconfigure(0, weight=1)    # Hàng chứa danh sách và form

        # ----- Frame chứa Danh sách Lái xe -----
        driver_list_frame = ttk.Labelframe(tab_frame, text="Danh sách Lái xe", padding=10)
        driver_list_frame.grid(row=0, column=0, padx=(5, 10), pady=5, sticky="nsew")
        driver_list_frame.rowconfigure(0, weight=1)
        driver_list_frame.columnconfigure(0, weight=1)

        # Treeview hiển thị danh sách lái xe
        driver_cols = ("id", "maNhanVien", "maThe", "tenNhanVien", "trangThai")
        self.driver_tree = ttk.Treeview(driver_list_frame, columns=driver_cols, show="headings", bootstyle=INFO, height=15) # Tăng chiều cao

        self.driver_tree.heading("id", text="ID")
        self.driver_tree.heading("maNhanVien", text="Mã NV")
        self.driver_tree.heading("maThe", text="Mã Thẻ")
        self.driver_tree.heading("tenNhanVien", text="Tên Lái xe")
        self.driver_tree.heading("trangThai", text="Trạng thái")

        self.driver_tree.column("id", width=40, anchor=tk.CENTER, stretch=False)
        self.driver_tree.column("maNhanVien", width=80, stretch=False)
        self.driver_tree.column("maThe", width=100, stretch=False)
        self.driver_tree.column("tenNhanVien", width=150, stretch=True)
        self.driver_tree.column("trangThai", width=80, stretch=False)

        driver_scrollbar = ttk.Scrollbar(driver_list_frame, orient=tk.VERTICAL, command=self.driver_tree.yview)
        self.driver_tree.configure(yscrollcommand=driver_scrollbar.set)

        self.driver_tree.grid(row=0, column=0, sticky="nsew")
        driver_scrollbar.grid(row=0, column=1, sticky="ns")

        # Gắn sự kiện chọn item trong Treeview
        self.driver_tree.bind("<<TreeviewSelect>>", self.on_driver_select)

        # Nút Làm mới danh sách lái xe
        refresh_driver_button = ttk.Button(driver_list_frame, text="Làm mới DS", command=self.refresh_driver_list, bootstyle=SECONDARY, width=15)
        refresh_driver_button.grid(row=1, column=0, columnspan=2, pady=(10,0))


        # ----- Frame chứa Form Nhập liệu Lái xe -----
        driver_form_frame = ttk.Labelframe(tab_frame, text="Thông tin Lái xe", padding=15)
        driver_form_frame.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="nsew")
        # Cấu hình cột cho form để label và entry thẳng hàng
        driver_form_frame.columnconfigure(1, weight=1)
        driver_form_frame.columnconfigure(3, weight=1)

        # Các trường nhập liệu (sử dụng grid) - Hàng 0
        ttk.Label(driver_form_frame, text="Mã NV (*):").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.driver_maNV_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_maNV_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(driver_form_frame, text="Mã Thẻ (*):").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.driver_maThe_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_maThe_entry.grid(row=0, column=3, padx=5, pady=3, sticky="ew")

        # Hàng 1
        ttk.Label(driver_form_frame, text="Tên Lái xe (*):").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.driver_tenNV_entry = ttk.Entry(driver_form_frame) # width sẽ theo grid co giãn
        self.driver_tenNV_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=3, sticky="ew")

        # Hàng 2
        ttk.Label(driver_form_frame, text="Số ĐT:").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.driver_sdt_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_sdt_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(driver_form_frame, text="Ngày Sinh:").grid(row=2, column=2, padx=5, pady=3, sticky="w")
        self.driver_ngaySinh_entry = DateEntry(driver_form_frame, width=18, dateformat="%Y-%m-%d") # Dùng DateEntry
        self.driver_ngaySinh_entry.grid(row=2, column=3, padx=5, pady=3, sticky="ew")

        # Hàng 3
        ttk.Label(driver_form_frame, text="Giới Tính:").grid(row=3, column=0, padx=5, pady=3, sticky="w")
        self.driver_gioiTinh_combo = ttk.Combobox(driver_form_frame, values=["Nam", "Nữ", "Khác"], state="readonly", width=18)
        self.driver_gioiTinh_combo.grid(row=3, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(driver_form_frame, text="Trạng Thái:").grid(row=3, column=2, padx=5, pady=3, sticky="w")
        self.driver_trangThai_combo = ttk.Combobox(driver_form_frame, values=["Hoạt động", "Tạm nghỉ", "Đã nghỉ"], state="readonly", width=18)
        self.driver_trangThai_combo.set("Hoạt động") # Mặc định
        self.driver_trangThai_combo.grid(row=3, column=3, padx=5, pady=3, sticky="ew")

        # Hàng 4
        ttk.Label(driver_form_frame, text="Chức Vụ:").grid(row=4, column=0, padx=5, pady=3, sticky="w")
        self.driver_chucVu_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_chucVu_entry.grid(row=4, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(driver_form_frame, text="Đơn Vị:").grid(row=4, column=2, padx=5, pady=3, sticky="w")
        self.driver_donVi_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_donVi_entry.grid(row=4, column=3, padx=5, pady=3, sticky="ew")

        # Hàng 5 - Phân Quyền, Label (ít dùng hơn?)
        ttk.Label(driver_form_frame, text="Phân Quyền:").grid(row=5, column=0, padx=5, pady=3, sticky="w")
        self.driver_phanQuyen_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_phanQuyen_entry.grid(row=5, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(driver_form_frame, text="Label NS:").grid(row=5, column=2, padx=5, pady=3, sticky="w")
        self.driver_labelNS_entry = ttk.Entry(driver_form_frame, width=20)
        self.driver_labelNS_entry.grid(row=5, column=3, padx=5, pady=3, sticky="ew")

        # Hàng 6 - Hình ảnh (Đơn giản là hiển thị đường dẫn và nút chọn)
        ttk.Label(driver_form_frame, text="Hình Ảnh:").grid(row=6, column=0, padx=5, pady=3, sticky="w")
        self.driver_hinhAnh_entry = ttk.Entry(driver_form_frame, state="readonly") # Chỉ hiển thị đường dẫn
        self.driver_hinhAnh_entry.grid(row=6, column=1, columnspan=2, padx=5, pady=3, sticky="ew")
        choose_image_button = ttk.Button(driver_form_frame, text="Chọn ảnh", command=self.choose_driver_image, width=8, bootstyle=INFO)
        choose_image_button.grid(row=6, column=3, padx=5, pady=3, sticky="e")

        # ----- Nút điều khiển Form -----
        form_button_frame = ttk.Frame(driver_form_frame)
        form_button_frame.grid(row=7, column=0, columnspan=4, pady=(15, 5)) # Đặt dưới cùng form

        new_button = ttk.Button(form_button_frame, text="Thêm mới", command=self.clear_driver_form, bootstyle=PRIMARY, width=12)
        new_button.pack(side=tk.LEFT, padx=10)

        save_button = ttk.Button(form_button_frame, text="Lưu", command=self.handle_save_driver, bootstyle=SUCCESS, width=12)
        save_button.pack(side=tk.LEFT, padx=10)

        delete_driver_button = ttk.Button(form_button_frame, text="Xóa", command=self.handle_delete_driver, bootstyle=DANGER, width=12)
        delete_driver_button.pack(side=tk.LEFT, padx=10)

        # Label trạng thái cho quản lý lái xe
        self.driver_manage_status_label = ttk.Label(driver_form_frame, text="Chọn lái xe từ danh sách hoặc nhấn 'Thêm mới'.", bootstyle=INFO)
        self.driver_manage_status_label.grid(row=8, column=0, columnspan=4, pady=(10,0), sticky="w")

        # Load danh sách lái xe ban đầu
        self.refresh_driver_list()
    # ----- Kết thúc setup_driver_management_tab -----


    # ----- CÁC HÀM MỚI CHO QUẢN LÝ LÁI XE -----
    def refresh_driver_list(self):
        """Làm mới danh sách lái xe trong Treeview."""
        try:
            for item in self.driver_tree.get_children():
                self.driver_tree.delete(item)
            drivers = get_all_nhan_su()
            for driver in drivers:
                # Lấy các giá trị theo đúng thứ tự cột đã định nghĩa
                values = (
                    driver.get('id', ''),
                    driver.get('maNhanVien', ''),
                    driver.get('maThe', ''),
                    driver.get('tenNhanVien', ''),
                    driver.get('trangThai', '')
                )
                self.driver_tree.insert("", tk.END, values=values)
            self.show_driver_manage_status("Đã tải danh sách lái xe.", INFO)
        except Exception as e:
             self.show_driver_manage_status(f"Lỗi tải danh sách lái xe: {e}", DANGER)

    def clear_driver_form(self, set_status=True):
        """Xóa trắng form nhập liệu lái xe và bỏ chọn."""
        self.selected_driver_id = None
        self.driver_image_path = None # Xóa đường dẫn ảnh

        self.driver_maNV_entry.delete(0, tk.END)
        self.driver_maThe_entry.delete(0, tk.END)
        self.driver_tenNV_entry.delete(0, tk.END)
        self.driver_sdt_entry.delete(0, tk.END)
        try:
            # Xóa ngày trong DateEntry và đặt lại ngày hiện tại nếu cần
            self.driver_ngaySinh_entry.entry.delete(0, tk.END)
            # self.driver_ngaySinh_entry.entry.insert(0, datetime.date.today().strftime(self.driver_ngaySinh_entry.dateformat))
        except Exception: pass # Bỏ qua nếu DateEntry chưa sẵn sàng
        self.driver_gioiTinh_combo.set("") # Xóa lựa chọn combobox
        self.driver_trangThai_combo.set("Hoạt động") # Đặt lại mặc định
        self.driver_chucVu_entry.delete(0, tk.END)
        self.driver_donVi_entry.delete(0, tk.END)
        self.driver_phanQuyen_entry.delete(0, tk.END)
        self.driver_labelNS_entry.delete(0, tk.END)
        self.driver_hinhAnh_entry.config(state="normal") # Cho phép sửa tạm
        self.driver_hinhAnh_entry.delete(0, tk.END)
        self.driver_hinhAnh_entry.config(state="readonly")# Đặt lại chỉ đọc

        # Bỏ chọn trong Treeview
        selection = self.driver_tree.selection()
        if selection:
            self.driver_tree.selection_remove(selection)

        if set_status:
            self.show_driver_manage_status("Sẵn sàng thêm lái xe mới.", PRIMARY)

    def on_driver_select(self, event=None):
        """Xử lý khi chọn một lái xe từ Treeview."""
        selected_items = self.driver_tree.selection()
        if not selected_items:
            # Nếu không có gì được chọn (có thể do người dùng click vào khoảng trống)
            # self.clear_driver_form() # Cân nhắc xem có nên xóa form không
            return

        selected_item = selected_items[0] # Chỉ xử lý item đầu tiên nếu chọn nhiều
        item_values = self.driver_tree.item(selected_item, 'values')

        if not item_values:
            self.clear_driver_form()
            return

        try:
            driver_id = int(item_values[0]) # Lấy ID từ cột đầu tiên
            self.load_driver_to_form(driver_id)
        except (ValueError, IndexError):
            self.show_driver_manage_status("Lỗi lấy ID lái xe từ danh sách.", DANGER)
            self.clear_driver_form()

    def load_driver_to_form(self, driver_id):
        """Tải thông tin chi tiết của lái xe vào form."""
        driver_data = get_nhan_su_by_id(driver_id)
        if not driver_data:
            self.show_driver_manage_status(f"Không tìm thấy thông tin cho lái xe ID {driver_id}.", WARNING)
            self.clear_driver_form()
            return

        self.clear_driver_form(set_status=False) # Xóa form trước khi load
        self.selected_driver_id = driver_id # Lưu ID đang sửa

        # Điền dữ liệu vào form
        self.driver_maNV_entry.insert(0, driver_data.get('maNhanVien', ''))
        self.driver_maThe_entry.insert(0, driver_data.get('maThe', ''))
        self.driver_tenNV_entry.insert(0, driver_data.get('tenNhanVien', ''))
        self.driver_sdt_entry.insert(0, driver_data.get('soDienThoai', ''))
        # Xử lý DateEntry
        ngay_sinh = driver_data.get('ngaySinh', '')
        if ngay_sinh:
             try:
                 # Cố gắng đặt ngày cho DateEntry, cần đúng định dạng
                 # date_obj = datetime.datetime.strptime(ngay_sinh, "%Y-%m-%d").date() # Hoặc định dạng khác
                 # self.driver_ngaySinh_entry.set_date(date_obj)
                 # Cách đơn giản hơn là insert chuỗi trực tiếp nếu định dạng lưu khớp
                 self.driver_ngaySinh_entry.entry.delete(0, tk.END)
                 self.driver_ngaySinh_entry.entry.insert(0, ngay_sinh)
             except ValueError as e:
                 print(f"Lỗi định dạng ngày sinh '{ngay_sinh}': {e}")
                 self.driver_ngaySinh_entry.entry.delete(0, tk.END) # Xóa nếu lỗi
        else:
             self.driver_ngaySinh_entry.entry.delete(0, tk.END)

        self.driver_gioiTinh_combo.set(driver_data.get('gioiTinh', ''))
        self.driver_trangThai_combo.set(driver_data.get('trangThai', 'Hoạt động')) # Mặc định nếu trống
        self.driver_chucVu_entry.insert(0, driver_data.get('chucVu', ''))
        self.driver_donVi_entry.insert(0, driver_data.get('donVi', ''))
        self.driver_phanQuyen_entry.insert(0, driver_data.get('phanQuyen', ''))
        self.driver_labelNS_entry.insert(0, driver_data.get('labelNhanSu', ''))

        # Xử lý hình ảnh
        hinh_anh_path = driver_data.get('hinhAnh', '')
        self.driver_image_path = hinh_anh_path # Lưu lại để dùng khi Lưu
        self.driver_hinhAnh_entry.config(state="normal")
        self.driver_hinhAnh_entry.delete(0, tk.END)
        self.driver_hinhAnh_entry.insert(0, hinh_anh_path)
        self.driver_hinhAnh_entry.config(state="readonly")

        self.show_driver_manage_status(f"Đang sửa thông tin lái xe: {driver_data.get('tenNhanVien', '')}", INFO)

    def choose_driver_image(self):
        """Mở hộp thoại chọn file ảnh."""
        # Xác định thư mục lưu ảnh (ví dụ: 'images/drivers' trong thư mục dự án)
        # image_dir = os.path.join(BASE_DIR, 'images', 'drivers') # BASE_DIR đã import ở db_manager
        # os.makedirs(image_dir, exist_ok=True) # Tạo thư mục nếu chưa có

        filepath = filedialog.askopenfilename(
            title="Chọn ảnh lái xe",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")],
            # initialdir=image_dir # Mở thư mục ảnh mặc định
        )
        if filepath:
            # Chỉ lưu đường dẫn tương đối hoặc tên file nếu muốn?
            # Hoặc có thể copy file vào thư mục dự án và lưu đường dẫn mới
            filename = os.path.basename(filepath)
            self.driver_image_path = filename # Hoặc filepath tùy cách lưu trữ
            self.driver_hinhAnh_entry.config(state="normal")
            self.driver_hinhAnh_entry.delete(0, tk.END)
            self.driver_hinhAnh_entry.insert(0, self.driver_image_path)
            self.driver_hinhAnh_entry.config(state="readonly")
            self.show_driver_manage_status(f"Đã chọn ảnh: {self.driver_image_path}", INFO)

    def handle_save_driver(self):
        """Lưu thông tin lái xe (Thêm mới hoặc Cập nhật)."""
        # Thu thập dữ liệu từ form
        data = {
            'maNhanVien': self.driver_maNV_entry.get().strip(),
            'maThe': self.driver_maThe_entry.get().strip(),
            'tenNhanVien': self.driver_tenNV_entry.get().strip(),
            'soDienThoai': self.driver_sdt_entry.get().strip(),
            'ngaySinh': self.driver_ngaySinh_entry.entry.get().strip(), # Lấy từ entry của DateEntry
            'gioiTinh': self.driver_gioiTinh_combo.get(),
            'trangThai': self.driver_trangThai_combo.get(),
            'chucVu': self.driver_chucVu_entry.get().strip(),
            'donVi': self.driver_donVi_entry.get().strip(),
            'phanQuyen': self.driver_phanQuyen_entry.get().strip(),
            'labelNhanSu': self.driver_labelNS_entry.get().strip(),
            'hinhAnh': self.driver_image_path if self.driver_image_path else None # Lấy đường dẫn đã lưu
        }

        # --- Validation cơ bản ---
        if not data['maThe'] or not data['tenNhanVien']:
            self.show_driver_manage_status("Lỗi: Mã Thẻ và Tên Lái xe là bắt buộc.", DANGER)
            return
        # Thêm các validation khác nếu cần (ví dụ: định dạng mã thẻ, sđt, ...)

        # Xử lý ngày sinh trống
        if not data['ngaySinh']:
            data['ngaySinh'] = None

        # Gọi hàm DB tương ứng (Add hoặc Update)
        if self.selected_driver_id is None:
            # --- Chế độ Thêm mới ---
            success, message = add_nhan_su(data)
        else:
            # --- Chế độ Cập nhật ---
            success, message = update_nhan_su(self.selected_driver_id, data)

        # Hiển thị kết quả và làm mới
        if success:
            self.show_driver_manage_status(message, SUCCESS)
            self.refresh_driver_list()
            self.clear_driver_form()
        else:
            self.show_driver_manage_status(message, DANGER)

    def handle_delete_driver(self):
        """Xóa lái xe được chọn."""
        if self.selected_driver_id is None:
            self.show_driver_manage_status("Vui lòng chọn lái xe cần xóa.", WARNING)
            return

        driver_name = self.driver_tenNV_entry.get() # Lấy tên để hiển thị trong xác nhận
        confirm = Messagebox.show_question(
            f"Bạn có chắc muốn xóa lái xe '{driver_name}' (ID: {self.selected_driver_id}) không?",
            "Xác nhận xóa lái xe",
            buttons=['No:secondary', 'Yes:danger'],
            parent=self
        )

        if confirm == "Yes":
            success, message = delete_nhan_su(self.selected_driver_id)
            if success:
                self.show_driver_manage_status(message, SUCCESS)
                self.refresh_driver_list()
                self.clear_driver_form()
            else:
                self.show_driver_manage_status(message, DANGER)


    def show_driver_manage_status(self, message, style=INFO):
        """Hiển thị thông báo trạng thái quản lý lái xe."""
        if hasattr(self, 'driver_manage_status_label') and self.driver_manage_status_label.winfo_exists():
            self.driver_manage_status_label.config(text=message, bootstyle=style)
            self.after(6000, lambda: self.driver_manage_status_label.config(text="") if self.winfo_exists() else None)
        else:
            print(f"Status (Driver Manage): {message}")
    # ----- KẾT THÚC CÁC HÀM QUẢN LÝ LÁI XE -----


    # ----- CÁC HÀM QUẢN LÝ USER (users table) GIỮ NGUYÊN -----
    def refresh_user_list(self):
        """Lấy dữ liệu người dùng từ DB và cập nhật Treeview."""
        try:
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
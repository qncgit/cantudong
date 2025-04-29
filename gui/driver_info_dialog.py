# gui/driver_info_dialog.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import DateEntry
import tkinter as tk
from tkinter import filedialog
import os
import datetime # Cần cho DateEntry

class DriverInfoDialog(ttk.Toplevel):
    """Popup Dialog để thêm hoặc sửa thông tin lái xe."""

    def __init__(self, parent, db_functions, driver_id=None):
        """
        Khởi tạo Dialog.
        Args:
            parent: Cửa sổ cha (AdminWindow).
            db_functions (dict): Dictionary chứa các hàm thao tác DB cần thiết.
                                 Ví dụ: {'get_by_id': func, 'add': func, 'update': func}
            driver_id (int, optional): ID của lái xe cần sửa. None nếu là thêm mới.
                                       Defaults to None.
        """
        mode_title = "Sửa thông tin Lái xe" if driver_id else "Thêm Lái xe mới"
        super().__init__(master=parent, title=mode_title)
        self.parent = parent
        self.db = db_functions # Lưu lại dict các hàm DB
        self.driver_id = driver_id
        self.success = False # Trạng thái trả về khi dialog đóng
        self.image_path_to_save = None # Lưu đường dẫn ảnh được chọn

        # --- Cấu hình cửa sổ dialog ---
        self.geometry("700x350") # Kích thước lớn hơn cho form chi tiết
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # --- Tạo Form nhập liệu ---
        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        # Các trường nhập liệu
        # Hàng 0
        ttk.Label(form_frame, text="Mã NV (*):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.maNV_entry = ttk.Entry(form_frame, width=25)
        self.maNV_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Mã Thẻ (*):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.maThe_entry = ttk.Entry(form_frame, width=25)
        self.maThe_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        # Hàng 1
        ttk.Label(form_frame, text="Tên Lái xe (*):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tenNV_entry = ttk.Entry(form_frame)
        self.tenNV_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        # Hàng 2
        ttk.Label(form_frame, text="Số ĐT:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sdt_entry = ttk.Entry(form_frame, width=25)
        self.sdt_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Ngày Sinh:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.ngaySinh_entry = DateEntry(form_frame, width=23, dateformat="%Y-%m-%d") # Điều chỉnh width
        self.ngaySinh_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        # Hàng 3
        ttk.Label(form_frame, text="Giới Tính:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.gioiTinh_combo = ttk.Combobox(form_frame, values=["Nam", "Nữ", "Khác"], state="readonly", width=23)
        self.gioiTinh_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Trạng Thái:").grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.trangThai_combo = ttk.Combobox(form_frame, values=["Hoạt động", "Tạm nghỉ", "Đã nghỉ"], state="readonly", width=23)
        self.trangThai_combo.set("Hoạt động")
        self.trangThai_combo.grid(row=3, column=3, padx=5, pady=5, sticky="ew")
        # Hàng 4
        ttk.Label(form_frame, text="Chức Vụ:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.chucVu_entry = ttk.Entry(form_frame, width=25)
        self.chucVu_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Đơn Vị:").grid(row=4, column=2, padx=5, pady=5, sticky="w")
        self.donVi_entry = ttk.Entry(form_frame, width=25)
        self.donVi_entry.grid(row=4, column=3, padx=5, pady=5, sticky="ew")
        # Hàng 5
        ttk.Label(form_frame, text="Phân Quyền:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.phanQuyen_entry = ttk.Entry(form_frame, width=25)
        self.phanQuyen_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Label NS:").grid(row=5, column=2, padx=5, pady=5, sticky="w")
        self.labelNS_entry = ttk.Entry(form_frame, width=25)
        self.labelNS_entry.grid(row=5, column=3, padx=5, pady=5, sticky="ew")
        # Hàng 6 - Hình ảnh
        ttk.Label(form_frame, text="Hình Ảnh:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.hinhAnh_entry = ttk.Entry(form_frame, state="readonly")
        self.hinhAnh_entry.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        choose_image_button = ttk.Button(form_frame, text="Chọn", command=self.choose_image, width=6, bootstyle=INFO)
        choose_image_button.grid(row=6, column=3, padx=5, pady=5, sticky="e")

        # --- Nút bấm Lưu/Hủy ---
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=7, column=0, columnspan=4, pady=(20, 0))

        save_button = ttk.Button(button_frame, text="Lưu thông tin", command=self.on_save, bootstyle=SUCCESS)
        save_button.pack(side=tk.LEFT, padx=15)

        cancel_button = ttk.Button(button_frame, text="Hủy bỏ", command=self.on_cancel, bootstyle=SECONDARY)
        cancel_button.pack(side=tk.LEFT, padx=15)

        # Load dữ liệu nếu là chế độ sửa
        if self.driver_id:
            self._load_data()

        # Căn giữa dialog trên cửa sổ cha
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

        # Đặt focus vào ô đầu tiên (hoặc ô Tên nếu sửa)
        if self.driver_id:
            self.tenNV_entry.focus_set()
            self.tenNV_entry.select_range(0, tk.END)
        else:
            self.maNV_entry.focus_set()


        # Chờ dialog đóng
        self.wait_window(self)

    def _load_data(self):
        """Tải dữ liệu của lái xe vào form (chế độ sửa)."""
        if 'get_by_id' not in self.db:
            Messagebox.show_error("Lỗi cấu hình: Thiếu hàm 'get_by_id'.", parent=self)
            self.on_cancel()
            return

        driver_data = self.db['get_by_id'](self.driver_id)
        if not driver_data:
            Messagebox.show_error(f"Không tìm thấy dữ liệu cho lái xe ID {self.driver_id}.", parent=self)
            self.on_cancel()
            return

        # Điền dữ liệu vào form
        self.maNV_entry.insert(0, driver_data.get('maNhanVien', ''))
        self.maThe_entry.insert(0, driver_data.get('maThe', ''))
        self.tenNV_entry.insert(0, driver_data.get('tenNhanVien', ''))
        self.sdt_entry.insert(0, driver_data.get('soDienThoai', ''))
        ngay_sinh = driver_data.get('ngaySinh', '')
        self.ngaySinh_entry.entry.delete(0, tk.END) # Xóa giá trị cũ (nếu có)
        if ngay_sinh:
             try:
                 self.ngaySinh_entry.entry.insert(0, ngay_sinh)
             except Exception as e:
                 print(f"Lỗi load ngày sinh '{ngay_sinh}': {e}")

        self.gioiTinh_combo.set(driver_data.get('gioiTinh', ''))
        self.trangThai_combo.set(driver_data.get('trangThai', 'Hoạt động'))
        self.chucVu_entry.insert(0, driver_data.get('chucVu', ''))
        self.donVi_entry.insert(0, driver_data.get('donVi', ''))
        self.phanQuyen_entry.insert(0, driver_data.get('phanQuyen', ''))
        self.labelNS_entry.insert(0, driver_data.get('labelNhanSu', ''))
        hinh_anh_path = driver_data.get('hinhAnh', '')
        self.image_path_to_save = hinh_anh_path # Lưu đường dẫn ban đầu
        self.hinhAnh_entry.config(state="normal")
        self.hinhAnh_entry.delete(0, tk.END)
        self.hinhAnh_entry.insert(0, hinh_anh_path)
        self.hinhAnh_entry.config(state="readonly")

    def choose_image(self):
        """Mở hộp thoại chọn file ảnh."""
        filepath = filedialog.askopenfilename(
            title="Chọn ảnh lái xe",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")],
            parent=self # Đảm bảo dialog chọn file hiện trên dialog này
        )
        if filepath:
            filename = os.path.basename(filepath)
            # --- QUAN TRỌNG: Xử lý lưu trữ file ảnh thực tế ---
            # Ví dụ: Copy file vào thư mục 'images/drivers' và lưu tên file
            # image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images', 'drivers')
            # os.makedirs(image_dir, exist_ok=True)
            # try:
            #     import shutil
            #     new_filepath = os.path.join(image_dir, filename)
            #     shutil.copy2(filepath, new_filepath) # copy2 giữ metadata
            #     self.image_path_to_save = filename # Chỉ lưu tên file vào DB
            #     print(f"Đã copy ảnh vào: {new_filepath}")
            # except Exception as e:
            #     print(f"Lỗi copy file ảnh: {e}")
            #     Messagebox.show_error(f"Không thể lưu file ảnh: {e}", parent=self)
            #     return # Không cập nhật nếu không copy được
            # --- Kết thúc xử lý file ---

            # Tạm thời chỉ lưu tên file/đường dẫn gốc (cần chỉnh sửa logic lưu trữ)
            self.image_path_to_save = filename

            self.hinhAnh_entry.config(state="normal")
            self.hinhAnh_entry.delete(0, tk.END)
            self.hinhAnh_entry.insert(0, self.image_path_to_save)
            self.hinhAnh_entry.config(state="readonly")

    def on_save(self):
        """Xử lý khi nhấn nút Lưu."""
        # Thu thập dữ liệu
        data = {
            'maNhanVien': self.maNV_entry.get().strip() or None,
            'maThe': self.maThe_entry.get().strip(),
            'tenNhanVien': self.tenNV_entry.get().strip(),
            'soDienThoai': self.sdt_entry.get().strip() or None,
            'ngaySinh': self.ngaySinh_entry.entry.get().strip() or None,
            'gioiTinh': self.gioiTinh_combo.get() or None,
            'trangThai': self.trangThai_combo.get(),
            'chucVu': self.chucVu_entry.get().strip() or None,
            'donVi': self.donVi_entry.get().strip() or None,
            'phanQuyen': self.phanQuyen_entry.get().strip() or None,
            'labelNhanSu': self.labelNS_entry.get().strip() or None,
            'hinhAnh': self.image_path_to_save # Lấy đường dẫn đã lưu
        }

        # Validation cơ bản
        if not data['maThe'] or not data['tenNhanVien']:
            Messagebox.show_warning("Mã Thẻ và Tên Lái xe là bắt buộc.", "Thiếu thông tin", parent=self)
            return

        # Gọi hàm DB tương ứng
        if self.driver_id is None: # Chế độ Thêm mới
            if 'add' not in self.db:
                 Messagebox.show_error("Lỗi cấu hình: Thiếu hàm 'add'.", parent=self)
                 return
            success, message = self.db['add'](data)
        else: # Chế độ Cập nhật
            if 'update' not in self.db:
                 Messagebox.show_error("Lỗi cấu hình: Thiếu hàm 'update'.", parent=self)
                 return
            success, message = self.db['update'](self.driver_id, data)

        # Xử lý kết quả
        if success:
            self.success = True # Đánh dấu thành công
            # Không hiển thị messagebox thành công ở đây nữa, để AdminWindow hiển thị
            self.destroy() # Đóng dialog
        else:
            Messagebox.show_error(message, "Lỗi", parent=self) # Hiển thị lỗi trên dialog này

    def on_cancel(self):
        """Xử lý khi nhấn nút Cancel hoặc nút X."""
        self.success = False
        self.destroy()
# gui/driver_info_dialog.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import DateEntry
import tkinter as tk
from tkinter import filedialog
import os
import datetime
# --- THÊM IMPORT ---
import threading
from utils.rfid_reader import read_rfid_card_sync # Import hàm đồng bộ
# --- KẾT THÚC IMPORT ---

class DriverInfoDialog(ttk.Toplevel):
    """Popup Dialog để thêm hoặc sửa thông tin lái xe."""

    def __init__(self, parent, db_functions, driver_id=None):
        mode_title = "Sửa thông tin Lái xe" if driver_id else "Thêm Lái xe mới"
        super().__init__(master=parent, title=mode_title)
        self.parent = parent
        self.db = db_functions
        self.driver_id = driver_id
        self.success = False
        self.image_path_to_save = None
        self._rfid_reading_thread = None # Theo dõi luồng đọc RFID

        self.geometry("650x480") # Tăng nhẹ chiều cao cho nút đọc thẻ và status
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        # --- Hàng 0: Mã NV và Mã Thẻ ---
        ttk.Label(form_frame, text="Mã NV (*):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.maNV_entry = ttk.Entry(form_frame, width=20) # Giảm width một chút
        self.maNV_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(form_frame, text="Mã Thẻ (*):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        # Frame con cho Mã thẻ và nút Đọc
        maThe_frame = ttk.Frame(form_frame)
        maThe_frame.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        maThe_frame.columnconfigure(0, weight=1) # Cho Entry co giãn

        self.maThe_entry = ttk.Entry(maThe_frame, width=15) # Giảm width để chừa chỗ cho nút
        self.maThe_entry.grid(row=0, column=0, sticky="ew")
        # --- THÊM NÚT ĐỌC THẺ ---
        self.read_rfid_button = ttk.Button(maThe_frame, text="Đọc thẻ", command=self.start_read_rfid_thread, width=8, bootstyle="outline-info")
        self.read_rfid_button.grid(row=0, column=1, padx=(5,0))
        # --- KẾT THÚC THÊM NÚT ---

        # --- Các hàng còn lại (Giữ nguyên) ---
        # Hàng 1
        ttk.Label(form_frame, text="Tên Lái xe (*):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tenNV_entry = ttk.Entry(form_frame)
        self.tenNV_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        # Hàng 2
        ttk.Label(form_frame, text="Số ĐT:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sdt_entry = ttk.Entry(form_frame, width=25)
        self.sdt_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(form_frame, text="Ngày Sinh:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.ngaySinh_entry = DateEntry(form_frame, width=23, dateformat="%Y-%m-%d")
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

        # --- THÊM LABEL TRẠNG THÁI RFID ---
        self.rfid_status_label = ttk.Label(form_frame, text="", bootstyle="info", font="-size 9")
        self.rfid_status_label.grid(row=7, column=0, columnspan=4, pady=(5, 0), sticky="w")
        # --- KẾT THÚC THÊM LABEL ---

        # --- Nút bấm Lưu/Hủy ---
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=8, column=0, columnspan=4, pady=(15, 0)) # Dịch xuống 1 hàng

        save_button = ttk.Button(button_frame, text="Lưu thông tin", command=self.on_save, bootstyle=SUCCESS)
        save_button.pack(side=tk.LEFT, padx=15)

        cancel_button = ttk.Button(button_frame, text="Hủy bỏ", command=self.on_cancel, bootstyle=SECONDARY)
        cancel_button.pack(side=tk.LEFT, padx=15)

        # Load dữ liệu nếu là sửa
        if self.driver_id:
            self._load_data()

        # Căn giữa dialog... (Giữ nguyên)
        self.update_idletasks()
        parent_x = parent.winfo_rootx(); parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width(); parent_height = parent.winfo_height()
        dialog_width = self.winfo_width(); dialog_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        x = max(0, x); y = max(0, y)
        self.geometry(f"+{x}+{y}")

        if self.driver_id: self.tenNV_entry.focus_set(); self.tenNV_entry.select_range(0, tk.END)
        else: self.maNV_entry.focus_set()

        self.wait_window(self)

    def _load_data(self):
        # ... (Hàm này giữ nguyên) ...
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
        # ... (Hàm này giữ nguyên) ...
        filepath = filedialog.askopenfilename(
            title="Chọn ảnh lái xe",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All Files", "*.*")],
            parent=self
        )
        if filepath:
            filename = os.path.basename(filepath)
            # Cần xử lý lưu trữ file ảnh thực tế ở đây
            self.image_path_to_save = filename
            self.hinhAnh_entry.config(state="normal")
            self.hinhAnh_entry.delete(0, tk.END)
            self.hinhAnh_entry.insert(0, self.image_path_to_save)
            self.hinhAnh_entry.config(state="readonly")

    def on_save(self):
        # ... (Hàm này giữ nguyên) ...
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
            'hinhAnh': self.image_path_to_save
        }
        if not data['maThe'] or not data['tenNhanVien']:
            Messagebox.show_warning("Mã Thẻ và Tên Lái xe là bắt buộc.", "Thiếu thông tin", parent=self)
            return
        if self.driver_id is None:
            if 'add' not in self.db: Messagebox.show_error("Lỗi: Thiếu hàm 'add'.", parent=self); return
            success, message = self.db['add'](data)
        else:
            if 'update' not in self.db: Messagebox.show_error("Lỗi: Thiếu hàm 'update'.", parent=self); return
            success, message = self.db['update'](self.driver_id, data)
        if success:
            self.success = True
            self.destroy()
        else: Messagebox.show_error(message, "Lỗi", parent=self)


    def on_cancel(self):
        # ... (Hàm này giữ nguyên) ...
        # Đảm bảo dừng luồng đọc thẻ nếu đang chạy
        if self._rfid_reading_thread and self._rfid_reading_thread.is_alive():
             print("[RFID Dialog] Hủy bỏ - Cố gắng dừng luồng đọc thẻ (nếu có thể)")
             # Việc dừng hẳn 1 thread từ bên ngoài không an toàn và không được khuyến khích.
             # Cách tốt hơn là thread đó phải tự kiểm tra cờ dừng.
             # Ở đây ta chỉ đảm bảo dialog đóng.
        self.success = False
        self.destroy()

    # --- CÁC HÀM MỚI XỬ LÝ RFID ---
    def update_rfid_status(self, message, style="info"):
        """Cập nhật label trạng thái RFID (an toàn với thread)."""
        try:
            # Sử dụng after(0, ...) để đảm bảo lệnh chạy trên main thread của Tkinter
            self.after(0, lambda: self.rfid_status_label.config(text=message, bootstyle=style))
        except tk.TclError:
            # Widget đã bị hủy (ví dụ: dialog đóng trước khi update xong)
            pass

    def _rfid_read_thread_target(self):
        """Hàm mục tiêu cho luồng đọc RFID."""
        card_id, message = read_rfid_card_sync() # Gọi hàm đọc đồng bộ

        # Gửi kết quả về main thread để cập nhật GUI
        self.after(0, self._update_rfid_entry, card_id, message)

        # Đặt lại trạng thái nút đọc thẻ (trong main thread)
        self.after(0, lambda: self.read_rfid_button.config(state="normal", text="Đọc thẻ"))
        # Reset cờ thread
        self._rfid_reading_thread = None

    def _update_rfid_entry(self, card_id, message):
        """Cập nhật ô Mã Thẻ và label trạng thái (chạy trên main thread)."""
        if card_id:
            self.maThe_entry.delete(0, tk.END)
            self.maThe_entry.insert(0, card_id)
            self.update_rfid_status(message, style="success")
        else:
            # Không xóa ô mã thẻ nếu đọc lỗi, để người dùng tự nhập
            self.update_rfid_status(message, style="danger")
            # Có thể thêm messagebox báo lỗi nếu muốn
            # Messagebox.show_error(message, "Lỗi đọc RFID", parent=self)

    def start_read_rfid_thread(self):
        """Bắt đầu luồng đọc thẻ RFID."""
        # Kiểm tra xem có luồng nào đang chạy không
        if self._rfid_reading_thread and self._rfid_reading_thread.is_alive():
            print("[RFID Dialog] Luồng đọc thẻ đang chạy.")
            return

        # Cập nhật trạng thái và vô hiệu hóa nút
        self.update_rfid_status("Đang chờ thẻ...", style="info")
        self.read_rfid_button.config(state="disabled", text="Đang đọc...")

        # Tạo và bắt đầu luồng mới
        self._rfid_reading_thread = threading.Thread(target=self._rfid_read_thread_target, daemon=True)
        self._rfid_reading_thread.start()
    # --- KẾT THÚC CÁC HÀM RFID ---
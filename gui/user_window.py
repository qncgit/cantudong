# gui/user_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.session import get_current_username, clear_current_user
import time
# --- XÓA CÁC IMPORT LIÊN QUAN ĐỔI MK ---
# from database.db_manager import get_user_password_hash, update_user_password
# from models.user_model import verify_password
# --- KẾT THÚC XÓA IMPORT ---
import tkinter as tk

class UserWindow(ttk.Toplevel):
    def __init__(self, master, logout_callback):
        super().__init__(master=master, title="Giao diện Cân Tự động")
        self.geometry("800x480")
        self.logout_callback = logout_callback
        self.username = get_current_username()
        self._weight_reading_job = None

        self.protocol("WM_DELETE_WINDOW", self.handle_close)

        # ----- Header -----
        header_frame = ttk.Frame(self, padding=10, bootstyle=INFO)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))

        welcome_label = ttk.Label(header_frame, text=f"Nhân viên vận hành: {self.username}", font="-size 12 -weight bold")
        welcome_label.pack(side=LEFT, padx=10)

        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)

        # ----- Chỉ còn nội dung chính (Giao diện Cân) -----
        # --- KHÔNG DÙNG NOTEBOOK NỮA ---
        # self.notebook = ttk.Notebook(self)
        # self.notebook.pack(pady=10, padx=10, fill=BOTH, expand=YES)
        # --- KẾT THÚC KHÔNG DÙNG NOTEBOOK ---

        # --- Frame chứa giao diện cân ---
        weighing_frame = ttk.Frame(self, padding=10)
        # self.notebook.add(weighing_frame, text=' Giao diện Cân ') # Không cần dòng này
        weighing_frame.pack(pady=10, padx=10, fill=BOTH, expand=YES) # Pack frame cân vào window
        self.setup_weighing_tab(weighing_frame) # Thiết lập nội dung trong frame này

        # --- XÓA PHẦN TẠO TAB TÀI KHOẢN VÀ CÁC HÀM LIÊN QUAN ---
        # account_tab = ttk.Frame(self.notebook, padding=20)
        # self.notebook.add(account_tab, text=' Quản lý Tài khoản ')
        # self.setup_account_tab(account_tab)
        # def setup_account_tab(...): ...
        # def handle_change_password(...): ...
        # def show_password_status(...): ...
        # --- KẾT THÚC XÓA ---

        self.start_reading_weight()

    # ----- CÁC HÀM SETUP WEIGHING TAB VÀ LIÊN QUAN ĐẾN CÂN GIỮ NGUYÊN -----
    def setup_weighing_tab(self, parent_frame):
        """Thiết lập nội dung cho Tab Giao diện Cân."""
        parent_frame.columnconfigure(0, weight=2)
        parent_frame.columnconfigure(1, weight=1)

        scale_frame = ttk.Labelframe(parent_frame, text="Thông tin Cân", padding=15)
        scale_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scale_frame.columnconfigure(1, weight=1)

        weight_label = ttk.Label(scale_frame, text="Khối lượng hiện tại:", font="-size 14")
        weight_label.grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        self.weight_display = ttk.Label(scale_frame, text="--- Kg", font="-size 24 -weight bold", bootstyle=SUCCESS, anchor=tk.E, width=15)
        self.weight_display.grid(row=0, column=1, padx=5, pady=10, sticky=tk.E)

        driver_label = ttk.Label(scale_frame, text="Lái xe:")
        driver_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.driver_info_label = ttk.Label(scale_frame, text="Chưa xác định", bootstyle=SECONDARY)
        self.driver_info_label.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        vehicle_label = ttk.Label(scale_frame, text="Biển số xe:")
        vehicle_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.vehicle_info_label = ttk.Label(scale_frame, text="Chưa xác định", bootstyle=SECONDARY)
        self.vehicle_info_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        weigh_button = ttk.Button(scale_frame, text="Thực hiện Cân", command=self.perform_weighing, bootstyle=PRIMARY, width=20)
        weigh_button.grid(row=3, column=0, columnspan=2, pady=20)

        status_label = ttk.Label(scale_frame, text="Trạng thái:")
        status_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_indicator = ttk.Label(scale_frame, text="Đang khởi tạo...", bootstyle=WARNING)
        self.status_indicator.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        integration_frame = ttk.Labelframe(parent_frame, text="Camera & RFID", padding=15)
        integration_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        camera_placeholder = ttk.Label(integration_frame, text="(Khu vực hiển thị camera)")
        camera_placeholder.pack(pady=10)
        rfid_status_label = ttk.Label(integration_frame, text="Trạng thái RFID:")
        rfid_status_label.pack(pady=5)
        self.rfid_status = ttk.Label(integration_frame, text="Đang chờ thẻ...", bootstyle=WARNING)
        self.rfid_status.pack(pady=5)

        history_frame = ttk.Labelframe(parent_frame, text="Lịch sử Cân Gần Đây", padding=15)
        history_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        history_text = ttk.ScrolledText(history_frame, height=5, width=80, state=DISABLED) # Giảm chiều cao history
        history_text.pack(fill=BOTH, expand=YES)
        self.history_text_widget = history_text

        parent_frame.rowconfigure(0, weight=3)
        parent_frame.rowconfigure(1, weight=1)

    def start_reading_weight(self):
        if self._weight_reading_job is None and self.winfo_exists():
            print("Bắt đầu đọc dữ liệu cân (giả lập)...")
            self.show_status_message("Sẵn sàng", SUCCESS)
            self.update_weight_display()

    def update_weight_display(self):
        try:
            if not self.winfo_exists():
                 self._weight_reading_job = None
                 return

            import random
            current_weight = random.randint(500, 5000)
            self.weight_display.config(text=f"{current_weight} Kg")

            self._weight_reading_job = self.after(1000, self.update_weight_display)
        except tk.TclError:
             print("Cửa sổ User đã đóng, dừng cập nhật cân.")
             self._weight_reading_job = None
        except Exception as e:
            print(f"Lỗi khi cập nhật hiển thị cân: {e}")
            if self.winfo_exists():
                self.weight_display.config(text="Lỗi đọc", bootstyle=DANGER)
                self._weight_reading_job = self.after(5000, self.update_weight_display)
            else:
                 self._weight_reading_job = None

    def stop_reading_weight(self):
        if self._weight_reading_job:
            self.after_cancel(self._weight_reading_job)
            self._weight_reading_job = None
            print("Đã dừng đọc dữ liệu cân.")

    def perform_weighing(self):
        try:
            if not self.winfo_exists(): return
            self.show_status_message("Đang thực hiện cân...", WARNING)
            self.update()

            current_weight_text = self.weight_display.cget("text").replace(" Kg", "")
            driver_info = self.driver_info_label.cget("text")
            vehicle_info = self.vehicle_info_label.cget("text")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            try:
                weight = float(current_weight_text)
            except ValueError:
                self.show_status_message("Lỗi: Không thể đọc khối lượng.", DANGER)
                return

            if "Chưa xác định" in driver_info or "Chưa xác định" in vehicle_info:
                self.show_status_message("Chưa xác định Lái xe/Biển số.", WARNING)
                return

            print(f"[{timestamp}] Cân: {weight} Kg, Xe: {vehicle_info}, LX: {driver_info}, User: {self.username}")
            print("=> (Giả lập) Đã lưu bản ghi cân.")

            self.history_text_widget.configure(state=NORMAL)
            log_entry = f"[{timestamp}] - {weight} Kg - Xe: {vehicle_info} - Lái xe: {driver_info}\n"
            self.history_text_widget.insert(END, log_entry)
            self.history_text_widget.see(END)
            self.history_text_widget.configure(state=DISABLED)

            self.show_status_message("Cân thành công!", SUCCESS)

        except Exception as e:
            print(f"Lỗi khi thực hiện cân: {e}")
            if self.winfo_exists():
                self.show_status_message(f"Lỗi cân: {e}", DANGER)

    def show_status_message(self, message, style=DEFAULT):
        if self.winfo_exists():
            self.status_indicator.config(text=message, bootstyle=style)
            if style != DANGER:
                 self.after(5000, lambda: self.status_indicator.config(text="Sẵn sàng", bootstyle=SUCCESS) if self.winfo_exists() else None)
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----

    # ----- CÁC HÀM CÒN LẠI GIỮ NGUYÊN -----
    def handle_logout(self):
        self.stop_reading_weight()
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        print("Người dùng cố gắng đóng cửa sổ User bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout()
    # ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----
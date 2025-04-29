# gui/user_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from utils.session import get_current_username, clear_current_user
import time
# Import các thành phần cần thiết cho đổi mật khẩu
from database.db_manager import get_user_password_hash, update_user_password
from models.user_model import verify_password
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
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=X, side=TOP, pady=(0, 5))

        welcome_label = ttk.Label(header_frame, text=f"Nhân viên vận hành: {self.username}", font="-size 12 -weight bold")
        welcome_label.pack(side=LEFT, padx=10)

        logout_button = ttk.Button(header_frame, text="Đăng xuất", command=self.handle_logout, bootstyle=(SECONDARY, OUTLINE))
        logout_button.pack(side=RIGHT, padx=10)

        # ----- Tạo Notebook (Tabs) -----
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill=BOTH, expand=YES)

        # --- Tab 1: Giao diện cân ---
        weighing_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(weighing_tab, text=' Giao diện Cân ')
        self.setup_weighing_tab(weighing_tab) # Gọi hàm thiết lập tab cân

        # --- Tab 2: Tài khoản ---
        account_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(account_tab, text=' Quản lý Tài khoản ')
        self.setup_account_tab(account_tab) # Gọi hàm thiết lập tab tài khoản

        # Bắt đầu đọc cân sau khi giao diện được tạo
        self.start_reading_weight()

    def setup_weighing_tab(self, parent_frame):
        """Thiết lập nội dung cho Tab Giao diện Cân."""
        parent_frame.columnconfigure(0, weight=2) # Cột thông tin cân
        parent_frame.columnconfigure(1, weight=1) # Cột camera, rfid

        # --- Khu vực hiển thị thông tin cân ---
        scale_frame = ttk.Labelframe(parent_frame, text="Thông tin Cân", padding=15)
        scale_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        scale_frame.columnconfigure(1, weight=1)

        weight_label = ttk.Label(scale_frame, text="Khối lượng hiện tại:", font="-size 14")
        weight_label.grid(row=0, column=0, padx=5, pady=10, sticky=W)
        self.weight_display = ttk.Label(scale_frame, text="--- Kg", font="-size 24 -weight bold", bootstyle=SUCCESS, anchor=E, width=15)
        self.weight_display.grid(row=0, column=1, padx=5, pady=10, sticky=E)

        driver_label = ttk.Label(scale_frame, text="Lái xe:")
        driver_label.grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.driver_info_label = ttk.Label(scale_frame, text="Chưa xác định", bootstyle=SECONDARY)
        self.driver_info_label.grid(row=1, column=1, padx=5, pady=5, sticky=W)

        vehicle_label = ttk.Label(scale_frame, text="Biển số xe:")
        vehicle_label.grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.vehicle_info_label = ttk.Label(scale_frame, text="Chưa xác định", bootstyle=SECONDARY)
        self.vehicle_info_label.grid(row=2, column=1, padx=5, pady=5, sticky=W)

        weigh_button = ttk.Button(scale_frame, text="Thực hiện Cân", command=self.perform_weighing, bootstyle=PRIMARY, width=20)
        weigh_button.grid(row=3, column=0, columnspan=2, pady=20)

        status_label = ttk.Label(scale_frame, text="Trạng thái:")
        status_label.grid(row=4, column=0, padx=5, pady=5, sticky=W)
        self.status_indicator = ttk.Label(scale_frame, text="Đang khởi tạo...", bootstyle=WARNING) # Trạng thái ban đầu
        self.status_indicator.grid(row=4, column=1, padx=5, pady=5, sticky=W)

        # --- Khu vực Camera và RFID ---
        integration_frame = ttk.Labelframe(parent_frame, text="Camera & RFID", padding=15)
        integration_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        camera_placeholder = ttk.Label(integration_frame, text="(Khu vực hiển thị camera)")
        camera_placeholder.pack(pady=10)
        rfid_status_label = ttk.Label(integration_frame, text="Trạng thái RFID:")
        rfid_status_label.pack(pady=5)
        self.rfid_status = ttk.Label(integration_frame, text="Đang chờ thẻ...", bootstyle=WARNING)
        self.rfid_status.pack(pady=5)

        # --- Bảng lịch sử ---
        history_frame = ttk.Labelframe(parent_frame, text="Lịch sử Cân Gần Đây", padding=15)
        history_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        history_text = ttk.ScrolledText(history_frame, height=10, width=80, state=DISABLED)
        history_text.pack(fill=BOTH, expand=YES)
        self.history_text_widget = history_text

    # --- Các hàm setup_account_tab, handle_change_password, show_password_status ---
    # --- Copy y hệt từ AdminWindow hoặc ManagerWindow vào đây ---
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


    # --- Các hàm liên quan đến cân (start_reading_weight, update_weight_display, etc.) ---
    def start_reading_weight(self):
        """Bắt đầu quá trình đọc dữ liệu cân định kỳ (giả lập)."""
        # Chỉ bắt đầu nếu chưa chạy
        if self._weight_reading_job is None:
            print("Bắt đầu đọc dữ liệu cân (giả lập)...")
            self.update_weight_display() # Cập nhật lần đầu và lên lịch tiếp theo
            self.show_status_message("Sẵn sàng", SUCCESS) # Cập nhật trạng thái ban đầu

    def update_weight_display(self):
        """Cập nhật hiển thị khối lượng (giả lập)."""
        try:
            # --- ĐIỂM TÍCH HỢP 1: ĐỌC DỮ LIỆU TỪ ĐẦU CÂN ---
            import random
            current_weight = random.randint(500, 5000)
            self.weight_display.config(text=f"{current_weight} Kg")

            # Lập lịch cập nhật tiếp theo sau 1 giây
            self._weight_reading_job = self.after(1000, self.update_weight_display)
        except tk.TclError:
             # Lỗi này xảy ra nếu cửa sổ bị hủy trong khi self.after đang chờ
             print("Cửa sổ User đã đóng, dừng cập nhật cân.")
             self._weight_reading_job = None # Đảm bảo dừng hẳn
        except Exception as e:
            print(f"Lỗi khi cập nhật hiển thị cân: {e}")
            self.weight_display.config(text="Lỗi đọc", bootstyle=DANGER)
            # Cố gắng khởi động lại sau 5 giây nếu cửa sổ chưa bị hủy
            if self.winfo_exists(): # Kiểm tra xem widget còn tồn tại không
                 self._weight_reading_job = self.after(5000, self.update_weight_display)
            else:
                 self._weight_reading_job = None

    def stop_reading_weight(self):
        """Dừng quá trình đọc dữ liệu cân định kỳ."""
        if self._weight_reading_job:
            self.after_cancel(self._weight_reading_job)
            self._weight_reading_job = None
            print("Đã dừng đọc dữ liệu cân.")

    def perform_weighing(self):
        """Xử lý khi nhấn nút 'Thực hiện Cân'."""
        try:
            self.show_status_message("Đang thực hiện cân...", WARNING)
            self.update() # Cập nhật giao diện

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

            # --- ĐIỂM TÍCH HỢP 4: LƯU RECORD VÀO DATABASE ---
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
            self.show_status_message(f"Lỗi cân: {e}", DANGER)


    def show_status_message(self, message, style=DEFAULT):
        """Hiển thị thông báo trạng thái và đặt lại sau vài giây."""
        if self.winfo_exists(): # Kiểm tra widget còn tồn tại không
            self.status_indicator.config(text=message, bootstyle=style)
            # Đặt lại trạng thái sau 5 giây nếu không phải lỗi
            if style != DANGER:
                 self.after(5000, lambda: self.status_indicator.config(text="Sẵn sàng", bootstyle=SUCCESS) if self.winfo_exists() else None)

    def handle_logout(self):
        """Xử lý sự kiện nhấn nút Đăng xuất."""
        self.stop_reading_weight() # Dừng đọc cân trước khi đóng
        clear_current_user()
        self.destroy()
        if self.logout_callback:
            self.logout_callback()

    def handle_close(self):
        """Xử lý khi người dùng đóng cửa sổ bằng nút X."""
        print("Người dùng cố gắng đóng cửa sổ User bằng nút 'X'. Thực hiện đăng xuất.")
        self.handle_logout() # Hành động tương tự đăng xuất
# main.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Import các thành phần cần thiết
from database.db_manager import init_db
from gui.login import LoginWindow
from gui.admin_window import AdminWindow
from gui.manager_window import ManagerWindow
from gui.user_window import UserWindow
from utils.session import get_current_role, is_user_logged_in, clear_current_user
from models.user_model import ADMIN, MANAGER, USER # Import các hằng số role

class WeighingApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # Ẩn cửa sổ gốc ban đầu
        self.current_window = None # Để theo dõi cửa sổ con đang mở (Toplevel)

        # Khởi tạo CSDL và bảng nếu cần
        print("Kiểm tra và khởi tạo CSDL...")
        init_db()
        print("CSDL sẵn sàng.")

        # Hiển thị cửa sổ đăng nhập đầu tiên
        self.show_login_window()

    def show_login_window(self):
        """Hiển thị cửa sổ đăng nhập."""
        # Dọn dẹp cửa sổ cũ nếu có
        self.cleanup_current_window()
        clear_current_user() # Đảm bảo session sạch khi hiển thị login

        # Tạo cửa sổ đăng nhập như một Frame trong root hoặc Toplevel mới
        # Cách 1: Dùng Toplevel (độc lập hơn)
        login_toplevel = ttk.Toplevel(self.root)
        login_toplevel.protocol("WM_DELETE_WINDOW", self.quit_app) # Đóng app nếu đóng login
        self.current_window = login_toplevel # Theo dõi cửa sổ hiện tại
        LoginWindow(login_toplevel, self.handle_login_success)

        # Cách 2: Nhúng Frame vào root (ít dùng hơn khi có nhiều cửa sổ)
        # self.root.deiconify() # Hiện lại root nếu dùng cách này
        # self.current_frame = LoginWindow(self.root, self.handle_login_success)

    def handle_login_success(self):
        """Xử lý sau khi đăng nhập thành công."""
        # Đóng cửa sổ đăng nhập (nếu là Toplevel)
        if isinstance(self.current_window, ttk.Toplevel):
            self.current_window.destroy()
            self.current_window = None

        # Lấy vai trò từ session
        role = get_current_role()

        # Mở cửa sổ tương ứng với vai trò
        if role == ADMIN:
            self.show_admin_window()
        elif role == MANAGER:
            self.show_manager_window()
        elif role == USER:
            self.show_user_window()
        else:
            print(f"Lỗi: Vai trò không xác định '{role}' sau khi đăng nhập.")
            # Có thể hiển thị lại cửa sổ đăng nhập hoặc thông báo lỗi
            self.show_login_window()

    def show_admin_window(self):
        """Hiển thị cửa sổ Admin."""
        self.cleanup_current_window()
        self.current_window = AdminWindow(self.root, self.handle_logout)

    def show_manager_window(self):
        """Hiển thị cửa sổ Manager."""
        self.cleanup_current_window()
        self.current_window = ManagerWindow(self.root, self.handle_logout)

    def show_user_window(self):
        """Hiển thị cửa sổ User."""
        self.cleanup_current_window()
        self.current_window = UserWindow(self.root, self.handle_logout)

    def handle_logout(self):
        """Xử lý khi người dùng đăng xuất từ một cửa sổ chức năng."""
        # Cửa sổ chức năng đã tự đóng trong hàm handle_logout của nó
        self.current_window = None # Đặt lại cửa sổ hiện tại
        # Hiển thị lại cửa sổ đăng nhập
        self.show_login_window()

    def cleanup_current_window(self):
        """Đóng và dọn dẹp cửa sổ Toplevel hiện tại (nếu có)."""
        if self.current_window and isinstance(self.current_window, ttk.Toplevel):
            try:
                # Nếu cửa sổ có phương thức dọn dẹp riêng (như dừng thread)
                if hasattr(self.current_window, 'stop_reading_weight'):
                     self.current_window.stop_reading_weight()
                self.current_window.destroy()
            except:
                print(f"Lỗi khi đóng cửa sổ trước") # Cửa sổ có thể đã bị đóng
        self.current_window = None
        # Nếu dùng Frame trong root thì cần gọi destroy cho frame đó
        # if hasattr(self, 'current_frame') and self.current_frame:
        #    self.current_frame.destroy()
        #    self.current_frame = None

    def quit_app(self):
        """Thoát hoàn toàn ứng dụng."""
        print("Đóng ứng dụng.")
        # Đảm bảo cửa sổ hiện tại (nếu có) được đóng sạch sẽ
        self.cleanup_current_window()
        self.root.quit() # Dừng mainloop
        self.root.destroy() # Hủy cửa sổ gốc

if __name__ == "__main__":
    # Chọn một theme cho ttkbootstrap (ví dụ: litera, cosmo, flatly, journal, darkly, superhero, ...)
    # Tham khảo: https://ttkbootstrap.readthedocs.io/en/latest/themes/
    # root = ttk.Window(themename="superhero")
    root = ttk.Window(themename="cosmo")

    app = WeighingApp(root)
    root.mainloop()
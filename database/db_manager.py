# database/db_manager.py
import sqlite3
import os
import datetime # Cần cho xử lý timestamp nếu cần thiết
from models.user_model import hash_password, verify_password, ADMIN, MANAGER, USER
from utils.session import get_current_username

# Xác định đường dẫn tới file database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'weighing.db')

# ----- CÁC HÀM get_db_connection GIỮ NGUYÊN -----
def get_db_connection():
  """Tạo và trả về một kết nối đến CSDL SQLite."""
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  # Bật hỗ trợ khóa ngoại nếu cần
  # conn.execute("PRAGMA foreign_keys = ON")
  return conn
# ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----

# ----- SỬA HÀM init_db ĐỂ THÊM BẢNG nhanSu -----
def init_db():
  """Khởi tạo CSDL và các bảng nếu chưa tồn tại."""
  conn = get_db_connection()
  cursor = conn.cursor()

  # --- Tạo bảng users (Giữ nguyên logic kiểm tra và tạo) ---
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
  table_exists = cursor.fetchone()
  if not table_exists:
      print("Đang tạo bảng 'users'...")
      create_table_sql = f"""
          CREATE TABLE users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('{ADMIN}', '{MANAGER}', '{USER}'))
          );
      """
      cursor.execute(create_table_sql)
      # Thêm user mẫu... (code giữ nguyên)
      print("Đang thêm các tài khoản users mẫu...")
      default_users = [
          ('admin', '123456', ADMIN),
          ('manager', '123456', MANAGER),
          ('user', '123456', USER)
      ]
      for username, plain_password, role in default_users:
          hashed_pass = hash_password(plain_password)
          if hashed_pass:
              try:
                  cursor.execute(
                      "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_pass, role)
                  )
                  # Bỏ print hash chi tiết ở đây
              except sqlite3.IntegrityError: pass # Bỏ qua nếu đã tồn tại
              except Exception as e: print(f"Lỗi thêm user {username}: {e}")
          else: print(f"Lỗi hash mật khẩu user {username}.")
      conn.commit()
      print("Tạo bảng 'users' và thêm tài khoản mẫu thành công.")
  else:
      print("Bảng 'users' đã tồn tại.")
      # Kiểm tra tài khoản mẫu có thể bỏ qua ở đây nếu không thực sự cần thiết mỗi lần chạy

  # --- Tạo bảng nhanSu ---
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nhanSu';")
  table_exists = cursor.fetchone()
  if not table_exists:
      print("Đang tạo bảng 'nhanSu'...")
      # Lưu ý kiểu dữ liệu TEXT cho các trường varchar, date, timestamp
      # Thêm NOT NULL cho các trường quan trọng
      cursor.execute('''
          CREATE TABLE nhanSu (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hinhAnh TEXT,                     -- Đường dẫn hoặc tên file ảnh
              trangThai TEXT DEFAULT 'Hoạt động', -- Trạng thái mặc định
              maNhanVien TEXT UNIQUE,           -- Mã nhân viên, nên là unique
              phanQuyen TEXT,                   -- Phân quyền riêng cho nhân sự?
              maThe TEXT UNIQUE NOT NULL,       -- Mã thẻ RFID, bắt buộc và unique
              tenNhanVien TEXT NOT NULL,        -- Tên nhân viên, bắt buộc
              soDienThoai TEXT,
              ngaySinh TEXT,                    -- Lưu dạng YYYY-MM-DD
              gioiTinh TEXT,
              chucVu TEXT,
              donVi TEXT,
              labelNhanSu TEXT,                 -- Label bổ sung
              thoiGian DATETIME DEFAULT CURRENT_TIMESTAMP -- Thời gian tạo/cập nhật cuối
          );
      ''')
      # Thêm các index để tăng tốc độ tìm kiếm/kiểm tra unique
      cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_nhanSu_maThe ON nhanSu(maThe);")
      cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_nhanSu_maNhanVien ON nhanSu(maNhanVien);")
      conn.commit()
      print("Tạo bảng 'nhanSu' thành công.")
  else:
      print("Bảng 'nhanSu' đã tồn tại.")
  # --- Kết thúc tạo bảng nhanSu ---

  conn.close()
# ----- KẾT THÚC SỬA HÀM init_db -----

# ----- CÁC HÀM verify_user, get_user_password_hash, set_user_password_by_admin (Giữ nguyên) -----
def verify_user(username, password):
  """
  Kiểm tra thông tin đăng nhập của người dùng.
  Args:
      username (str): Tên đăng nhập.
      password (str): Mật khẩu (chưa băm).
  Returns:
      tuple(str, str) | None: Trả về (username, role) nếu hợp lệ, None nếu không.
  """
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
  user_record = cursor.fetchone()
  conn.close()

  if user_record:
      stored_hash = user_record['password']
      role = user_record['role']
      # print(f"Attempting login for '{username}'. Stored hash: {stored_hash[:10]}...") # Debug
      # Gọi hàm verify_password từ user_model để so sánh hash
      if verify_password(stored_hash, password):
          # print(f"Xác thực thành công cho '{username}'.") # Giảm bớt log không cần thiết
          return user_record['username'], role
      else:
          print(f"Xác thực thất bại cho '{username}': Mật khẩu không khớp.")
  else:
      print(f"Xác thực thất bại: Không tìm thấy người dùng '{username}'.")

  return None

def get_user_password_hash(username):
    """Lấy hash mật khẩu hiện tại của người dùng."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    conn.close()
    if record:
        # print(f"Hash lấy từ DB cho '{username}': {record['password'][:10]}...") # Debug
        return record['password']
    # print(f"Không tìm thấy hash cho '{username}' trong DB.") # Debug
    return None

def set_user_password_by_admin(username, new_plain_password):
    """
    Đặt mật khẩu mới cho người dùng (bởi Admin).
    Hàm này KHÔNG kiểm tra mật khẩu cũ.
    Args:
        username (str): Tên người dùng cần đặt mật khẩu.
        new_plain_password (str): Mật khẩu mới do Admin nhập (chưa băm).
    Returns:
        tuple(bool, str): (True/False, message)
    """
    if not new_plain_password:
        msg = "Lỗi: Mật khẩu mới không được để trống."
        print(msg)
        return False, msg

    new_hashed_password = hash_password(new_plain_password)
    if not new_hashed_password:
        msg = f"Lỗi: Không thể băm mật khẩu mới cho {username}."
        print(msg)
        return False, msg

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
        conn.commit()
        if cursor.rowcount > 0:
            msg = f"Đã đặt mật khẩu mới cho người dùng '{username}' thành công."
            print(msg)
            return True, msg
        else:
            msg = f"Không tìm thấy người dùng '{username}' để đặt mật khẩu."
            print(msg)
            return False, msg
    except Exception as e:
        error_msg = f"Lỗi CSDL khi đặt mật khẩu cho '{username}': {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()
# ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----


# ----- CÁC HÀM QUẢN LÝ USER add_user, get_all_users, delete_user (Giữ nguyên) -----
def add_user(username, plain_password, role):
    """Thêm người dùng mới vào CSDL."""
    if role not in [ADMIN, MANAGER, USER]: # Đảm bảo vai trò hợp lệ
        msg = f"Lỗi: Vai trò '{role}' không hợp lệ."
        print(msg)
        return False, msg # Trả về thêm thông báo lỗi

    hashed_pass = hash_password(plain_password)
    if not hashed_pass:
        msg = "Lỗi: Không thể băm mật khẩu."
        print(msg)
        return False, msg

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed_pass, role))
        conn.commit()
        msg = f"Đã thêm người dùng '{username}' thành công."
        # print(msg) # Giảm log
        return True, msg
    except sqlite3.IntegrityError:
        msg = f"Lỗi: Tên đăng nhập '{username}' đã tồn tại."
        print(msg)
        return False, msg
    except Exception as e:
        error_msg = f"Lỗi CSDL khi thêm người dùng: {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()

def get_all_users():
    """Lấy danh sách tất cả người dùng (không bao gồm mật khẩu)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users ORDER BY role, username")
    users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in users]

def delete_user(username):
    """Xóa người dùng khỏi CSDL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_admin = get_current_username()
        if username == current_admin:
             msg = "Lỗi: Admin không thể tự xóa chính mình."
             print(msg)
             return False, msg

        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        if cursor.rowcount > 0:
            msg = f"Đã xóa người dùng '{username}'."
            print(msg)
            return True, msg
        else:
            msg = f"Không tìm thấy người dùng '{username}' để xóa."
            print(msg)
            return False, msg
    except Exception as e:
        error_msg = f"Lỗi CSDL khi xóa người dùng '{username}': {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()
# ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----

# ----- HÀM QUẢN LÝ TÀI KHOẢN ADMIN update_user_password (Giữ nguyên) -----
def update_user_password(username, new_plain_password):
    """
    Cập nhật mật khẩu mới cho người dùng (chỉ dùng cho Admin đổi MK của mình).
    Hàm này kiểm tra mật khẩu cũ (được thực hiện ở GUI).
    Args:
        username (str): Tên người dùng cần cập nhật.
        new_plain_password (str): Mật khẩu mới dạng thô.
    Returns:
        bool: True nếu cập nhật thành công, False nếu thất bại.
    """
    new_hashed_password = hash_password(new_plain_password)
    if not new_hashed_password:
        print(f"Lỗi: Không thể băm mật khẩu mới cho {username}.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
        conn.commit()
        if cursor.rowcount > 0:
            # print(f"Đã cập nhật mật khẩu cho người dùng '{username}' thành công.") # Giảm log
            return True
        else:
            print(f"Lỗi: Không tìm thấy người dùng '{username}' để cập nhật mật khẩu.")
            return False
    except Exception as e:
        print(f"Lỗi CSDL khi cập nhật mật khẩu cho '{username}': {e}")
        return False
    finally:
        conn.close()
# ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----


# ----- THÊM CÁC HÀM MỚI CHO QUẢN LÝ NHÂN SỰ (nhanSu table) -----
def add_nhan_su(data):
    """
    Thêm một nhân sự mới vào CSDL.
    Args:
        data (dict): Dictionary chứa thông tin nhân sự, key là tên cột.
                     Các key bắt buộc tối thiểu: 'maThe', 'tenNhanVien'.
                     Các key tùy chọn: 'hinhAnh', 'trangThai', 'maNhanVien', 'phanQuyen',
                                     'soDienThoai', 'ngaySinh', 'gioiTinh', 'chucVu',
                                     'donVi', 'labelNhanSu'.
                     Trường 'thoiGian' sẽ tự động được thêm.
    Returns:
        tuple(bool, str): (True/False, message)
    """
    # Xác định các cột hợp lệ trong bảng nhanSu (trừ id và thoiGian tự động)
    valid_columns = ['hinhAnh', 'trangThai', 'maNhanVien', 'phanQuyen', 'maThe',
                     'tenNhanVien', 'soDienThoai', 'ngaySinh', 'gioiTinh',
                     'chucVu', 'donVi', 'labelNhanSu']
    # Lọc dữ liệu đầu vào chỉ lấy các cột hợp lệ
    filtered_data = {k: v for k, v in data.items() if k in valid_columns and v is not None and v != ''}

    # Kiểm tra các trường bắt buộc
    if not filtered_data.get('maThe') or not filtered_data.get('tenNhanVien'):
        return False, "Lỗi: Mã thẻ và Tên nhân viên là bắt buộc."

    # Chuẩn bị câu lệnh SQL
    columns = ', '.join(filtered_data.keys())
    placeholders = ', '.join('?' * len(filtered_data))
    sql = f'INSERT INTO nhanSu ({columns}) VALUES ({placeholders})'
    values = tuple(filtered_data.values())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        msg = f"Đã thêm nhân sự '{filtered_data.get('tenNhanVien', '')}' thành công."
        # print(msg) # Giảm log
        return True, msg
    except sqlite3.IntegrityError as e:
        error_str = str(e).lower()
        if 'unique constraint failed: nhansu.mathe' in error_str:
             msg = f"Lỗi: Mã thẻ '{filtered_data.get('maThe', '')}' đã tồn tại."
        elif 'unique constraint failed: nhansu.manhanvien' in error_str and filtered_data.get('maNhanVien'):
             msg = f"Lỗi: Mã nhân viên '{filtered_data.get('maNhanVien', '')}' đã tồn tại."
        else:
             msg = f"Lỗi CSDL (Integrity): {e}"
        print(msg)
        return False, msg
    except Exception as e:
        error_msg = f"Lỗi CSDL khi thêm nhân sự: {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()

def get_all_nhan_su():
    """Lấy danh sách tất cả nhân sự (một số cột chính)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Chọn các cột cần thiết cho Treeview
    cursor.execute("SELECT id, maNhanVien, maThe, tenNhanVien, trangThai, chucVu, donVi FROM nhanSu ORDER BY tenNhanVien")
    nhan_su_list = cursor.fetchall()
    conn.close()
    return [dict(ns) for ns in nhan_su_list]

def get_nhan_su_by_id(nhan_su_id):
    """Lấy thông tin chi tiết của một nhân sự bằng ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nhanSu WHERE id = ?", (nhan_su_id,))
    nhan_su = cursor.fetchone()
    conn.close()
    if nhan_su:
        return dict(nhan_su)
    return None

def update_nhan_su(nhan_su_id, data):
    """
    Cập nhật thông tin nhân sự.
    Args:
        nhan_su_id (int): ID của nhân sự cần cập nhật.
        data (dict): Dictionary chứa thông tin cần cập nhật.
    Returns:
        tuple(bool, str): (True/False, message)
    """
    # Xác định các cột hợp lệ
    valid_columns = ['hinhAnh', 'trangThai', 'maNhanVien', 'phanQuyen', 'maThe',
                     'tenNhanVien', 'soDienThoai', 'ngaySinh', 'gioiTinh',
                     'chucVu', 'donVi', 'labelNhanSu']
    # Lọc dữ liệu cập nhật, cho phép giá trị rỗng để xóa thông tin
    update_data = {k: v for k, v in data.items() if k in valid_columns}

    if not update_data:
        return False, "Không có dữ liệu hợp lệ để cập nhật."

    # Kiểm tra các trường bắt buộc không bị xóa rỗng
    if update_data.get('maThe') == '':
        return False, "Lỗi: Mã thẻ không được để trống."
    if update_data.get('tenNhanVien') == '':
         return False, "Lỗi: Tên nhân viên không được để trống."

    # Thêm cập nhật thời gian
    update_data['thoiGian'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Tạo phần SET của câu lệnh SQL
    set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
    sql = f"UPDATE nhanSu SET {set_clause} WHERE id = ?"
    # Thêm nhan_su_id vào cuối tuple values
    values = tuple(update_data.values()) + (nhan_su_id,)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        if cursor.rowcount > 0:
            msg = f"Cập nhật thông tin nhân sự ID {nhan_su_id} thành công."
            # print(msg) # Giảm log
            return True, msg
        else:
            # Trường hợp ID không tồn tại
            msg = f"Không tìm thấy nhân sự với ID {nhan_su_id} để cập nhật."
            print(msg)
            return False, msg
    except sqlite3.IntegrityError as e:
        error_str = str(e).lower()
        if 'unique constraint failed: nhansu.mathe' in error_str:
             msg = f"Lỗi: Mã thẻ '{update_data.get('maThe', '')}' đã tồn tại cho nhân sự khác."
        elif 'unique constraint failed: nhansu.manhanvien' in error_str and update_data.get('maNhanVien'):
             msg = f"Lỗi: Mã nhân viên '{update_data.get('maNhanVien', '')}' đã tồn tại cho nhân sự khác."
        else:
             msg = f"Lỗi CSDL (Integrity): {e}"
        print(msg)
        return False, msg
    except Exception as e:
        error_msg = f"Lỗi CSDL khi cập nhật nhân sự: {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()

def delete_nhan_su(nhan_su_id):
    """Xóa nhân sự khỏi CSDL bằng ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM nhanSu WHERE id = ?", (nhan_su_id,))
        conn.commit()
        if cursor.rowcount > 0:
            msg = f"Đã xóa nhân sự ID {nhan_su_id}."
            print(msg)
            return True, msg
        else:
            msg = f"Không tìm thấy nhân sự ID {nhan_su_id} để xóa."
            print(msg)
            return False, msg
    except Exception as e:
        # Xử lý lỗi khóa ngoại nếu có bảng khác tham chiếu đến nhanSu
        error_msg = f"Lỗi CSDL khi xóa nhân sự ID {nhan_su_id}: {e}"
        print(error_msg)
        return False, error_msg
    finally:
        conn.close()
# ----- KẾT THÚC CÁC HÀM QUẢN LÝ NHÂN SỰ -----
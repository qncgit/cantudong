# database/db_manager.py
import sqlite3
import os
from models.user_model import hash_password, verify_password, ADMIN, MANAGER, USER

# Xác định đường dẫn tới file database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'weighing.db')

def get_db_connection():
  """Tạo và trả về một kết nối đến CSDL SQLite."""
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn

def init_db():
  """Khởi tạo CSDL và bảng users nếu chưa tồn tại. Thêm tài khoản mẫu."""
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
  table_exists = cursor.fetchone()

  if not table_exists:
      print("Đang tạo bảng 'users'...")
      # ---- SỬA ĐỔI Ở ĐÂY ----
      # Sử dụng f-string để nhúng trực tiếp các giá trị role vào câu lệnh CREATE
      # Lưu ý dấu nháy đơn bao quanh các giá trị chuỗi trong SQL
      create_table_sql = f"""
          CREATE TABLE users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('{ADMIN}', '{MANAGER}', '{USER}'))
          );
      """
      # Thực thi câu lệnh CREATE TABLE đã được định dạng
      cursor.execute(create_table_sql)
      # ---- KẾT THÚC SỬA ĐỔI ----

      print("Đang thêm các tài khoản mẫu (mật khẩu: 123456)...")
      default_users = [
          ('admin', '123456', ADMIN),
          ('manager', '123456', MANAGER),
          ('user', '123456', USER)
      ]
      for username, plain_password, role in default_users:
          hashed_pass = hash_password(plain_password)
          if hashed_pass:
              try:
                  # Câu lệnh INSERT vẫn dùng placeholder bình thường
                  cursor.execute(
                      "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_pass, role)
                  )
                  print(f"Đã thêm tài khoản: {username} (Hash: {hashed_pass[:10]}...)")
              except sqlite3.IntegrityError:
                  print(f"Tài khoản '{username}' đã tồn tại.")
              except Exception as e:
                  print(f"Lỗi khi thêm tài khoản {username}: {e}")
          else:
              print(f"Lỗi: Không thể băm mật khẩu cho tài khoản {username}.")

      conn.commit()
      print("Khởi tạo CSDL và thêm tài khoản mẫu thành công.")
  else:
      print("Bảng 'users' đã tồn tại.")
      # Optional: Kiểm tra/thêm lại user mẫu nếu cần
      # ...

  conn.close()


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
          print(f"Xác thực thành công cho '{username}'.")
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

def update_user_password(username, new_plain_password):
    """
    Cập nhật mật khẩu mới cho người dùng (sau khi đã băm).
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
            print(f"Đã cập nhật mật khẩu cho người dùng '{username}' thành công.")
            return True
        else:
            # Điều này không nên xảy ra nếu username được lấy từ session hợp lệ
            print(f"Lỗi: Không tìm thấy người dùng '{username}' để cập nhật mật khẩu (dữ liệu không nhất quán?).")
            return False
    except Exception as e:
        print(f"Lỗi CSDL khi cập nhật mật khẩu cho '{username}': {e}")
        return False
    finally:
        conn.close()

# --- Các hàm CRUD khác cho User (giữ nguyên) ---
def add_user(username, plain_password, role):
    # ... (giữ nguyên code)
    pass

def get_all_users():
    # ... (giữ nguyên code)
    pass

def delete_user(username):
    # ... (giữ nguyên code)
    pass
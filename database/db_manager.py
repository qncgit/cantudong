# database/db_manager.py
import sqlite3
import os
import datetime # Cần cho xử lý timestamp nếu cần thiết
from models.user_model import hash_password, verify_password, ADMIN, MANAGER, USER
from utils.session import get_current_username

# Xác định đường dẫn tới file database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'weighing.db')

# ----- get_db_connection, init_db (Giữ nguyên) -----
def get_db_connection():
  """Tạo và trả về một kết nối đến CSDL SQLite."""
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  # conn.execute("PRAGMA foreign_keys = ON")
  return conn

def init_db():
  """Khởi tạo CSDL và các bảng nếu chưa tồn tại."""
  conn = get_db_connection()
  cursor = conn.cursor()

  # --- Tạo bảng users (Giữ nguyên) ---
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
              except sqlite3.IntegrityError: pass
              except Exception as e: print(f"Lỗi thêm user {username}: {e}")
          else: print(f"Lỗi hash mật khẩu user {username}.")
      conn.commit()
      print("Tạo bảng 'users' và thêm tài khoản mẫu thành công.")
  else:
      print("Bảng 'users' đã tồn tại.")

  # --- Tạo bảng nhanSu (Giữ nguyên) ---
  cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nhanSu';")
  table_exists = cursor.fetchone()
  if not table_exists:
      print("Đang tạo bảng 'nhanSu'...")
      cursor.execute('''
          CREATE TABLE nhanSu (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              hinhAnh TEXT,
              trangThai TEXT DEFAULT 'Hoạt động',
              maNhanVien TEXT UNIQUE,
              phanQuyen TEXT,
              maThe TEXT UNIQUE NOT NULL,
              tenNhanVien TEXT NOT NULL,
              soDienThoai TEXT,
              ngaySinh TEXT,
              gioiTinh TEXT,
              chucVu TEXT,
              donVi TEXT,
              labelNhanSu TEXT,
              thoiGian DATETIME DEFAULT CURRENT_TIMESTAMP
          );
      ''')
      cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_nhanSu_maThe ON nhanSu(maThe);")
      cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_nhanSu_maNhanVien ON nhanSu(maNhanVien);")
      conn.commit()
      print("Tạo bảng 'nhanSu' thành công.")
  else:
      print("Bảng 'nhanSu' đã tồn tại.")

  conn.close()
# ----- KẾT THÚC init_db -----


# ----- CÁC HÀM verify_user, get_user_password_hash, set_user_password_by_admin (Giữ nguyên) -----
def verify_user(username, password):
  """
  Kiểm tra thông tin đăng nhập của người dùng.
  """
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
  user_record = cursor.fetchone()
  conn.close()
  if user_record:
      stored_hash = user_record['password']
      role = user_record['role']
      if verify_password(stored_hash, password):
          return user_record['username'], role
      else: print(f"Xác thực thất bại cho '{username}': Mật khẩu không khớp.")
  else: print(f"Xác thực thất bại: Không tìm thấy người dùng '{username}'.")
  return None

def get_user_password_hash(username):
    """Lấy hash mật khẩu hiện tại của người dùng."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    record = cursor.fetchone()
    conn.close()
    return record['password'] if record else None

def set_user_password_by_admin(username, new_plain_password):
    """
    Đặt mật khẩu mới cho người dùng (bởi Admin).
    """
    if not new_plain_password: return False, "Lỗi: Mật khẩu mới không được để trống."
    new_hashed_password = hash_password(new_plain_password)
    if not new_hashed_password: return False, f"Lỗi: Không thể băm mật khẩu mới cho {username}."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
        conn.commit()
        if cursor.rowcount > 0: return True, f"Đã đặt mật khẩu mới cho '{username}'."
        else: return False, f"Không tìm thấy người dùng '{username}'."
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()
# ----- KẾT THÚC PHẦN GIỮ NGUYÊN -----


# ----- HÀM add_user (Giữ nguyên logic, chỉ cần dùng khi add mới) -----
def add_user(username, plain_password, role):
    """Thêm người dùng mới vào CSDL."""
    if role not in [ADMIN, MANAGER, USER]: return False, f"Lỗi: Vai trò '{role}' không hợp lệ."
    hashed_pass = hash_password(plain_password)
    if not hashed_pass: return False, "Lỗi: Không thể băm mật khẩu."
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (username, hashed_pass, role))
        conn.commit()
        return True, f"Đã thêm người dùng '{username}'."
    except sqlite3.IntegrityError: return False, f"Lỗi: Tên đăng nhập '{username}' đã tồn tại."
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()
# ----- KẾT THÚC HÀM add_user -----


# ----- HÀM get_all_users (Giữ nguyên) -----
def get_all_users():
    """Lấy danh sách tất cả người dùng (không bao gồm mật khẩu)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users ORDER BY role, username")
    users = cursor.fetchall()
    conn.close()
    return [dict(user) for user in users]
# ----- KẾT THÚC HÀM get_all_users -----

# ----- THÊM HÀM get_user_by_id -----
def get_user_by_id(user_id):
    """Lấy thông tin user (trừ password) bằng ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None
# ----- KẾT THÚC THÊM HÀM -----

# ----- THÊM HÀM update_user_info -----
def update_user_info(user_id, username, role):
    """Cập nhật username và role cho user bằng ID (Admin)."""
    if role not in [ADMIN, MANAGER, USER]: return False, f"Lỗi: Vai trò '{role}' không hợp lệ."
    if not username: return False, "Lỗi: Tên đăng nhập không được để trống."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET username = ?, role = ? WHERE id = ?", (username, role, user_id))
        conn.commit()
        if cursor.rowcount > 0: return True, f"Cập nhật thông tin user ID {user_id} thành công."
        else: return False, f"Không tìm thấy user ID {user_id} để cập nhật."
    except sqlite3.IntegrityError: return False, f"Lỗi: Tên đăng nhập '{username}' đã tồn tại."
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()
# ----- KẾT THÚC THÊM HÀM -----


# ----- HÀM delete_user (Giữ nguyên) -----
def delete_user(username):
    """Xóa người dùng khỏi CSDL."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_admin = get_current_username()
        if username == current_admin: return False, "Lỗi: Admin không thể tự xóa chính mình."
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        if cursor.rowcount > 0: return True, f"Đã xóa người dùng '{username}'."
        else: return False, f"Không tìm thấy người dùng '{username}'."
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()
# ----- KẾT THÚC HÀM delete_user -----


# ----- HÀM update_user_password (Giữ nguyên - cho Admin đổi MK của mình) -----
def update_user_password(username, new_plain_password):
    """Cập nhật mật khẩu mới cho chính Admin."""
    new_hashed_password = hash_password(new_plain_password)
    if not new_hashed_password: return False # Lỗi băm đã được print
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hashed_password, username))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Lỗi CSDL khi cập nhật mật khẩu cho '{username}': {e}")
        return False
    finally: conn.close()
# ----- KẾT THÚC HÀM update_user_password -----


# ----- CÁC HÀM QUẢN LÝ NHÂN SỰ (nhanSu table) GIỮ NGUYÊN -----
# add_nhan_su, get_all_nhan_su, get_nhan_su_by_id, update_nhan_su, delete_nhan_su
def add_nhan_su(data):
    """
    Thêm một nhân sự mới vào CSDL.
    """
    valid_columns = ['hinhAnh', 'trangThai', 'maNhanVien', 'phanQuyen', 'maThe',
                     'tenNhanVien', 'soDienThoai', 'ngaySinh', 'gioiTinh',
                     'chucVu', 'donVi', 'labelNhanSu']
    filtered_data = {k: v for k, v in data.items() if k in valid_columns and v is not None and v != ''}
    if not filtered_data.get('maThe') or not filtered_data.get('tenNhanVien'):
        return False, "Lỗi: Mã thẻ và Tên nhân viên là bắt buộc."
    columns = ', '.join(filtered_data.keys())
    placeholders = ', '.join('?' * len(filtered_data))
    sql = f'INSERT INTO nhanSu ({columns}) VALUES ({placeholders})'
    values = tuple(filtered_data.values())
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        return True, f"Đã thêm nhân sự '{filtered_data.get('tenNhanVien', '')}'."
    except sqlite3.IntegrityError as e:
        error_str = str(e).lower()
        if 'unique constraint failed: nhansu.mathe' in error_str: msg = f"Lỗi: Mã thẻ '{filtered_data.get('maThe', '')}' đã tồn tại."
        elif 'unique constraint failed: nhansu.manhanvien' in error_str and filtered_data.get('maNhanVien'): msg = f"Lỗi: Mã NV '{filtered_data.get('maNhanVien', '')}' đã tồn tại."
        else: msg = f"Lỗi CSDL (Integrity): {e}"
        print(msg)
        return False, msg
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()

def get_all_nhan_su():
    """Lấy danh sách tất cả nhân sự (một số cột chính)."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
    return dict(nhan_su) if nhan_su else None

def update_nhan_su(nhan_su_id, data):
    """
    Cập nhật thông tin nhân sự.
    """
    valid_columns = ['hinhAnh', 'trangThai', 'maNhanVien', 'phanQuyen', 'maThe',
                     'tenNhanVien', 'soDienThoai', 'ngaySinh', 'gioiTinh',
                     'chucVu', 'donVi', 'labelNhanSu']
    update_data = {k: v for k, v in data.items() if k in valid_columns}
    if not update_data: return False, "Không có dữ liệu hợp lệ để cập nhật."
    if update_data.get('maThe') == '': return False, "Lỗi: Mã thẻ không được để trống."
    if update_data.get('tenNhanVien') == '': return False, "Lỗi: Tên nhân viên không được để trống."
    update_data['thoiGian'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
    sql = f"UPDATE nhanSu SET {set_clause} WHERE id = ?"
    values = tuple(update_data.values()) + (nhan_su_id,)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, values)
        conn.commit()
        if cursor.rowcount > 0: return True, f"Cập nhật nhân sự ID {nhan_su_id} thành công."
        else: return False, f"Không tìm thấy nhân sự ID {nhan_su_id}."
    except sqlite3.IntegrityError as e:
        error_str = str(e).lower()
        if 'unique constraint failed: nhansu.mathe' in error_str: msg = f"Lỗi: Mã thẻ '{update_data.get('maThe', '')}' đã tồn tại."
        elif 'unique constraint failed: nhansu.manhanvien' in error_str and update_data.get('maNhanVien'): msg = f"Lỗi: Mã NV '{update_data.get('maNhanVien', '')}' đã tồn tại."
        else: msg = f"Lỗi CSDL (Integrity): {e}"
        print(msg)
        return False, msg
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()

def delete_nhan_su(nhan_su_id):
    """Xóa nhân sự khỏi CSDL bằng ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM nhanSu WHERE id = ?", (nhan_su_id,))
        conn.commit()
        if cursor.rowcount > 0: return True, f"Đã xóa nhân sự ID {nhan_su_id}."
        else: return False, f"Không tìm thấy nhân sự ID {nhan_su_id}."
    except Exception as e: return False, f"Lỗi CSDL: {e}"
    finally: conn.close()
# ----- KẾT THÚC CÁC HÀM QUẢN LÝ NHÂN SỰ -----
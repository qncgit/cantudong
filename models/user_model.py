# models/user_model.py
import hashlib

# Định nghĩa các hằng số cho vai trò người dùng
ADMIN = 'Admin'
MANAGER = 'Manager'
USER = 'User'

ROLES = [ADMIN, MANAGER, USER]

def hash_password(password):
  """
  Băm mật khẩu sử dụng SHA-256.
  Args:
      password (str): Mật khẩu dạng chuỗi thô.
  Returns:
      str: Chuỗi hex của mật khẩu đã được băm.
  """
  if not password:
      # print("Cảnh báo: Mật khẩu trống không được băm.") # Gỡ comment nếu muốn debug
      return None # Trả về None nếu mật khẩu trống
  password_bytes = password.encode('utf-8')
  sha256_hash = hashlib.sha256()
  sha256_hash.update(password_bytes)
  hashed_password = sha256_hash.hexdigest()
  # print(f"Hashing '{password}' -> '{hashed_password}'") # Gỡ comment nếu muốn debug
  return hashed_password

def verify_password(stored_password_hash, provided_password):
  """
  Xác minh mật khẩu được cung cấp với hash đã lưu.
  Args:
      stored_password_hash (str): Hash mật khẩu lấy từ CSDL.
      provided_password (str): Mật khẩu người dùng nhập vào (chưa băm).
  Returns:
      bool: True nếu mật khẩu khớp, False nếu không.
  """
  if not stored_password_hash or not provided_password:
      # print("Cảnh báo: Hash đã lưu hoặc mật khẩu cung cấp bị trống.") # Gỡ comment nếu muốn debug
      return False
  # Băm mật khẩu được cung cấp để so sánh
  provided_password_hash = hash_password(provided_password)
  # print(f"Verifying: Stored='{stored_password_hash}', Provided hashed='{provided_password_hash}'") # Gỡ comment nếu muốn debug
  return stored_password_hash == provided_password_hash

# (Tùy chọn) Có thể thêm class User ở đây nếu cần quản lý đối tượng phức tạp hơn
# utils/session.py

# Biến toàn cục (hoặc dùng class) để lưu trữ thông tin phiên đăng nhập
_current_user_session = {
    "username": None,
    "role": None,
    "is_logged_in": False
}

def set_current_user(username, role):
  """Lưu thông tin người dùng hiện tại vào phiên."""
  global _current_user_session
  _current_user_session["username"] = username
  _current_user_session["role"] = role
  _current_user_session["is_logged_in"] = True
  print(f"Phiên hoạt động: Người dùng '{username}' với vai trò '{role}' đã đăng nhập.")

def get_current_user():
  """Lấy thông tin người dùng đang đăng nhập."""
  global _current_user_session
  if _current_user_session["is_logged_in"]:
      return _current_user_session["username"], _current_user_session["role"]
  return None, None

def get_current_username():
    """Lấy tên người dùng đang đăng nhập."""
    global _current_user_session
    return _current_user_session.get("username")

def get_current_role():
    """Lấy vai trò người dùng đang đăng nhập."""
    global _current_user_session
    return _current_user_session.get("role")

def is_user_logged_in():
    """Kiểm tra xem có ai đang đăng nhập không."""
    global _current_user_session
    return _current_user_session["is_logged_in"]


def clear_current_user():
  """Xóa thông tin phiên khi người dùng đăng xuất."""
  global _current_user_session
  logged_out_user = _current_user_session["username"]
  _current_user_session["username"] = None
  _current_user_session["role"] = None
  _current_user_session["is_logged_in"] = False
  if logged_out_user:
    print(f"Phiên hoạt động: Người dùng '{logged_out_user}' đã đăng xuất.")
  else:
    print("Phiên hoạt động: Không có người dùng nào đăng xuất (phiên đã trống).")
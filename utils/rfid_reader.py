# utils/rfid_reader.py
import time
import random
import threading

# --- PHẦN NÀY CẦN THAY THẾ BẰNG THƯ VIỆN VÀ CODE ĐỌC RFID THỰC TẾ ---
# Ví dụ nếu dùng thư viện 'pyserial' cho đầu đọc serial:
# import serial
# def connect_rfid_reader(port='/dev/ttyUSB0', baudrate=9600):
#     try:
#         ser = serial.Serial(port, baudrate, timeout=1)
#         print(f"Đã kết nối đầu đọc RFID trên {port}")
#         return ser
#     except serial.SerialException as e:
#         print(f"Lỗi kết nối đầu đọc RFID: {e}")
#         return None
#
# def read_card_from_serial(serial_connection):
#     if not serial_connection or not serial_connection.is_open:
#         return None, "Đầu đọc chưa kết nối"
#     try:
#         # Gửi lệnh yêu cầu đọc thẻ (tùy thuộc vào đầu đọc)
#         # serial_connection.write(b'READ_COMMAND\n')
#         print("Đang chờ thẻ RFID...")
#         line = serial_connection.readline().decode('utf-8').strip()
#         if line:
#             # Xử lý chuỗi nhận được để lấy ID thẻ
#             card_id = line # Hoặc xử lý phức tạp hơn
#             print(f"Đọc được thẻ: {card_id}")
#             return card_id, "Đọc thẻ thành công"
#         else:
#             # Timeout hoặc không có dữ liệu
#             return None, "Không có thẻ hoặc timeout"
#     except Exception as e:
#         print(f"Lỗi khi đọc thẻ: {e}")
#         return None, f"Lỗi đọc thẻ: {e}"
# --- KẾT THÚC PHẦN THỰC TẾ (VÍ DỤ) ---


# --- HÀM GIẢ LẬP ---
_fake_reader_lock = threading.Lock() # Đảm bảo chỉ 1 luồng đọc tại 1 thời điểm

def read_rfid_card_sync():
    """
    Hàm đồng bộ giả lập việc đọc thẻ RFID.
    Hàm này sẽ block cho đến khi "đọc" xong hoặc lỗi.
    Returns:
        tuple(str | None, str): (card_id, message)
               card_id là None nếu có lỗi.
    """
    with _fake_reader_lock: # Khóa để tránh nhiều lần gọi đồng thời (giả lập)
        print("[RFID Giả lập] Đang chờ thẻ...")
        # Giả lập thời gian chờ đọc
        time.sleep(random.uniform(1.5, 3.0))

        # Giả lập kết quả đọc (70% thành công, 30% lỗi/timeout)
        if random.random() < 0.85:
            # Tạo một ID thẻ giả lập (ví dụ: 8 ký tự hex)
            card_id = ''.join(random.choices('0123456789ABCDEF', k=8))
            message = "Đọc thẻ thành công (giả lập)"
            print(f"[RFID Giả lập] Đọc được: {card_id}")
            return card_id, message
        else:
            error_choice = random.choice(["Timeout", "Lỗi kết nối", "Không có thẻ"])
            message = f"Lỗi đọc thẻ: {error_choice} (giả lập)"
            print(f"[RFID Giả lập] {message}")
            return None, message
# --- KẾT THÚC HÀM GIẢ LẬP ---

# Bạn có thể giữ lại hàm này hoặc tích hợp trực tiếp vào GUI
# Hàm này không cần thiết nếu GUI tự quản lý thread
# def read_rfid_in_thread(callback):
#     """Chạy việc đọc RFID trong thread và gọi callback khi hoàn thành."""
#     def thread_target():
#         card_id, message = read_rfid_card_sync()
#         # Gọi callback từ thread chính (nếu callback là hàm GUI)
#         # Cần cơ chế để chuyển lại main thread, ví dụ dùng queue hoặc scheduler của GUI
#         callback(card_id, message) # Đây là ví dụ đơn giản, có thể gây lỗi GUI

#     thread = threading.Thread(target=thread_target)
#     thread.daemon = True # Thoát cùng chương trình chính
#     thread.start()
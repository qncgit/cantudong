import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSizePolicy,
    QFormLayout, QSpacerItem, QGridLayout
)
from PyQt5.QtGui import QFont, QColor, QPixmap, QImage, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer, pyqtSlot

# (Lớp VideoThread giữ nguyên)
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    def __init__(self, camera_index=0):
        super().__init__()
        self._run_flag = True; self.camera_index = camera_index; self.cap = None
    def run(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened(): print(f"Lỗi: Không thể mở camera {self.camera_index}"); return
        while self._run_flag:
            ret, cv_img = self.cap.read()
            if ret: self.change_pixmap_signal.emit(cv_img)
            self.msleep(30)
        if self.cap: self.cap.release()
    def stop(self):
        self._run_flag = False; self.wait()
        if self.cap: self.cap.release()

class WeighingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("PHẦN MỀM CÂN TỰ ĐỘNG QNC")

        self.default_width = 800
        self.default_height = 480
        self.setFixedSize(self.default_width, self.default_height)

        self.led_font_id = -1
        self.webcam_label = None
        # self.webcam_frame_for_ratio = None # Không cần thiết nữa nếu đặt kích thước cố định
        self.thread = None
        self.zoom_factor = 3.0 # Giữ zoom cố định
        self.flip_webcam_horizontally = True

        self.init_ui()
        self.load_styles()
        self.start_webcam()

    def init_ui(self):
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(5, 5, 5, 5)
        main_v_layout.setSpacing(5)

        top_bar_widget = self._create_top_bar()
        main_v_layout.addWidget(top_bar_widget)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        # Tạo các panel với màu nền được chỉ định
        step1_widget = self._create_step1_panel()
        step2_widget = self._create_step2_panel()
        step3_widget = self._create_step3_panel()
        step4_widget = self._create_step4_panel() # Bước 4 giữ nền mặc định (xanh từ mainWindow) hoặc trắng nếu CSS content_widget áp dụng

        grid_layout.addWidget(step1_widget, 0, 0)
        grid_layout.addWidget(step2_widget, 0, 1)
        grid_layout.addWidget(step3_widget, 1, 0)
        grid_layout.addWidget(step4_widget, 1, 1)

        grid_layout.setColumnStretch(0, 3) # Tỷ lệ cột Trái
        grid_layout.setColumnStretch(1, 7) # Tỷ lệ cột Phải
        
        grid_layout.setRowStretch(0, 1) # Hàng trên
        grid_layout.setRowStretch(1, 1) # Hàng dưới (có thể điều chỉnh nếu bảng cần cao hơn)

        main_v_layout.addLayout(grid_layout)
        main_v_layout.setStretchFactor(grid_layout, 1)

        buttons_layout = self._create_buttons_panel()
        main_v_layout.addLayout(buttons_layout)

        status_bar_layout = self._create_status_bar()
        main_v_layout.addLayout(status_bar_layout)
        
        self.setLayout(main_v_layout)

    def _create_top_bar(self):
        # (Giữ nguyên như phiên bản 800x480 trước)
        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 2, 5, 2); layout.setSpacing(5)
        title_label = QLabel("PHẦN MỀM CÂN TỰ ĐỘNG QNC"); title_label.setObjectName("mainTitleLabel")
        title_font = title_label.font(); title_font.setPointSize(16); title_label.setFont(title_font)
        layout.addWidget(title_label)
        layout.addSpacerItem(QSpacerItem(5, 10, QSizePolicy.Preferred, QSizePolicy.Minimum))
        weight_layout = QHBoxLayout(); weight_layout.setSpacing(2)
        self.weight_display_label = QLabel("35563"); self.weight_display_label.setObjectName("weightDisplayLabel")
        if self.led_font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(self.led_font_id)[0]
            led_font = QFont(font_family, 28, QFont.Bold); self.weight_display_label.setFont(led_font)
        else: self.weight_display_label.setStyleSheet("font-size: 28pt; font-weight: bold;")
        weight_unit = QLabel("Kg"); weight_unit.setObjectName("weightUnitLabel")
        unit_font = weight_unit.font(); unit_font.setPointSize(14); weight_unit.setFont(unit_font)
        weight_layout.addWidget(self.weight_display_label); weight_layout.addWidget(weight_unit, 0, Qt.AlignBottom)
        layout.addLayout(weight_layout)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        time_connection_layout = QVBoxLayout(); time_connection_layout.setSpacing(0)
        time_connection_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        time_label = QLabel("Thời gian: 09/05/2025 14:23:12"); time_label.setObjectName("timeLabel")
        connection_label = QLabel("Đã kết nối: 172.40.1.2"); connection_label.setObjectName("connectionLabel")
        time_font = time_label.font(); time_font.setPointSize(7); time_label.setFont(time_font); connection_label.setFont(time_font)
        time_connection_layout.addWidget(time_label); time_connection_layout.addWidget(connection_label)
        layout.addLayout(time_connection_layout)
        return widget

    def _create_panel_widget(self, title_text, object_name_prefix, content_bg_color=None): # Thêm tham số màu nền
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0); container_layout.setSpacing(0)
        title_label = QLabel(title_text)
        title_label.setObjectName(f"stepTitle_{object_name_prefix}")
        panel_title_font = title_label.font(); panel_title_font.setPointSize(9); title_label.setFont(panel_title_font)
        container_layout.addWidget(title_label)
        content_widget = QWidget()
        content_widget.setObjectName(f"{object_name_prefix}_content_widget")
        
        # Đặt màu nền cho content_widget nếu được chỉ định
        style = "padding: 4px;" # Giữ padding nhỏ
        if content_bg_color:
            style += f" background-color: {content_bg_color};"
        # Giữ lại viền xanh từ CSS chung, chỉ thay đổi nền
        content_widget.setStyleSheet(f"QWidget[objectName=\"{object_name_prefix}_content_widget\"] {{ {style} }}")

        container_layout.addWidget(content_widget)
        # Với kích thước cố định, SizePolicy ít quan trọng hơn, nhưng Expanding vẫn tốt để lấp đầy ô lưới
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return container, content_widget
    
    def _add_form_row(self, form_layout, key_text, value_text, is_value_success=False):
        # (Giữ nguyên)
        key_label = QLabel(key_text); key_label.setProperty("isKeyLabel", True)
        value_label = QLabel(value_text)
        if is_value_success: value_label.setProperty("isSuccessText", True)
        form_font = key_label.font(); form_font.setPointSize(7); key_label.setFont(form_font); value_label.setFont(form_font)
        form_layout.addRow(key_label, value_label)
        return key_label, value_label

    def _create_step1_panel(self):
        container, content_widget = self._create_panel_widget("BƯỚC 1: QUÉT THẺ LÁI XE RFID", "step1", content_bg_color="white")
        # (Nội dung của step1_panel giữ nguyên)
        layout = QFormLayout(content_widget)
        layout.setLabelAlignment(Qt.AlignLeft); layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop); layout.setVerticalSpacing(3)
        self._add_form_row(layout, "Kết quả:", "THÀNH CÔNG", True); self._add_form_row(layout, "Mã thẻ:", "456213647827", True)
        self._add_form_row(layout, "Mã nhân viên:", "NBCN.1096"); self._add_form_row(layout, "Họ và tên:", "Đặng Chí Sơn")
        self._add_form_row(layout, "Năm sinh:", "20/02/1998"); self._add_form_row(layout, "Đơn vị:", "Phân xưởng Cơ giới")
        self._add_form_row(layout, "Chức vụ:", "Lái xe"); self._add_form_row(layout, "Trạng thái:", "ĐANG LÀM", True)
        layout.addItem(QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Giữ spacer để đẩy nội dung lên
        return container
    
    def _create_step2_panel(self):
        container, content_widget = self._create_panel_widget("BƯỚC 2: QUÉT MÃ LỆNH CAMERA USB", "step2", content_bg_color="white")
        main_h_layout = QHBoxLayout(content_widget)
        main_h_layout.setContentsMargins(2,2,2,2)
        main_h_layout.setSpacing(2)

        self.webcam_label = QLabel("Đang kết nối...")
        self.webcam_label.setObjectName("webcamFeedLabel")
        self.webcam_label.setAlignment(Qt.AlignCenter)
        self.webcam_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored) # Để setPixmap kiểm soát kích thước

        webcam_frame = QFrame()
        webcam_frame.setObjectName("qrCodeFrame") # Nền đen cho frame webcam
        webcam_frame_layout = QVBoxLayout(webcam_frame)
        webcam_frame_layout.addWidget(self.webcam_label)
        webcam_frame_layout.setContentsMargins(1,1,1,1) # Viền đen nhỏ quanh webcam_label
        
        # Ước tính kích thước cho webcam_frame để cố gắng đạt tỷ lệ 1:1
        # Chiều cao của một ô lưới khoảng (480 - top_bar - buttons - status_bar - spacing) / 2
        # Giả sử chiều cao mỗi ô lưới khoảng 150-180px.
        # Với tỷ lệ cột 3:7, chiều rộng của ô webcam (cột 1, step2) sẽ là (800 * 7/10) / 2 (do có info_area)
        # Đây là ước tính rất thô, cần điều chỉnh.
        # Cho một kích thước vuông nhỏ ban đầu.
        desired_cam_size = 150 # Kích thước mong muốn cho cạnh của khung vuông webcam
        webcam_frame.setFixedSize(desired_cam_size, desired_cam_size)
        # webcam_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # Kích thước cố định

        main_h_layout.addWidget(webcam_frame, 0, Qt.AlignCenter) # Stretch factor 0, căn giữa

        info_area_widget = QWidget()
        info_layout = QFormLayout(info_area_widget)
        info_layout.setLabelAlignment(Qt.AlignLeft); info_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop); info_layout.setVerticalSpacing(3)
        self._add_form_row(info_layout, "Kết quả:", "THÀNH CÔNG", True); self._add_form_row(info_layout, "Mã lệnh:", "NB-000001", True)
        self._add_form_row(info_layout, "Tên hàng hoá:", "Đá 1x2"); self._add_form_row(info_layout, "Phân loại:", "Nội bộ")
        self._add_form_row(info_layout, "Kiểu cân:", "Tải - Bì"); self._add_form_row(info_layout, "Nhập:", "Bãi dự phòng Núi Rùa 1")
        self._add_form_row(info_layout, "Xuất:", "Dây chuyền 3"); self._add_form_row(info_layout, "Loại xe:", "70 Tấn")
        self._add_form_row(info_layout, "Ngày bắt đầu:", "09/05/2025"); self._add_form_row(info_layout, "Giờ bắt đầu:", "20:00")
        self._add_form_row(info_layout, "Trạng thái:", "SẴN SÀNG", True)
        info_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_h_layout.addWidget(info_area_widget, 1) # Info area co giãn để lấp đầy phần còn lại
        return container

    def _create_step3_panel(self):
        container, content_widget = self._create_panel_widget("BƯỚC 3: PHƯƠNG TIỆN UHF", "step3", content_bg_color="white")
        # (Nội dung của step3_panel giữ nguyên)
        layout = QFormLayout(content_widget)
        layout.setLabelAlignment(Qt.AlignLeft); layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop); layout.setVerticalSpacing(3)
        self._add_form_row(layout, "Kết quả:", "THÀNH CÔNG", True); self._add_form_row(layout, "Mã thẻ:", "123636564125", True)
        self._add_form_row(layout, "Biển số xe:", "14Z1 - 134.32"); self._add_form_row(layout, "Loại xe:", "70 Tấn")
        self._add_form_row(layout, "Thương hiệu:", "HOWO"); self._add_form_row(layout, "Đơn vị:", "Phân xưởng Cơ giới")
        self._add_form_row(layout, "Chức vụ:", "Lái xe"); self._add_form_row(layout, "Trạng thái:", "ĐANG LÀM", True)
        layout.addItem(QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        return container

    def _create_step4_panel(self): # Bước 4 có thể giữ nền xanh hoặc đổi thành trắng
        # container, content_widget = self._create_panel_widget("BƯỚC 4: XÁC NHẬN KẾT QUẢ", "step4", content_bg_color="white")
        container, content_widget = self._create_panel_widget("BƯỚC 4: XÁC NHẬN KẾT QUẢ", "step4") # Giữ nền xanh mặc định từ CSS
        # (Nội dung bảng giữ nguyên như đã điều chỉnh cho 800x480)
        layout = QVBoxLayout(content_widget); layout.setContentsMargins(0,0,0,0)
        table = QTableWidget(); table.setObjectName("resultTable"); table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["TT", "Mã NV", "Mã Lệnh", "Mã PT", "Lần Cân", "Thời Gian", "Trạng Thái"])
        header_font = table.horizontalHeader().font(); header_font.setPointSize(7); table.horizontalHeader().setFont(header_font)
        table_font = table.font(); table_font.setPointSize(7); table.setFont(table_font)
        table.verticalHeader().setDefaultSectionSize(18); table.horizontalHeader().setDefaultSectionSize(50)
        data = [
            ["6", "456213647827", "NB-000001", "123636564125", "Cân L2", "09/05/25 14:05", "Chờ XN"],
            ["5", "456213647827", "NB-000001", "123636564125", "Cân L1", "09/05/25 13:05", "Đã ĐB"],
            ["4", "456213647827", "NB-000001", "123636564125", "Cân L2", "09/05/25 12:05", "Đã ĐB"],
            ["3", "456213647827", "NB-000001", "123636564125", "Cân L1", "09/05/25 11:05", "Đã ĐB"],
            ["2", "456213647827", "NB-000001", "123636564125", "Cân L2", "09/05/25 10:05", "Đã ĐB"],
            ["1", "456213647827", "NB-000001", "123636564125", "Cân L1", "09/05/25 09:05", "Đã ĐB"]
        ]
        table.setRowCount(len(data))
        for r, rd in enumerate(data):
            for c, cd in enumerate(rd):
                item = QTableWidgetItem(cd); item.setTextAlignment(Qt.AlignCenter)
                if c == 6 and cd == "Chờ XN": item.setBackground(QColor("#FFC107")); item.setForeground(QColor("#5B4100"))
                elif c == 6 and cd == "Đã ĐB": item.setForeground(QColor("#1E8449"))
                table.setItem(r, c, item)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for i in range(table.columnCount()):
             if i == table.columnCount() -1 : table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
             elif i == 0: table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
             else: table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents) 
        table.verticalHeader().setVisible(False); table.setAlternatingRowColors(True); table.setShowGrid(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers); layout.addWidget(table)
        return container
        
    def _create_buttons_panel(self):
        # (Giữ nguyên như phiên bản 800x480)
        layout = QHBoxLayout(); layout.setSpacing(10)
        btns_data = [("HUỶ", "huyButton"), ("CÂN LẠI", "canLaiButton"), ("IN PHIẾU", "inPhieuButton"), ("XÁC NHẬN", "xacNhanButton")]
        btns = []
        for text, obj_name in btns_data:
            btn = QPushButton(text); btn.setObjectName(obj_name)
            btn_font = btn.font(); btn_font.setPointSize(8); btn.setFont(btn_font)
            btn.setStyleSheet("padding: 4px 6px; margin-top: 2px; margin-bottom: 2px;")
            btns.append(btn)
        layout.addWidget(btns[0], 1); layout.addWidget(btns[1], 1)
        layout.addSpacerItem(QSpacerItem(15, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(btns[2], 1); layout.addWidget(btns[3], 1)
        return layout

    def _create_status_bar(self):
        # (Giữ nguyên như phiên bản 800x480)
        layout = QHBoxLayout(); layout.setSpacing(3)
        statuses = {"NET:OK":"status_internet", "RFID:OK":"status_rfid", "CÂN:OK":"status_daucan", 
                    "QR:OK":"status_qrcode", "ONVIF:3/3":"status_onvif", "SYNC:0":"status_sync"}
        for text, obj_name in statuses.items():
            label = QLabel(text); label.setObjectName(obj_name); label.setAlignment(Qt.AlignCenter)
            status_font = label.font(); status_font.setPointSize(7); label.setFont(status_font)
            label.setStyleSheet(f"QLabel[objectName=\"{obj_name}\"] {{ padding: 2px 1px; margin-top:1px; margin-bottom:1px; }}")
            layout.addWidget(label, 1)
        return layout
    
    # --- Các hàm webcam giữ nguyên ---
    def start_webcam(self):
        if self.webcam_label is None: QTimer.singleShot(100, self.start_webcam); return
        self.thread = VideoThread(camera_index=0)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

    def apply_digital_zoom(self, frame, zoom_factor):
        if zoom_factor < 1.0: zoom_factor = 1.0
        if zoom_factor == 1.0: return frame
        h, w = frame.shape[:2]
        crop_w, crop_h = int(w / zoom_factor), int(h / zoom_factor)
        mid_x, mid_y = w // 2, h // 2
        x1, y1 = mid_x - crop_w // 2, mid_y - crop_h // 2
        x1, y1 = max(0, x1), max(0, y1)
        actual_crop_w, actual_crop_h = min(crop_w, w - x1), min(crop_h, h - y1)
        if actual_crop_w <= 0 or actual_crop_h <= 0: return frame 
        cropped_frame = frame[y1:y1 + actual_crop_h, x1:x1 + actual_crop_w]
        if cropped_frame.shape[0] > 0 and cropped_frame.shape[1] > 0:
            return cv2.resize(cropped_frame, (w, h), interpolation=cv2.INTER_LINEAR)
        return frame

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img_original):
        if self.webcam_label is None or cv_img_original is None or cv_img_original.size == 0: return
        processed_img = cv_img_original
        if self.flip_webcam_horizontally: processed_img = cv2.flip(processed_img, 1)
        zoomed_img = self.apply_digital_zoom(processed_img, self.zoom_factor)
        qt_img = self.convert_cv_qt(zoomed_img)
        if qt_img.isNull(): return
        
        # Scale pixmap để vừa với webcam_label, giữ tỷ lệ
        # Kích thước của webcam_label được kiểm soát bởi webcam_frame (đã setFixedSize)
        scaled_pixmap = qt_img.scaled(self.webcam_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.webcam_label.setPixmap(scaled_pixmap)

    def convert_cv_qt(self, cv_img):
        if cv_img is None or cv_img.size == 0: return QPixmap() 
        try:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            if h == 0 or w == 0: return QPixmap()
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            return QPixmap.fromImage(convert_to_Qt_format)
        except cv2.error as e: print(f"Lỗi OpenCV: {e}"); return QPixmap()

    def load_styles(self):
        style_sheet = """
            #mainWindow { background-color: #00529B; font-family: Arial, sans-serif; }
            #mainTitleLabel { color: white; } 
            #weightDisplayLabel { color: #D92D20; }
            #weightUnitLabel { color: white; } 
            #timeLabel, #connectionLabel { color: white; }

            QLabel[objectName^="stepTitle_"] {
                background-color: #28a745; color: white;
                font-weight: bold; margin-bottom: 0px; /* padding và font-size trong Python */
            }
            /* CSS chung cho content_widget (viền xanh) */
            QWidget[objectName$="_content_widget"] {
                border: 1px solid #28a745; border-top: none;
                /* padding được set trong Python, màu nền cũng trong Python */
            }
            QLabel[property="isKeyLabel"] { font-weight: bold; color: #2c3e50; }
            QLabel[property="isSuccessText"] { color: #28a745; font-weight: bold; }

            #qrCodeFrame { background-color: black; border-radius: 2px; } /* Nền cho webcam_frame */
            #webcamFeedLabel { color: #777; /* Hiển thị "Đang kết nối..." */ }

            #resultTable {
                gridline-color: #D0D0D0; background-color: white; /* Nền bảng trắng */
                alternate-background-color: #F0F8FF; border: 1px solid #D0D0D0;
            }
            #resultTable QHeaderView::section {
                background-color: #28a745; color: white; padding: 2px;
                border: none; border-right: 1px solid #1E8449; font-weight: bold;
            }
            #resultTable QHeaderView::section:last { border-right: none; }
            #resultTable::item { padding: 1px; 
                border-bottom: 1px solid #E0E0E0; border-right: 1px solid #EAEAEA;
            }
            #resultTable::item:selected { background-color: #AED6F1; color: black; }
            
            QPushButton[objectName$="Button"] {
                color: white; border-radius: 3px;
                font-weight: bold; border: none; min-height: 18px;
            }
            #huyButton { background-color: #D92D20; } #huyButton:hover { background-color: #C82333; }
            #canLaiButton { background-color: #FF8C00; } #canLaiButton:hover { background-color: #E07B00; }
            #inPhieuButton { background-color: #007BFF; } #inPhieuButton:hover { background-color: #0069D9; }
            #xacNhanButton { background-color: #28a745; } #xacNhanButton:hover { background-color: #218838; }
            
            QLabel[objectName^="status_"] {
                background-color: #1D8348; color: white; 
                font-weight: bold; border-radius: 2px; min-height: 16px;
            }
        """
        self.setStyleSheet(style_sheet)

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning(): print("Đang dừng webcam..."); self.thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WeighingApp()
    window.show()
    sys.exit(app.exec_())

import sys
import os
import datetime
import calendar
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QMenu, QAction, QPushButton, QGridLayout, QFrame, QCheckBox,
                             QSystemTrayIcon, QStyle)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QCursor, QIcon, QPixmap, QPainter, QColor, QBrush
from lunar_python import Lunar, Solar

# ========== Windows 开机启动支持 ==========
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "GeekCalendar"

def get_app_launch_command():
    """获取启动当前应用的命令字符串。
    打包成 exe 时返回 exe 路径；以脚本方式运行时返回 pythonw + 脚本路径。"""
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    else:
        # 优先用 pythonw.exe 静默运行；找不到则退回 python.exe
        py_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(py_dir, 'pythonw.exe')
        runner = pythonw if os.path.exists(pythonw) else sys.executable
        script = os.path.abspath(sys.argv[0])
        return f'"{runner}" "{script}"'

def is_autostart_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_NAME)
            return bool(value)
    except (FileNotFoundError, OSError):
        return False
    except Exception:
        return False

def set_autostart(enable: bool):
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, get_app_launch_command())
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"设置开机启动失败: {e}")
        return False


def create_tray_icon():
    """动态生成一个极客风格的日历托盘图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 圆角背景
    painter.setBrush(QBrush(QColor("#007ACC")))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 10, 10)
    
    # 顶部一条小白条
    painter.setBrush(QBrush(QColor("#FFFFFF")))
    painter.drawRoundedRect(4, 4, 56, 14, 10, 10)
    
    # 日期数字
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Consolas", 22, QFont.Bold)
    painter.setFont(font)
    today = str(datetime.date.today().day)
    painter.drawText(pixmap.rect().adjusted(0, 8, 0, 0), Qt.AlignCenter, today)
    
    painter.end()
    return QIcon(pixmap)

class ClickableLabel(QLabel):
    clicked = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.date_obj = None
        self.setCursor(Qt.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.date_obj:
            self.clicked.emit(self.date_obj)

class CalendarWindow(QWidget):
    def __init__(self, main_app=None):
        super().__init__()
        self.main_app = main_app
        self.current_date = datetime.date.today()
        self.selected_date = datetime.date.today()
        self.themes = [
            {"name": "极简白", "bg": "#FFFFFF", "panel": "#F3F4F6", "btn": "#E5E7EB", "btn_hover": "#D1D5DB", "border": "#E5E7EB", "title": "#F9FAFB", "text": "#1F2937", "muted": "#9CA3AF", "highlight": "rgba(0, 0, 0, 0.05)", "highlight_border": "#D1D5DB"},
            {"name": "极客黑", "bg": "#1E1E1E", "panel": "#252526", "btn": "#2D2D30", "btn_hover": "#3E3E42", "border": "#3E3E42", "title": "#333333", "text": "#D4D4D4", "muted": "#888888", "highlight": "rgba(255, 255, 255, 0.1)", "highlight_border": "#555555"},
            {"name": "深空蓝", "bg": "#0F172A", "panel": "#1E293B", "btn": "#1E293B", "btn_hover": "#334155", "border": "#334155", "title": "#0B1120", "text": "#CBD5E1", "muted": "#64748B", "highlight": "rgba(255, 255, 255, 0.1)", "highlight_border": "#475569"},
            {"name": "护眼绿", "bg": "#1A2421", "panel": "#22302A", "btn": "#22302A", "btn_hover": "#2C3E36", "border": "#2C3E36", "title": "#111A17", "text": "#C2D6C8", "muted": "#758C7F", "highlight": "rgba(255, 255, 255, 0.1)", "highlight_border": "#4B5E54"},
            {"name": "赛博紫", "bg": "#241432", "panel": "#301A42", "btn": "#301A42", "btn_hover": "#402359", "border": "#402359", "title": "#190B26", "text": "#D8B4E2", "muted": "#92769E", "highlight": "rgba(255, 255, 255, 0.1)", "highlight_border": "#5D3A7A"},
            {"name": "秋叶褐", "bg": "#2B211E", "panel": "#382A26", "btn": "#382A26", "btn_hover": "#4A3A35", "border": "#4A3A35", "title": "#1D1513", "text": "#E5D1CF", "muted": "#9C8C89", "highlight": "rgba(255, 255, 255, 0.1)", "highlight_border": "#6E5A54"},
        ]
        self.current_theme_idx = 1 # 默认黑
        self.initUI()

    def apply_theme(self):
        theme = self.themes[self.current_theme_idx]
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['bg']};
                color: {theme['text']};
                font-family: 'Consolas', 'Microsoft YaHei';
            }}
            QPushButton {{
                background-color: {theme['btn']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 6px 12px;
                color: {theme['text']};
                font-size: 13px;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background-color: {theme['btn_hover']};
                border: 1px solid #007ACC;
                color: {theme['text']};
            }}
            QPushButton:pressed {{
                background-color: #007ACC;
                color: #FFFFFF;
            }}
            #CloseBtn {{
                background-color: transparent;
                border: none;
                font-weight: bold;
                font-size: 16px;
                color: {theme['muted']};
                border-radius: 0px;
            }}
            #CloseBtn:hover {{
                background-color: #E81123;
                color: white;
            }}
            #ThemeBtn {{
                background-color: transparent;
                border: 1px solid {theme['border']};
                border-radius: 12px;
                font-size: 12px;
                padding: 2px 10px;
                color: {theme['text']};
            }}
            #ThemeBtn:hover {{
                background-color: {theme['btn_hover']};
            }}
            #DetailPanel {{
                background-color: {theme['panel']};
                border-radius: 8px;
            }}
        """)
        self.title_bar.setStyleSheet(f"background-color: {theme['title']};")
        self.lbl_main_title.setStyleSheet(f"color: {theme['text']}; font-size: 13px; font-weight: bold; font-family: 'Microsoft YaHei'; background-color: transparent;")
        if hasattr(self, 'cb_seconds'):
            self.cb_seconds.setStyleSheet(f"color: {theme['text']}; font-family: 'Microsoft YaHei'; font-size: 13px; background-color: transparent;")
        if hasattr(self, 'detail_line'):
            self.detail_line.setStyleSheet(f"border-top: 1px solid {theme['border']}; background-color: transparent;")

    def show_theme_menu(self):
        menu = QMenu(self)
        theme = self.themes[self.current_theme_idx]
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme['panel']};
                color: {theme['text']};
                border: 1px solid {theme['border']};
                font-family: 'Microsoft YaHei';
            }}
            QMenu::item {{
                padding: 6px 25px 6px 25px;
            }}
            QMenu::item:selected {{
                background-color: #007ACC;
                color: white;
            }}
        """)
        
        for idx, t in enumerate(self.themes):
            action = QAction(t["name"], self)
            action.triggered.connect(lambda checked, i=idx: self.set_theme(i))
            menu.addAction(action)
            
        menu.exec_(self.btn_theme.mapToGlobal(QPoint(0, self.btn_theme.height() + 2)))

    def set_theme(self, idx):
        self.current_theme_idx = idx
        self.apply_theme()
        self.update_calendar()
        self.update_details()

    def initUI(self):
        # 无边框，保留作为独立窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(850, 520)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- 极客风格自定义标题栏 ---
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(35)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 0, 0)
        
        self.lbl_main_title = QLabel("📅 极客万年历")
        
        self.cb_seconds = QCheckBox("显示秒")
        self.cb_seconds.setCursor(Qt.PointingHandCursor)
        if self.main_app:
            self.cb_seconds.setChecked(self.main_app.show_seconds)
        self.cb_seconds.stateChanged.connect(self.toggle_seconds)
        
        self.btn_theme = QPushButton("🎨 主题")
        self.btn_theme.setObjectName("ThemeBtn")
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setFixedSize(70, 24)
        self.btn_theme.clicked.connect(self.show_theme_menu)

        btn_close = QPushButton("×")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(45, 35)
        btn_close.clicked.connect(self.hide)
        
        title_layout.addWidget(self.lbl_main_title)
        title_layout.addStretch()
        title_layout.addWidget(self.cb_seconds)
        title_layout.addSpacing(15)
        title_layout.addWidget(self.btn_theme)
        title_layout.addWidget(btn_close)
        
        main_layout.addWidget(self.title_bar)
        
        # --- 主内容区 ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # 左侧：日历网格
        left_layout = QVBoxLayout()
        
        # 头部导航
        header_layout = QHBoxLayout()
        self.btn_prev_year = QPushButton("<<")
        self.btn_prev_month = QPushButton("<")
        self.btn_prev_year.setFixedWidth(40)
        self.btn_prev_month.setFixedWidth(40)
        
        self.lbl_title = QLabel()
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; font-family: 'Consolas', 'Microsoft YaHei'; background-color: transparent;")
        
        self.btn_today = QPushButton("Today")
        self.btn_today.clicked.connect(self.go_today)

        self.btn_next_month = QPushButton(">")
        self.btn_next_year = QPushButton(">>")
        self.btn_next_month.setFixedWidth(40)
        self.btn_next_year.setFixedWidth(40)

        header_layout.addWidget(self.btn_prev_year)
        header_layout.addWidget(self.btn_prev_month)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_today)
        header_layout.addWidget(self.btn_next_month)
        header_layout.addWidget(self.btn_next_year)
        
        left_layout.addLayout(header_layout)
        left_layout.addSpacing(10)
        
        # 星期头
        grid = QGridLayout()
        grid.setSpacing(6)
        weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        for i, wd in enumerate(weekdays):
            lbl = QLabel(wd)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; color: #007ACC; padding: 5px 0; font-size: 13px; font-family: 'Consolas'; background-color: transparent;")
            grid.addWidget(lbl, 0, i)
        
        self.day_labels = []
        for row in range(1, 7):
            row_labels = []
            for col in range(7):
                lbl = ClickableLabel()
                lbl.setAlignment(Qt.AlignCenter)
                lbl.clicked.connect(self.on_date_clicked)
                lbl.setFixedSize(65, 60)
                grid.addWidget(lbl, row, col)
                row_labels.append(lbl)
            self.day_labels.append(row_labels)
            
        left_layout.addLayout(grid)
        left_layout.addStretch()
        
        # 右侧：侧边详情栏
        self.detail_panel = QFrame()
        self.detail_panel.setObjectName("DetailPanel")
        self.detail_panel.setFixedWidth(280)
        detail_layout = QVBoxLayout(self.detail_panel)
        detail_layout.setContentsMargins(20, 25, 20, 25)
        detail_layout.setSpacing(15)
        
        self.lbl_detail_day = QLabel("01")
        self.lbl_detail_day.setAlignment(Qt.AlignCenter)
        self.lbl_detail_day.setStyleSheet("font-size: 72px; font-weight: bold; color: #007ACC; font-family: 'Consolas'; background-color: transparent;")
        
        self.lbl_detail_date = QLabel("2024-01-01  Monday")
        self.lbl_detail_date.setAlignment(Qt.AlignCenter)
        self.lbl_detail_date.setStyleSheet("font-size: 16px; background-color: transparent;")
        
        self.lbl_detail_lunar = QLabel("农历")
        self.lbl_detail_lunar.setAlignment(Qt.AlignCenter)
        self.lbl_detail_lunar.setStyleSheet("font-size: 18px; font-weight: bold; background-color: transparent;")
        
        self.lbl_detail_bazi = QLabel("干支")
        self.lbl_detail_bazi.setAlignment(Qt.AlignCenter)
        
        # 宜和忌
        yi_ji_layout = QHBoxLayout()
        self.lbl_yi = QLabel()
        self.lbl_yi.setWordWrap(True)
        self.lbl_yi.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_yi.setStyleSheet("background-color: transparent;")
        
        self.lbl_ji = QLabel()
        self.lbl_ji.setWordWrap(True)
        self.lbl_ji.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_ji.setStyleSheet("background-color: transparent;")
        
        yi_ji_layout.addWidget(self.lbl_yi)
        yi_ji_layout.addWidget(self.lbl_ji)
        
        detail_layout.addWidget(self.lbl_detail_day)
        detail_layout.addWidget(self.lbl_detail_date)
        detail_layout.addWidget(self.lbl_detail_lunar)
        detail_layout.addWidget(self.lbl_detail_bazi)
        
        self.detail_line = QFrame()
        self.detail_line.setFrameShape(QFrame.HLine)
        detail_layout.addWidget(self.detail_line)
        
        detail_layout.addLayout(yi_ji_layout)
        detail_layout.addStretch()
        
        content_layout.addLayout(left_layout)
        content_layout.addWidget(self.detail_panel)
        
        main_layout.addLayout(content_layout)
        
        self.btn_prev_month.clicked.connect(self.prev_month)
        self.btn_next_month.clicked.connect(self.next_month)
        self.btn_prev_year.clicked.connect(self.prev_year)
        self.btn_next_year.clicked.connect(self.next_year)
        
        self.apply_theme()
        self.update_calendar()
        self.update_details()

    def toggle_seconds(self, state):
        if self.main_app:
            self.main_app.show_seconds = (state == Qt.Checked)
            self.main_app.update_time()

    def go_today(self):
        self.current_date = datetime.date.today()
        self.selected_date = datetime.date.today()
        self.update_calendar()
        self.update_details()

    def prev_month(self):
        month = self.current_date.month - 1
        year = self.current_date.year
        if month == 0:
            month = 12
            year -= 1
        self.current_date = datetime.date(year, month, 1)
        self.update_calendar()

    def next_month(self):
        month = self.current_date.month + 1
        year = self.current_date.year
        if month == 13:
            month = 1
            year += 1
        self.current_date = datetime.date(year, month, 1)
        self.update_calendar()

    def prev_year(self):
        self.current_date = datetime.date(self.current_date.year - 1, self.current_date.month, 1)
        self.update_calendar()

    def next_year(self):
        self.current_date = datetime.date(self.current_date.year + 1, self.current_date.month, 1)
        self.update_calendar()

    def on_date_clicked(self, date_obj):
        self.selected_date = date_obj
        self.update_calendar()
        self.update_details()

    def update_calendar(self):
        year = self.current_date.year
        month = self.current_date.month
        self.lbl_title.setText(f"{year} - {month:02d}")
        
        cal = calendar.Calendar(firstweekday=6) # 0=Mon, 6=Sun
        days = cal.monthdatescalendar(year, month)
        
        today = datetime.date.today()
        theme = self.themes[self.current_theme_idx]
        
        for row in range(6):
            for col in range(7):
                lbl = self.day_labels[row][col]
                if row < len(days):
                    date_obj = days[row][col]
                    lbl.date_obj = date_obj
                    
                    day_str = str(date_obj.day)
                    
                    dt = datetime.datetime.combine(date_obj, datetime.time())
                    lunar = Lunar.fromDate(dt)
                    lunar_day_str = lunar.getDayInChinese()
                    if lunar_day_str == '初一':
                        lunar_day_str = lunar.getMonthInChinese() + '月'
                    
                    display_text = lunar_day_str
                    
                    # 节假日和节气高亮配色
                    l_fest = lunar.getFestivals()
                    s_fest = Solar.fromDate(dt).getFestivals()
                    jq = lunar.getJieQi()
                    
                    if jq: 
                        display_text = jq
                        color = "#B8860B" if theme['bg'] == "#FFFFFF" else "#D7BA7D"
                    elif l_fest: 
                        display_text = l_fest[0]
                        color = "#D32F2F" if theme['bg'] == "#FFFFFF" else "#F44747"
                    elif s_fest: 
                        display_text = s_fest[0]
                        color = "#005A9E" if theme['bg'] == "#FFFFFF" else "#569CD6"
                    else:
                        color = theme['muted']
                    
                    is_today = (date_obj == today)
                    is_selected = (date_obj == self.selected_date)
                    is_current_month = (date_obj.month == month)
                    
                    text_color = theme['text'] if is_current_month else theme['muted']
                    if not is_current_month:
                        color = theme['border']
                        
                    html = f'''
                    <div style="text-align: center; margin: 0; padding: 0;">
                        <div style="font-size: 20px; color: {text_color}; font-family: 'Consolas'; font-weight: {'bold' if is_today or is_selected else 'normal'};">{day_str}</div>
                        <div style="font-size: 11px; color: {color}; margin-top: 2px; font-family: 'Microsoft YaHei';">{display_text}</div>
                    </div>
                    '''
                    lbl.setText(html)
                    
                    # 动态边框和背景 (悬浮、选中、今天)
                    bg_color = "transparent"
                    border_css = "1px solid transparent"
                    
                    if is_selected:
                        bg_color = theme['highlight']
                        border_css = "1px solid #007ACC"
                    elif is_today:
                        bg_color = theme['highlight']
                        border_css = f"1px solid {theme['highlight_border']}"
                        
                    lbl.setStyleSheet(f"""
                        QLabel {{
                            background-color: {bg_color};
                            border: {border_css};
                            border-radius: 6px;
                        }}
                        QLabel:hover {{
                            background-color: {theme['btn_hover']};
                            border: 1px solid {theme['border']};
                        }}
                    """)
                else:
                    lbl.date_obj = None
                    lbl.setText("")
                    lbl.setStyleSheet("background-color: transparent; border: none;")

    def update_details(self):
        date_obj = self.selected_date
        self.lbl_detail_day.setText(f"{date_obj.day:02d}")
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.lbl_detail_date.setText(f"{date_obj.year}-{date_obj.month:02d}-{date_obj.day:02d}  {weekdays[date_obj.weekday()]}")
        
        dt = datetime.datetime.combine(date_obj, datetime.time())
        lunar = Lunar.fromDate(dt)
        
        lunar_str = f"农历 {lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
        self.lbl_detail_lunar.setText(lunar_str)
        
        bazi_str = f"{lunar.getYearInGanZhiExact()}年 {lunar.getMonthInGanZhiExact()}月 {lunar.getDayInGanZhiExact()}日"
        
        theme = self.themes[self.current_theme_idx]
        self.lbl_detail_bazi.setText(bazi_str)
        self.lbl_detail_bazi.setStyleSheet(f"font-size: 14px; color: {theme['muted']}; background-color: transparent;")
        
        yi = lunar.getDayYi()
        ji = lunar.getDayJi()
        
        yi_html = f"<span style='color:#569CD6; font-weight:bold; font-size:16px;'>宜</span><br><br>" + \
                  "<br>".join([f"<span style='color:{theme['text']}; font-size:13px;'>{item}</span>" for item in yi[:8]]) # 最多显示8个
                  
        ji_html = f"<span style='color:#F44747; font-weight:bold; font-size:16px;'>忌</span><br><br>" + \
                  "<br>".join([f"<span style='color:{theme['text']}; font-size:13px;'>{item}</span>" for item in ji[:8]])
                  
        self.lbl_yi.setText(yi_html)
        self.lbl_ji.setText(ji_html)

    # 使无边框窗口可以拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'dragPos'):
            delta = QPoint(event.globalPos() - self.dragPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.dragPos = event.globalPos()


class DesktopCalendar(QWidget):
    def __init__(self):
        super().__init__()
        self.calendar_window = None
        self.show_seconds = False
        self.initUI()
        self.init_tray()
        self.oldPos = self.pos()
    
    def init_tray(self):
        """初始化系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(create_tray_icon())
        self.tray_icon.setToolTip("极客万年历")
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                font-family: 'Microsoft YaHei';
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 25px 6px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #007ACC;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #3E3E42;
                margin: 4px 8px;
            }
        """)
        
        action_show_widget = QAction("显示/隐藏 桌面时钟", self)
        action_show_widget.triggered.connect(self.toggle_widget)
        
        action_show_calendar = QAction("打开万年历", self)
        action_show_calendar.triggered.connect(self.show_calendar_window)
        
        self.action_autostart = QAction("开机自动启动", self)
        self.action_autostart.setCheckable(True)
        self.action_autostart.setChecked(is_autostart_enabled())
        self.action_autostart.triggered.connect(self.toggle_autostart)
        
        action_about = QAction("关于", self)
        action_about.triggered.connect(self.show_about)
        
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(action_show_widget)
        tray_menu.addAction(action_show_calendar)
        tray_menu.addSeparator()
        tray_menu.addAction(self.action_autostart)
        tray_menu.addSeparator()
        tray_menu.addAction(action_about)
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        # 双击托盘 = 打开大日历; 单击 = 切换桌面微件显示
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_calendar_window()
        elif reason == QSystemTrayIcon.Trigger:
            self.toggle_widget()
    
    def toggle_widget(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
    
    def show_calendar_window(self):
        if self.calendar_window is None:
            self.calendar_window = CalendarWindow(self)
        self.calendar_window.show()
        self.calendar_window.activateWindow()
        self.calendar_window.raise_()
    
    def show_about(self):
        self.tray_icon.showMessage(
            "极客万年历",
            "一个极客风格的桌面万年历\n双击图标打开日历，单击切换桌面时钟",
            QSystemTrayIcon.Information,
            3000
        )
    
    def toggle_autostart(self, checked):
        success = set_autostart(checked)
        if success:
            actual = is_autostart_enabled()
            self.action_autostart.setChecked(actual)
            self.tray_icon.showMessage(
                "极客万年历",
                "已开启开机自动启动" if actual else "已关闭开机自动启动",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.action_autostart.setChecked(is_autostart_enabled())
            self.tray_icon.showMessage(
                "极客万年历",
                "设置失败，请检查权限",
                QSystemTrayIcon.Warning,
                2000
            )

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(5)

        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #FFFFFF; font-size: 36px; font-weight: bold; font-family: 'Consolas', 'Microsoft YaHei'; background-color: transparent;")
        self.layout.addWidget(self.time_label)

        self.solar_label = QLabel(self)
        self.solar_label.setAlignment(Qt.AlignCenter)
        self.solar_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-family: 'Microsoft YaHei'; background-color: transparent;")
        self.layout.addWidget(self.solar_label)

        self.lunar_label = QLabel(self)
        self.lunar_label.setAlignment(Qt.AlignCenter)
        self.lunar_label.setStyleSheet("color: #B0C4DE; font-size: 14px; font-family: 'Microsoft YaHei'; background-color: transparent;")
        self.layout.addWidget(self.lunar_label)

        self.festival_label = QLabel(self)
        self.festival_label.setAlignment(Qt.AlignCenter)
        self.festival_label.setStyleSheet("color: #D7BA7D; font-size: 12px; font-family: 'Microsoft YaHei'; background-color: transparent;")
        self.layout.addWidget(self.festival_label)

        # 桌面微件也改为极客暗黑风
        self.setStyleSheet("""
            DesktopCalendar {
                background-color: rgba(24, 24, 24, 200);
                border: 1px solid #333333;
                border-radius: 12px;
            }
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        self.update_time()
        self.adjustSize()
        self.position_to_bottom_right()

    def update_time(self):
        now = datetime.datetime.now()
        if getattr(self, 'show_seconds', False):
            self.time_label.setText(now.strftime("%H:%M:%S"))
        else:
            self.time_label.setText(now.strftime("%H:%M"))
        
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_str = weekdays[now.weekday()]
        self.solar_label.setText(now.strftime(f"%Y-%m-%d  {weekday_str}"))

        lunar = Lunar.fromDate(now)
        lunar_date_str = f"农历 {lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
        bazi_str = f"{lunar.getYearInGanZhiExact()}年 {lunar.getMonthInGanZhiExact()}月 {lunar.getDayInGanZhiExact()}日"
        self.lunar_label.setText(f"{lunar_date_str}  {bazi_str}")

        solar = Solar.fromDate(now)
        festivals = []
        
        lunar_festivals = lunar.getFestivals()
        if lunar_festivals: festivals.extend(lunar_festivals)
            
        solar_festivals = solar.getFestivals()
        if solar_festivals: festivals.extend(solar_festivals)
            
        jieqi = lunar.getJieQi()
        if jieqi: festivals.append(jieqi)

        if festivals:
            self.festival_label.setText(" · ".join(festivals))
            self.festival_label.show()
        else:
            self.festival_label.hide()

    def position_to_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_calendar_window()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3E3E42;
                font-family: 'Microsoft YaHei';
            }
            QMenu::item {
                padding: 5px 25px 5px 25px;
            }
            QMenu::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        
        quit_action = QAction("Exit / 退出", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        
        menu.exec_(pos)

if __name__ == '__main__':
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 即使所有窗口关闭，托盘仍保持存活
    app.setWindowIcon(create_tray_icon())
    ex = DesktopCalendar()
    ex.show()
    sys.exit(app.exec_())

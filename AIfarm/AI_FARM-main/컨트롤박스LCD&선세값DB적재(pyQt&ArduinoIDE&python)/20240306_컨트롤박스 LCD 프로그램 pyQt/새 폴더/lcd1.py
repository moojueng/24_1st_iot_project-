import sys
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.uic import loadUi
from PyQt5.QtGui import QColor
from serial import Serial

# 시리얼 통신을 위한 포트와 속도 설정
serial_port = '/dev/ttyACM0'  # 아두이노가 연결된 포트에 따라 변경
baud_rate = 9600

# LED 핀 번호 정의
LED_PINS = {
    "pushButton_1": 13,
    "pushButton_2": 12,
    "pushButton_3": 11
}

# LED 상태를 저장하는 딕셔너리
LED_status = {pin: False for _, pin in LED_PINS.items()}

def get_sensor_values():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1111",
        database="flask_login_demo"
    )
    cursor = connection.cursor()

    cursor.execute("SELECT Temperature, Humidity FROM Dht11_data ORDER BY Timestamp DESC LIMIT 1")
    temperature_humidity = cursor.fetchone()

    cursor.execute("SELECT Soil_moisture FROM Soil_moisture_data ORDER BY Timestamp DESC LIMIT 1")
    soil_moisture = cursor.fetchone()

    cursor.execute("SELECT Intensity FROM Light_intensity_data ORDER BY Recorded_at DESC LIMIT 1")
    intensity = cursor.fetchone()

    cursor.close()
    connection.close()

    return temperature_humidity, soil_moisture, intensity

class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        loadUi("lcd1.ui", self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(2000)

        # 시리얼 포트 초기화
        self.serial = Serial(serial_port, baud_rate)

        # 버튼 초기 설정
        for button_name, pin in LED_PINS.items():
            button = getattr(self, button_name)
            button.clicked.connect(lambda _, p=pin: self.toggle_led(p))
        self.update_led_button_text()

    def update_data(self):
        temperature_humidity, soil_moisture, intensity = get_sensor_values()
        if temperature_humidity and soil_moisture and intensity:
            temperature, humidity = temperature_humidity
            self.update_display(temperature, humidity, soil_moisture[0], intensity[0])

    def update_display(self, temperature, humidity, soil_moisture, intensity):
        self.temp_label.setText("온도: {} ℃".format(temperature))
        self.humi_label.setText("습도: {} %".format(humidity))
        self.soil_label.setText("토양 수분: {}".format(soil_moisture))
        self.light_label.setText("조도: {}".format(intensity))

        # 온도에 따른 배경색 설정
        self.set_background_color(self.temp_label, temperature)

        # 습도에 따른 배경색 설정
        self.set_background_color(self.humi_label, humidity)

        # 토양 수분에 따른 배경색 설정
        self.set_background_color(self.soil_label, soil_moisture)

        # 조도에 따른 배경색 설정
        self.set_background_color(self.light_label, intensity)

    def set_background_color(self, label, value):
        if value > 30:
            color = QColor('red')
        elif value < 20:
            color = QColor('yellow')
        else:
            color = QColor('green')

        label.setAutoFillBackground(True)
        palette = label.palette()
        palette.setColor(label.backgroundRole(), color)
        label.setPalette(palette)

    def toggle_led(self, pin):
        global LED_status
        LED_status[pin] = not LED_status[pin]
        if LED_status[pin]:
            self.serial.write(b'ON,' + str(pin).encode() + b'\n')  # 아두이노에 ON 신호를 보냄
        else:
            self.serial.write(b'OFF,' + str(pin).encode() + b'\n')  # 아두이노에 OFF 신호를 보냄
        self.update_led_button_text()

    def update_led_button_text(self):
        for button_name, pin in LED_PINS.items():
            button = getattr(self, button_name)
            if LED_status[pin]:
                button.setText(f"{button_name} OFF")
            else:
                button.setText(f"{button_name} ON")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())

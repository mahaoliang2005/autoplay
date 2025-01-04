import serial
import serial.tools.list_ports
#import time
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Checking port: {port.device}, VID: {port.vid}, PID: {port.pid}")
        if port.vid == 0x2341 and port.pid == 0x006D:
            print(f"Arduino found on port: {port.device}")
            return port.device
    return None

# 发送数据
def send_data(port, direction, distance, key):
    if port is None:
        print("Error: No Arduino port found.")
        return
    # 打开串口，注意将串口号改为 'COM3'
    ser = serial.Serial(port, 9600, timeout=1)
    #time.sleep(2)  # 等待 Arduino 准备好
    data = f"{direction}:{distance}:{key}"
    ser.write(data.encode())  # 将字符串编码成字节并发送
    print(f"Data '{data}' sent to Arduino on port {port}")
    # 关闭串口
    ser.close()

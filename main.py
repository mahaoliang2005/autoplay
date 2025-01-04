from OBScapture import  capture_frame
from turnLeftOrRight import find_target#, target_map
from Arduino_sender import send_data, find_arduino_port
from keyboardCotroller import get_random_key#, map_key
from datetime import datetime
import os
import shutil
import atexit
import keyboard

current_date = datetime.now().strftime("%Y-%m-%d")
save_directory = f"C:\\Users\\mahaoliang2005\\Downloads\\{current_date}"
# 结束时删除文件夹的函数
def delete_directory_on_exit(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)  # 删除整个文件夹及其内容
        print(f"已删除截图文件夹: {directory}")
# 注册退出时自动删除文件夹的功能
atexit.register(delete_directory_on_exit, save_directory)
# 初始化上一个键为空
previous_key = None
num = 1
while True:
    try: 
        # 检查是否按下了Esc键
        if keyboard.is_pressed('esc'):
            print("Esc键被按下, 程序结束")
            break
        capture_frame(2, num)
        key = get_random_key(previous_key)
        previous_key = key
        direction, distance = find_target(num)
        arduino_port = find_arduino_port()
        send_data(arduino_port, direction, distance, key)
        num += 1
    except KeyboardInterrupt:
        print("程序结束")
        break
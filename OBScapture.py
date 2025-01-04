import cv2
import time
import os
from datetime import datetime
# 打开OBS虚拟摄像头 (假设虚拟摄像头的设备索引为0)
cap = cv2.VideoCapture(1)  # 如果有多个摄像头设备，可能需要修改索引值

if not cap.isOpened():
    print("无法打开虚拟摄像头")
    exit()
# 设置摄像头分辨率
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
# 获取当前日期作为文件夹名
current_date = datetime.now().strftime("%Y-%m-%d")
# 创建保存路径
save_directory = f"C:\\Users\\mahaoliang2005\\Downloads\\{current_date}"

# 如果文件夹不存在，则创建
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# 定期截屏函数
def capture_frame(interval, num):
    # 读取摄像头帧
    ret, frame = cap.read()

    if not ret:
        print("无法获取摄像头帧")
        return

    # 保存帧为图像, 按照时间戳命名
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_directory, f"screenshot_{num}.png")
    cv2.imwrite(filename, frame)

    print(f"截屏保存为: {filename}")

    # 检查保存的文件数量是否达到100张
    delete_oldest_if_needed(save_directory, max_files=10)
        
    # 等待一段时间后再次截屏
    time.sleep(interval)

# 删除最早保存的文件函数
def delete_oldest_if_needed(directory, max_files):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    if len(files) >= max_files:
        oldest_file = min(files, key=os.path.getctime)  # 找到最早创建的文件
        os.remove(oldest_file)  # 删除最早的文件
        print(f"已删除最早的文件: {oldest_file}")

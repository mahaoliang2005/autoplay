import cv2
import os
import numpy as np
from PIL import Image
from datetime import datetime

# 获取当前日期作为文件夹名
current_date = datetime.now().strftime("%Y-%m-%d")
template_path = f"c:\\Users\\mahaoliang2005\\Documents\\works\\main\\target1.png"
screenshot_folder = f"C:\\Users\\mahaoliang2005\\Downloads\\{current_date}"

# Check if the folder exists
if not os.path.exists(screenshot_folder):
    print(f"Folder {screenshot_folder} does not exist.")
    exit(1)

def filter_white_color(image):
    # 转换为HSV颜色空间
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 定义白色的HSV范围
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 25, 255])
    
    # 创建白色掩码
    mask = cv2.inRange(hsv_image, lower_white, upper_white)
    
    # 应用掩码过滤图像，保留白色区域
    white_filtered_image = cv2.bitwise_and(image, image, mask=mask)
    
    return white_filtered_image

# HSV颜色空间过滤红色部分的函数
def filter_red_color(image):
    # 转换为HSV颜色空间
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 定义红色的HSV范围
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    # 构建两个红色掩码
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    
    # 合并掩码
    mask = mask1 + mask2
    
    # 应用掩码过滤图像，保留红色区域
    red_filtered_image = cv2.bitwise_and(image, image, mask=mask)
    
    return red_filtered_image

# 多尺度模板匹配的函数
def multi_scale_template_match(screenshot, template, scales, threshold):
    gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    best_match = None
    best_val = 0
    best_scale = 1

    template_h, template_w = template.shape[:2]
    
    for scale in scales:
        # 缩放模板
        scaled_template = cv2.resize(template, (int(template_w * scale), int(template_h * scale)))
        scaled_template_gray = cv2.cvtColor(scaled_template, cv2.COLOR_BGR2GRAY)

        # 进行模板匹配
        result = cv2.matchTemplate(gray_screenshot, scaled_template_gray, cv2.TM_CCOEFF_NORMED)

        # 获取最佳匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 如果匹配度超过阈值并且是当前最好的匹配
        if max_val > threshold and max_val > best_val:
            best_val = max_val
            best_match = (max_loc, scaled_template.shape[1], scaled_template.shape[0])
            best_scale = scale

    return best_match, best_val, best_scale

def find_target(num):
    # 读取截图和目标模板
    screenshot_path = f"{screenshot_folder}\\screenshot_{num}.png"

    # 打开图片
    image = Image.open(screenshot_path)

    # 获取图片的尺寸
    width, height = image.size

    # 计算屏幕的中点
    mid_screen_x = width // 2

    screenshot = cv2.imread(screenshot_path)
    template = cv2.imread(template_path)

    # 过滤掉非红色部分
    screenshot = filter_red_color(screenshot)
    template = filter_red_color(template)
    # 设定缩放比例范围和匹配阈值
    scales = np.linspace(1, 1.5, 5)
    threshold = 0.2

    # 多尺度匹配
    best_match, best_val, best_scale = multi_scale_template_match(screenshot, template, scales, threshold)

    if best_match is not None:
        top_left_prevous = best_match[0]
        w, h = best_match[1], best_match[2]
        bottom_right_prevous = (top_left_prevous[0] + w, top_left_prevous[1] + h)
        mid_x_prevous = (top_left_prevous[0] + bottom_right_prevous[0]) // 2

        # 修正 fix_x 的计算，只需要在 x 轴方向上进行调整
        fix_x = int(1.5 * (mid_x_prevous - top_left_prevous[0]))

        # 调整 top_left 和 bottom_right 的 x 坐标
        top_left = (top_left_prevous[0] - fix_x, top_left_prevous[1])
        bottom_right = (bottom_right_prevous[0] - fix_x, bottom_right_prevous[1])
        mid_x = (top_left[0] + bottom_right[0]) // 2
        # 在原图上画出矩形框标识匹配区域
        cv2.rectangle(screenshot, top_left, bottom_right, (0, 0, 255), 2)
        print(f"middle x of the screen: {mid_screen_x}")
        print(f"middle x of the matched region: {mid_x}")

        # 判断目标在屏幕的左边还是右边
        direction = 'right' if mid_x > mid_screen_x else 'left'
        # 计算距离
        distance = abs(mid_x - mid_screen_x)
        # 显示结果
        #cv2.imshow('Detected', screenshot)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        return direction, distance
    else:
        print("No match found.")
        return "None", "None"
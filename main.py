import tkinter as tk
from tkinter import filedialog
import fitz
import cv2
from PIL import ImageTk, Image
import numpy as np
import tempfile
from tkinter import ttk
import threading

# 全局变量
pdf_path = ""
output_pdf_path = ""
current_page = 0
threshold_value = 128
progress = 0

def select_pdf_file():
    global pdf_path, current_page, output_pdf_path

    # 将进度条更新为0
    update_progress(0)
    # 重置显示的文件位置
    file_location.set("")

    # 打开文件对话框以选择PDF文件
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    print("select:"+pdf_path)
    # 如果选择了PDF文件，则显示第一页的内容
    if pdf_path:
        # 使用 fitz 打开 PDF 文件
        doc = fitz.open(pdf_path)
        current_page = 0
        update_image()
        # 更新页面调节滑块的最大值
        page_slider.config(to=doc.page_count)
        # 关闭 PDF 文件
        doc.close()

def update_image():
    global pdf_path, current_page, threshold_value

    # 检查PDF路径是否为空
    if not pdf_path:
        return

    # 使用 fitz 打开 PDF 文件
    doc = fitz.open(pdf_path)

    # 如果页面索引超出范围，则设置为最后一页
    if current_page >= doc.page_count:
        current_page = doc.page_count - 1

    # 加载页面
    page = doc.load_page(current_page)

    # 将页面转换为图像
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # 对图像进行处理
    img_binary = remove_watermark_gray(img,threshold_value,)
    # 创建图像的Tkinter对象
    img_pil = Image.fromarray(img_binary)

    # 缩放图像以适应页面大小
    page_width = canvas.winfo_width()
    page_height = canvas.winfo_height()
    img_pil.thumbnail((page_width, page_height))

    # 转换为Tkinter图像对象
    img_tk = ImageTk.PhotoImage(img_pil)

    # 更新标签的图像
    label.config(image=img_tk)
    label.image = img_tk

    # 关闭 PDF 文件
    doc.close()

def remove_watermark():
    global pdf_path, threshold_value, current_page,output_pdf_path,progress

    # 检查PDF路径是否为空
    if not pdf_path:
        return

    # 使用 fitz 打开 PDF 文件
    doc = fitz.open(pdf_path)

    # 保存处理后的图像的列表地址
    temp_image_path_list=[]
    # 临时文件夹储存临时图片
    temp_dir = tempfile.TemporaryDirectory(prefix="tmpImage")
    temp_dir_path = temp_dir.name

    for page_number in range(doc.page_count):
        # 加载页面
        page = doc.load_page(page_number)

        # 将页面转换为图像
        pix = page.get_pixmap(dpi=200,alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img = img.convert("RGB")  # 将图像转换为RGB模式

        # 执行水印去除等处理
        repaired_image = remove_watermark_gray(np.array(img), threshold_value,)
        # 保存图片
        repaired_image_path = save_to_img(repaired_image,temp_dir_path)
        file_location.set("processing page:"+str(page_number))

        # 更新进度条
        progress = int((page_number/doc.page_count)*progressbar_len/2)
        update_progress(progress)

        # 记录所有文件的路径
        temp_image_path_list.append(repaired_image_path)
    # 关闭 PDF 文件
    doc.close()
    # 输入的路径
    output_pdf_path = pdf_path[:-4]+"_remove-watermark.pdf"

    # 创建一个空的PDF文档对象
    doc_out = fitz.open()
    doc_len = len(temp_image_path_list)


    for temp_image_path in temp_image_path_list:
        # 打开临时图像文件并创建Pixmap对象
        with fitz.Pixmap(temp_image_path) as img_pixmap:
            img_pixmap = fitz.Pixmap(temp_image_path)
            # 创建一个新的PDF页面
            pdf_page = doc_out.new_page(width=img_pixmap.width, height=img_pixmap.height)

            # 将图像插入到PDF页面中
            pdf_page.insert_image(pdf_page.rect, pixmap=img_pixmap)

        # 终端显示进度
        print(f"当前页面{doc_out.page_count} ,共{doc_len}")

        # 显示到界面中
        file_location.set(f"Prepared {doc_out.page_count}//{doc_len}")

        add_progress = int((doc_out.page_count/doc_len)*(progressbar_len/2))
        update_progress(add_progress+progress)


    # 保存PDF文件
    doc_out.save(output_pdf_path)
    doc_out.close()
    temp_dir.cleanup()
    file_location.set(output_pdf_path)
    print("PDF生成完成！")
import asyncio
import fitz

async def save_pdf_async(doc_out, output_pdf_path):
    # 保存PDF文件
    await asyncio.sleep(0)  # 允许事件循环切换到其他任务
    doc_out.save(output_pdf_path)
    doc_out.close()

def remove_watermark_thread():

    b_thread = threading.Thread(target=remove_watermark, )

    # 启动线程
    b_thread.start()

    # 等待线程结束
    b_thread.join()
def save_to_img(repaired_image,temp_dir_path):
    # 将修复后的图像转换为PIL.Image.Image对象
    repaired_img_pil = Image.fromarray(repaired_image)

    # 创建临时文件保存修复后的图像
    temp_image_file = tempfile.NamedTemporaryFile(suffix=".png", dir=temp_dir_path, delete=False)
    temp_image_path = temp_image_file.name
    print("生成临时文件地址为:"+ temp_image_path)
    repaired_img_pil.save(temp_image_path)

    # 关闭临时文件
    temp_image_file.close()
    return temp_image_path


def show_pdf_page(value):
    global current_page

    page_number = int(value)
    if page_number >= 1:
        current_page = page_number - 1
        update_image()


def update_threshold(value):
    global threshold_value

    threshold_value = int(value)
    update_image()


def remove_watermark_gray(img, threshold_value,):
    img = np.array(img)
    # 将图像转换为灰度图像
    img_gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    # 进行二值化处理
    _, img_binary = cv2.threshold(np.array(img_gray), threshold_value, 255, cv2.THRESH_BINARY)

    # 对遮罩层进行腐蚀操作
    kernel = np.ones((3, 3), np.uint8)
    eroded_mask = cv2.erode(img_binary, kernel, iterations=2)
    eroded_mask = cv2.GaussianBlur(eroded_mask,(3, 3),0)

    # 将遮罩层应用到原图中
    repaired_image = cv2.bitwise_and(img, img, mask=~eroded_mask)
    repaired_image[eroded_mask!=0] =[255,255,255] # 待改进
    return repaired_image

def update_canvas_size():
    canvas_width = root.winfo_width()
    canvas_height = root.winfo_height() - select_button.winfo_height() - page_slider_frame.winfo_height() - threshold_slider_frame.winfo_height() - 100
    canvas.config(width=canvas_width, height=canvas_height)

def update_progress(value):
    # 更新进度条的值
    progressbar['value'] = value
    print("进度条"+str(value))
    root.update_idletasks()

def on_window_resize(event):
    update_canvas_size()
    update_image()

# 创建线程避免阻塞界面ui
def thread_it(func,):
    """ 将函数打包进线程 """
    myThread = threading.Thread(target=func, )
    myThread .setDaemon(True)  # 主线程退出就直接让子线程跟随退出,不论是否运行完成。
    myThread .start()

# 创建主窗口
root = tk.Tk()
root.title("PDF Viewer")

# 获取屏幕的宽度和高度
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 计算窗口的初始宽度和高度
window_width = int(screen_width * 0.4)
window_height = int(screen_height * 0.8)

# 设置窗口初始大小
root.geometry(f"{window_width}x{window_height}")

# 创建选择按钮
select_button = tk.Button(root, text="Select PDF", command=select_pdf_file)
select_button.pack(pady=3)

# 创建页面调节滑块
page_slider_frame = tk.Frame(root)
page_slider_frame.pack(pady=2)
page_label = tk.Label(page_slider_frame, text="页码")
page_label.pack(side=tk.LEFT)
page_slider = tk.Scale(page_slider_frame, from_=1, to=1, orient=tk.HORIZONTAL, length=window_width - 80, command=show_pdf_page)
page_slider.pack(side=tk.LEFT)

# 创建阈值调节滑块
threshold_slider_frame = tk.Frame(root)
threshold_slider_frame.pack(pady=1)
threshold_label = tk.Label(threshold_slider_frame, text="阈值")
threshold_label.pack(side=tk.LEFT)
threshold_slider = tk.Scale(threshold_slider_frame, from_=0, to=255, orient=tk.HORIZONTAL, length=window_width - 80, command=update_threshold)
threshold_slider.set(threshold_value)
threshold_slider.pack(side=tk.LEFT)

# 创建图像显示区域
canvas = tk.Canvas(root)
canvas.pack(pady=3)

# 创建图像标签
label = tk.Label(canvas)
label.place(relx=0.5, rely=0.5, anchor="center")

# 创建Remove Watermark按钮
remove_watermark_button = tk.Button(root, text="Remove Watermark", command=lambda :thread_it(remove_watermark_thread))
remove_watermark_button.pack(pady=1)

# 创建progressBar
progressbar_len=300
progressbar = ttk.Progressbar(root, length=progressbar_len, mode='determinate',maximum=progressbar_len)
progressbar.pack(pady=1)


# 创建输入文件的显示位置
file_lcoation_frame = tk.Frame(root)
file_lcoation_frame.pack(pady=1)
file_location_label = tk.Label(file_lcoation_frame, text="文件位置:")
file_location_label.pack(side=tk.LEFT)
file_location = tk.StringVar()
tk.Label(file_lcoation_frame, textvariable=file_location).pack()



# 监听窗口大小变化事件
root.bind("<Configure>", on_window_resize)


# 运行主循环
root.mainloop()

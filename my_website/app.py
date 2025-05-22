from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import os
import uuid
from PIL import Image, ImageEnhance, ImageFilter
from werkzeug.utils import secure_filename
import traceback

# 配置参数
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE  # 设置Flask的最大内容长度

# 创建上传目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def remove_watermark(input_path, output_path):
    """
    水印处理核心函数
    使用PIL库进行简单的图像处理，模拟去水印效果
    """
    try:
        # 读取图像
        img = Image.open(input_path)
        
        # 应用一系列滤镜处理来模拟去水印效果
        
        # 1. 锐化图像
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        # 2. 提高对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # 3. 调整亮度
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # 4. 应用轻微的模糊以平滑处理后的图像
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # 保存结果
        img.save(output_path)
        print(f"图像处理完成: {output_path}")
        return True
        
    except Exception as e:
        print(f"处理图像时出错: {str(e)}")
        traceback.print_exc()
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    try:
        # 验证文件
        if 'image' not in request.files:
            return jsonify({"error": "未选择文件"}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "无效文件"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"error": "仅支持JPG/PNG格式"}), 400

        # 保存原始文件
        file_uuid = uuid.uuid4().hex
        original_filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"original_{file_uuid}.png")
        file.save(input_path)
        print(f"原始文件已保存: {input_path}")

        # 处理文件
        output_filename = f"processed_{file_uuid}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        if remove_watermark(input_path, output_path):
            # 创建完整的URL路径，确保浏览器能正确获取图片
            return jsonify({"image_url": url_for('download_file', filename=output_filename, _external=True)}), 200
        else:
            return jsonify({"error": "水印去除失败，请重试"}), 500

    except Exception as e:
        print(f"处理请求时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """提供文件下载"""
    try:
        # 确保文件存在
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return jsonify({"error": "文件不存在"}), 404
        
        print(f"提供文件下载: {file_path}")    
        # 使用send_from_directory，确保文件作为附件下载
        return send_from_directory(
            directory=app.config['UPLOAD_FOLDER'],
            path=filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "文件下载失败"}), 404

@app.route('/preview/<filename>')
def preview_file(filename):
    """预览处理后的图片"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"预览文件时出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "文件预览失败"}), 404

if __name__ == '__main__':
    print("启动Flask应用...")
    app.run(debug=True, host='0.0.0.0', port=5000)
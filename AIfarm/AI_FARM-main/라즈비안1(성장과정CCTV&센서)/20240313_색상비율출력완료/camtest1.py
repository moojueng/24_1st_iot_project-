import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np

app = Flask(__name__)

# 이미지가 저장될 폴더 설정
CAPTURED_IMAGES_FOLDER = os.path.join(app.static_folder, 'images')
if not os.path.exists(CAPTURED_IMAGES_FOLDER):
    os.makedirs(CAPTURED_IMAGES_FOLDER)

# 마지막으로 캡처된 이미지의 경로를 저장하는 변수
last_captured_image_path = None

@app.route('/')
def index():
    return render_template('camtest1.html')

@app.route('/get_images', methods=['GET'])
def get_images():
    images = []
    # 이미지 폴더에서 모든 이미지 파일을 가져와서 내림차순으로 정렬
    for filename in sorted(os.listdir(CAPTURED_IMAGES_FOLDER), reverse=True):
        if filename.endswith('.jpg'):
            image_path = os.path.join('/static/images', filename)
            images.append({'name': filename, 'path': image_path})
    return jsonify(images)

@app.route('/capture', methods=['POST'])
def capture():
    try:
        image_data = request.form['image']
        # 이미지 파일로 저장
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.join(CAPTURED_IMAGES_FOLDER, now + '.jpg')
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(image_data.split(',')[1]))
        # 캡처된 이미지의 경로를 저장
        global last_captured_image_path
        last_captured_image_path = '/static/images/' + now + '.jpg'
        return jsonify({'image_path': last_captured_image_path})
    except Exception as e:
        error_message = str(e)
        print("Error while capturing image:", error_message)
        return jsonify({'error': error_message}), 500

@app.route('/search_images', methods=['POST'])
def search_images():
    try:
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        # 입력된 날짜를 YYYYMMDD 형식으로 변환
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")

        images = []
        for filename in os.listdir(CAPTURED_IMAGES_FOLDER):
            if filename.endswith('.jpg'):
                file_date = filename.split('.')[0]
                # 파일명의 날짜 부분만 추출하여 YYYYMMDD 형식으로 변환
                file_date = file_date[:8]
                if start_datetime <= file_date <= end_datetime:
                    image_path = os.path.join('/static/images', filename)
                    images.append({'name': filename, 'path': image_path})

        # 날짜 내림차순으로 정렬
        images.sort(key=lambda x: x['name'], reverse=True)

        # 각 날짜별로 마지막 이미지만 가져오기
        last_images = {}
        for image in images:
            file_date = image['name'].split('.')[0][:8]
            if file_date not in last_images:
                last_images[file_date] = image

        return jsonify({'images': list(last_images.values())})
    except Exception as e:
        error_message = str(e)
        print("Error while searching images:", error_message)
        return jsonify({'error': error_message}), 500

@app.route('/analyze_images', methods=['POST'])
def analyze_images():
    try:
        image_paths = request.json['image_paths']

        black_ratios = []
        for image_path in image_paths:
            # 이미지 불러오기
            image = cv2.imread(os.path.join(app.static_folder, image_path.strip('/')))
            # 그레이스케일 변환
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 이진화
            _, binary_image = cv2.threshold(gray_image, 30, 255, cv2.THRESH_BINARY)
            # 검정색 픽셀 수 계산
            black_pixels = np.sum(binary_image == 0)
            # 전체 픽셀 수 계산
            total_pixels = binary_image.size
            # 검정색 픽셀 비율 계산
            black_ratio = black_pixels / total_pixels * 100
            black_ratios.append(black_ratio)

        return jsonify({'black_ratios': black_ratios})
    except Exception as e:
        error_message = str(e)
        print("Error while analyzing images:", error_message)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
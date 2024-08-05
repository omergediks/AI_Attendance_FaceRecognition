from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import cv2
import imgaug.augmenters as iaa
import face_recognition
import sqlite3
import numpy as np
import datetime

app = Flask(__name__)
CORS(app)

# Veritabanı bağlantısı ve tablo oluşturma
def init_db():
    conn = sqlite3.connect('face_recognition.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            face_encoding BLOB NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Görüntü augmentasyonu için ayar
augmenters = iaa.Sequential([
    iaa.Affine(rotate=(-30, 30)),
    iaa.AddToHueAndSaturation((-10, 10)),
    iaa.AdditiveGaussianNoise(scale=(0.01*255, 0.05*255)),
    iaa.Fliplr(0.5),
    iaa.SomeOf((0, 2), [
        iaa.Crop(percent=(0, 0.1)),
        iaa.Dropout(p=(0, 0.1)),
        iaa.Add((-20, 20)),
    ])
])

# Kişi ekleme
@app.route('/add_person', methods=['POST'])
def add_person():
    try:
        data = request.get_json()
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        image_data = data.get('photo')

        # Base64 verisini decode et
        _, image_data = image_data.split(',')
        image = np.frombuffer(base64.b64decode(image_data), np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': 'Invalid image data'}), 400

        all_images = [image] + [augmenters(image=image) for _ in range(10)]

        conn = sqlite3.connect('face_recognition.db')
        c = conn.cursor()

        # Aynı ad ve soyadla kayıt olup olmadığını kontrol et
        c.execute('''
            SELECT id FROM people WHERE first_name = ? AND last_name = ?
        ''', (first_name, last_name))
        existing_person = c.fetchone()

        if existing_person:
            return jsonify({'message': 'Person already exists'}), 400

        for img in all_images:
            face_locations = face_recognition.face_locations(img)
            face_encodings = face_recognition.face_encodings(img, face_locations)

            for face_encoding in face_encodings:
                face_encoding_bytes = face_encoding.tobytes()
                c.execute('''
                    INSERT INTO people (first_name, last_name, face_encoding) 
                    VALUES (?, ?, ?)
                ''', (first_name, last_name, face_encoding_bytes))
                conn.commit()
                break

        conn.close()
        return jsonify({'message': 'Person added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Yüzleri tanıma
@app.route('/recognize_faces', methods=['POST'])

def recognize_faces():
    if request.content_type != 'application/json':
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    try:
        # JSON verisini al
        data = request.get_json()
        image_data = data.get('image')
        
        # Base64 verisini decode et
        _, image_data = image_data.split(',')
        image = np.frombuffer(base64.b64decode(image_data), np.uint8)
        group_image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        if group_image is None:
            return jsonify({'error': 'Invalid image data'}), 400

        conn = sqlite3.connect('face_recognition.db')
        c = conn.cursor()

        face_locations = face_recognition.face_locations(group_image)
        face_encodings = face_recognition.face_encodings(group_image, face_locations)

        recognized_faces = []

        threshold = 0.58
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            face_encoding_bytes = np.array(face_encoding).tobytes()
            c.execute('SELECT id, first_name, last_name, face_encoding FROM people')
            known_faces = c.fetchall()

            name = "Unknown"
            best_match_distance = threshold
            person_id = None

            for person in known_faces:
                db_face_encoding = np.frombuffer(person[3], dtype=np.float64)
                face_distance = face_recognition.face_distance([db_face_encoding], face_encoding)[0]
                if face_distance < best_match_distance:
                    best_match_distance = face_distance
                    name = f"{person[1]} {person[2]}"
                    person_id = person[0]

            if name != "Unknown":
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute('''
                    INSERT INTO attendance (person_id, timestamp) 
                    VALUES (?, ?)
                ''', (person_id, timestamp))
                conn.commit()

                cv2.rectangle(group_image, (left, top), (right, bottom), (0, 255, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(group_image, f"{name} ({best_match_distance:.2f})", (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

                # Crop face from the image
                face_image = group_image[top:bottom, left:right]
                _, face_buffer = cv2.imencode('.jpg', face_image)
                face_base64 = base64.b64encode(face_buffer).decode('utf-8')

                recognized_faces.append({
                    'name': name,
                    'confidence': 1 - best_match_distance,
                    'box': [top, right, bottom, left],
                    'photoDataUrl': f"data:image/jpeg;base64,{face_base64}"  # Add photoDataUrl
                })

        conn.close()

        # Fotoğrafı Base64 formatına çevir
        _, buffer = cv2.imencode('.jpg', group_image)
        base64_image = base64.b64encode(buffer).decode('utf-8')

        return jsonify({'recognized_faces': recognized_faces, 'image_base64': base64_image}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Make sure Flask is accessible from outside localhost

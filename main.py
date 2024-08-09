import cv2
import threading
import time
from flask import Flask, Response
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

# Global variables to control camera, audio, and server
camera_on = False
audio_on = False
server_running = False
video_frame = None

# Flask app to stream video
app = Flask(__name__)

def capture_video():
    global camera_on, video_frame
    cap = cv2.VideoCapture(0)  # Start video capture from default camera
    while camera_on:
        ret, frame = cap.read()
        if ret:
            video_frame = frame
        time.sleep(0.1)
    cap.release()

def stream_video():
    global video_frame
    while True:
        if video_frame is None:
            continue
        _, jpeg = cv2.imencode('.jpg', video_frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(stream_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_server():
    global server_running
    if not server_running:
        server_running = True
        threading.Thread(target=app.run, kwargs={'port': 5000, 'debug': False, 'use_reloader': False}).start()

def stop_server():
    global server_running
    if server_running:
        server_running = False
        # Flask doesn't provide a straightforward way to stop the server programmatically.

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')

        # Button to turn the camera on/off
        self.camera_btn = Button(text="Turn Camera On")
        self.camera_btn.bind(on_press=self.toggle_camera)
        layout.add_widget(self.camera_btn)

        # Button to enable/disable audio
        self.audio_btn = Button(text="Enable Audio")
        self.audio_btn.bind(on_press=self.toggle_audio)
        layout.add_widget(self.audio_btn)

        # Button to start/stop the streaming server
        self.server_btn = Button(text="Start Server")
        self.server_btn.bind(on_press=self.toggle_server)
        layout.add_widget(self.server_btn)

        # Button to exit the application
        self.exit_btn = Button(text="Exit")
        self.exit_btn.bind(on_press=self.stop_app)
        layout.add_widget(self.exit_btn)

        return layout

    def toggle_camera(self, instance):
        global camera_on
        if not camera_on:
            camera_on = True
            self.camera_btn.text = "Turn Camera Off"
            threading.Thread(target=capture_video).start()
        else:
            camera_on = False
            self.camera_btn.text = "Turn Camera On"

    def toggle_audio(self, instance):
        global audio_on
        audio_on = not audio_on
        self.audio_btn.text = "Disable Audio" if audio_on else "Enable Audio"
        # Implement audio handling here

    def toggle_server(self, instance):
        global server_running
        if not server_running:
            start_server()
            self.server_btn.text = "Stop Server"
        else:
            stop_server()
            self.server_btn.text = "Start Server"

    def stop_app(self, instance):
        stop_server()
        App.get_running_app().stop()

if __name__ == '__main__':
    MyApp().run()

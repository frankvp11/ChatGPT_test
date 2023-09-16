# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.graphics.texture import Texture
from camera4kivy import Preview
import numpy as np
from kivy.utils import platform

kv_string = ('''
<CameraApp>:
    orientation: 'vertical'
    Preview:
        id: camera
        play: False
        resolution: (640, 480)
        size_hint_y: 0.9
    BoxLayout:
        size_hint_y: 0.1
        Button:
            text: "Toggle Camera"
            on_press: root.toggle_camera()
        Button:
            text: "Capture Image"
            on_press: root.capture_image()
''')
Builder.load_string(kv_string)

class CameraApp(BoxLayout):
    def toggle_camera(self):
        if self.ids.camera.play:
            self.ids.camera.connect_camera()
            self.ids.camera.play = False
        else:
            self.ids.camera.disconnect_camera()
            self.ids.camera.play = True

    def capture_image(self):
        # Capture the image from the camera
        self.ids.camera.export_to_png("temp.jpg")
        self.ids.camera.disconnect_camera()
        self.ids.camera.clear_widgets()
        self.ids.camera.add_widget(Image(source="temp.jpg"))
    


class MyApp(App):
    def build(self):
        return CameraApp()

if __name__ == '__main__':
    MyApp().run()

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

if platform == 'android':
    from android.permissions import request_permissions, Permission
#
kv_string = ('''
<CameraApp>:
    orientation: 'vertical'
    Preview:
        id: camera
        play: True
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
        if platform == 'android':
            def android_callback(permissions, status):
                if all(status):
                    self.camera_toggle()
                    print('passed permission checks')
            request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.INTERNET, Permission.RECORD_AUDIO], android_callback)
        else:
            self.camera_toggle()

    def camera_toggle(self):
        if self.ids.camera.play:
            self.ids.camera.connect_camera(data_format="rgba", enable_video=False)
            self.ids.camera.play = False
        else:
            self.ids.camera.disconnect_camera()
            self.ids.camera.play = True

    def capture_image(self):
        # Capture the image from the camera
        image = self.ids.camera.export_as_image()
        image.texture.flip_vertical()
        self.ids.camera.disconnect_camera()
        self.ids.camera.clear_widgets()
        self.ids.camera.add_widget(Image(texture=image.texture))
    


class MyApp(App):
    def build(self):
        return CameraApp()

if __name__ == '__main__':
    MyApp().run()

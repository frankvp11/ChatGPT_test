# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.graphics.texture import Texture
from camera4kivy import Preview
import numpy as np
from kivy.utils import platform


#new imports
from ultralytics import YOLO
import cv2

if platform == 'android':
    from android.permissions import request_permissions, Permission
#


'''
        size_hint_y: 0.2
        TextInput:
            text: "Rows:"
        TextInput:
            text: "Columns:"
'''
kv_string = ('''
<CameraApp>:
    orientation: 'vertical'
    Preview:
        id: camera
        play: True
        resolution: (640, 480)
        size_hint_y: 0.6
    BoxLayout:
        size_hint_y: 0.2
        DropDown:
            Button: 
                text: "RREF"
                on_press: root.select("item1")
            Button:
                text: "REF"
                on_press: root.select("item2")
    BoxLayout:
        size_hint_y: 0.2
        Button:
            text: "Solve"
            on_press: root.solve()
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
    

    def sort_bboxes(self, bboxes):
    # Calculate the center y-coordinate of each bounding box
        bboxes = sorted(bboxes, key=lambda x: ((x[1] + x[3]) / 2, x[0]))

        # Determine the average height of bounding boxes to use as a heuristic
        avg_height = sum([box[3] - box[1] for box in bboxes]) / len(bboxes)

        sorted_bboxes = []
        row = []
        for i in range(len(bboxes)):
            row.append(bboxes[i])

            if i == len(bboxes) - 1 or bboxes[i+1][1] - bboxes[i][3] > avg_height / 2:
                row = sorted(row, key=lambda x: x[0])  # sort the row based on x
                sorted_bboxes.extend(row)
                row = []

        return sorted_bboxes    

    def form_matrix(self, bboxes, N=3, M=3):
        # Sort by y value
        bboxes = sorted(bboxes, key=lambda x: x[1])
        avg_height = sum([box[3] - box[1] for box in bboxes]) / len(bboxes)
        avg_width=  sum([box[2] - box[0] for box in bboxes]) / len(bboxes)
        #debugging
        print(f"Average height {avg_height}, width {avg_width}")
        # Group into rows. Basically, if it's y coordinate is too big a gap between the previous, it will consider it a new row.
        rows = []
        row = [bboxes[0]]
        for i in range(1, len(bboxes)):
            if bboxes[i][1] > row[-1][1]+(avg_height * 0.75):  # adjustable factor
                rows.append(row)
                row = []
            row.append(bboxes[i])
        rows.append(row)  # Add the last row
        print(f" Rows {rows}")
        # rows = rows[:1]
        # Group within rows for multi-digit numbers.
        def group_bboxes(row, M):
            row = sorted(row, key=lambda x: x[0])
            numbers = []

            while len(row) > M:
                # Calculate horizontal gaps between adjacent bounding boxes
                gaps = [(row[i+1][0] - row[i][2], i) for i in range(len(row)-1)]
                # Find the smallest gap
                smallest_gap = min(gaps, key=lambda x: x[0])

                # Merge bounding boxes that have the smallest gap
                idx_to_merge = smallest_gap[1]
                merged_bbox = [
                    row[idx_to_merge][0],
                    row[idx_to_merge][1],
                    row[idx_to_merge+1][2],
                    max(row[idx_to_merge][3], row[idx_to_merge+1][3]),
                    float(str(int(row[idx_to_merge][4])) + str(int(row[idx_to_merge+1][4])))
                ]

                # Replace the original bounding boxes with the merged one
                row = row[:idx_to_merge] + [merged_bbox] + row[idx_to_merge+2:]

            for bbox in row:
                numbers.append(str(int(bbox[4])))

            return numbers

        matrix = []
        for row in rows:
            matrix.append(group_bboxes(row, M))


        return matrix
  
    def kivy_to_opencv(self, kivy_image):
        # Extract pixel data from Kivy Image's texture
        image_data = np.frombuffer(kivy_image.texture.pixels, dtype=np.uint8)

        # Reshape the data
        image_data = image_data.reshape(kivy_image.texture.size[1], kivy_image.texture.size[0], 4)

        # Convert from RGBA to BGR
        opencv_image = cv2.cvtColor(image_data, cv2.COLOR_RGBA2GRAY) # COLOR_RGBA2BGR
        _, thresh = cv2.threshold(opencv_image, 90, 255, cv2.THRESH_BINARY)
        thresh = cv2.bitwise_not(thresh)
        binary_bgr_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        return binary_bgr_image

    def solve(self):
        self.model = YOLO("best2.pt")
        new_image =  self.kivy_to_opencv(self.image)
        new_image = cv2.flip(new_image, -1)  # The '-1' denotes both horizontal and vertical flipping
        
        new_image = cv2.flip(new_image, 0)

        # newvalue = newvalue.reshape(height, width, 4)
        results = self.model.predict(new_image, conf=0.4)
        for result in results:
            
            for (x0, y0, x1, y1), (cls) in zip(result.boxes.xyxy, result.boxes.cls):
                # print(cls.item())
                cv2.rectangle(new_image, (int(x0), int(y0)), (int(x1), int(y1)), color=(0,255,0), thickness=2)
                cv2.putText(new_image, str(cls.item()), (int(x0), int(y0)-5), fontFace = cv2.FONT_ITALIC, fontScale = 0.6, color = (0, 255, 0), thickness=2)

        # cv2.imshow("image", new_image)

        list_of_coords =[ ]
        for box in results:
            for (x0, y0, x1, y1), (cls) in zip(box.boxes.xyxy, box.boxes.cls):
                list_of_coords.append([x0.item(), y0.item(), x1.item(), y1.item(), cls.item()])
        try:
            sorted_boxes = (self.sort_bboxes(list_of_coords))

            matrix = self.form_matrix(sorted_boxes, 3, 4)
        except:
            #print("oh well!")
            matrix = [[1,2,3], [4,5,6], [7,8,9]]
        self.ids.camera.clear_widgets()

        size_x = 1 / len(matrix)
        size_y=  1 / len(matrix[0])
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                self.ids.camera.add_widget(
                    Label(text=str(matrix[i][j]), pos_hint=(200, 200), size_hint=(size_x, size_y))
                )
                print("added widget!")



    def capture_image(self):
        # Capture the image from the camera
        self.image = self.ids.camera.export_as_image()
        self.image.texture.flip_vertical()
        self.image.texture.flip_horizontal()
        self.ids.camera.disconnect_camera()
        self.ids.camera.clear_widgets()
        self.ids.camera.add_widget(Image(texture=self.image.texture))
    


class MyApp(App):
    def build(self):
        return CameraApp()

if __name__ == '__main__':
    MyApp().run()

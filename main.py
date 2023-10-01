# main.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.graphics.texture import Texture
from camera4kivy import Preview
import numpy as np
from kivy.utils import platform
from kivy.uix.textinput import TextInput
# import sympy
import requests
#new imports
# from ultralytics import YOLO
import cv2

if platform == 'android':
    from android.permissions import request_permissions, Permission

        # Button:
        #     text: "Compute Solution"
        #     on_press: root.handle_solve(main_button.text)
        #     size_hint_x: 0.5




kv_string = ('''
<CameraApp>:
    orientation: 'vertical'

    Preview:
        id: camera
        play: True
        resolution: (640, 480)
        size_hint_y: 0.6

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: 0.1

        Button:
            id: main_button
            text: 'Click for Dropdown'
            on_release: dropdown.open(self)
            size_hint_x: 0.5
        DropDown:
            id: dropdown
            size_hint_y: None
            height: 0  # Start with 0 height so it doesn't show

            Button:
                text: 'Reduced Row Echelon Form'
                size_hint_y: None
                height: 44
                on_release: 
                    root.ids.main_button.text = self.text
                    dropdown.select(self.text)
                    dropdown.height = 0  # Collapse dropdown after selecting
            Button:
                text: 'To be determined'
                size_hint_y: None
                height: 44
                on_release: 
                    root.ids.main_button.text = self.text
                    dropdown.select(self.text)
                    dropdown.height = 0  # Collapse dropdown after selecting
            Button:
                text: 'To be determined'
                size_hint_y: None
                height: 44
                on_release: 
                    root.ids.main_button.text = self.text
                    dropdown.select(self.text)
                    dropdown.height = 0  # Collapse dropdown after selecting

    BoxLayout:
        size_hint_y: 0.1
        Button:
            text: "Extract Matrix"
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
        # Sort by y value to group by rows
        def group_by_rows(bboxes):
            bboxes = sorted(bboxes, key=lambda x: x[1])
            avg_height = sum([box[3] - box[1] for box in bboxes]) / len(bboxes)

            # Group into rows
            rows = []
            row = [bboxes[0]]
            for i in range(1, len(bboxes)):
                if bboxes[i][1] > row[-1][1] + (avg_height * 0.5):  # adjustable factor
                    rows.append(sorted(row, key=lambda x : x[0]))
                    row = []
                row.append(bboxes[i])
            rows.append(sorted(row, key=lambda x : x[0]))  # Add the last row
            return rows

        # Group each row into columns using x-coordinates
        def group_by_columns(bboxes):
            bboxes_sorted = sorted(bboxes, key=lambda x: x[0])
            avg_width = sum([box[2] - box[0] for box in bboxes_sorted]) / len(bboxes_sorted)

            cols = []
            col = [bboxes_sorted[0]]
            temp = [box[-1] for box in bboxes_sorted]
            for i in range(1, len(bboxes_sorted)):
                # Calculate the gap between the current bounding box and the previous one
                gap =  bboxes_sorted[i][0] -col[-1][0] 
                # If the gap is larger than half the average width, create a new column
                if abs(gap) > (avg_width * 0.5):  # adjustable factor

                    cols.append(sorted(col, key=lambda x : x[1]))
                    col = []
                
                col.append(bboxes_sorted[i])

            # Append the last column
            if col:
                cols.append(sorted(col, key=lambda x : x[1]))

            return cols

        rows = group_by_rows(bboxes)
        new_rows =[]
        for row in rows:
            new_rows.append([i[-1] for i in row])
        rows = new_rows
        print(f"Rows {new_rows}")
        cols = group_by_columns(bboxes)
        new_cols = []
        for col in cols:
            new_cols.append([i[-1] for i in col])
        cols = new_cols
        print(f"Columns {cols}")

        def merge_matrices(rows_matrix, cols_matrix):
            # Calculate dimensions
            num_rows = len(rows_matrix)

            num_cols = max(max(len(row) for row in rows_matrix), max(len(col) for col in cols_matrix))

            merged_matrix = []

            # Iterate over each cell by row and column
            for i in range(num_rows):
                row = []
                for j in range(num_cols):
                    if len(rows_matrix) > i and len(rows_matrix[i]) > j:
                        row_value = rows_matrix[i][j]
                    else:
                        row_value = ""

                    if len(cols_matrix) > j and len(cols_matrix[j]) > i:
                        col_value = cols_matrix[j][i]
                    else:
                        col_value = ""

                    # Choose value from either rows_matrix or cols_matrix. If both have a value, they should match
                    if row_value and col_value and row_value != col_value:
                        print(f"Conflicting values at {i}, {j}: {row_value} vs. {col_value}")
                        row.append(" ")
                    else:
                        value = row_value or col_value
                        row.append(value)
                merged_matrix.append(row)

            return merged_matrix
        return merge_matrices(rows, cols)


  
    def kivy_to_opencv(self, kivy_image):
        image_data = np.frombuffer(kivy_image.texture.pixels, dtype=np.uint8)
        image_data = image_data.reshape(kivy_image.texture.size[1], kivy_image.texture.size[0], 4)
        opencv_image = cv2.cvtColor(image_data, cv2.COLOR_RGBA2GRAY) # COLOR_RGBA2BGR
        img_blurred = cv2.GaussianBlur(opencv_image, (5, 5), 0)
        img_threshold = cv2.adaptiveThreshold(
            img_blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        thresh = cv2.bitwise_not(img_threshold)
        binary_bgr_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        return binary_bgr_image

    def solve(self):
        # self.model = YOLO("best_float32.tflite")
        new_image =  self.kivy_to_opencv(self.image)
        new_image = cv2.flip(new_image, -1)  #
        
        new_image = cv2.flip(new_image, 0)
        is_success, image_buf = cv2.imencode(".jpg", new_image)
        if not is_success:
            print("Failed to encode image")
            return

        # Use the requests library to send the image
        files = {'file': ("image2.jpg", image_buf.tobytes(), 'image/jpg')}
        try:
            API_ENDPOINT = "http://127.0.0.1:8000/predict/"
            response = requests.post(API_ENDPOINT, files=files)
            if response.status_code == 200:
                print(response.json())
                matrix = response.json()['predictions']
            else:
                print(f"Failed with status code: {response.status_code}, response: {response.text}")
                matrix = [[1,2, 3]]
        except Exception as e:
            print(f"Exception occurred: {str(e)}")





        self.ids.camera.clear_widgets()
        self.grid_layout = GridLayout(cols=len(matrix[0]), size_hint=(0.5, 0.5))

        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                self.grid_layout.add_widget(TextInput(text=str(matrix[i][j]), size_hint=(0.5, 0.5)))

        self.ids.camera.add_widget(self.grid_layout)

    def get_matrix_from_input(self, grid_layout):
        """Get the matrix values from the grid of TextInput widgets."""
        matrix = []
        row = []
        for i, child in enumerate(grid_layout.children):
            row.append(float(child.text))
            if (i + 1) % grid_layout.cols == 0:  
                matrix.append(row)
                row = []
        matrix.reverse()  
        for m in matrix:
            m.reverse()
        return matrix
    

    # def reduced_row_echelon_form(self, matrix):
    #     m = sympy.Matrix(matrix)
    #     return m.rref()


    # def handle_solve(self, option):
    #     abbrev = ''.join([word[0] for word in option.split()]).lower()

    #     if (abbrev == "rref"):
    #         matrix = self.get_matrix_from_input(self.grid_layout)
    #         matrix = self.reduced_row_echelon_form(matrix)[0].tolist()
    #         self.grid_layout.clear_widgets()
    #         for i in range(len(matrix)):
    #             for j in range(len(matrix[i])):
    #                 answer = round(matrix[i][j])
    #                 self.grid_layout.add_widget(TextInput(text=str(answer), size_hint=(0.5, 0.5)))


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

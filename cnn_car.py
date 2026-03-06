import tflite_runtime.interpreter as tflite
import numpy as np
import cv2
from cam_car import*

class CnnCar(CamCar):

    def __init__(self):
        super().__init__()


    def predict_steering_angle(self):
        interpreter = tflite.Interpreter(model_path="PiCar_model_260305_1853.tflite") # path=Pfad zur .tflite Datei
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        interpreter.allocate_tensors()

        # img = cv2.imread("/home/pi/scripts/PiCar/pictures/2026-02-27_18_41_44.804_10000000210c65be_121.jpg")
        self.get_image()
        img = self.image

        # fac_t, fac_b = 0.28,0
        # h, w = img.shape[:2]
        # bottom = int(h - fac_b*h)
        # top = int(fac_t*h)
        # img_cropped = img[top:bottom,:,:]

        new_img = cv2.resize(img, (224, 224))
        new_img = new_img.astype(np.float32)
        new_img /= 255.
        new_img = np.expand_dims(new_img, axis=0)

        interpreter.set_tensor(input_details[0]['index'], new_img)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        return max(min(int(output_data[0][0]),135),45)
    

    def fahrmodus_cnn(self):
        while True:
            self.get_image()
            angle_predict = self.predict_steering_angle()
            self.steering_angle = self.glaettung_alpha(steering_angle=angle_predict, alpha=0.8)
            self.save_image()
            if self.state == "stop":
                print("CamCar Ende")
                break

def main():
    car = CnnCar()
    steering_angle = car.predict_steering_angle()
    print(steering_angle)

if __name__ == "__main__":
    main()
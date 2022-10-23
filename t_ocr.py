import time

import cv2 as cv
import numpy as np


def pos_to_char(pos):
    if pos < 10:
        return chr(ord('0') + pos)
    if 9 <= pos < 36:
        return chr(ord('a') + pos - 10)
    elif pos >= 36:
        return chr(ord('A') + pos - 36)

def predict_image(model, image):
    image = image[:, 20:100, :]
    image = cv.cvtColor(image, cv.COLOR_RGBA2GRAY)
    image = np.expand_dims(image, axis=(0, -1)).astype(np.float32)
    image /= 255.0
    image -= 0.5
    image *= 2
    rst = model.predict(image).squeeze()
    idxs = np.argmax(rst, axis=-1)
    txt = ''
    confs = []
    cnt = 0
    for idx in idxs:
        txt += pos_to_char(idx)
        confs.append(rst[cnt, idx])
        cnt += 1
    return txt, confs




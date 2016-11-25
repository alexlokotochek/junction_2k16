import settings
import cv2
import numpy as np


def cv_point(point):
    return (point[0], settings.HEIGHT - point[1])


def main():
    frame = np.ndarray([settings.HEIGHT, settings.WIDTH, 3])
    cv2.line(frame, cv_point((600, 10)), cv_point((250, 20)), (255, 255, 255))
    while True:
        cv2.imshow('simulator', frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break


if __name__ == '__main__':
    main()

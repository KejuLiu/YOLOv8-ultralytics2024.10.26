# Ultralytics YOLO 🚀, AGPL-3.0 license

import math

import cv2

from ultralytics import solutions
from ultralytics.utils.checks import check_imshow
from ultralytics.utils.plotting import Annotator, colors


class DistanceCalculation:
    """A class for calculating the distance between two objects in a real-time video stream using their tracking
    data.
    """

    def __init__(self, **kwargs):
        """
        Initializes an instance of the DistanceCalculation class, setting up configurations for tracking and calculating
        distances between objects.

        Args:
            **kwargs: Arbitrary keyword arguments for configuring the distance calculation process, such as parameters for object detection, tracking precision, and measurement units.
        """
        import ast

        self.args = solutions.solutions_yaml_load(kwargs)
        self.args.update(kwargs)
        self.annotator = None

        # Prediction & tracking information
        self.clss = None
        self.boxes = None
        self.trk_ids = None
        self.centroids = []

        # Mouse event information
        self.left_mouse_count = 0
        self.selected_boxes = {}

        self.env_check = check_imshow(warn=True)  # Check if environment supports imshow
        self.args["line_color"] = ast.literal_eval(self.args["line_color"])
        self.args["centroid_color"] = ast.literal_eval(self.args["centroid_color"])
        print(f"Ultralytics Solutions ✅ {self.args}")

    def mouse_event_for_distance(self, event, x, y, flags, param):
        """
        Manages mouse events for selecting regions in a real-time video stream.

        Args:
            event (int): The type of mouse event (e.g., cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN).
            x (int): The X-coordinate of the mouse pointer.
            y (int): The Y-coordinate of the mouse pointer.
            flags (int): Flags related to the event (e.g., cv2.EVENT_FLAG_CTRLKEY, cv2.EVENT_FLAG_SHIFTKEY).
            param (dict): Additional parameters passed to the function.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.left_mouse_count += 1
            if self.left_mouse_count <= 2:
                for box, track_id in zip(self.boxes, self.trk_ids):
                    if box[0] < x < box[2] and box[1] < y < box[3] and track_id not in self.selected_boxes:
                        self.selected_boxes[track_id] = box

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.selected_boxes = {}
            self.left_mouse_count = 0

    def calculate_distance(self, centroid1, centroid2):
        """
        Computes the distance between two centroids.

        Args:
            centroid1 (tuple): The (x, y) coordinates of the first centroid.
            centroid2 (tuple): The (x, y) coordinates of the second centroid.

        Returns:
            (tuple): The distance in meters and millimeters.
        """
        pixel_distance = math.sqrt((centroid1[0] - centroid2[0]) ** 2 + (centroid1[1] - centroid2[1]) ** 2)
        distance_m = pixel_distance / self.args["pixels_per_meter"]
        return distance_m, distance_m * 1000

    def start_process(self, im0, tracks):
        """
        Processes a video frame to compute the distance between two bounding boxes.

        Args:
            im0 (ndarray): The image frame.
            tracks (list): A list of tracks obtained from the object tracking process.

        Returns:
            im0 (ndarray): The processed image frame.
        """
        self.boxes, self.clss, self.trk_ids = solutions.extract_tracks(tracks)
        if self.trk_ids is not None:
            self.annotator = Annotator(im0, line_width=self.args["line_thickness"])
            for box, cls, track_id in zip(self.boxes, self.clss, self.trk_ids):
                self.annotator.box_label(box, color=colors(int(cls), True), label=self.args["names"][int(cls)])

                if len(self.selected_boxes) == 2:
                    for trk_id in self.selected_boxes.keys():
                        if trk_id == track_id:
                            self.selected_boxes[track_id] = box

            if len(self.selected_boxes) == 2:
                self.centroids = [
                    (
                        int((self.selected_boxes[trk_id][0] + self.selected_boxes[trk_id][2]) // 2),
                        int((self.selected_boxes[trk_id][1] + self.selected_boxes[trk_id][3]) // 2),
                    )
                    for trk_id in self.selected_boxes
                ]

                distance_m, distance_mm = self.calculate_distance(self.centroids[0], self.centroids[1])
                self.annotator.plot_distance_and_line(
                    distance_m, distance_mm, self.centroids, self.args["line_color"], self.args["centroid_color"]
                )

            self.centroids = []

        # Display the image if the environment supports it and view_img is set to True
        if self.args["view_img"] and self.env_check:
            cv2.namedWindow(self.args["window_name"])
            cv2.setMouseCallback(self.args["window_name"], self.mouse_event_for_distance)
            cv2.imshow(self.args["window_name"], im0)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                return

        return im0


if __name__ == "__main__":
    names = {0: "person", 1: "car"}  # example class names
    distance_calculation = DistanceCalculation(names=names)

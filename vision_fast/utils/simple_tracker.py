"""
simple_tracker.py

A lightweight Euclidean Distance Tracker (Centroid Tracking).
Assigns unique IDs to objects across frames based on spatial proximity.

Key Features:
- Deregisters objects that leave the frame.
- assigning persistent IDs even if detection flickers (max_disappeared).
- Used to map Vehicles -> Dummy Profiles.
"""

import math

class SimpleTracker:
    def __init__(self, max_disappeared=10, max_distance=150):
        """
        Args:
            max_disappeared (int): Frames to keep ID alive without detection.
            max_distance (int): Max pixels to associate a new detection with old ID.
        """
        self.next_object_id = 0
        self.objects = {}  # ID -> Centroid (x, y)
        self.disappeared = {} # ID -> Frames since last seen
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1
        return self.next_object_id - 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects):
        """
        Update tracker with a list of bounding box rectangles.
        Args:
            rects: List of [x1, y1, x2, y2]
        Returns:
            objects: Dict of {object_id: centroid}
        """
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        # 1. Calculate input centroids
        input_centroids = []
        for (startX, startY, endX, endY) in rects:
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids.append((cX, cY))

        # 2. If no objects tracked, register all
        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i])
        
        # 3. Match inputs to existing objects
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Compute Distance Matrix (Simple Euclidean)
            # Row = Object ID, Col = Input Centroid
            D = []
            for i in range(len(object_centroids)):
                row = []
                for j in range(len(input_centroids)):
                    dist = math.hypot(object_centroids[i][0] - input_centroids[j][0],
                                      object_centroids[i][1] - input_centroids[j][1])
                    row.append(dist)
                D.append(row)

            # Find smallest distance pairs
            # For simplicity without scipy/numpy: Greedy assignment
            # Find min in D, assign, set row/col to infinity, repeat
            
            rows = set(range(len(object_ids)))
            cols = set(range(len(input_centroids)))
            
            used_rows = set()
            used_cols = set()

            # Flatten and sort matches by distance
            matches = []
            for r in rows:
                for c in cols:
                    matches.append((D[r][c], r, c))
            
            matches.sort(key=lambda x: x[0]) # Sort by distance

            for (d, r, c) in matches:
                if r in used_rows or c in used_cols:
                    continue
                
                if d > self.max_distance:
                    continue

                object_id = object_ids[r]
                self.objects[object_id] = input_centroids[c]
                self.disappeared[object_id] = 0
                used_rows.add(r)
                used_cols.add(c)

            # 4. Handle Disappeared
            unused_rows = rows - used_rows
            for r in unused_rows:
                object_id = object_ids[r]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            # 5. Handle New Detections
            unused_cols = cols - used_cols
            for c in unused_cols:
                self.register(input_centroids[c])

        return self.objects

# read serial communication data and parse

import serial
import threading
from collections import deque


class SerialReader:
    def __init__(self, port):
        self.serial = serial.Serial(port, baudrate=250000)
        self.data_queue = deque(maxlen=10000)
        self.running = False
        self.thread = None
        self.sample_rate = None
        self.lof_score = None
        self.detected_class = None
        self.feature_vector = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._read_data, daemon=True)
        self.thread.start()

    def _read_data(self):
        while self.running:
            line = self.serial.readline().decode().strip()
            if line.startswith("Acc:"):
                # in format :"Acc:0.1, 0.2, 0.3"
                line = line.split(":")[-1]

                x, y, z = map(float, line.split(","))
                self.data_queue.append((x, y, z))
            elif line.startswith("P1:Hz"):
                # in format :"P1:Hz:100"
                # parse the line to extract sample rate
                self.sample_rate = float(line.split("=")[-1])
            elif line.startswith("P2:Features"):
                # in format :"P2:Features:0.1,0.2,0.3"
                # parse the line to extract feature vector
                line = line.split(":")[-1]
                splitted_line = line.split(",")[0:-1]
                self.feature_vector = list(map(float, splitted_line))
            elif line.startswith("P3:LOF"):
                # in format :"P3:LOF = 0.1"
                # parse the line to extract LOF score
                self.lof_score = float(line.split("=")[-1])
            elif line.startswith("P4:"):
                # in format :"P4:Detected class = 0"
                # parse the line to extract detected class
                self.detected_class = int(line.split("=")[-1])

    def get_latest_acc(self):
        if self.data_queue:
            return self.data_queue[-1]
        return None

    def has_data(self):
        return len(self.data_queue) > 0

    def __del__(self):
        self.running = False
        self.serial.close()
        print("Serial port closed.")

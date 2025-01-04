### Files

- **Arduino_sender.py**: Contains functions to find the Arduino port and send data to the Arduino.
- **keyboardCotroller.py**: Contains functions to generate random keys and map keys based on a target map.
- **main.py**: The main script that orchestrates the entire process, including capturing frames, finding targets, sending data to the Arduino, and handling keyboard inputs.
- **OBScapture.py**: Contains functions to capture frames from a virtual camera and manage saved screenshots.
- **turnLeftOrRight.py**: Contains functions to process images, filter colors, and perform template matching to determine the direction and distance of a target.

## Setup

1. Ensure you have Python installed on your system.
2. Install the required Python packages:
    ```sh
    pip install pyserial opencv-python pillow keyboard
    ```

## Usage

1. Connect your Arduino device to your computer.
2. Run the  script:
    ```sh
    python main.py
    ```
3. The script will start capturing frames, processing images, and sending data to the Arduino based on the detected targets and generated keys.
4. Press the `Esc` key to stop the script.

## Functions

### Arduino_sender.py

- `find_arduino_port()`: Finds the Arduino port based on VID and PID.
- `send_data_to_arduino()`: Sends data to the Arduino.

### keyboardCotroller.py

- `generate_random_key()`: Generates a random key based on the previous key.
- `map_keys()`: Maps keys based on the target map.

### OBScapture.py

- `capture_frame()`: Captures a frame from the virtual camera and saves it as an image.
- `delete_oldest_file()`: Deletes the oldest file in the directory if the number of files exceeds the maximum limit.

### turnLeftOrRight.py

- `filter_non_white_colors()`: Filters out non-white colors from the image.
- `filter_non_red_colors()`: Filters out non-red colors from the image.
- `template_matching()`: Performs multi-scale template matching to find the best match.
- `find_target()`: Finds the target in the screenshot and determines the direction and distance.

### main.py

- `delete_directory_on_exit()`: Deletes the specified directory on exit.
- Main loop: Captures frames, generates keys, finds targets, sends data to the Arduino, and handles keyboard inputs.

## License

This project is licensed under the MIT License.
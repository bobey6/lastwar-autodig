import pyautogui
import time
import pygame
import datetime
import pytz
import sys
from threading import Thread, Event
import signal

# Initialize pygame for audio playback
pygame.mixer.init()

# Global flag to control the main loop
running = True
stop_event = Event()

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit the script"""
    global running
    print("\nCtrl+C detected! Exiting script...")
    running = False
    stop_event.set()
    sys.exit(0)

# Set up the signal handler
signal.signal(signal.SIGINT, signal_handler)

def get_est_timestamp():
    """Get current timestamp in EST timezone"""
    est = pytz.timezone('US/Eastern')
    utc_now = datetime.datetime.now(pytz.utc)
    est_now = utc_now.astimezone(est)
    return est_now.strftime('%Y-%m-%d %H:%M:%S EST')

def countdown_timer(seconds, step_name, stop_event):
    """Display a countdown timer for a given step"""
    start_time = time.time()
    while time.time() - start_time < seconds and not stop_event.is_set():
        remaining = int(seconds - (time.time() - start_time))
        print(f"\r{step_name} - Time remaining: {remaining} seconds", end="")
        time.sleep(0.5)
    print()  # New line after countdown finishes

def start_countdown(seconds, step_name):
    """Start a countdown timer in a separate thread"""
    countdown_thread = Thread(target=countdown_timer, args=(seconds, step_name, stop_event))
    countdown_thread.daemon = True
    countdown_thread.start()
    return countdown_thread

def find_image(image_names, confidence=0.8, timeout=60, click_type=None, show_countdown=True):
    """
    Look for specified images on the screen
    
    Args:
        image_names: List of image filenames to search for
        confidence: Confidence threshold for image recognition
        timeout: How long to search before giving up (seconds)
        click_type: None, 'single', or 'double'
        show_countdown: Whether to show countdown timer
        
    Returns:
        (found_image_name, location) or (None, None) if timeout
    """
    if isinstance(image_names, str):
        image_names = [image_names]
    
    if show_countdown:
        countdown_thread = start_countdown(
            timeout, 
            f"Looking for {', '.join(image_names)}"
        )
        
    start_time = time.time()
    while time.time() - start_time < timeout and running:
        for img_name in image_names:
            try:
                location = pyautogui.locateCenterOnScreen(img_name, confidence=confidence)
                if location:
                    print(f"\n{get_est_timestamp()} Found {img_name} with confidence {confidence}")
                    
                    if click_type == 'single':
                        pyautogui.click(location)
                        print(f"{get_est_timestamp()} Single clicked {img_name}")
                    elif click_type == 'double':
                        pyautogui.doubleClick(location)
                        print(f"{get_est_timestamp()} Double clicked {img_name}")
                        
                    stop_event.set()  # Stop any running countdown
                    time.sleep(0.5)  # Brief pause after action
                    stop_event.clear()  # Reset the stop event
                    
                    return img_name, location
            except:
                # Silently continue if there's an error
                pass
                
        # Small pause between attempts to reduce CPU usage
        time.sleep(0.1)
    
    # If we reach here, we didn't find any image within timeout
    print(f"\n{get_est_timestamp()} Could not find any of: {', '.join(image_names)}")
    return None, None

def play_sound(sound_file):
    """Play a sound file using pygame"""
    try:
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
    except:
        print(f"{get_est_timestamp()} Could not play sound: {sound_file}")

def main_process():
    """Main automated process loop"""
    global running
    
    while running:
        print(f"\n{get_est_timestamp()} Starting the process...")
        
        # Step 1: Look for dig.png or dig_bluestacks.png
        print(f"{get_est_timestamp()} Looking for dig.png or dig_bluestacks.png...")
        found_img, _ = find_image(['dig.png', 'dig_bluestacks.png'], confidence=0.70, timeout=60, click_type='double', show_countdown=False)
        
        if not running:
            break
            
        if found_img is None:
            # Timeout occurred, start over
            continue
            
        # If we found dig_bluestacks.png, play sound and start over
        if found_img == 'dig_bluestacks.png':
            play_sound('dingdong.mp3')
            print(f"{get_est_timestamp()} Found dig_bluestacks.png - starting over")
            continue
        elif found_img == 'dig.png':
            play_sound('dingdong.mp3')
            
        # Step 2: Look for dig_cords.png or dig_cords_drone.png
        found_img, _ = find_image(['dig_cords.png', 'dig_cords_drone.png'], confidence=0.70, timeout=60, click_type='double')
        if found_img is None or not running:
            continue  # Timeout occurred, start over

        # Step 3: Look for start_digging1.png or start_digging1_drone.png
        found_img, _ = find_image(['start_digging1.png', 'start_digging1_drone.png'], confidence=0.70, timeout=60, click_type='single')
        if found_img is None or not running:
            continue  # Timeout occurred, start over
            
        # Step 4: Look for start_digging2.png or start_digging2_drone.png (with retry logic)
        retry_count = 0
        while retry_count < 2 and running:
            found_img, _ = find_image(['start_digging2.png', 'start_digging2_drone.png'], confidence=0.75, timeout=15, click_type='double')
            if found_img:
                break
            
            if not running:
                break
                
            # If not found, go back and click start_digging1 again
            print(f"{get_est_timestamp()} Going back to start_digging1...")
            found_img, _ = find_image(['start_digging1.png', 'start_digging1_drone.png'], confidence=0.70, timeout=60, click_type='single')
            if found_img is None:
                break  # If we can't find it, break the retry loop and start over
                
            retry_count += 1
        
        if found_img is None or not running:
            continue  # Timeout occurred, start over

        # Step 5: Look for start_digging3.png (with retry logic)
        retry_count = 0
        while retry_count < 2 and running:
            found_img, _ = find_image('start_digging3.png', confidence=0.75, timeout=8, click_type='double')
            if found_img:
                break
                
            if not running:
                break
                
            # If not found, go back and click start_digging2 again
            print(f"{get_est_timestamp()} Going back to start_digging2...")
            found_img, _ = find_image(['start_digging2.png', 'start_digging2_drone.png'], confidence=0.75, timeout=60, click_type='double')
            if found_img is None:
                break  # If we can't find it, break the retry loop and start over
                
            retry_count += 1
            
        if found_img is None or not running:
            continue  # Timeout occurred, start over

        # Step 6: Look for start_digging4.png every 50ms, wait up to 5 minutes
        print(f"{get_est_timestamp()} Looking for start_digging4.png (checking every 50ms, waiting up to 5 minutes)...")
        start_time = time.time()
        found = False
        
        # Start countdown for this longer wait
        countdown_thread = start_countdown(300, "Looking for start_digging4.png")
        
        while time.time() - start_time < 300 and running and not found:  # 5 minutes = 300 seconds
            try:
                location = pyautogui.locateCenterOnScreen('start_digging4.png', confidence=0.75)
                if location:
                    print(f"\n{get_est_timestamp()} Found start_digging4.png with confidence 0.75")
                    pyautogui.doubleClick(location)
                    print(f"{get_est_timestamp()} Double clicked start_digging4.png")
                    found = True
                    stop_event.set()  # Stop the countdown
                    time.sleep(0.5)
                    stop_event.clear()
                    break
            except:
                pass
            time.sleep(0.05)  # 50 milliseconds
            
        if not found or not running:
            continue  # Timeout occurred, start over

        # Step 7: Look for finish_digging.png
        found_img, _ = find_image('finish_digging.png', confidence=0.8, timeout=60, click_type='single')
        if found_img is None or not running:
            continue  # Timeout occurred, start over
            
        print(f"{get_est_timestamp()} Completed one cycle, starting over...")

if __name__ == "__main__":
    print(f"{get_est_timestamp()} Starting dig automation script")
    print("Press Ctrl+C to exit")
    
    try:
        main_process()
    except KeyboardInterrupt:
        print("\nExiting script...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        pygame.quit()

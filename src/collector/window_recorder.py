import os
import subprocess
import time
from enum import Enum
from typing import Optional

from .logging_config import get_logger
from .window_manager import WindowManager

logger = get_logger(__name__)

# FFmpeg command constants
DEFAULT_FRAMERATE = 30
DEFAULT_BITRATE = "4000k"
DEFAULT_CODEC = "h264"


class Quality(Enum):
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"


class WindowRecorder:
    """Records a window using FFmpeg with coordinates from WindowManager."""

    def __init__(self, window_manager: WindowManager, quality: Quality = Quality.SLOW):
        """
        Initialize WindowRecorder with a WindowManager instance.

        Args:
            window_manager: WindowManager instance to get window information
        """
        self.window_manager = window_manager
        self.recording_process: Optional[subprocess.Popen] = None
        self.current_output_file: Optional[str] = None
        self.quality = quality

    def start_recording(self,
                        output_dir: str,
                        filename: Optional[str] = None,
                        video_codec: str = DEFAULT_CODEC,
                        audio: bool = False,
                        audio_device: Optional[str] = None,
                        framerate: int = DEFAULT_FRAMERATE,
                        quality: Quality = None,
                        bitrate: str = DEFAULT_BITRATE) -> bool:
        if self.recording_process:
            logger.warning("Recording already in progress")
            return False

        if quality is None:
            quality = self.quality

        try:
            # Get window coordinates from WindowManager
            rect = self.window_manager.get_rect()
            if not rect:
                logger.error("Failed to get window coordinates")
                return False

            left, top, right, bottom = rect
            width = right - left
            height = bottom - top

            # Prepare output filename
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.mp4"

            output_path = os.path.join(output_dir, filename)
            self.current_output_file = output_path

            # Build FFmpeg command
            command = [
                "ffmpeg",
                "-f", "gdigrab",
                "-framerate", str(framerate),
                "-offset_x", str(left),
                "-offset_y", str(top),
                "-video_size", f"{width}x{height}",
                "-i", "desktop",
            ]

            # Add audio if requested
            if audio:
                # If no specific audio device is provided, try to use a default one
                if not audio_device:
                    # Try common device names or let FFmpeg use default
                    audio_device = "麦克风 (HECATE G1500 BAR)"  # Using the device found on your system

                command.extend([
                    "-f", "dshow",
                    "-i", f"audio={audio_device}",
                ])

            # Add output options
            command.extend([
                "-c:v", video_codec,
                "-preset", quality.value,
                "-b:v", bitrate,
                "-pix_fmt", "yuv420p",  # For better compatibility
                "-y",  # Overwrite output file if exists
                output_path
            ])

            logger.info(f"Starting recording to {output_path}")
            logger.info(f"FFmpeg command: {' '.join(command)}")

            # Start FFmpeg process using parent's stdout/stderr for direct output
            self.recording_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,  # Keep stdin pipe for sending 'q' to stop
                # Using parent process stdout/stderr by default
                text=True,  # Enable text mode for easier string handling
                creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
            )

            # Wait briefly to ensure process started

            # Check if the process started successfully
            if self.recording_process.poll() is not None:
                logger.error(f"FFmpeg failed to start (exit code: {self.recording_process.returncode})")
                self.recording_process = None
                return False

            logger.info("Recording started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process = None
            return False

    def stop_recording(self) -> bool:
        """
        Stop the current recording by gracefully terminating the FFmpeg process.

        Returns:
            bool: True if recording was stopped successfully, False otherwise
        """
        if not self.recording_process:
            logger.warning("No recording in progress")
            return False

        try:
            logger.info("Stopping FFmpeg recording process...")

            # Try to send 'q' to FFmpeg for graceful termination
            try:
                self.recording_process.communicate(input="q", timeout=5)
            except subprocess.TimeoutExpired:
                # If 'q' command times out, force termination
                logger.warning("FFmpeg did not terminate after sending 'q', forcing termination")
                self.recording_process.terminate()
                self.recording_process.wait(timeout=5)

            # Double-check process is terminated
            if self.recording_process.poll() is None:
                logger.warning("FFmpeg still running, killing process")
                self.recording_process.kill()
                self.recording_process.wait(timeout=2)

            logger.info(f"Recording stopped: {self.current_output_file}")
            self.recording_process = None

            return True

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            # Force terminate if needed
            if self.recording_process and self.recording_process.poll() is None:
                self.recording_process.kill()
                self.recording_process = None
            return False

    def is_recording(self) -> bool:
        """
        Check if recording is in progress.

        Returns:
            bool: True if recording is in progress, False otherwise
        """
        return self.recording_process is not None and self.recording_process.poll() is None

    def get_output_file(self) -> Optional[str]:
        """
        Get the current output file path.

        Returns:
            Optional[str]: Path to current output file if recording, None otherwise
        """
        return self.current_output_file if self.is_recording() else None

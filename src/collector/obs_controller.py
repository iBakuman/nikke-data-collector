import os
import time
from dataclasses import dataclass
from typing import Optional

# For OBS Websocket
import obsws_python as obs

from .logging_config import get_logger
from .window_manager import WindowManager

logger = get_logger(__name__)


@dataclass
class OBSInfo:
    host: str = "localhost"
    port: int = 4455
    password: str = ""
    timeout: int = 5


class OBSController:
    """Controls OBS Studio via Websocket API to record window content."""

    def __init__(self, window_manager: WindowManager, scene_name: str = "collector", obs_info: OBSInfo = OBSInfo()):
        """
        Initialize OBSController with a WindowManager instance.

        Args:
            window_manager: WindowManager instance to get window information
            obs_info: OBS websocket connection information
        """
        self.window_manager = window_manager
        self.obs_info = obs_info
        self.client: Optional[obs.ReqClient] = None
        self.current_output_file: Optional[str] = None
        self.is_connected = False
        self.scene_name = scene_name

    def connect(self) -> bool:
        """
        Connect to OBS Studio via websocket.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to OBS at {self.obs_info.host}:{self.obs_info.port}")
            self.client = obs.ReqClient(
                host=self.obs_info.host,
                port=self.obs_info.port,
                password=self.obs_info.password,
                timeout=self.obs_info.timeout,
            )

            # Test connection
            version = self.client.get_version()
            logger.info(f"Connected to OBS Studio {version.obs_version}")
            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Error connecting to OBS: {e}")
            self.client = None
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from OBS Studio websocket."""
        if self.client:
            logger.info("Disconnecting from OBS")
            self.client = None
            self.is_connected = False

    def setup_window_capture(self, input_name: str = "NIKKE") -> bool:
        """
        Create or update a window capture source in OBS.

        Args:
            input_name: Name of the source in OBS

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        try:
            # Get window information
            window_info = self.window_manager.get_window_info()
            if not window_info:
                logger.error("Failed to get window information")
                return False

            # 1. Check and create scene if needed
            scenes = self.client.get_scene_list()
            scene_exists = False

            # Check if scene exists in OBS
            for scene in scenes.scenes:
                if isinstance(scene, dict) and 'sceneName' in scene:
                    if scene['sceneName'] == self.scene_name:
                        scene_exists = True
                        break
                elif hasattr(scene, 'scene_name') and scene.scene_name == self.scene_name:
                    scene_exists = True
                    break

            # Create the scene if it doesn't exist
            if not scene_exists:
                logger.info(f"Creating scene '{self.scene_name}'")
                self.client.create_scene(self.scene_name)

            # 2. Remove existing input if it exists
            try:
                self.client.remove_input(name=input_name)
                logger.info(f"Removed existing source '{input_name}'")
            except Exception:
                # Source might not exist, that's fine
                pass

            # 3. Create the window capture source
            logger.info(f"Creating window capture source '{input_name}'")

            # Create source settings
            source_settings = {
                "window": self.window_manager.process_name,
                "capture_window_title": True,
            }

            # Create the input using proper parameter names for OBS WebSocket
            # Based on the error, we use proper parameter names
            self.client.create_input(
                sceneName=self.scene_name,
                inputName=input_name,
                inputKind="window_capture",
                inputSettings=source_settings,
                sceneItemEnabled=True
            )

            logger.info(f"Window capture source '{input_name}' configured successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up window capture: {e}")
            return False

    def start_recording(self, output_dir: str, filename: Optional[str] = None) -> bool:
        """
        Start recording in OBS Studio.

        Args:
            output_dir: Directory to save the recording
            filename: Optional filename override (OBS output settings will be used if not specified)

        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        if self.is_recording():
            logger.warning("Recording already in progress")
            return False

        try:
            profile_list = self.client.get_profile_list()
            profiles = profile_list.profiles
            logger.info(f"Available profiles: {profile_list.profiles}")
            # Prepare output path if filename is specified
            if filename:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)

                # Try to configure output settings
                logger.info(f"Setting recording output path to {output_dir}")
                self.client.set_profile_parameter(
                    category="Output",
                    name="RecFilePath",
                    value=output_dir
                )

                # Set filename without extension (OBS adds it)
                base_filename = os.path.splitext(filename)[0]
                self.client.set_profile_parameter(
                    category="Output",
                    name="RecFormat",
                    value=base_filename
                )

                self.current_output_file = output_path
            else:
                # Get current recording path from OBS
                try:
                    rec_path = self.client.get_profile_parameter(
                        category="Output",
                        name="RecFilePath"
                    )
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    rec_dir = rec_path.value if hasattr(rec_path, 'value') else "."
                    self.current_output_file = os.path.join(rec_dir, f"recording_{timestamp}.mp4")
                except Exception:
                    # Use default path if we can't get the current path
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    self.current_output_file = f"recording_{timestamp}.mp4"

            # Start recording
            logger.info("Starting OBS recording")
            self.client.start_record()
            logger.info(f"Recording started. Output will be saved to {self.current_output_file}")
            return True

        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False

    def stop_recording(self) -> bool:
        """
        Stop the current recording.

        Returns:
            bool: True if recording was stopped successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        if not self.is_recording():
            logger.warning("No recording in progress")
            return False

        try:
            logger.info("Stopping OBS recording")
            result = self.client.stop_record()

            # Get output path from result if available
            if hasattr(result, 'outputPath'):
                self.current_output_file = result.outputPath
            elif hasattr(result, 'output_path'):
                self.current_output_file = result.output_path
            elif hasattr(result, 'path'):
                self.current_output_file = result.path

            logger.info(f"Recording stopped: {self.current_output_file}")
            return True

        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False

    def is_recording(self) -> bool:
        """
        Check if recording is in progress.

        Returns:
            bool: True if recording is in progress, False otherwise
        """
        if not self.is_connected or not self.client:
            return False

        try:
            status = self.client.get_record_status()
            return status.active if hasattr(status, 'active') else False
        except Exception:
            return False

    def get_output_file(self) -> Optional[str]:
        """
        Get the current output file path.

        Returns:
            Optional[str]: Path to current output file if recording, None otherwise
        """
        return self.current_output_file if self.is_recording() else None

    def start_streaming(self) -> bool:
        """
        Start streaming in OBS.

        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        if self.is_streaming():
            logger.warning("Streaming already in progress")
            return False

        try:
            logger.info("Starting OBS streaming")
            self.client.start_stream()
            logger.info("Streaming started")
            return True

        except Exception as e:
            logger.error(f"Error starting streaming: {e}")
            return False

    def stop_streaming(self) -> bool:
        """
        Stop the current streaming.

        Returns:
            bool: True if streaming was stopped successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        if not self.is_streaming():
            logger.warning("No streaming in progress")
            return False

        try:
            logger.info("Stopping OBS streaming")
            self.client.stop_stream()
            logger.info("Streaming stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping streaming: {e}")
            return False

    def is_streaming(self) -> bool:
        """
        Check if streaming is in progress.

        Returns:
            bool: True if streaming is in progress, False otherwise
        """
        if not self.is_connected or not self.client:
            return False

        try:
            status = self.client.get_stream_status()
            return status.active if hasattr(status, 'active') else False
        except Exception:
            return False

    def take_screenshot(self, output_path: str, source_name: str = "NIKKE Capture", width: int = 1920,
                        height: int = 1080) -> bool:
        """
        Take a screenshot using OBS.

        Args:
            output_path: Path to save the screenshot
            source_name: Name of the source to capture
            width: Width of the screenshot
            height: Height of the screenshot

        Returns:
            bool: True if screenshot was taken successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            logger.error("Not connected to OBS")
            return False

        try:
            # Ensure directory exists
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            logger.info(f"Taking screenshot with OBS, saving to {output_path}")

            # Take screenshot of the source using proper parameter names
            self.client.save_source_screenshot(
                sourceName=source_name,
                imageFormat="png",
                imageFilePath=output_path,
                imageWidth=width,
                imageHeight=height,
                imageCompressionQuality=100
            )

            logger.info(f"Screenshot saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False

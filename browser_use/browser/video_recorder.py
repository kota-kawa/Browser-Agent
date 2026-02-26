# EN: Describe this block with a docstring.
# JP: このブロックの説明をドキュメント文字列で記述する。
"""Video Recording Service for Browser Use Sessions."""

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import base64
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import logging
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import math
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
import subprocess
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from pathlib import Path
# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from typing import Optional

# EN: Import required modules.
# JP: 必要なモジュールをインポートする。
from browser_use.browser.profile import ViewportSize

# EN: Handle exceptions around this block.
# JP: このブロックで例外処理を行う。
try:
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import imageio.v2 as iio
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import imageio_ffmpeg
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	import numpy as np
	# EN: Import required modules.
	# JP: 必要なモジュールをインポートする。
	from imageio.core.format import Format

	# EN: Assign value to IMAGEIO_AVAILABLE.
	# JP: IMAGEIO_AVAILABLE に値を代入する。
	IMAGEIO_AVAILABLE = True
except ImportError:
	# EN: Assign value to IMAGEIO_AVAILABLE.
	# JP: IMAGEIO_AVAILABLE に値を代入する。
	IMAGEIO_AVAILABLE = False

# EN: Assign value to logger.
# JP: logger に値を代入する。
logger = logging.getLogger(__name__)


# EN: Define function `_get_padded_size`.
# JP: 関数 `_get_padded_size` を定義する。
def _get_padded_size(size: ViewportSize, macro_block_size: int = 16) -> ViewportSize:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""Calculates the dimensions padded to the nearest multiple of macro_block_size."""
	# EN: Assign value to width.
	# JP: width に値を代入する。
	width = int(math.ceil(size['width'] / macro_block_size)) * macro_block_size
	# EN: Assign value to height.
	# JP: height に値を代入する。
	height = int(math.ceil(size['height'] / macro_block_size)) * macro_block_size
	# EN: Return a value from the function.
	# JP: 関数から値を返す。
	return ViewportSize(width=width, height=height)


# EN: Define class `VideoRecorderService`.
# JP: クラス `VideoRecorderService` を定義する。
class VideoRecorderService:
	# EN: Describe this block with a docstring.
	# JP: このブロックの説明をドキュメント文字列で記述する。
	"""
	Handles the video encoding process for a browser session using imageio.

	This service captures individual frames from the CDP screencast, decodes them,
	and appends them to a video file using a pip-installable ffmpeg backend.
	It automatically resizes frames to match the target video dimensions.
	"""

	# EN: Define function `__init__`.
	# JP: 関数 `__init__` を定義する。
	def __init__(self, output_path: Path, size: ViewportSize, framerate: int):
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Initializes the video recorder.

		Args:
		    output_path: The full path where the video will be saved.
		    size: A ViewportSize object specifying the width and height of the video.
		    framerate: The desired framerate for the output video.
		"""
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.output_path = output_path
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.size = size
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.framerate = framerate
		# EN: Assign annotated value to target variable.
		# JP: target variable に型付きの値を代入する。
		self._writer: Optional['Format.Writer'] = None
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self._is_active = False
		# EN: Assign value to target variable.
		# JP: target variable に値を代入する。
		self.padded_size = _get_padded_size(self.size)

	# EN: Define function `start`.
	# JP: 関数 `start` を定義する。
	def start(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Prepares and starts the video writer.

		If the required optional dependencies are not installed, this method will
		log an error and do nothing.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not IMAGEIO_AVAILABLE:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(
				'MP4 recording requires optional dependencies. Please install them with: pip install "browser-use[video]"'
			)
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self.output_path.parent.mkdir(parents=True, exist_ok=True)
			# The macro_block_size is set to None because we handle padding ourselves
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._writer = iio.get_writer(
				str(self.output_path),
				fps=self.framerate,
				codec='libx264',
				quality=8,  # A good balance of quality and file size (1-10 scale)
				pixelformat='yuv420p',  # Ensures compatibility with most players
				macro_block_size=None,
			)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._is_active = True
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.debug(f'Video recorder started. Output will be saved to {self.output_path}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Failed to initialize video writer: {e}')
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._is_active = False

	# EN: Define function `add_frame`.
	# JP: 関数 `add_frame` を定義する。
	def add_frame(self, frame_data_b64: str) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Decodes a base64-encoded PNG frame, resizes it, pads it to be codec-compatible,
		and appends it to the video.

		Args:
		    frame_data_b64: A base64-encoded string of the PNG frame data.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_active or not self._writer:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Assign value to frame_bytes.
			# JP: frame_bytes に値を代入する。
			frame_bytes = base64.b64decode(frame_data_b64)

			# Build a filter chain for ffmpeg:
			# 1. scale: Resizes the frame to the user-specified dimensions.
			# 2. pad: Adds black bars to meet codec's macro-block requirements,
			#    centering the original content.
			# EN: Assign value to vf_chain.
			# JP: vf_chain に値を代入する。
			vf_chain = (
				f'scale={self.size["width"]}:{self.size["height"]},'
				f'pad={self.padded_size["width"]}:{self.padded_size["height"]}:(ow-iw)/2:(oh-ih)/2:color=black'
			)

			# EN: Assign value to output_pix_fmt.
			# JP: output_pix_fmt に値を代入する。
			output_pix_fmt = 'rgb24'
			# EN: Assign value to command.
			# JP: command に値を代入する。
			command = [
				imageio_ffmpeg.get_ffmpeg_exe(),
				'-f',
				'image2pipe',  # Input format from a pipe
				'-c:v',
				'png',  # Specify input codec is PNG
				'-i',
				'-',  # Input from stdin
				'-vf',
				vf_chain,  # Video filter for resizing and padding
				'-f',
				'rawvideo',  # Output format is raw video
				'-pix_fmt',
				output_pix_fmt,  # Output pixel format
				'-',  # Output to stdout
			]

			# Execute ffmpeg as a subprocess
			# EN: Assign value to proc.
			# JP: proc に値を代入する。
			proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			out, err = proc.communicate(input=frame_bytes)

			# EN: Branch logic based on a condition.
			# JP: 条件に応じて処理を分岐する。
			if proc.returncode != 0:
				# EN: Assign value to err_msg.
				# JP: err_msg に値を代入する。
				err_msg = err.decode(errors='ignore').strip()
				# EN: Branch logic based on a condition.
				# JP: 条件に応じて処理を分岐する。
				if 'deprecated pixel format used' not in err_msg.lower():
					# EN: Raise an exception.
					# JP: 例外を送出する。
					raise OSError(f'ffmpeg error during resizing/padding: {err_msg}')
				else:
					# EN: Evaluate an expression.
					# JP: 式を評価する。
					logger.debug(f'ffmpeg warning during resizing/padding: {err_msg}')

			# Convert the raw output bytes to a numpy array with the padded dimensions
			# EN: Assign value to img_array.
			# JP: img_array に値を代入する。
			img_array = np.frombuffer(out, dtype=np.uint8).reshape((self.padded_size['height'], self.padded_size['width'], 3))

			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._writer.append_data(img_array)
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.warning(f'Could not process and add video frame: {e}')

	# EN: Define function `stop_and_save`.
	# JP: 関数 `stop_and_save` を定義する。
	def stop_and_save(self) -> None:
		# EN: Describe this block with a docstring.
		# JP: このブロックの説明をドキュメント文字列で記述する。
		"""
		Finalizes the video file by closing the writer.

		This method should be called when the recording session is complete.
		"""
		# EN: Branch logic based on a condition.
		# JP: 条件に応じて処理を分岐する。
		if not self._is_active or not self._writer:
			# EN: Return a value from the function.
			# JP: 関数から値を返す。
			return

		# EN: Handle exceptions around this block.
		# JP: このブロックで例外処理を行う。
		try:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			self._writer.close()
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.info(f'📹 Video recording saved successfully to: {self.output_path}')
		except Exception as e:
			# EN: Evaluate an expression.
			# JP: 式を評価する。
			logger.error(f'Failed to finalize and save video: {e}')
		finally:
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._is_active = False
			# EN: Assign value to target variable.
			# JP: target variable に値を代入する。
			self._writer = None

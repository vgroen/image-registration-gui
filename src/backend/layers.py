from PyQt5.QtCore import QObject, pyqtSignal

import numpy as np
import cv2

import threading
import queue

import resource

import src.backend.conover as conover

class Layer(QObject): # Inherit QObject to use signals
    pixelsChanged = pyqtSignal()
    maskChanged = pyqtSignal()
    interpolationChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._filepath = None

        # RGB float32
        self._full_resolution = None
        self._full_resolution_masked = None

        # RGBA float32
        self._full_resolution_interpolated = None

        # RGBA float32
        self._changed_interpolation_coeff = False

        # RGBA float32 - Alpha for threshold
        self._full_resolution_mask = None
        self._downscaled_mask = None
        self._downscale_factor = 1
        self._changed_mask = True

        self._downscaled_content = None

        self._interpolation_coeff = (None, None)

        self._mask_queue = queue.Queue()
        self._thread = None
        self._stop_thread = True


    def width(self):
        if self._full_resolution is not None:
            return self._full_resolution.shape[1]
        return 0

    def height(self):
        if self._full_resolution is not None:
            return self._full_resolution.shape[0]
        return 0


    def filePath(self):
        return self._filepath
    
    def setFilePath(self, file_path):
        self._filepath = file_path
    

    def setInterpolationCoefficients(self, coeffx, coeffy):
        if (coeffx is None
            or coeffy is None
            or len(coeffx) == 0
            or len(coeffy) == 0
            or len(coeffx) != len(coeffy)
        ):
            self._interpolation_coeff = (None, None)
        else:
            self._interpolation_coeff = (coeffx, coeffy)
            self._full_resolution_interpolated = conover.deformImage(
                self.fullResolutionInterpolated(),
                self._interpolation_coeff[0],
                self._interpolation_coeff[1]
            ).astype(
                dtype=np.float32, subok=True, copy=False
            )
        
        self.interpolationChanged.emit()


    def fullResolutionInterpolated(self):
        if (self._interpolation_coeff[0] is None
            or self._interpolation_coeff[1] is None
            or self._full_resolution_interpolated is None
        ):
            self._full_resolution_interpolated = cv2.cvtColor(
                self.fullResolutionPixels().astype(np.float32),
                cv2.COLOR_RGB2RGBA
            )
        
        return self._full_resolution_interpolated
    

    def setFullResolutionInterpolated(self, pixels):
        if len(pixels.shape) < 2 or pixels.shape[2] != 4:
            return
        
        self._full_resolution_interpolated = pixels


    def fullResolutionMasked(self):
        if self.fullResolutionPixels() is None or self.fullResolutionMask() is None:
            return None
        
        if self._full_resolution_masked is None or self._changed_mask:
            _, mask = cv2.threshold(self.fullResolutionMask()[:,:,3], 0, 1, cv2.THRESH_BINARY_INV)
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB).astype(
                dtype=np.float16, subok=True, copy=False)

            self._full_resolution_masked = self.fullResolutionPixels() * mask
            self._changed_mask = False

        return self._full_resolution_masked
    

    def fullResolutionPixels(self):
        return self._full_resolution
    
    def setFullResolutionPixels(self, pixels):
        if pixels is None or len(pixels.shape) < 2:
            return
        
        if len(pixels.shape) == 2 or pixels.shape[2] == 1:
            # Monochrome
            pixels = cv2.cvtColor(pixels, cv2.COLOR_GRAY2RGB)
        elif pixels.shape[2] == 4:
            # RGBA
            pixels = cv2.cvtColor(pixels, cv2.COLOR_RGBA2RGB)
        
        if pixels.dtype == np.uint8:
            pixels = (pixels / 255).astype(
                dtype=np.float16, subok=True, copy=False)
        elif pixels.dtype == np.uint16:
            pixels = (pixels / 65535).astype(
                dtype=np.float16, subok=True, copy=False)
        else:
            pixels = pixels.astype(
                dtype=np.float16, subok=True, copy=False)

        self._full_resolution = pixels

        self.pixelsChanged.emit()
    

    def downscaleFactor(self):
        return self._downscale_factor


    def downscaledPixels(self):
        if self._downscaled_content is None:
            return self.fullResolutionPixels()
        return self._downscaled_content
    
    def downscaledMask(self):
        if self._downscaled_mask is None:
            return self.fullResolutionMask()
        return self._downscaled_mask
    
    def fullResolutionMask(self):
        return self._full_resolution_mask
    

    def endThread(self):
        self._stop_thread = True
        if self._thread is not None:
            self._thread.join()
        while self._mask_queue.qsize() > 0:
            self._mask_queue.get()

    
    def setFullResolutionMask(self, width, height):
        self.endThread()

        # Create the new mask
        self._full_resolution_mask = np.zeros((height, width, 4), dtype=np.float32)

        # Create a downscaled version
        leading_dim = max(width, height)
        self._downscale_factor = min(1, 1000 / leading_dim)

        if self._downscale_factor == 1:
            self._thread = None
        else:
            self._thread = threading.Thread(target=self._consumeMaskQueue)
            self._thread.daemon = True
            self._stop_thread = False
            self._thread.start()

            dw = int(width * self._downscale_factor)
            dh = int(height * self._downscale_factor)
            self._downscaled_mask = np.zeros((dh, dw, 4), dtype=np.float32)
            self._downscaled_content = cv2.resize(
                cv2.cvtColor(
                    self.fullResolutionPixels().astype(np.float32),
                    cv2.COLOR_RGB2RGBA
                ),
                (dw, dh),
                interpolation=cv2.INTER_CUBIC
            )

        self._changed_mask = True
        self.maskChanged.emit()
    

    def drawCircleToMask(self, cx, cy, radius, value):
        if self._downscale_factor == 1:
            cv2.circle(
                self._full_resolution_mask,
                (int(cx), int(cy)),
                int(radius),
                value, -1, -1, 0
            )
        else:
            self._mask_queue.put((
                (int(cx), int(cy)), int(radius), value
            ))

        cv2.circle(
            self._downscaled_mask,
            (
                int(cx * self._downscale_factor),
                int(cy * self._downscale_factor),
            ),
            int(radius * self._downscale_factor),
            value,
            -1, -1, 0
        )

        self._changed_mask = True
        self.maskChanged.emit()
    

    def _consumeMaskQueue(self):
        while not self._stop_thread:
            center, radius, value = self._mask_queue.get()
            cv2.circle(
                self._full_resolution_mask,
                center,
                radius,
                value,
                -1, -1, 0
            )


    def setImageData(self, file_path, pixels):
        if file_path is None or pixels is None:
            return
        
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        self.setFilePath(file_path)
        self.setFullResolutionPixels(pixels)
        self.setFullResolutionMask(pixels.shape[1], pixels.shape[0])

        self._full_resolution_masked = None
        self.fullResolutionMasked()

        print("{} MB".format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - before) // 1e3))

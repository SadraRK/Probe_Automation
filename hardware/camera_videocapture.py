try:
    from PySpin import PySpin
except Exception:
    from pyspin import PySpin
import cv2

class VideoCapture:
    """
    Open a FLIR camera for video capturing.

    Attributes
    ----------
    cam : PySpin.CameraPtr
        camera
    nodemap : PySpin.INodeMap
        nodemap represents the elements of a camera description file.
    grabTimeout : uint64_t
        a 64bit value that represents a timeout in milliseconds
    streamID : uint64_t
        The stream to grab the image.

    Methods
    -------
    read()
        returns the next frame.
    release()
        Closes capturing device.
    isOpened()
        Whether a camera is open or not.
    set(propId, value)
        Sets a property.
    get(propId)
        Gets a property.
    """

    def __init__(self, index):
        """
        Parameters
        ----------
        index : int
            id of the video capturing device to open.
        """
        self._system = PySpin.System.GetInstance()
        self._cam_list = self._system.GetCameras()
        # num_cam = self.cam_list.GetSize()
        try:
            if type(index) is int:
                self.cam = self._cam_list.GetByIndex(index)
            else:
                self.cam = self._cam_list.GetBySerial(index)
        except Exception:
            print("camera failed to properly initialize!")
            return None

        self.cam.Init()
        self.nodemap = self.cam.GetNodeMap()

        s_node_map = self.cam.GetTLStreamNodeMap()
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        handling_mode_entry = handling_mode.GetEntryByName('NewestOnly')
        handling_mode.SetIntValue(handling_mode_entry.GetValue())

        self.grabTimeout = PySpin.EVENT_TIMEOUT_INFINITE
        self.streamID = 0

    def __del__(self):
        try:
            if self.cam.IsStreaming():
                self.cam.EndAcquisition()
            self.cam.DeInit()
            del self.cam
            self._cam_list.Clear()
            self._system.ReleaseInstance()
        except Exception:
            pass

    def release(self):
        """
        Closes capturing device. The method call VideoCapture destructor.
        """
        self.__del__()

    def isOpened(self):
        """
        Returns true if video capturing has been initialized already.
        """
        try:
            return self.cam.IsValid()
        except Exception:
            return False

    def read(self):
        """
        returns the next frame.

        Returns
        -------
        retval : bool
            false if no frames has been grabbed.
        image : array_like 
            grabbed image is returned here. If no image has been grabbed the image will be None.
        """
        if not self.cam.IsStreaming():
            node_pixel_format = PySpin.CEnumerationPtr(self.nodemap.GetNode('PixelFormat'))
            node_pixel_format.SetIntValue(node_pixel_format.GetEntryByName('RGB8').GetValue())
            self.cam.BeginAcquisition()

        image = self.cam.GetNextImage(self.grabTimeout, self.streamID)
        if image.IsIncomplete():
            return False, None

        image_converted = image.Convert(PySpin.PixelFormat_BGR8)
        img_NDArray = image_converted.GetNDArray()
        image.Release()
        return True, img_NDArray

    def set(self, propId, value):
        """
        Sets a property in the VideoCapture.

        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties
        value : int or float or bool
            Value of the property.
        
        Returns
        -------
        retval : bool
           True if property setting success.
        """
        # Exposure setting
        if propId == cv2.CAP_PROP_EXPOSURE:
            # Auto
            if value < 0:
                return self._set_ExposureAuto(PySpin.ExposureAuto_Continuous)

            # Manual
            ret = self._set_ExposureAuto(PySpin.ExposureAuto_Continuous)
            if not ret:
                return False
            return self._set_ExposureTime(value)

        # Gain setting
        if propId == cv2.CAP_PROP_GAIN:
            # Auto
            if value < 0: return self._set_GainAuto(PySpin.GainAuto_Continuous)

            # Manual
            ret = self._set_GainAuto(PySpin.GainAuto_Off)
            if not ret: return False
            return self._set_Gain(value)

        # Brightness(EV) setting
        if propId == cv2.CAP_PROP_BRIGHTNESS:
            return self._set_Brightness(value)

        # Gamma setting
        if propId == cv2.CAP_PROP_GAMMA:
            return self._set_Gamma(value)

        # FrameRate setting
        if propId == cv2.CAP_PROP_FPS:
            return self._set_FrameRate(value)

        # BackLigth setting
        if propId == cv2.CAP_PROP_BACKLIGHT:
            return self._set_BackLight(value)

        # Trigger Mode setting (ON/OFF)
        if propId == cv2.CAP_PROP_TRIGGER:
            return self._set_Trigger(value)

        # TriggerDelay setting
        if propId == cv2.CAP_PROP_TRIGGER_DELAY:
            return self._set_TriggerDelay(value)

        return False

    def get(self, propId):
        """
        Returns the specified VideoCapture property.
        
        Parameters
        ----------
        propId_id : cv2.VideoCaptureProperties
            Property identifier from cv2.VideoCaptureProperties
        
        Returns
        -------
        value : int or float or bool
           Value for the specified property. Value False is returned when querying a property that is not supported.
        """
        if propId == cv2.CAP_PROP_EXPOSURE:
            return self._get_ExposureTime()

        if propId == cv2.CAP_PROP_GAIN:
            return self._get_Gain()

        if propId == cv2.CAP_PROP_BRIGHTNESS:
            return self._get_Brightness()

        if propId == cv2.CAP_PROP_GAMMA:
            return self._get_Gamma()

        if propId == cv2.CAP_PROP_FRAME_WIDTH:
            return self._get_Width()

        if propId == cv2.CAP_PROP_FRAME_HEIGHT:
            return self._get_Height()

        if propId == cv2.CAP_PROP_FPS:
            return self._get_FrameRate()

        if propId == cv2.CAP_PROP_TEMPERATURE:
            return self._get_Temperature()

        if propId == cv2.CAP_PROP_BACKLIGHT:
            return self._get_BackLight()

        if propId == cv2.CAP_PROP_TRIGGER:
            return self._get_Trigger()

        if propId == cv2.CAP_PROP_TRIGGER_DELAY:
            return self._get_TriggerDelay()

        return False

    def __clip(self, a, a_min, a_max):
        return min(max(a, a_min), a_max)

    def _set_ExposureTime(self, value):
        if not type(value) in (int, float): return False
        exposureTime_to_set = self.__clip(value, self.cam.ExposureTime.GetMin(), self.cam.ExposureTime.GetMax())
        self.cam.ExposureTime.SetValue(exposureTime_to_set)
        return True

    def _set_ExposureAuto(self, value):
        self.cam.ExposureAuto.SetValue(value)
        return True

    def _set_Gain(self, value):
        if not type(value) in (int, float): return False
        gain_to_set = self.__clip(value, self.cam.Gain.GetMin(), self.cam.Gain.GetMax())
        self.cam.Gain.SetValue(gain_to_set)
        return True

    def _set_GainAuto(self, value):
        self.cam.GainAuto.SetValue(value)
        return True

    def _set_Brightness(self, value):
        if not type(value) in (int, float): return False
        brightness_to_set = self.__clip(value, self.cam.AutoExposureEVCompensation.GetMin(),
                                        self.cam.AutoExposureEVCompensation.GetMax())
        self.cam.AutoExposureEVCompensation.SetValue(brightness_to_set)
        return True

    def _set_Gamma(self, value):
        if not type(value) in (int, float): return False
        gamma_to_set = self.__clip(value, self.cam.Gamma.GetMin(), self.cam.Gamma.GetMax())
        self.cam.Gamma.SetValue(gamma_to_set)
        return True

    def _set_FrameRate(self, value):
        if not type(value) in (int, float): return False
        self.cam.AcquisitionFrameRateEnable.SetValue(True)
        fps_to_set = self.__clip(value, self.cam.AcquisitionFrameRate.GetMin(), self.cam.AcquisitionFrameRate.GetMax())
        self.cam.AcquisitionFrameRate.SetValue(fps_to_set)
        return True

    def _set_BackLight(self, value):
        if value:
            backlight_to_set = PySpin.DeviceIndicatorMode_Active
        elif not value:
            backlight_to_set = PySpin.DeviceIndicatorMode_Inactive
        else:
            return False
        self.cam.DeviceIndicatorMode.SetValue(backlight_to_set)
        return True

    def _set_Trigger(self, value):
        if value:
            trigger_mode_to_set = PySpin.TriggerMode_On
        elif not value:
            trigger_mode_to_set = PySpin.TriggerMode_Off
        else:
            return False

        self.cam.TriggerMode.SetValue(trigger_mode_to_set)
        return True

    def _set_TriggerDelay(self, value):
        if not type(value) in (int, float): return False
        delay_to_set = self.__clip(value, self.cam.TriggerDelay.GetMin(), self.cam.TriggerDelay.GetMax())
        self.cam.TriggerDelay.SetValue(delay_to_set)
        return True

    def _get_ExposureTime(self):
        return self.cam.ExposureTime.GetValue()

    def _get_Gain(self):
        return self.cam.Gain.GetValue()

    def _get_Brightness(self):
        return self.cam.AutoExposureEVCompensation.GetValue()

    def _get_Gamma(self):
        return self.cam.Gamma.GetValue()

    def _get_Width(self):
        return self.cam.Width.GetValue()

    def _get_Height(self):
        return self.cam.Height.GetValue()

    def _get_FrameRate(self):
        return self.cam.AcquisitionFrameRate.GetValue()

    def _get_Temperature(self):
        return self.cam.DeviceTemperature.GetValue()

    def _get_BackLight(self):
        status = self.cam.DeviceIndicatorMode.GetValue()
        return (True if status == PySpin.DeviceIndicatorMode_Active else
                False if status == PySpin.DeviceIndicatorMode_Inactive else
                status)

    def _get_Trigger(self):
        status = self.cam.TriggerMode.GetValue()
        return (True if status == PySpin.TriggerMode_On else
                False if status == PySpin.TriggerMode_Off else
                status)

    def _get_TriggerDelay(self):
        return self.cam.TriggerDelay.GetValue()

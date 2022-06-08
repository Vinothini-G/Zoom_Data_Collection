import argparse
import subprocess

from zoom import Zoom

#default virtual camera device number
DEFAULT_VIRTUAL_CAMERA_DEVICE_NO = 5
#default name of the virtual camera
DEFAULT_VIRTUAL_CAMERA_DEVICE_NAME = 'VirtCam'
#default video file location
DEFAULT_VIDEO_FILE_LOCATION = '/mnt/hdd1/public_files/vca-qoe-vid.mp4' # vca-qoe-vid.mp4 or zoom-vid.mp4

def arg_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--config',help='Config file')
    parser.add_argument('--n_minions',type=int,help='Number of minions')
    parser.add_argument('--video',default=DEFAULT_VIDEO_FILE_LOCATION,
        help=f'Video to run through virtual camera. Pass empty string to disable [Default: {DEFAULT_VIDEO_FILE_LOCATION}]')
    parser.add_argument('--virtual-camera-device-no',default=DEFAULT_VIRTUAL_CAMERA_DEVICE_NO,
        help=f'Which virtual camera device to use [Default: {DEFAULT_VIRTUAL_CAMERA_DEVICE_NO}]')
    parser.add_argument('--virtual-camera-device-name',default=DEFAULT_VIRTUAL_CAMERA_DEVICE_NAME,
        help=f'Name of the virtual camera device [Default: {DEFAULT_VIRTUAL_CAMERA_DEVICE_NAME}]')

    return parser 

def main():
    parser = arg_parser()
    parser.add_argument('url', type=str, help='URL of the meeting to join')
    args = parser.parse_args()

    # with GoogleMeet(args.url, args, isMinion=True) as vca:
    with Zoom(args.url, args, isMinion=True) as vca:
        #start conference call from minion
        print("#### Minion args :: ", args)

        vca.login_zoom()
        vca.launch_driver()
        # vca.get_webrtc()
        vca.end_call()


if __name__ == '__main__':
    main()
import logging
import subprocess
import time 
from selenium import webdriver 
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

logging.basicConfig(format='%(asctime)s\t%(filename)s:%(lineno)d\t%(message)s', datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Zoom:
    def __init__(self, url, args, isMinion=True):
        self.args = args
        # print("### ARGS :: ", args)
        self.timer = 90 #seconds
        self.url = url
        self.profile = "/home/vinothini/.config/google-chrome" #/Default

        self.virtual_camera_feed = None
        self.isMinion = isMinion

        self.email = "vinothinisekar.g@gmail.com"
        self.password = "zoomData@123"


    def __enter__(self):
        """acquire resources -- start virtual camera, begin piping video, and start Chrome web driver"""
        if not self.isMinion and self.args.video and self.args.video != '':
            #use ffmpeg to pipe video into virtual camera
            self.virtual_camera_feed = subprocess.Popen([
                'ffmpeg',
                '-loglevel', 'quiet',
                '-stream_loop',
                '-1',
                '-re',
                '-i', self.args.video,
                '-map', '0:v',
                '-f', 'v4l2',
                f'/dev/video{self.args.virtual_camera_device_no}',
            ])

        #Set up web driver 
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument('--no-sandbox')

        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--start-maximizes')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

        return self

    
    def __exit__(self, exc_type, exc_value, traceback):
        """release acquired resources"""

        #shut down virtual camera feed if it is running
        if self.virtual_camera_feed:
            self.virtual_camera_feed.kill()

        #close the web driver
        self.browser.quit()


    def login_zoom(self):
        print("Zoom Login Attempt... ")
        self.driver.get('https://us04web.zoom.us/signin')

        #Enter login credentials
        account = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "email")))
        account.send_keys(self.email)
        passwrd = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))
        passwrd.send_keys(self.password)
        # self.driver.get_screenshot_as_file("login1.png")

        # Click the login button
        element = self.driver.find_element_by_xpath("//div[@class='signin']")
        button = element.find_element(By.TAG_NAME, "button")
        button.click()
        # self.driver.get_screenshot_as_file("login2.png")
        time.sleep(2)
        self.driver.get_screenshot_as_file("Zoom_Login.png")


    def launch_driver(self,duration=90): 
        #Get internal chrome tab that holds stats about webrtc sessions
        self.browser.get("chrome://webrtc-internals/")

        self.browser.execute_script("window.open('');")
        #switch to newly opened window
        self.browser.switch_to.window(self.browser.window_handles[1])
        time.sleep(2)


    def end_call(self):
        #press red end call button 
        leaveCall = WebDriverWait(self.browser, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//button[text()="Leave"]')))
        ActionChains(self.browser).move_to_element(leaveCall[0]).click().perform()
        time.sleep(3)
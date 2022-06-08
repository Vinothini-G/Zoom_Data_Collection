import logging
from pathlib import Path
from signal import SIGINT, SIGTERM
from subprocess import Popen, PIPE
from influxdb import InfluxDBClient, DataFrameClient
from time import gmtime, strftime, time
import salt.client
import validators
import statistics
import re

# number of times to attempt uploading data
UPLOAD_ATTEMPTS = 10

logging.basicConfig(format='%(asctime)s\t%(filename)s:%(lineno)d\t%(message)s', datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MinionHandler:
    project_path = "/mnt/hdd1/irene/VCA-QoE/ucsb-rpi/" #"/home/ubuntu/active-measurements/"
    _git = "git --git-dir={0}.git --work-tree={0}".format(project_path)
    local = None
    client = None

    def __init__(self, minion_id, in_minion=False):
        if not isinstance(minion_id, str):
            raise Exception(minion_id + " is not a string")

        if not in_minion:
            self.local = salt.client.LocalClient()
        self.minion_id = minion_id.strip()
        self.client = InfluxDBClient(host='snl-server-3.cs.ucsb.edu', port=8086, username='admin', password='ucsbsnl!!',
                                     ssl=True, verify_ssl=True)
        self.client.switch_database('netrics1')

        self.ts = str(int(time()))
        self.tshark_jid = ''

    @staticmethod
    def validate_address(address):
        if validators.url(address):
            return True
        if validators.domain(address):
            return True
        if validators.ip_address.ipv4(address):
            return True

        return False

    @staticmethod
    def parse_ping_output(output):
        ping_output = []
        lines = output.splitlines()
        for line in lines:
            if line.strip().startswith("64"):
                ping_output.append(re.findall(r'\d+\.*\d*', line)[-1])

        return [float(v) for v in ping_output]

    @staticmethod
    def calculate_average_video_quality(video_statistics):
        average_buffer_health = 0
        average_width = 0
        average_height = 0
        average_frame_rate = 0

        for stat in video_statistics['stats']:
            resolution = stat['current_optimal_res']
            width, height, frame_rate = re.findall(r'\d+\.*\d*', resolution)[:3]

            average_width += int(width)
            average_height += int(height)
            average_frame_rate += int(frame_rate)
            average_buffer_health += float(stat['buffer_health'])

        average_width /= len(video_statistics['stats'])
        average_height /= len(video_statistics['stats'])
        average_frame_rate /= len(video_statistics['stats'])
        average_buffer_health /= len(video_statistics['stats'])
        return average_width, average_height, average_frame_rate, average_buffer_health

    def _create_data_point(self, field, value):
        if not isinstance(field, str):
            raise Exception("field should be string")
        return ({
            "measurement": "networks",
            "tags": {
                "user": self.minion_id,
            },
            "time": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            "fields": {
                field: value
            }
        })

    def _upload_ping_result(self, address, ping):
        if not address:
            raise Exception("address cannot be empty")
        if not isinstance(ping, float):
            raise Exception("ping is not a valid number: {}".format(ping))

        return self.client.write_points([self._create_data_point("ping_to_{}".format(address), ping)])

    def _upload_speedtest_result(self, download, upload):
        if not isinstance(download, float) or not isinstance(upload, float):
            raise Exception("download/upload is not a valid number: {}/{}".format(download, upload))

        return self.client.write_points([self._create_data_point("speedtest_download", download),
                                         self._create_data_point("speedtest_upload", upload)])

    def upload_youtube_result(self, video_statistics):
        average_width, average_height, average_frame_rate, average_buffer_health = MinionHandler\
            .calculate_average_video_quality(video_statistics)

        return self.client.write_points([{
            "measurement": "networks",
            "tags": {
                "user": self.minion_id,
            },
            "time": strftime("%Y-%m-%dT%H:%M:%SZ", gmtime()),
            "fields": {
                'YouTube_average_width': average_width,
                'YouTube_average_height': average_height,
                'YouTube_average_frame_rate': average_frame_rate,
                'YouTube_average_buffer_health': average_buffer_health
            }
        }])

    def check_youtube_status(self):
        try:
            query = "SELECT mean(\"YouTube_average_buffer_health\") AS \"mean_YouTube_average_buffer_health\" from networks where time > now()-2m and \"user\"='{}'".format(self.minion_id)
            result = self.client.query(query)
            print(result.raw)
            if len(result.raw['series']) == 0:
                return None
            print(result.raw['series'][0]['values'][0][1])
            return result.raw['series'][0]['values'][0][1]
        finally:
            return 100

    def runCommand(self, command):
        logger.info(f"running: {command} on: {self.minion_id}")
        output = self.local.cmd(self.minion_id, 'cmd.run', [command])
        return output[self.minion_id]

    def isUp(self):
        print(self.minion_id)
        status = self.local.cmd(self.minion_id, 'test.ping')[self.minion_id]
        return status

    def runGitCommand(self, command):
        print(self.runCommand("{} {}".format(self._git, command)))

    def updateCode(self):
        self.runGitCommand("pull")

    def runYoutubeExperiment(self):
        print(self.runCommand('cd {}ucsb/ && python3 ./selenium_scripts/youtube_video.py'.format(self.project_path)))

    def ping(self, address, count=1, upload=False):
        try:
            address = address.strip()
            validation = MinionHandler.validate_address(address)
            if not validation:
                raise Exception("invalid address {}".format(address))
            if not isinstance(count, int):
                raise Exception("count should be an integer")

            ping_output = self.runCommand("ping {} -c {}".format(address, count))
            ping_output = MinionHandler.parse_ping_output(ping_output)
            if len(ping_output) == 0:
                raise Exception("Ping error")

            mean_ping = statistics.mean(ping_output)
            if upload:
                self._upload_ping_result(address, mean_ping)
            return mean_ping
        finally:
            return 0

    def speed_test(self, upload=False):
        output = self.runCommand("speedtest-cli --simple")
        try:
            speedtest_output = []
            lines = output.splitlines()
            for line in lines:
                speedtest_output.append(float(re.findall(r'\d+\.*\d*', line)[0]))
            print(lines, "speedtest_output: ", speedtest_output)
            if len(speedtest_output) < 3:
                return None
            if upload:
                self._upload_speedtest_result(speedtest_output[1], speedtest_output[2])
            return speedtest_output[1], speedtest_output[2]
        finally:
            return None


    def capturePackets(self):
        pi_id = str(self.minion_id) 
        command = 'tshark -i eth0 -a duration:300 -w ' + pi_id + '.pcap' #capture for 5 mins 
        logger.info(f"running: {command} on: {self.minion_id}")

        output = self.local.cmd_async(self.minion_id, 'cmd.run', [command])
        logger.info(f"job id: {output}")
        self.tshark_jid = output
        #return output[self.minion_id]


    def runVcaExperiment(self, url):
        minion_path = "VCA-QoE"
        print(self.runCommand('python3 {}/run_vca.py {}'.format(minion_path, url)))


    #minion -> master 
    def upload_vca_webrtc(self):
        #pi-mapping = {"raspi-1": "128.111.45.120", "raspi-4": "128.111.52.161", "raspi-8": "128.111.45.232", "raspi-9": "128.111.45.121"}
        pi_id = str(self.minion_id) 
        #command = "salt \'" + pi_id + "\' cp.push webrtc_internals_dump.txt upload_path=\'/mnt/hdd1/irene/PROJECTS/VCA-QoE/ucsb-rpi/webrtc\'"
        return self.upload(pi_id, "/root/webrtc_internals_dump.txt", f"{pi_id}-{self.ts}.json")


    #minion -> master 
    def upload_vca_packets(self):
        pi_id = str(self.minion_id) 
        #command = "salt \'" + pi_id + "\' cp.push webrtc_internals_dump.txt upload_path=\'/mnt/hdd1/irene/PROJECTS/VCA-QoE/ucsb-rpi/webrtc\'"
        assert self.tshark_jid
        logger.info("Killing tshark with SIGTERM.")
        logger.info(f'\t{self.local.cmd(self.minion_id, "saltutil.signal_job", [self.tshark_jid, SIGTERM])}')

        return self.upload(pi_id, f"/root/{pi_id}.pcap", f"{pi_id}-{self.ts}.pcap")

    def upload(self, pi_id, filename, dest_filename):
        """Upload the given file to the server."""
        command = f"curl -T {filename} http://snl-server-3.cs.ucsb.edu/upload/{dest_filename}",
        logger.info(f"Moving {filename} from {pi_id} to SNL server as {dest_filename}")
        logger.info(f'\tdisk usg: {self.local.cmd(self.minion_id, "cmd.run", [f"du -h {filename}"])[self.minion_id]}')
        logger.info(f'\tchecksum: {self.local.cmd(self.minion_id, "cmd.run", [f"md5sum {filename}"])[self.minion_id]}')
        logger.info(f"\t{command}")
        for i in range(UPLOAD_ATTEMPTS):
            logger.info(f"(attempt {i})")
            output = self.local.cmd(self.minion_id, "cmd.run", [
                command
            ], full_return=True)[self.minion_id]
            if output["retcode"] == 0:
                logger.info(f'{output["retcode"]}\tupload succeeded')
                return output["ret"]
            else:
                logger.warn(f'{output["retcode"]}\tfailed to upload\n{output["ret"]}')
        logger.error("Could not upload " + filename + " from " + pi_id + " to SNL server")

 



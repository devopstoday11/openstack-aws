"""
Image converter module
"""
import os
import subprocess
import json
import logging
from modules.utils import load_data

logger = logging.getLogger(__name__)
class ImageConverter(object):
    """
    Converts qcow2 image to raw format.
    """
    def __init__(self, bucket, region, container_json_path):
        """
        Initilaization Image converter.
        """
        self.bucket = bucket
        self.region = region
        self.container_json_path = container_json_path

    def create_snapshot(self, disk):
        """
        creates snapshot
        """
        disk_split = disk.split('/')
        disk_name = disk_split[-1]
        root_disk = None
        #Assuming sda as root partition
        if disk_split[-2].endswith('sda'):
            root_disk = '!@root_disk'
        url = "https://s3-{}.amazonaws.com/{}/{}".format(self.region, self.bucket, disk_name)
        container_json = {
            'Url':url,
            'Description':"Example image originally in QCOW2 format",
            'Format':'raw'
            }
        load_data(self.container_json_path, container_json)
        description = "trilio_" + disk_name[:-4]
        logger.info("snap shot intilization started...")
        cmd = "aws ec2 import-snapshot --description {} \
        --disk-container file://{}".format(description, self.container_json_path)
        imp_snap = os.popen(cmd)
        get_snap_id = imp_snap.read()
        snap_id = json.loads(get_snap_id)
        task_id = snap_id.get("ImportTaskId")
        logger.info("Imported Task Id is: %s", task_id)
        count = 0
        while True:
            des_snap = os.popen((\
                "aws ec2 describe-import-snapshot-tasks --import-task-id {0}").format(task_id))
            progress = des_snap.read()
            task = json.loads(progress)
            task_info = task['ImportSnapshotTasks']
            import time
            time.sleep(30)
            prog = task_info[0].get('SnapshotTaskDetail', {}).get('Status')
            if prog == "completed":
                snapshot_id = task_info[0]['SnapshotTaskDetail']['SnapshotId']
                logger.info("Snapshot created successfully with Id %s", snapshot_id)
                break
            else:
                count = count + 1
                logger.info("Snapshot creation is inprogress %s", count*'.')
        if root_disk:
            snapshot_id = snapshot_id + root_disk
        return snapshot_id

    def copy_disks_to_s3(self, disks):
        """
        copy converted raw disk to S3.
        """
        for disk in disks:
            logger.info("object copy intialized...")
            cmd = "aws s3 cp {} s3://{} --acl public-read".format(disk, self.bucket)
            os.system(cmd)
            logger.info("object %s copy Done..", disk)


    def convert_image_to_raw(self, disk_files):
        """
        Converts qcow2 image to raw.
        """
        raw_disks = []
        for disk in disk_files:
            qemu_info = subprocess.Popen(["qemu-img", "info", disk], \
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out1, err1 = qemu_info.communicate()
            logger.info("output %s", out1)
            logger.info("Error..!! %s", err1)
            raw_disk_name = disk + '.raw'
            if os.path.exists(raw_disk_name):
                logger.info("raw file already exists, Hence skipping the convertion..")
            else:
                qemu_convert = subprocess.Popen(["qemu-img", "convert", \
                                                 disk, raw_disk_name], \
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE\
                    )
                out2, err2 = qemu_convert.communicate()
                logger.info("output %s", out2)
                logger.info("Error..!! %s", err2)
                logger.info("Image converted.....")
            raw_disks.append(raw_disk_name)

        return raw_disks

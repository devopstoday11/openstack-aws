"""
Writen this module with Facade design pattern, which is often used when a
system is very complex or difficult to understand because the system has
a large number of interdependent classes or its source code
is unavailable. This pattern hides the complexities of the larger system
and provides a simpler interface to the client. It typically involves a
single wrapper class that contains a set of members required by the client.
These members access the system on behalf of the facade client and hide the
implementation details.
"""

import logging
from modules.workload_parser import Parser
from modules.image_converter import ImageConverter
from modules.boto_adapter import BotoAdapter

class App(object):
    """
    Exposes api to CLI and UI
    """
    def __init__(self, bucket, region,\
                 container_json_path, trilio_base_dir, key_pair):
        """
        App Class Constructor

        - **parameters**, **types**, **return** and **return types**::

            param bucket: s3 bucket name
            type args: str
            param region: amazon region name
            type args: str
            param container_json_path: container json
            type args: str
            param trilio_base_dir: Trilio vault base directory
            type args: str
            key_pair: key pair to login instance
            type args: str
        """
        self.parser_obj = Parser(trilio_base_dir)
        self.ic_obj = ImageConverter(bucket, region, container_json_path)
        self.boto_obj = BotoAdapter(region, key_pair)
        self.logger = logging.getLogger(__name__)
    def get_workloads(self):
        """
        Returns list of workloads under trilio vault directory
        if availabel otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::

            returns workloads:
            type: list
        """

        return self.parser_obj.get_workloads()

    def get_snapshots_from_workload(self, workload_name):
        """
        Returns list of snapshots dictonaries, Each dictionary contains snapshot name,
        snapshot path, size and snapshot_db inforation.

        - **parameters**, **types**, **return** and **return types**::

            param workload_name: Name of the workload
            type workload_name: str
            returns snapshots:
            type: list
        """
        if isinstance(str(workload_name), str):
            return self.parser_obj.get_snapshots_from_workload(workload_name)
        else:
            self.logger.info("expected dictionary but got %s", type(workload_name))
        return None

    def get_snapshot_from_workload(self, snap_shot_name, workload):
        """
        Returns snapshot dictonary if availabel otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::
            param snap_shot_name: Name of the snapshot
            type snap_shot_name: str
            param workload_name: Name of the workload
            type workload_name: str
            returns snapshots:
            type: list
        """
        return self.parser_obj.get_snapshot_from_workload(snap_shot_name, workload)

    def get_vms_from_snapshots(self, snapshot):
        """
        Returns vm dictonaries form given snapshot if available
        otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::
            param snap_shot_name: Name of the snapshot
            type snap_shot_name: str
            returns vms:
            type: list
        """
        return self.parser_obj.get_vms_from_snapshots(snapshot)

    def get_latest_snapshot(self, workload):
        """
        Returns latest snapshot from given workload.

        - **parameters**, **types**, **return** and **return types**::
            param snap_shot_name: Name of the snapshot
            type snap_shot_name: str
            param workload_name: Name of the workload
            type workload_name: str
            returns snapshot:
            type: dict
        """
        return self.parser_obj.get_latest_snapshot(workload)

    def convert_image_to_raw(self, disks):
        """
        Converts to QCOW2 image to RAW format
        """
        if isinstance(disks, list):
            return self.ic_obj.convert_image_to_raw(disks)
        else:
            self.logger.info("expected string but got %s", type(disks))
        return None

    def copy_disks_to_s3(self, disks):
        """
        copy raw images to Amazon S3 to take snapshots
        """
        if isinstance(disks, list):
            return self.ic_obj.copy_disks_to_s3(disks)
        else:
            self.logger.info("expected string but got %s", type(disks))
        return None

    def create_snapshot(self, disk):
        """
        Creates snapshot
        """
        return self.ic_obj.create_snapshot(disk)

    def register_ami(self, snapshot_id):
        """
        Register AMI in aws
        """
        return self.boto_obj.register_ami(snapshot_id)

    def lanuch_instance(self, ami_id, snap_ids, vm_dict):
        """
        Launch instance in AWS EC2.
        """
        return self.boto_obj.lanuch_instance(ami_id, snap_ids, vm_dict)

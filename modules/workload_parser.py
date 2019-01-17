"""
Workload parser
"""
from os import path, walk
import datetime
import logging
logger = logging.getLogger(__name__)
from modules.utils import get_data, get_time, bytes_to_mb, WorkloadException

class Parser(object):
    """
    Workload parser
    """
    def __init__(self, trilio_base_dir):
        """
        constructor of Parser class
        """
        self.base_dir = trilio_base_dir
        self.res_data = None
        self.vms = None
    def get_workloads(self):
        """
        Returns list of workloads under trilio vault directory
        if availabel otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::

            returns workloads:
            type: list
        """
        try:  
            for root, dirs, files in walk(self.base_dir):
                if dirs:
                    workloads = [directory for directory in dirs if directory.startswith("workload_")]
                    return workloads
                else:
                    return None
        except Exception as e:
            raise WorkloadException(e)

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
        try:
            path_to_walk = path.join(self.base_dir, workload_name)
            snapshots = []
            if path.isdir(path_to_walk) and path.exists(path_to_walk):
                for root, dirs, files in walk(path_to_walk):
                    if dirs:
                        for directory in dirs:
                            if directory.startswith("snapshot_"):
                                path_to_snapshot = path.join(path_to_walk, directory)
                                path_to_snapshot_db = path.join(path_to_snapshot, "snapshot_db")
                                snapshot_data = get_data(path_to_snapshot_db)
                                snap_time = get_time(snapshot_data.get("updated_at"))
                                snapshot_data.update(
                                    {
                                        'path':path_to_snapshot,
                                        'time':snap_time,
                                        'size_in_mb': bytes_to_mb(snapshot_data.get("size")),
                                        'restore_size_in_mb':
                                        bytes_to_mb(snapshot_data.get("restore_size")),
                                    }
                                )
                                snapshots.append(snapshot_data)
                        return snapshots
                    else:
                        logger.info("No snapshots found in %s", workload_name)
                        return None
            else:
                logger.info("Not a directory or path not exist.")
        except Exception as e:
            raise WorkloadException(e)
    def get_snapshot_from_workload(self, snap_shot_name, workload):
        """
        Returns snapshot dictonary if availabel otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::
            param snap_shot_name: Name of the snapshot
            type snap_shot_name: str
            param workload: Name of the workload
            type workload: str
            returns snapshots:
            type: list
        """
        try:
            snap_shots = self.get_snapshots_from_workload(workload)
            if snap_shot_name in snap_shots:
                #snap_shot_name = "snapshot_" + snap_shot_name
                snapshot = path.join(self.base_dir, path.join(workload, snap_shot_name))
                return snapshot
            else:
                logger.info("no snap exists with following name %s", snap_shot_name)
            return None
        except Exception as e:
            raise WorkloadException(e)

    def get_snapshot_by_name(self, snap_shot_name, workload=None):
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
        try:
            if workload:
                return self.get_snapshot_from_workload(snap_shot_name, workload)
            else:
                workloads = self.get_workloads()
                for workloa in workloads:
                    snapshot = self.get_snapshot_from_workload(snap_shot_name, workloa)
                    if snapshot:
                        break
            return snapshot
        except Exception as e:
            raise WorkloadException(e)

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
        try:
            snap_shots = self.get_snapshots_from_workload(workload)
            latest = datetime.datetime.strptime('1800-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
            for snap in snap_shots:
                curr = datetime.datetime.strptime(snap['time'], '%Y-%m-%d %H:%M:%S')
                if curr > latest:
                    latest = curr
                    latest_snap_shot = snap
            return latest_snap_shot
        except Exception as e:
            raise WorkloadException(e)

    def _get_disk_path(self, disk_dbs):
        """
        Helper function: read the dis_db and returns disk paths.
        """
        disks = []
        for disk_db in disk_dbs:
            data = get_data(disk_db)
            disk = data[0].get('vault_url')
            disk_path = path.join(self.base_dir, disk[1:])
            disks.append(disk_path)
        return disks

    def _update_vm_data(self, snap_path):
        """
        update vm_data
        """
        for vm_dict in self.vms:
            for res in self.res_data:
                if res['vm_id'] == vm_dict['id']:
                    if res['resource_type'] == 'nic':
                        path_to_network = path.join(snap_path, 'network')
                        path_to_network_vm_res_id = path.join(
                            path_to_network, 'vm_res_id_' + res['id'])
                        vm_dict.update({
                            'nic_db_path':path.join(path_to_network_vm_res_id, 'network_db')})
                    elif res['resource_type'] == 'security_group':
                        path_to_security_group = path.join(snap_path, 'security_group')
                        sg_path = path.join(
                            path_to_security_group, 'vm_res_id_' + res['id'])
                        vm_dict.update({'sg_db_path':path.join(
                            sg_path, 'security_group_db')})
                    elif res['resource_type'] == 'disk':
                        path_to_vm = path.join(snap_path, 'vm_id_' + vm_dict['id'])
                        path_to_vm_res_id = path.join(path_to_vm, 'vm_res_id_' + res['id'])
                        paths = vm_dict.get('disk_db_path', [])
                        paths.append(path.join(path_to_vm_res_id, 'disk_db'))
                    elif res['resource_type'] == 'flavor':
                        vm_dict.update({'flavor': res.get('resource_name')})
                        metadata = res.get('metadata')
                        for meta in metadata:

                            if meta.get('key', '') == 'ram':
                                vm_dict.update({'ram_in_mb': int(meta.get('value', 0))})
                            elif meta.get('key', '') == 'vcpus':
                                vm_dict.update({'cpus': int(meta.get('value', 0))})
                            elif meta.get('key', '') == 'swap':
                                vm_dict.update({'swap': meta.get('value', 0)})
                    elif res['resource_type'] == 'subnet':

                        path_to_network = path.join(snap_path, 'network')
                        path_to_network_vm_res_id = path.join(
                            path_to_network, 'vm_res_id_' + res['id'])
                        vm_dict.update({'subnet_path':path.join(\
                            path_to_network_vm_res_id, 'network_db')})

                if res['resource_type'] == 'subnet':
                    if res['resource_name'] == "private-subnet":
                        path_to_network = path.join(snap_path, 'network')
                        path_to_network_vm_res_id = path.join(
                            path_to_network, 'vm_res_id_' + res['id'])
                        vm_dict.update({'subnet_path':path.join(\
                            path_to_network_vm_res_id, 'network_db')})
            vm_dict.update({'disks': self._get_disk_path(vm_dict.get('disk_db_path', []))})

    def get_vms_from_snapshots(self, snapshot):
        """
        Returns vm dictonaries form given snapshot if available otherwise returns None.

        - **parameters**, **types**, **return** and **return types**::
            param snap_shot_name: Name of the snapshot
            type snap_shot_name: str
            returns vms:
            type: list
        """
        try:
            snap_path = snapshot.get('path')
            snapshot_vms_db_path = path.join(snap_path, "snapshot_vms_db")
            if snapshot_vms_db_path:
                vms_data = get_data(snapshot_vms_db_path)
            resource_db_path = path.join(snap_path, "resources_db")
            self.res_data = get_data(resource_db_path)
            self.vms = []
            for vm_dict in vms_data:
                vms_dict = {
                    'name':vm_dict.get('vm_name'),
                    'path':path.join(snap_path, "vm_id_" + vm_dict.get('vm_id')),
                    'id':vm_dict.get('vm_id'),
                    'security_group':"a",
                    'network':'b',
                    'disk_db_path':[]
                }
                self.vms.append(vms_dict)
            self._update_vm_data(snap_path)
            return self.vms
        except Exception as e:
            raise WorkloadException(e)
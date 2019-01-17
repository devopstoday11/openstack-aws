"""
command line
"""
import sys
import os
from os.path import join
import logging
import pickle
from tabulate import tabulate

#base_dir = os.path.dirname(os.path.dirname(__file__))
CWD = os.getcwd()
CWD = CWD.split('/')
BASE_DIR = ('/'.join(CWD[:-1]))
sys.path.append(BASE_DIR)
from modules.app import App
from modules.utils import (\
    setup_logging, get_data, get_time, WorkloadException,\
    ImageConverterException, BotoException)

class Trilio(object):
    """
    command line
    """
    def __init__(self):
        """
        constructor
        """
        cfg = get_data('config')
        bucket = cfg.get('bucket_name')
        region = cfg.get('region')
        self.trilio_base_dir = cfg.get('trilio_base_dir')
        container_json_path = cfg.get('container_json_path')
        key_pair = cfg.get('key_pair')
        self.app = App(bucket, region, container_json_path,\
                       self.trilio_base_dir, key_pair)
        setup_logging(name=cfg.get('app_name'), level=cfg.get('log_level'))
        self.logger = logging.getLogger(__name__)

    def _update_network_info(self, vm_dict):
        """
        Updates network info
        """
        network_data = get_data(vm_dict['nic_db_path'])
        for network in network_data:
            for meta in network.get('metadata'):
                if meta.get('key') == 'ip_address':
                    vm_dict.update({'ip':meta.get('value')})
                elif meta.get('key') == 'router_name':
                    vm_dict.update({'router_name':meta.get('value')})
        return vm_dict
    def _update_subnet_info(self, vm_dict):
        """
        updates subnet info
        """
        network_data = get_data(vm_dict['subnet_path'])
        for network in network_data:
            pickl = pickle.loads(network.get('pickle'))
            cidr = pickl.get('cidr')
            vm_dict.update({'cidr':cidr, 'subnet_name':pickl.get('name')})
        return vm_dict
    def _create_vm(self, vm_dict):
        """
        Create vm in Amazon EC2.
        """
        vm_dict = self._update_network_info(vm_dict)
        try:
            vm_dict = self._update_subnet_info(vm_dict)
            raw_disks = self.app.convert_image_to_raw(vm_dict.get('disks', []))
            self.app.copy_disks_to_s3(raw_disks)
            #snap_ids = ['snap-0319d9e0da0d632d1','snap-043204df28f1bbeb3']
            snap_ids = []
            for disk in raw_disks:
                snap_id = self.app.create_snapshot(disk)
                snap_ids.append(snap_id)
        except Exception as err:
            raise ImageConverterException(err)
        try:
            snap_id = 0
            for snap in snap_ids:
                if snap.endswith("!@root_disk"):
                    snap_id = snap.split("!@")[0]
            if snap_id:
                ami_id = self.app.register_ami(snap_id)
                instance = self.app.lanuch_instance(ami_id, snap_ids, vm_dict)
                print "Instance launched sucessfully with ID ***{}***".format(instance[0].id)
                self.logger.info("Instance launched sucessfully with ID ***%s***", instance[0].id)
        except Exception as err:
            raise BotoException(err)

    def run(self):
        """
        Simple comand line interface
        """
        try:
            workloads = self.app.get_workloads()
            self.logger.info("available workloads.....")
            self.logger.info(workloads)
            headers = ['SNo', 'Name', 'Id', 'Host Name', 'Created Time']
            data_list = [headers]
            for sno, workload in enumerate(workloads, 1):
                work_load_path = join(self.trilio_base_dir, workload)
                work_load_db_path = join(work_load_path, 'workload_db')
                workload_data = get_data(work_load_db_path)
                workload_list = [sno, \
                                 workload_data.get('display_name'), workload_data.get('id'), \
                                 workload_data.get('host'), get_time(workload_data.get('created_at'))]
                data_list.append(workload_list)
    
            print tabulate(data_list, tablefmt="grid", headers="firstrow")
            user_input_wl = int(raw_input("select one of the worklods listed above: "))-1
            workload = workloads[user_input_wl]
            self.logger.info("Selected workload is..%s", data_list[user_input_wl+1][1])
            while True:
                #try:
                user_input2 = raw_input(\
                    "Do you want to recreate entire" \
                    "workload(by default takes latest snapshot) y/n : ").lower()

                if user_input2 == 'yes' or user_input2 == 'y':
                    snapshot = self.app.get_latest_snapshot(workload)
                    vms = self.app.get_vms_from_snapshots(snapshot)
                    for vm_dict in vms:
                        self._create_vm(vm_dict)
                    break
                elif user_input2 == 'no' or user_input2 == 'n':
                    self.logger.info("listing available snapshots under given workload %s",\
                                     workload)
                    print "listing available snapshots under given workload {}".format(workload)
                    snapshots = self.app.get_snapshots_from_workload(workload)
                    headers = ['SNo', 'Name', 'Id', 'Time', 'Size(MB)']
                    data_list = [headers]
                    for sno, snapshot in enumerate(snapshots, 1):
                        data = [sno, snapshot.get('display_name'), snapshot.get('id'), \
                                snapshot.get('time'), snapshot.get('size_in_mb')]
                        data_list.append(data)
                    print tabulate(data_list, tablefmt="grid", headers="firstrow")
                    user_input_snap = int(raw_input("select one of the snapshots listed above: "))-1
                    snapshot = snapshots[user_input_snap]
                    while True:
                        user_input2 = raw_input(\
                            "Do you want to restore all the vms under given snapshot {} y/n : "\
                            .format(snapshot.get('id'))).lower()

                        if user_input2 == 'yes' or user_input2 == 'y':
                            vms = self.app.get_vms_from_snapshots(snapshot)
                            for vm_dict in vms:
                                self._create_vm(vm_dict)

                            break
                        elif user_input2 == 'no' or user_input2 == 'n':

                            print "listing available vms \
                            under given snapshot \n {}".format(snapshot.get('id'))
                            self.logger.info("listing available vms under given snapshot \n %s", \
                                             snapshot.get('id'))

                            vms = self.app.get_vms_from_snapshots(snapshot)
                            headers = ['SNo', 'Name', 'Id']
                            data_list = [headers]

                            for sno, virtulamachine in enumerate(vms, 1):
                                data = [sno, virtulamachine.get('name'), virtulamachine.get('id')]
                                data_list.append(data)
                            print tabulate(data_list, tablefmt="grid", headers="firstrow")
                            user_input_vm = int(raw_input("select one of the vm listed above: "))
                            vm_dict = vms[user_input_vm-1]
                            print "selected vm", vm_dict['name']
                            self.logger.info("selected vm %s", vm_dict['name'])
                            self._create_vm(vm_dict)
                            break
                    break

        except WorkloadException as workload_err:
            print "Error found in workload parser.. {}".format(workload_err)

        except ImageConverterException as err:
            print "Error found in Image converter..{}".format(err)
            
        except BotoException as boto_err:
            print "Error found in Boto interface.. {}".format(boto_err)
        except Exception as err:
                print err
        finally:
            sys.exit()
def main():
    """
    Execution starts from here
    """
    obj = Trilio()
    obj.run()

if __name__ == "__main__":
    main()

"""
Boto interface
"""

import datetime
import logging
import boto3
logger = logging.getLogger(__name__)

class BotoAdapter(object):
    """
    Responsible for AWS operations..
    """

    def __init__(self, region, key_pair):
        self.vpc = None
        self.vm_dict = None
        self.key_pair = key_pair
        self.ec2 = boto3.resource('ec2', region_name=region)

    def register_ami(self, snapshot_id):
        """
        Register the AMI with the specified snapshot ID and parameters.
        """
        ami_id = self.ec2.register_image(\
            Architecture='x86_64',
            BlockDeviceMappings=
            [
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'SnapshotId': snapshot_id,
                        },
                    },
                ],

            Description='trilioami',
            Name='trilioami' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            RootDeviceName='/dev/sda1',
            VirtualizationType='hvm'\
        )
        logger.info("AMI created successfully....!!!")
        logger.info("AMI ID ***%s***", ami_id.id)
        print "AMI created successfully with ID ***{}***".format(ami_id.id)
        return ami_id.id


    def lanuch_instance(self, ami_id, snap_ids, vm_dict):
        """
        launch instace with specified amiId and other attributes
        """
        self.vm_dict = vm_dict
        subnet_id = self._create_vpc()
        sg_id = self._create_sec_group()
        snap_id_list = []
        for snap in snap_ids:
            if not snap.endswith("!@root_disk"):
                snap_id_list.append(snap)
        block_device_mappings = []
        for snp, device in zip(snap_id_list, list(map(chr, range(98, 98+len(snap_id_list))))):
            bdm = {
                'DeviceName': '/dev/sd'+device,
                'Ebs': {
                    'DeleteOnTermination': True,
                    'SnapshotId': snp,
                    },
                }
            block_device_mappings.append(bdm)

        instance = self.ec2.create_instances(
            ImageId=ami_id,
            InstanceType=self.vm_dict.get('flavor'),
            MinCount=1, MaxCount=1,
            KeyName=self.key_pair,
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': True,
                    'DeleteOnTermination': True,
                    'Description': 'testing from boto3',
                    'DeviceIndex': 0,
                    'Groups': [
                        sg_id,
                        ],
                    'PrivateIpAddress': self.vm_dict.get('ip'),
                    'SubnetId': subnet_id
                    },
                ],
            BlockDeviceMappings=block_device_mappings
            )
        return instance

    def _create_vpc(self):
        """
        Create VPC
        """
        vpc_cidr = self.vm_dict.get('cidr')
        self.vpc = self.ec2.create_vpc(CidrBlock=vpc_cidr)
        #we can assign a name to vpc, or any resource, by using tag
        self.vpc.create_tags(Tags=[{"Key": "Name", "Value": "Trilio_new"}])
        self.vpc.wait_until_available()
        internet_gateway = self._create_and_attach_ig()
        route_table = self._create_route_table(internet_gateway)
        subnet_id = self._create_subnet(route_table)
        logger.info("VPC created with id : %s", self.vpc.id)
        return subnet_id

    def _create_and_attach_ig(self):
        '''
        # create then attach internet gateway
        '''
        internet_gateway = self.ec2.create_internet_gateway('trilio_igw')
        self.vpc.attach_internet_gateway(InternetGatewayId=internet_gateway.id)
        logger.info("Internet gateway attached to VPC..")
        return  internet_gateway

    def _create_route_table(self, internet_gateway, dest_cidr_bloack='0.0.0.0/0'):
        '''
        create a route table and a public route
        '''
        route_table = self.vpc.create_route_table(self.vm_dict.get('router_name'))
        route_table.create_route(
            DestinationCidrBlock=dest_cidr_bloack,
            GatewayId=internet_gateway.id
        )
        return route_table

    def _create_subnet(self, route_table):
        '''
        create subnet
        '''
        subnet_cidr = self.vm_dict.get('cidr')
        subnet = self.ec2.create_subnet(CidrBlock=subnet_cidr, VpcId=self.vpc.id)
        #associate the route table with the subnet
        route_table.associate_with_subnet(SubnetId=subnet.id)
        return subnet.id

    def _create_sec_group(self):
        '''
        Create sec group
        '''
        sec_group = self.ec2.create_security_group(
            GroupName='trilio_sg', Description='Trilio sec group', VpcId=self.vpc.id)
        sec_group.authorize_ingress(
            CidrIp='0.0.0.0/0',
            IpProtocol='TCP',
            FromPort=22,
            ToPort=22
        )
        logger.info("security group created with id : %s", sec_group.id)
        return sec_group.id

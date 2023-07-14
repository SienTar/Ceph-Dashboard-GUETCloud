# -*- coding: UTF-8 -*-
import ceph_argparse
import subprocess

class Ceph_Volume():

    def lvm_create_subprocess(self, block, objectstore, wal = None, db = None): # 使用subprocess
        '''
        一步添加新的OSD: ceph-volume lvm create --data {vg/lv} --block.wal {partition} --block.db {/path/to/device}
        :param block: str, 指定OSD的数据分区, 应为LV、分区或PV的路径
        :param objectstore: str, 指定对象存储后端类型, 满足CephChoices(strings = '--filestore|--bluestore')
        :param wal: str, 指定OSD的WAL分区, 应为LV、分区或PV的路径, 不指定时默认不设置WAL分区, 仅在objectstore为 '--bluestore' 时生效
        :param db: str, 指定OSD的DB分区, 应为LV、分区或PV的路径, 不指定时默认不设置DB分区, 仅在objectstore为 '--bluestore' 时生效
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''
        try:
            cmd = ['ceph-volume', 'lvm', 'create']

            if not isinstance(block, str):
                return TypeError('变量block的类型错误, 应为str')
            cmd.append('--data')
            cmd.append(block)

            if not isinstance(objectstore, str):
                return TypeError('变量objectstore的类型错误, 应为str')
            objectstore_validator = ceph_argparse.CephChoices(strings = '--filestore|--bluestore')
            objectstore_validator.valid(objectstore)
            cmd.append(objectstore)

            if objectstore == '--bluestore':
                if wal is not None:
                    if not isinstance(wal, str):
                        return TypeError('变量wal的类型错误, 应为str')
                    cmd.append('--block.wal')
                    cmd.append(wal)
                if db is not None:
                    if not isinstance(db, str):
                        return TypeError('变量db的类型错误, 应为str')
                    cmd.append('--block.db')
                    cmd.append(db)

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

    def lvm_list_subprocess(self): # 使用subprocess
        '''
        查看OSD对应的磁盘: ceph-volume lvm list
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''
        try:
            cmd = ['ceph-volume', 'lvm', 'list']

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

    def lvm_zap_device_subprocess(self, device, destory = False): # 使用subprocess
        '''
        清空准备用于OSD的磁盘: ceph-volume lvm zap {vg/lv; partition; PV} [--destroy]
        :param device: list, 指定LV、分区或PV的路径, 允许多个, 元素为str
        :param destory: bool, 表示强制执行, 不指定时默认为False, 满足CephBool(strings = '')
        :param destory: bool, 满足CephBool(strings = ''), 用于强制操作, 一般在zap失败后追加该参数以提高成功率, 不指定时默认为False
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''

        try:
            cmd = ['ceph-volume', 'lvm', 'zap']

            if not isinstance(device, list):
                return TypeError('变量device的类型错误, 应为list')
            for s in device:
                if not isinstance(s, str):
                    return TypeError('变量device的元素类型错误, 应为str')
                cmd.append(s)

            if destory is not False:
                if not isinstance(destory, bool):
                    return TypeError('变量destory的类型错误, 应为bool')
                destory_validator = ceph_argparse.CephBool(strings = '')
                destory_validator.valid(str(destory))
                cmd.append('--destroy')

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

    def lvm_zap_osd_id_subprocess(self, osd_id, osd_fsid = None): # 使用subprocess
        '''
        清空指定OSD与其分区的关联信息: ceph-volume lvm zap --osd-id {id} [--osd-fsid {fsid}]
        :param osd_id: int, 指定OSD的ID, 满足CephInt(range = '0')
        :param osd_fsid: str, 指定OSD的FSID, 满足CephString(goodchars = '[A-Fa-f0-9-]'), 不指定时默认留空
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''

        try:
            cmd = ['ceph-volume', 'lvm', 'zap']

            if not isinstance(osd_id, int):
                return TypeError('变量osd_id的类型错误, 应为int')
            osd_id_validator = ceph_argparse.CephInt(range = '0')
            osd_id_validator.valid(str(osd_id))
            cmd.append('--osd-id')
            cmd.append(str(osd_id))

            if osd_fsid is not None:
                if not isinstance(osd_fsid, str):
                    return TypeError('变量osd_fsid的类型错误, 应为str')
                path_validator = ceph_argparse.CephString(goodchars = '[A-Fa-f0-9-]')
                path_validator.valid(osd_fsid)
                cmd.append('--osd-fsid')
                cmd.append(osd_fsid)

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

    def lvm_prepare_subprocess(self, block, objectstore, wal = None, db = None): # 使用subprocess
        '''
        为新的OSD准备磁盘: ceph-volume lvm prepare --data {vg/lv} --block.wal {partition} --block.db {/path/to/device}
        :param block: str, 指定OSD的数据分区, 应为LV、分区或PV的路径
        :param objectstore: str, 指定对象存储后端类型, 满足CephChoices(strings = '--filestore|--bluestore')
        :param wal: str, 指定OSD的WAL分区, 应为LV、分区或PV的路径, 不指定时默认不设置WAL分区, 仅在objectstore为 '--bluestore' 时生效
        :param db: str, 指定OSD的DB分区, 应为LV、分区或PV的路径, 不指定时默认不设置DB分区, 仅在objectstore为 '--bluestore' 时生效
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''
        try:
            cmd = ['ceph-volume', 'lvm', 'prepare']

            if not isinstance(block, str):
                return TypeError('变量block的类型错误, 应为str')
            cmd.append('--data')
            cmd.append(block)

            if not isinstance(objectstore, str):
                return TypeError('变量objectstore的类型错误, 应为str')
            objectstore_validator = ceph_argparse.CephChoices(strings = '--filestore|--bluestore')
            objectstore_validator.valid(objectstore)
            cmd.append(objectstore)

            if objectstore == '--bluestore':
                if wal is not None:
                    if not isinstance(wal, str):
                        return TypeError('变量wal的类型错误, 应为str')
                    cmd.append('--block.wal')
                    cmd.append(wal)
                if db is not None:
                    if not isinstance(db, str):
                        return TypeError('变量db的类型错误, 应为str')
                    cmd.append('--block.db')
                    cmd.append(db)

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

    def lvm_activate_subprocess(self, all, id = None, fsid = None): # 使用subprocess
        '''
        激活指定OSD的或全部OSD: ceph-volume lvm activate {ID} {FSID} 或 ceph-volume lvm activate {ID} {FSID}
        :param id: int, 指定OSD的ID, 满足CephInt(range = '0'), all为False时必须指定该参数, all为True时忽略该参数
            该参数可从 "ceph-volume lvm prepare" 或  "ceph-volume lvm prepare" 命令的输出文本中获取
        :param fsid: str, 指定OSD的FSID, 满足CephString(goodchars = '[A-Fa-f0-9-]'), all为False时必须指定该参数, all为True时忽略该参数
            该参数可从 "ceph-volume lvm prepare" 或  "ceph-volume lvm prepare" 命令的输出文本中获取
        :param all: bool, 满足CephBool(strings = ''), 用于指定所有的OSD
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        '''

        try:
            cmd = ['ceph-volume', 'lvm', 'activate']

            if all is not False:
                if not isinstance(all, bool):
                    return TypeError('变量all的类型错误, 应为bool')
                all_validator = ceph_argparse.CephBool(strings = '')
                all_validator.valid(str(all))
                cmd.append('--all')
            else:
                if not isinstance(id, int):
                    return TypeError('变量id的类型错误, 应为int')
                id_validator = ceph_argparse.CephInt(range = '0')
                id_validator.valid(str(id))
                cmd.append(str(id))

                if not isinstance(fsid, str):
                    return TypeError('变量fsid的类型错误, 应为str')
                path_validator = ceph_argparse.CephString(goodchars = '[A-Fa-f0-9-]')
                path_validator.valid(fsid)
                cmd.append(fsid)

            result = ['', '']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e

# 实例化Ceph_Volume对象
if __name__ == '__main__':

    _ceph_volume = Ceph_Volume()

    arg1 = True
    arg2 = 2
    arg3 = '147fdc6d-26de-472e-a157-a3d6eae1d886'
    arg4 = '/dev/ceph-7467a65d-6afc-4035-92e1-7786008dd64c/osd-wal-675efdae-5464-4046-a93a-318b4ffcc76d'
    arg5 = '/dev/ceph-8e5fd1f0-276b-42e9-b55e-d3af72cd620a/osd-db-89d7fce3-6290-4d58-b28c-3eec0ed95584'
    result = _ceph_volume.lvm_activate_subprocess(arg1)
    print(result)
    print(type(result))

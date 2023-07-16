# -*- coding: UTF-8 -*-
import rados
import ceph_argparse
import json
#import six # 用于变量类型six.string_types
import os
import subprocess
import time
from enum import Enum

class StatusCodeEnum(Enum):
    CEPH_OK = (0, 'Success') # 成功
    CEPH_ERROR = (-1, 'Error') # 错误
    CEPH_SERVER_ERR = (500, 'Server Exception') # 服务器异常

    CEPH_THROTTLING_ERR = (4001, 'Frequent Visits') # 访问过于频繁
    CEPH_NECESSARY_PARAM_ERR = (4002, 'Missing Required Parameter') # 缺少必传参数
    CEPH_USER_ERR = (4003, 'User name error') # 用户名错误
    CEPH_PWD_ERR = (4004, 'Password error') # 密码错误
    CEPH_CPWD_ERR = (4005, 'Password inconsistency') # 密码不一致
    CEPH_MOBILE_ERR = (4006, 'Mobile number error') # 手机号错误
    CEPH_SMS_CODE_ERR = (4007, 'Incorrect SMS verification code') # 短信验证码有误
    CEPH_SESSION_ERR = (4008, 'User not logged in') # 用户未登录

    CEPH_DB_ERR = (5000, 'Data error') # 数据错误
    CEPH_NODATA_ERR = (5001, 'No Data') # 无数据
    CEPH_PARAM_ERR = (5002, 'Parameter Error') # 参数错误

    @property
    def code(self):
        '''获取状态码'''
        return self.value[0]

    @property
    def message(self):
        '''获取状态码信息'''
        return self.value[1]

class CephError(Exception):
    '''
    运行Ceph命令时出现的错误产生的异常
    :param cmd: 发生错误的cmd
    :param msg: 错误的解释
    '''

    def __init__(self, cmd, msg):
        self.cmd = cmd
        self.msg = msg

class Ceph():

    def __init__(self):
        try:
            self.cluster = rados.Rados(conffile = '')
        except TypeError as e:
            print('参数验证错误: {}'.format(e))
            raise e
        print('创建了集群句柄')

        try:
            self.cluster.connect()
        except Exception as e:
            print('集群连接错误: {}'.format(e))
            raise e
        print('成功连接集群')

    def run_ceph_command(self, cmd, inbuf):
        try:
            result = self.cluster.mon_command(json.dumps(cmd), inbuf = inbuf)
            if result[0] is not 0:
                print(result)
                raise CephError(cmd = cmd, msg = os.strerror(abs(result[0])))
            return result
        except rados.Error as e:
            raise e
        finally:
            self._close()

    def _close(self):
        self.cluster.shutdown()

    # ceph auth add/caps/get-or-create

    def auth_add(self, entity, caps = None):
        '''
        从指定文件、或随机生成key (实体 (用户) 不存在时会自动创建)、和/或命令中指定的权限, 为指定实体 (用户) 添加授权信息
        :param entity: str, 指定的实体 (用户) 名
        :param caps: list, 允许多个, 元素为str, 权限内容, 不指定时默认为不添加任何权限
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth add', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        if caps is not None:
            if not isinstance(caps, list):
                return TypeError('变量caps的类型错误, 应为list')
            cmd['caps'] = caps

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_caps(self, entity, caps = None):
        '''
        从指定的命令中为指定实体 (用户) 添加权限
        :param entity: str, 指定的实体 (用户) 名
        :param caps: list, 允许多个, 元素为str, 权限内容, 不指定时默认为不添加任何权限
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth caps', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        if caps is not None:
            if not isinstance(caps, list):
                return TypeError('变量caps的类型错误, 应为list')
            cmd['caps'] = caps

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_get_or_create(self, entity, caps = None):
        '''
        从指定文件、或随机生成key (实体 (用户) 不存在时会自动创建)、和/或命令中指定的权限, 为指定实体 (用户) 添加授权信息 (与auth_add()基本一致)
        :param entity: str, 指定的实体 (用户) 名
        :param caps: list, 允许多个, 元素为str, 权限内容, 不指定时默认为不添加任何权限
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth get-or-create', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        if caps is not None:
            if not isinstance(caps, list):
                return TypeError('变量caps的类型错误, 应为list')
            cmd['caps'] = caps

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    '''
    entity命名规则:

        对于客户端实体 (用户): entity = 'client.<name>'
            其中: <name>为实体 (用户) 名中自行指定的部分, 建议针对不同类型的caps用例分别采取规范化的命名
            以下caps用例均为客户端实体 (用户)

    caps用例:

        对于最高权限的管理员实体 (用户) (比如默认的client.admin): caps = ['mds', 'allow *', 'mgr', 'allow *', 'mon', 'allow *', 'osd', 'allow *']

        对于RBD实体 (用户): caps = ['mon', 'allow r', 'osd', 'allow class-read object_prefix rbd_children, allow rwx pool = <rbdpool>']
            其中: <rbdpool>为指定的存储池
                  可以指定多个池, 写法参照Ceph FS实体 (用户) 以及OpenStack Cinder实体 (用户)

        对于Ceph FS实体 (用户): caps = ['mon', 'allow r', 'mds', 'allow rw, allow rw path = /<cephfs>', 'osd', 'allow rwx pool = <cephfs_data>, allow rwx pool = <cephfs_metadata>']
            其中: <cephfs>为Ceph FS实例名称, 默认为 "cephfs"
                  <cephfs_data>为Ceph FS实例使用的数据池, 默认实例 "cephfs" 的数据池默认为 "cephfs_data"
                  <cephfs_metadata>为Ceph FS实例使用的元数据池, 默认实例 "cephfs" 的元数据池默认为 "cephfs_metadata"

        对于OpenStack Glance实体 (用户): caps = ['mon', 'allow r', 'osd', 'allow class-read object_prefix rbd_children, allow rwx pool = <images>']
            其中: <images>为Ceph为OpenStack提供的镜像池, 一般为 "images"

        对于OpenStack Cinder实体 (用户): caps = ['mon', 'allow r', 'osd', 'allow class-read object_prefix rbd_children, allow rwx pool = <volumes>, allow rwx pool = <vms>, allow rx pool = <images>']
            其中: <volumes>为Ceph为OpenStack提供的卷池, 一般为 "volumes"
                  <vms>为Ceph为OpenStack提供的实例池, 一般为 "vms"
                  <images>为Ceph为OpenStack提供的镜像池, 一般为 "images"

        对于使用ceph-csi对接的Kubernetes实体 (用户): caps = ['mon', 'profile rbd', 'osd', 'profile rbd pool = <k8spool>', 'mgr', 'profile rbd pool = <k8spool>']
            其中: <k8spool>为Ceph为使用ceph-csi对接的Kubernetes提供的存储池
    '''

    # ceph auth others

    def auth_del(self, entity):
        '''
        删除指定实体 (用户) 及其所有权限
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth del', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_export(self, entity = None):
        '''
        为实体 (用户) 写入keyring, 如果未给定, 则写入主keyring
        :param entity: str, 指定的实体 (用户) 名, 不指定时默认作用于所有实体 (用户)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth export', 'format': 'json'}

        if entity is not None:
            if not isinstance(entity, str):
                return TypeError('变量entity的类型错误, 应为str')
            cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_get(self, entity):
        '''
        获取指定实体 (用户) 的key, 写入kering文件中
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth get', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_get_key(self, entity):
        '''
        获取指定实体 (用户) 的key, 仅显示key
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth get-key', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_list(self):
        '''
        列出授权状态 (列出的具体内容与auth_export()不指定entity时基本一致)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth list', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_ls(self):
        '''
        列出授权状态 (列出的具体内容与auth_export()不指定entity时基本一致)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth ls', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_print_key(self, entity):
        '''
        打印指定实体 (用户) 的key, 仅打印key (与auth_get_key()基本一致)
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth print-key', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_print__key(self, entity):
        '''
        打印指定实体 (用户) 的key, 仅打印key (与auth_get_key()基本一致)
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth print_key', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def auth_rm(self, entity):
        '''
        删除指定实体 (用户) 及其所有权限
        :param entity: str, 指定的实体 (用户) 名
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'auth rm', 'format': 'json'}

        if not isinstance(entity, str):
            return TypeError('变量entity的类型错误, 应为str')
        cmd['entity'] = entity

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph crash

    def crash_ls(self):
        '''
        查看进程崩溃信息
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'crash ls', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def crash_info(self, id): # 部分完成测试, 因暂时没有可用的崩溃信息ID, 目前为止无法测出返回值为0的结果
        '''
        查看某个崩溃信息
        :param id: str, 崩溃信息ID, 如 '2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'crash info', 'format': 'json'}

        if not isinstance(id, str):
            return TypeError('变量id的类型错误, 应为str')
        cmd['id'] = id

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def crash_archive(self, id): # 部分完成测试, 因暂时没有可用的崩溃信息ID, 目前为止无法测出返回值为0的结果
        '''
        将某一个崩溃守护进程crash信息进行存档
        :param id: str, 崩溃信息ID, 如 '2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'crash archive', 'format': 'json'}

        if not isinstance(id, str):
            return TypeError('变量id的类型错误, 应为str')
        cmd['id'] = id

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def crash_archive_all(self):
        '''
        将所有崩溃守护进程进行存档
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'crash archive-all', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph mon

    def mon_dump(self, epoch = None):
        '''
        获取MON节点信息
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'mon dump', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def mon_stat(self):
        '''
        获取MON节点状态信息
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'mon stat', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd crush get-device-class/rm-device-class/set-device-class

    def osd_crush_get_device_class(self, ids):
        '''
        获取OSD等级
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush get-device-class', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rm_device_class(self, ids):
        '''
        删除OSD等级
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rm-device-class', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_set_device_class(self, _class, ids):
        '''
        设置OSD等级
        :param class: (string)
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush set-device-class', 'format': 'json'}

        if not isinstance(_class, str):
            return TypeError('变量class的类型错误, 应为str')
        cmd['class'] = _class

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd crush rule

    def osd_crush_rule_create_replicated(self, name, root, type, _class = None):
        '''
        创建多副本CRUSH规则
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则名称
        :param root: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则的根节点
        :param type: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则的故障域类型
        :param class: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则限定分布的OSD等级, 可选参数, 不指定时默认忽略OSD等级
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule create-replicated', 'format': 'json'}

        if not isinstance(name, str):
           return TypeError('变量class的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if not isinstance(root, str):
           return TypeError('变量class的类型错误, 应为str')
        root_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        root_validator.valid(root)
        cmd['root'] = root

        if not isinstance(type, str):
           return TypeError('变量class的类型错误, 应为str')
        type_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        type_validator.valid(type)
        cmd['type'] = type

        if _class is not None:
            if not isinstance(_class, str):
               return TypeError('变量_class的类型错误, 应为str')
            class_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
            class_validator.valid(_class)
            cmd['class'] = _class

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_dump(self, name = None):
        '''
        获取指定CRUSH规则的信息, 包括副本数、故障域等
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则名称, 不指定时默认作用于所有CRUSH规则
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule dump', 'format': 'json'}

        if name is not None:
            if not isinstance(name, str):
                return TypeError('变量name的类型错误, 应为str')
            name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
            name_validator.valid(name)
            cmd['name'] = name

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_list(self):
        '''
        获取CRUSH规则列表
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule list', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_ls(self):
        '''
        获取CRUSH规则列表
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule ls', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_ls_by_class(self, _class):
        '''
        获取指定OSD等级的CRUSH规则列表
        :param class: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), OSD等级
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule ls-by-class', 'format': 'json'}

        if not isinstance(_class, str):
           return TypeError('变量_class的类型错误, 应为str')
        class_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        class_validator.valid(_class)
        cmd['class'] = _class

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_rename(self, srcname, dstname):
        '''
        重命名CRUSH规则
        :param srcname: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 原名称
        :param dstname: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 目标名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule rename', 'format': 'json'}

        if not isinstance(srcname, str):
            return TypeError('变量srcname的类型错误, 应为str')
        srcname_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        srcname_validator.valid(srcname)
        cmd['srcname'] = srcname

        if not isinstance(dstname, str):
            return TypeError('变量dstname的类型错误, 应为str')
        dstname_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        dstname_validator.valid(dstname)
        cmd['dstname'] = dstname

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rule_rm(self, name):
        '''
        删除CRUSH规则
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), CRUSH规则名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rule rm', 'format': 'json'}

        if not isinstance(name, str):
           return TypeError('变量class的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd crush others

    def osd_crush_add_bucket(self, name, type):
        '''
        添加一个无父的bucket
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), bucket名称
        :param type: str, bucket类型
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush add-bucket', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if not isinstance(type, str):
            return TypeError('变量type的类型错误, 应为str')
        cmd['type'] = type

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_dump(self):
        '''
        获取CRUSH map的全部信息, 包括集群拓扑结构以及rule
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush dump', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_ls(self, node):
        '''
        获取CRUSH树中某个节点的下一级子节点列表
        :param node: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 节点名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush ls', 'format': 'json'}

        if not isinstance(node, str):
            return TypeError('变量node的类型错误, 应为str')
        node_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        node_validator.valid(node)
        cmd['node'] = node

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_remove(self, name, ancestor = None): # 部分完成测试, ancestor参数未测试
        '''
        删除一个节点
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 节点名称
        :param ancestor: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 指定的组先节点名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush remove', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if ancestor is not None:
            if not isinstance(ancestor, str):
                return TypeError('变量ancestor的类型错误, 应为str')
            ancestor_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
            ancestor_validator.valid(ancestor)
            cmd['ancestor'] = ancestor

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rename_bucket(self, srcname, dstname):
        '''
        重命名bucket
        :param srcname: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 原名称
        :param dstname: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 目标名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rename-bucket', 'format': 'json'}

        if not isinstance(srcname, str):
            return TypeError('变量srcname的类型错误, 应为str')
        srcname_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        srcname_validator.valid(srcname)
        cmd['srcname'] = srcname

        if not isinstance(dstname, str):
            return TypeError('变量dstname的类型错误, 应为str')
        dstname_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        dstname_validator.valid(dstname)
        cmd['dstname'] = dstname

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_reweight(self, name, weight):
        '''
        调整一个leaf节点 (一般为OSD) 权重, 此处更改的是weight, 而不是reweight
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), leaf节点 (一般为OSD) 名称
        :param weight: float, 满足CephFloat(range = '0.0'), 新权重值
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush reweight', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if not isinstance(weight, float):
            return TypeError('变量weight的类型错误, 应为float')
        weight_validator = ceph_argparse.CephFloat(range = '0.0')
        weight_validator.valid(weight)
        cmd['weight'] = weight

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_reweight_all(self):
        '''
        重新计算权重
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush reweight-all', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_reweight_subtree(self, name, weight):
        '''
        调整一个节点下所有leaf节点 (一般为OSD) 的权重, 此处更改的是weight, 而不是reweight
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 节点名称
        :param weight: float, 满足CephFloat(range = '0.0'), 新权重值
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush reweight-subtree', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if not isinstance(weight, float):
            return TypeError('变量weight的类型错误, 应为float')
        weight_validator = ceph_argparse.CephFloat(range = '0.0')
        weight_validator.valid(weight)
        cmd['weight'] = weight

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_crush_rm(self, name, ancestor = None): # 部分完成测试, ancestor参数未测试
        '''
        删除一个节点
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 节点名称
        :param ancestor: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 指定的组先节点名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd crush rm', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if ancestor is not None:
            if not isinstance(ancestor, str):
                return TypeError('变量ancestor的类型错误, 应为str')
            ancestor_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
            ancestor_validator.valid(ancestor)
            cmd['ancestor'] = ancestor

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd deep-scrub/repair/scrub

    def osd_deep_scrub(self, who): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于deep以及scrubbing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间
        '''
        深度刷新指定OSD
        :param who: str, OSD名称, 'osd.<id>' 或 '<id>' 均可, <X>为OSD的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd deep-scrub', 'format': 'json'}

        if not isinstance(who, str):
            return TypeError('变量who的类型错误, 应为str')
        cmd['who'] = who

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_repair(self, who): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于repairing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间, 可以体现repair进度或成功的是scrub error以及pg inconsistent的告警数量减少
        '''
        修复指定OSD
        :param who: str, OSD名称, 'osd.<id>' 或 '<id>' 均可, <X>为OSD的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd repair', 'format': 'json'}

        if not isinstance(who, str):
            return TypeError('变量who的类型错误, 应为str')
        cmd['who'] = who

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_scrub(self, who): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于scrubbing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间
        '''
        刷新指定OSD
        :param who: str, OSD名称, 'osd.<id>' 或 '<id>' 均可, <X>为OSD的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd scrub', 'format': 'json'}

        if not isinstance(who, str):
            return TypeError('变量who的类型错误, 应为str')
        cmd['who'] = who

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd down/in/out/pause/unpause

    def osd_down(self, ids):
        '''
        设置OSD down
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd down', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_in(self, ids):
        '''
        设置OSD in
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd in', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_out(self, ids):
        '''
        设置OSD out
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd out', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pause(self):
        '''
        设置OSD停止读写
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pause', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_unpause(self):
        '''
        设置OSD可以读写
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd unpause', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd erasure-code-profile

    def osd_erasure_code_profile_get(self, name):
        '''
        获取纠删码模版信息
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 纠删码模版名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {"prefix": "osd erasure-code-profile get", "format": "json"}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_erasure_code_profile_ls(self):
        '''
        删除纠删码模版列表
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {"prefix": "osd erasure-code-profile ls", "format": "json"}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_erasure_code_profile_rm(self, name):
        '''
        删除纠删码模版
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 纠删码模版名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {"prefix": "osd erasure-code-profile rm", "format": "json"}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_erasure_code_profile_set(self, name, profile = None, force = False):
        '''
        创建纠删码模版
        :param name: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 纠删码模版名称
        :param profile: list, 允许多个, 元素为str, 每个元素的格式为 '<key> = <value>', 其中<key>为参数名称, <value>为参数值, 不指定时所有参数均为默认值
            基本参数:
                crush-device-class: CRUSH规则限定分布的OSD等级, 默认为空, 忽略OSD等级
                crush-failure-domain: CRUSH规则的故障域类型, 默认为host
                    CRUSH map中该类型的节点数量不得小于k+m:
                        如小于k+m但不小于k, 应用该规则的存储池的PG将卡在incomplete状态
                        如小于k, 应用该规则的存储池的PG将卡在unknown状态
                crush-root: CRUSH规则的根节点, 默认为default
                jerasure-per-chunk-alignment: 默认为false
                k: 数据块数量, 默认为2
                m: 校验块数量, 默认为1
                plugin: 纠删码插件, 默认为jerasure
                technique: 解码方式, 默认为reed_sol_van
                w: 默认为8
            一般而言, jerasure-per-chunk-alignment和w无需设置, 保留默认即可, 其他参数按需设置
        :param force: bool, 满足CephBool(strings = ''), 用于在参数有变化的情况下强制覆盖已有模版的操作, 不指定时默认为False以防止敏感操作被误触发
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {"prefix": "osd erasure-code-profile set", "format": "json"}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        name_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        name_validator.valid(name)
        cmd['name'] = name

        if profile is not None:
            if not isinstance(profile, list):
                return TypeError('变量profile的类型错误, 应为str')
            for s in profile:
                if not isinstance(s, str):
                    return TypeError('变量profile的元素类型错误, 应为str')
            cmd['profile'] = profile

        if force is not False:
            if not isinstance(force, bool):
                return TypeError('变量force的类型错误, 应为bool')
            force_validator = ceph_argparse.CephBool(strings = '')
            force_validator.valid(str(force))
            cmd['force'] = force

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd get

    def osd_getcrushmap(self, epoch = None):
        '''
        获取二进制的CRUSH map
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd getcrushmap', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_getmap(self, epoch = None):
        '''
        获取二进制的OSD map
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd getmap', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = int(epoch)

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_getmaxosd(self):
        '''
        获取最大的OSD ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd getmaxosd', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd ls

    def osd_ls(self, epoch = None):
        '''
        列出有效OSD的ID
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd ls', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = int(epoch)

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_ls_tree(self, name, epoch = None):
        '''
        列出指定bucket下有效OSD的ID
        :param name: str, bucket名称
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd ls-tree', 'format': 'json'}

        if not isinstance(name, str):
            return TypeError('变量name的类型错误, 应为str')
        cmd['name'] = name

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = int(epoch)

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_lspools(self):
        '''
        获取存储池的基本信息
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd lspools', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd pool

    def osd_pool_application_disable(self, pool, app, yes_i_really_mean_it = False):
        '''
        停用存储池中的应用 (RBD镜像、Ceph FS实例或RGW)
        :param pool: str, 满足CephPoolname, 存储池名称
        :param app: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 应用名称
        :param yes_i_really_mean_it: bool, 满足CephBool(strings = ''), 用于确认敏感操作, 不指定时默认为False以防止敏感操作被误触发
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool application disable', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(app, str):
            return TypeError('变量app的类型错误, 应为str')
        cmd['app'] = app

        if yes_i_really_mean_it is not False:
            if not isinstance(yes_i_really_mean_it, bool):
                return TypeError('变量yes_i_really_mean_it的类型错误, 应为bool')
            yes_i_really_mean_it_validator = ceph_argparse.CephBool(strings = '')
            yes_i_really_mean_it_validator.valid(str(yes_i_really_mean_it))
            cmd['yes_i_really_mean_it'] = yes_i_really_mean_it

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_application_enable(self, pool, app):
        '''
        启用存储池中的应用 (RBD镜像、Ceph FS实例或RGW)
        :param pool: str, 满足CephPoolname, 存储池名称
        :param app: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 应用名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool application enable', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(app, str):
            return TypeError('变量app的类型错误, 应为str')
        app_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
        app_validator.valid(app)
        cmd['app'] = app

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_create(self, pool, pg_num, pgp_num, pool_type = None, erasure_code_profile = None, rule = None):
        '''
        创建存储池
        :param pool: str, 满足CephPoolname, 存储池名称
        :param pg_num: int, 满足CephInt(range = '0'), pg_num参数值
        :param pgp_num: int, 满足CephInt(range = '0'), pgp_num参数值
        :param pool_type: str, 满足CephChoices(strings = 'replicated|erasure')
            存储池类型, 不指定时默认为 'replicated'
        :param erasure_code_profile: str, 满足CephString(goodchars = '[A-Za-z0-9-_.]'), 纠删码模版名称, 仅在pool_type为 'erasure' 时生效
        :param rule: str, CRUSH规则名称, 多副本默认为 'replicated_rule', 纠删码池默认新建或应用与存储池同名 (即pool) 的CRUSH规则
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool create', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(pg_num, int):
            return TypeError('变量pg_num的类型错误, 应为int')
        pg_num_validator = ceph_argparse.CephInt(range = '0')
        pg_num_validator.valid(str(pg_num))
        cmd['pg_num'] = pg_num

        if not isinstance(pgp_num, int):
            return TypeError('变量pgp_num的类型错误, 应为int')
        pgp_num_validator = ceph_argparse.CephInt(range = '0')
        pgp_num_validator.valid(str(pgp_num))
        cmd['pgp_num'] = pgp_num

        if pool_type is not None:
            if not isinstance(pool_type, str):
                return TypeError('变量pool_type的类型错误, 应为str')
            pool_type_validator = ceph_argparse.CephChoices(strings = 'replicated|erasure')
            pool_type_validator.valid(pool_type)
            cmd['pool_type'] = pool_type

            if pool_type == 'erasure':
                if erasure_code_profile is not None:
                    if not isinstance(erasure_code_profile, str):
                        return TypeError('变量erasure_code_profile的类型错误, 应为str')
                    erasure_code_profile_validator = ceph_argparse.CephString(goodchars = '[A-Za-z0-9-_.]')
                    erasure_code_profile_validator.valid(erasure_code_profile)
                    cmd['erasure_code_profile'] = erasure_code_profile

        if rule is not None:
            if not isinstance(rule, str):
                return TypeError('变量rule的类型错误, 应为str')
            cmd['rule'] = rule

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_delete(self, pool, pool2 = None, yes_i_really_really_mean_it = False):
        '''
        删除存储池
        :param pool: str, 满足CephPoolname, 存储池名称
        :param pool2: str, 满足CephPoolname, 重复输入存储池名称 (与pool相同), 用于确认敏感操作
        :param yes_i_really_really_mean_it: bool, 满足CephBool(strings = ''), 用于确认敏感操作, 不指定时默认为False以防止敏感操作被误触发
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool delete', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if pool2 is not None:
            if not isinstance(pool2, str):
                return TypeError('变量pool2的类型错误, 应为str')
            cmd['pool2'] = pool2

        if yes_i_really_really_mean_it is not False:
            if not isinstance(yes_i_really_really_mean_it, bool):
                return TypeError('变量yes_i_really_really_mean_it的类型错误, 应为bool')
            yes_i_really_really_mean_it_validator = ceph_argparse.CephBool(strings = '')
            yes_i_really_really_mean_it_validator.valid(str(yes_i_really_really_mean_it))
            cmd['yes_i_really_really_mean_it'] = yes_i_really_really_mean_it

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_get(self, pool, var):
        '''
        获取存储池参数值
        :param pool: str, 满足CephPoolname, 存储池名称
        :param var: str, 满足CephChoices(strings = 'size|min_size|pg_num|pgp_num|crush_rule|hashpspool|nodelete|nopgchange|nosizechange|write_fadvise_dontneed|noscrub|nodeep-scrub|hit_set_type|hit_set_period|hit_set_count|hit_set_fpp|use_gmt_hitset|target_max_objects|target_max_bytes|cache_target_dirty_ratio|cache_target_dirty_high_ratio|cache_target_full_ratio|cache_min_flush_age|cache_min_evict_age|erasure_code_profile|min_read_recency_for_promote|all|min_write_recency_for_promote|fast_read|hit_set_grade_decay_rate|hit_set_search_last_n|scrub_min_interval|scrub_max_interval|deep_scrub_interval|recovery_priority|recovery_op_priority|scrub_priority|compression_mode|compression_algorithm|compression_required_ratio|compression_max_blob_size|compression_min_blob_size|csum_type|csum_min_block|csum_max_block|allow_ec_overwrites|fingerprint_algorithm|pg_autoscale_mode|pg_autoscale_bias|pg_num_min|target_size_bytes|target_size_ratio')
            存储池参数名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool get', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(var, str):
            return TypeError('变量var的类型错误, 应为str')
        var_validator = ceph_argparse.CephChoices(strings = 'size|min_size|pg_num|pgp_num|crush_rule|hashpspool|nodelete|nopgchange|nosizechange|write_fadvise_dontneed|noscrub|nodeep-scrub|hit_set_type|hit_set_period|hit_set_count|hit_set_fpp|use_gmt_hitset|target_max_objects|target_max_bytes|cache_target_dirty_ratio|cache_target_dirty_high_ratio|cache_target_full_ratio|cache_min_flush_age|cache_min_evict_age|erasure_code_profile|min_read_recency_for_promote|all|min_write_recency_for_promote|fast_read|hit_set_grade_decay_rate|hit_set_search_last_n|scrub_min_interval|scrub_max_interval|deep_scrub_interval|recovery_priority|recovery_op_priority|scrub_priority|compression_mode|compression_algorithm|compression_required_ratio|compression_max_blob_size|compression_min_blob_size|csum_type|csum_min_block|csum_max_block|allow_ec_overwrites|fingerprint_algorithm|pg_autoscale_mode|pg_autoscale_bias|pg_num_min|target_size_bytes|target_size_ratio')
        var_validator.valid(var)
        cmd['var'] = var

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_ls(self, detail = None):
        '''
        获取存储池列表
        :param detail: str, 满足CephChoices(strings = 'detail')
            'detail' 表示显示详细信息, 不指定时默认不启用该参数
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool ls', 'format': 'json'}

        if detail is not None:
            if not isinstance(detail, str):
                return TypeError('变量detail的类型错误, 应为str')
            detail_validator = ceph_argparse.CephChoices(strings = 'detail')
            detail_validator.valid(detail)
            cmd['detail'] = detail

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_rename(self, srcpool, destpool):
        '''
        修改存储池名称
        :param srcpool: str, 满足CephPoolname, 原名称
        :param destpool: str, 满足CephPoolname, 目标名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool rename', 'format': 'json'}

        if not isinstance(srcpool, str):
            return TypeError('变量srcpool的类型错误, 应为str')
        cmd['srcpool'] = srcpool

        if not isinstance(destpool, str):
            return TypeError('变量destpool的类型错误, 应为str')
        cmd['destpool'] = destpool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_repair(self, who): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于repairing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间, 可以体现repair进度或成功的是scrub error以及pg inconsistent的告警数量减少
        '''
        修改存储池名称
        :param who: list, 元素为str, 满足CephPoolname, 允许多个, 有效输入范围为1个或多个存储池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool repair', 'format': 'json'}

        for s in who:
            if not isinstance(s, str):
                return TypeError('变量who的元素类型错误, 应为str')
        cmd['who'] = who

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_rm(self, pool, pool2 = None, yes_i_really_really_mean_it = False):
        '''
        删除存储池
        :param pool: str, 满足CephPoolname, 存储池名称
        :param pool2: str, 满足CephPoolname, 重复输入存储池名称 (与pool相同), 用于确认敏感操作
        :param yes_i_really_really_mean_it: bool, 满足CephBool(strings = ''), 用于确认敏感操作, 不指定时默认为False以防止敏感操作被误触发
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool rm', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if pool2 is not None:
            if not isinstance(pool2, str):
                return TypeError('变量pool2的类型错误, 应为str')
            cmd['pool2'] = pool2

        if yes_i_really_really_mean_it is not False:
            if not isinstance(yes_i_really_really_mean_it, bool):
                return TypeError('变量yes_i_really_really_mean_it的类型错误, 应为bool')
            yes_i_really_really_mean_it_validator = ceph_argparse.CephBool(strings = '')
            yes_i_really_really_mean_it_validator.valid(str(yes_i_really_really_mean_it))
            cmd['yes_i_really_really_mean_it'] = yes_i_really_really_mean_it

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_set(self, pool, var, val):
        '''
        设置存储池参数
        :param pool: str, 满足CephPoolname, 存储池名称
        :param var: str, 满足CephChoices(strings = 'size|min_size|pg_num|pgp_num|pgp_num_actual|crush_rule|hashpspool|nodelete|nopgchange|nosizechange|write_fadvise_dontneed|noscrub|nodeep-scrub|hit_set_type|hit_set_period|hit_set_count|hit_set_fpp|use_gmt_hitset|target_max_bytes|target_max_objects|cache_target_dirty_ratio|cache_target_dirty_high_ratio|cache_target_full_ratio|cache_min_flush_age|cache_min_evict_age|min_read_recency_for_promote|min_write_recency_for_promote|fast_read|hit_set_grade_decay_rate|hit_set_search_last_n|scrub_min_interval|scrub_max_interval|deep_scrub_interval|recovery_priority|recovery_op_priority|scrub_priority|compression_mode|compression_algorithm|compression_required_ratio|compression_max_blob_size|compression_min_blob_size|csum_type|csum_min_block|csum_max_block|allow_ec_overwrites|fingerprint_algorithm|pg_autoscale_mode|pg_autoscale_bias|pg_num_min|target_size_bytes|target_size_ratio')
            存储池参数名称
        :param val: str, 存储池参数值
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool set', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(var, str):
            return TypeError('变量var的类型错误, 应为str')
        var_validator = ceph_argparse.CephChoices(strings = 'size|min_size|pg_num|pgp_num|pgp_num_actual|crush_rule|hashpspool|nodelete|nopgchange|nosizechange|write_fadvise_dontneed|noscrub|nodeep-scrub|hit_set_type|hit_set_period|hit_set_count|hit_set_fpp|use_gmt_hitset|target_max_bytes|target_max_objects|cache_target_dirty_ratio|cache_target_dirty_high_ratio|cache_target_full_ratio|cache_min_flush_age|cache_min_evict_age|min_read_recency_for_promote|min_write_recency_for_promote|fast_read|hit_set_grade_decay_rate|hit_set_search_last_n|scrub_min_interval|scrub_max_interval|deep_scrub_interval|recovery_priority|recovery_op_priority|scrub_priority|compression_mode|compression_algorithm|compression_required_ratio|compression_max_blob_size|compression_min_blob_size|csum_type|csum_min_block|csum_max_block|allow_ec_overwrites|fingerprint_algorithm|pg_autoscale_mode|pg_autoscale_bias|pg_num_min|target_size_bytes|target_size_ratio')
        var_validator.valid(var)
        cmd['var'] = var

        if not isinstance(val, str):
            return TypeError('变量val的类型错误, 应为str')
        cmd['val'] = val

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_pool_stats(self, pool_name = None):
        '''
        获取存储池的实时状态
        :param pool: pool_name, 满足CephPoolname, 指定存储池名称, 如忽略该参数则对所有存储池生效
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd pool stats', 'format': 'json'}

        if pool_name is not None:
            if not isinstance(pool_name, str):
                return TypeError('变量pool_name的类型错误, 应为str')
            cmd['pool_name'] = pool_name

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd reweight/test-reweight

    def osd_reweight(self, id, weight):
        '''
        设置OSD的reweight值
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD编号
        :param weight: float, 满足CephFloat(range = '0.0|1.0'), reweight值
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd reweight', 'format': 'json'}

        if not isinstance(id, int):
            return TypeError('变量id的类型错误, 应为int')
        id_validator = ceph_argparse.CephInt(range = '0')
        id_validator.valid(str(id))
        cmd['id'] = id

        if not isinstance(weight, float):
            return TypeError('变量weight的类型错误, 应为float')
        weight_validator = ceph_argparse.CephFloat(range = '0.0|1.0')
        weight_validator.valid(weight)
        cmd['weight'] = weight

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_reweight_by_pg(self, oload = None, max_change = None, max_osds = None, pools = None):
        '''
        根据PG调整OSD的reweight值
        :param oload: int, 满足CephInt(range = '100')且不可取等号, 与平均负载的百分比值, 不指定时默认为120
        :param max_change: float, 满足CephFloat(range = '0.0')且不可取等号, 每个OSD的reweight值的最大调整量, 不指定时默认为0.05
        :param max_osds: int, 满足CephInt(range = '0')且不可取等号, 单次最多调整的OSD数量, 不指定时默认为4
        :param pools: list, 元素为str, 满足CephPoolname, 允许多个, 有效输入范围为1个或多个存储池名称, 不指定时默认作用于所有存储池
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd reweight-by-pg', 'format': 'json'}

        if oload is not None:
            if not isinstance(oload, int):
                return TypeError('变量oload的类型错误, 应为int')
            oload_validator = ceph_argparse.CephInt(range = '100')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload

        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError('变量max_change的类型错误, 应为float')
            max_change_validator = ceph_argparse.CephFloat(range = '0.0')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError('变量max_osds的类型错误, 应为int')
            max_osds_validator = ceph_argparse.CephInt(range = '0')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds

        if pools is not None:
            if not isinstance(pools, list):
                return TypeError('变量pools的类型错误, 应为list')
            for s in pools:
                if not isinstance(s, str):
                    return TypeError('变量pools的元素类型错误, 应为str')
            cmd['pools'] = pools

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_reweight_by_utilization(self, oload = None, max_change = None, max_osds = None, no_increasing = False):
        '''
        根据空间利用率调整OSD的reweight值
        :param oload: int, 满足CephInt(range = '100')且不可取等号, 与平均负载的百分比值, 不指定时默认为120
        :param max_change: float, 满足CephFloat(range = '0.0')且不可取等号, 每个OSD的reweight值的最大调整量, 不指定时默认为0.05
        :param max_osds: int, 满足CephInt(range = '0')且不可取等号, 单次最多调整的OSD数量, 不指定时默认为4
        :param no_increasing: bool, 满足CephBool(strings = ''), 用于表示是否允许上调reweight值, 不指定时默认为False (允许上调)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd reweight-by-utilization', 'format': 'json'}

        if oload is not None:
            if not isinstance(oload, int):
                return TypeError('变量oload的类型错误, 应为int')
            oload_validator = ceph_argparse.CephInt(range = '100')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload

        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError('变量max_change的类型错误, 应为float')
            max_change_validator = ceph_argparse.CephFloat(range = '0.0')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError('变量max_osds的类型错误, 应为int')
            max_osds_validator = ceph_argparse.CephInt(range = '0')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds

        if no_increasing is not False:
            if not isinstance(no_increasing, bool):
                return TypeError('变量no_increasing的类型错误, 应为bool')
            no_increasing_validator = ceph_argparse.CephBool(strings = '')
            no_increasing_validator.valid(str(no_increasing))
            cmd['no_increasing'] = no_increasing

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_test_reweight_by_pg(self, oload = None, max_change = None, max_osds = None, pools = None): # 部分完成测试, 运行成功, 但返回值不为0
        '''
        根据PG调整OSD的reweight值, 仅输出测试结果, 不实际进行调整
        :param oload: int, 满足CephInt(range = '100')且不可取等号, 与平均负载的百分比值, 不指定时默认为120
        :param max_change: float, 满足CephFloat(range = '0.0')且不可取等号, 每个OSD的reweight值的最大调整量, 不指定时默认为0.05
        :param max_osds: int, 满足CephInt(range = '0')且不可取等号, 单次最多调整的OSD数量, 不指定时默认为4
        :param pools: list, 元素为str, 满足CephPoolname, 允许多个, 有效输入范围为1个或多个存储池名称, 不指定时默认作用于所有存储池
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd test-reweight-by-pg', 'format': 'json'}

        if oload is not None:
            if not isinstance(oload, int):
                return TypeError('变量oload的类型错误, 应为int')
            oload_validator = ceph_argparse.CephInt(range = '100')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload

        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError('变量max_change的类型错误, 应为float')
            max_change_validator = ceph_argparse.CephFloat(range = '0.0')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError('变量max_osds的类型错误, 应为int')
            max_osds_validator = ceph_argparse.CephInt(range = '0')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds

        if pools is not None:
            if not isinstance(pools, list):
                return TypeError('变量pools的类型错误, 应为list')
            for s in pools:
                if not isinstance(s, str):
                    return TypeError('变量pools的元素类型错误, 应为str')
            cmd['pools'] = pools

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_test_reweight_by_utilization(self, oload = None, max_change = None, max_osds = None, no_increasing = False):
        '''
        根据空间利用率调整OSD的reweight值, 仅输出测试结果, 不实际进行调整
        :param oload: int, 满足CephInt(range = '100')且不可取等号, 与平均负载的百分比值, 不指定时默认为120
        :param max_change: float, 满足CephFloat(range = '0.0')且不可取等号, 每个OSD的reweight值的最大调整量, 不指定时默认为0.05
        :param max_osds: int, 满足CephInt(range = '0')且不可取等号, 单次最多调整的OSD数量, 不指定时默认为4
        :param no_increasing: bool, 满足CephBool(strings = ''), 用于表示是否允许上调reweight值, 不指定时默认为False (允许上调)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd test-reweight-by-utilization', 'format': 'json'}

        if oload is not None:
            if not isinstance(oload, int):
                return TypeError('变量oload的类型错误, 应为int')
            oload_validator = ceph_argparse.CephInt(range = '100')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload

        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError('变量max_change的类型错误, 应为float')
            max_change_validator = ceph_argparse.CephFloat(range = '0.0')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError('变量max_osds的类型错误, 应为int')
            max_osds_validator = ceph_argparse.CephInt(range = '0')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds

        if no_increasing is not False:
            if not isinstance(no_increasing, bool):
                return TypeError('变量no_increasing的类型错误, 应为bool')
            no_increasing_validator = ceph_argparse.CephBool(strings = '')
            no_increasing_validator.valid(str(no_increasing))
            cmd['no_increasing'] = no_increasing

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd set/unset

    def osd_set(self, key):
        '''
        设置OSD属性 (标志位)
        :param key: str, 满足CephChoices(strings = 'full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim|pglog_hardlimit')
            标志位名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd set', 'format': 'json'}

        if not isinstance(key, str):
            return TypeError('变量key的类型错误, 应为str')
        key_validator = ceph_argparse.CephChoices(strings = 'full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim|pglog_hardlimit')
        key_validator.valid(key)
        cmd['key'] = key

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_unset(self, key):
        '''
        取消设置OSD属性 (标志位)
        :param key: str, 满足CephChoices(strings = 'full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim')
            标志位名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd unset', 'format': 'json'}

        if not isinstance(key, str):
            return TypeError('变量key的类型错误, 应为str')
        key_validator = ceph_argparse.CephChoices(strings = 'full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim')
        key_validator.valid(key)
        cmd['key'] = key

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd tier

    def osd_tier_add(self, pool, tierpool, force_nonempty = False):
        '''
        设置Cache Tier, 指定一个存储池作为另一个存储池的缓存池
        :param pool: str, 满足CephPoolname, 数据池名称
        :param tierpool: str, 满足CephPoolname, 缓存池名称
        :param force_nonempty: bool, 满足CephBool(strings = ''), 用于表示是否加上参数 '--force_nonempty', 不指定时默认为False (不加该参数)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier add', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(tierpool, str):
            return TypeError('变量tierpool的类型错误, 应为str')
        cmd['tierpool'] = tierpool

        if force_nonempty is not False:
            if not isinstance(force_nonempty, bool):
                return TypeError('变量force_nonempty的类型错误, 应为bool')
            force_nonempty_validator = ceph_argparse.CephBool(strings = '')
            force_nonempty_validator.valid(str(force_nonempty))
            cmd['force_nonempty'] = force_nonempty

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_add_cache(self, pool, tierpool, size):
        '''
        设置Cache Tier, 指定一个存储池作为另一个存储池的缓存池, 并指定缓存容量
        :param pool: str, 满足CephPoolname, 数据池名称
        :param tierpool: str, 满足CephPoolname, 缓存池名称
        :param size: int, 满足CephInt(range = '0')
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier add-cache', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(tierpool, str):
            return TypeError('变量tierpool的类型错误, 应为str')
        cmd['tierpool'] = tierpool

        if not isinstance(size, int):
            return TypeError('变量size的类型错误, 应为int')
        size_validator = ceph_argparse.CephInt(range = '0')
        size_validator.valid(str(size))
        cmd['size'] = size

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_cache_mode(self, pool, mode):
        '''
        设置Cachr Tier缓存池的缓存模式
        :param pool: str, 满足CephPoolname, 缓存池名称
        :param mode: str, 满足CephChoices(strings = 'none|writeback|forward|readonly|readforward|proxy|readproxy')
            缓存模式
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier cache-mode', 'format': 'json'}

        if not isinstance(mode, str):
            return TypeError('变量mode的类型错误, 应为str')
        mode_validator = ceph_argparse.CephChoices(strings = 'none|writeback|forward|readonly|readforward|proxy|readproxy')
        mode_validator.valid(mode)
        cmd['mode'] = mode

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_remove(self, pool, tierpool):
        '''
        移除Cache Tier的设置
        :param pool: str, 满足CephPoolname, 数据池名称
        :param tierpool: str, 满足CephPoolname, 缓存池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier remove', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(tierpool, str):
            return TypeError('变量tierpool的类型错误, 应为str')
        cmd['tierpool'] = tierpool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_remove_overlay(self, pool):
        '''
        移除覆盖池引流
        :param pool: str, 满足CephPoolname, 数据池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier remove-overlay', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_rm(self, pool, tierpool):
        '''
        移除Cache Tier的设置
        :param pool: str, 满足CephPoolname, 数据池名称
        :param tierpool: str, 满足CephPoolname, 缓存池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier rm', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(tierpool, str):
            return TypeError('变量tierpool的类型错误, 应为str')
        cmd['tierpool'] = tierpool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_rm_overlay(self, pool):
        '''
        移除覆盖池引流
        :param pool: str, 满足CephPoolname, 数据池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier rm-overlay', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tier_set_overlay(self, pool, overlaypool):
        '''
        设置覆盖池引流
        :param pool: str, 满足CephPoolname, 数据池名称
        :param overlaypool: str, 满足CephPoolname, 覆盖池名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tier set-overlay', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(overlaypool, str):
            return TypeError('变量overlaypool的类型错误, 应为str')
        cmd['overlaypool'] = overlaypool

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph osd others

    def osd_blocked_by(self):
        '''
        获取阻塞的OSD列表
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd blocked-by', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_df(self, output_method = None, filter_by = None, filter = None):
        '''
        获取OSD的信息, 如命令ceph osd df
        :param output_method: str, 满足CephChoices(strings = 'plain|tree')
            输出方式, 'plain' 为直接列出, 'tree' 为树状列出, 不指定时默认为 'plain'
        :param filter_by: str, 满足CephChoices(strings = 'class|name')
            筛选方式, 'class' 为按OSD等级筛选, 'name' 为按bucket名称筛选, 不指定时默认不筛选
        :param filter: str, 筛选关键字, 当不指定filter_by时不可指定, 当filter_by为 'class' 时为OSD等级名称, 当filter_by为 'name' 时为bucket名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd df', 'format': 'json'}

        if output_method is not None:
            if not isinstance(output_method, str):
                return TypeError('变量output_method的类型错误, 应为str')
            output_method_validator = ceph_argparse.CephChoices(strings = 'plain|tree')
            output_method_validator.valid(output_method)
            cmd['output_method'] = output_method

        if filter_by is not None:
            if not isinstance(filter_by, str):
                return TypeError('变量filter_by的类型错误, 应为str')
            filter_by_validator = ceph_argparse.CephChoices(strings = 'class|name')
            filter_by_validator.valid(filter_by)
            cmd['filter_by'] = filter_by

            if filter is not None:
                if not isinstance(filter, str):
                    return TypeError('变量filter的类型错误, 应为str')
                cmd['filter'] = filter

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_dump(self, epoch = None):
        '''
        获取OSD的总体情况, 如命令ceph osd dump
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd dump', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_find(self, id):
        '''
        获取指定OSD ID的定位信息, 如所在主机及其IP地址等信息
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD编号
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd find', 'format': 'json'}

        if not isinstance(id, int):
            return TypeError('变量id的类型错误, 应为int')
        id_validator = ceph_argparse.CephInt(range = '0')
        id_validator.valid(str(id))
        cmd['id'] = id

        print(cmd)
        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_map(self, pool, object, nspace = None): # 部分完成测试, nspace未测试
        '''
        获取存储池池中指定对象的分布
        :param pool: str, 满足CephPoolname, 存储池名称
        :param object: str, 满足CephObjectname, 对象名称
        :param nspace: str, 命名空间名称
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd map', 'format': 'json'}

        if not isinstance(pool, str):
            return TypeError('变量pool的类型错误, 应为str')
        cmd['pool'] = pool

        if not isinstance(object, str):
            return TypeError('变量object的类型错误, 应为str')
        cmd['object'] = object

        if nspace is not None:
            if not isinstance(nspace, str):
                return TypeError('变量nspace的类型错误, 应为str')
            cmd['nspace'] = nspace

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_metadata(self, id = None):
        '''
        获取指定OSD ID的元数据信息 (默认全部OSD)
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD的ID, 不指定时默认作用于所有OSD
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd metadata', 'format': 'json'}

        if id is not None:
            if not isinstance(id, int):
                return TypeError('变量id的类型错误, 应为int')
            id_validator = ceph_argparse.CephInt(range = '0')
            id_validator.valid(str(id))
            cmd['id'] = id

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_perf(self):
        '''
        获取OSD性能统计
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd perf', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_primary_affinity(self, id, weight):
        '''
        设置OSD的主亲和权重 (即在OSD在PG的peer中被选为主节点的权重)
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD的ID, 不指定时默认作用于所有OSD
        :param weight: float, 满足CephFloat(range = '0.0|1.0'), 主亲和权重值
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd primary-affinity', 'format': 'json'}

        if not isinstance(id, int):
            return TypeError('变量id的类型错误, 应为int')
        id_validator = ceph_argparse.CephInt(range = '0')
        id_validator.valid(str(id))
        cmd['id'] = id

        if not isinstance(weight, float):
            return TypeError('变量weight的类型错误, 应为float')
        weight_validator = ceph_argparse.CephFloat(range = '0.0|1.0')
        weight_validator.valid(weight)
        cmd['weight'] = weight

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_purge(self, id, force = False, yes_i_really_mean_it = False): # 未完成测试, Ceph无法识别id参数, 整型、字符串、整型列表和字符串列表均无法识别
        '''
        彻底删除OSD (等价于依次执行了 "ceph osd crush remove"、"ceph auth del" 和 "ceph osd rm")
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD的ID
        :param force: bool, 满足CephBool(strings = ''), 用于强制操作, 不指定时默认为False以防止敏感操作被误触发
        :param yes_i_really_mean_it: bool, 满足CephBool(strings = ''), 用于确认敏感操作, 不指定时默认为False以防止敏感操作被误触发
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd purge', 'format': 'json'}

        if not isinstance(id, int):
            return TypeError('变量id的类型错误, 应为int')
        id_validator = ceph_argparse.CephInt(range = '0')
        id_validator.valid(str(id))
        cmd['id'] = id

        if force is not False:
            if not isinstance(force, bool):
                return TypeError('变量force的类型错误, 应为bool')
            force_validator = ceph_argparse.CephBool(strings = '')
            force_validator.valid(str(force))
            cmd['force'] = force

        if yes_i_really_mean_it is not False:
            if not isinstance(yes_i_really_mean_it, bool):
                return TypeError('变量yes_i_really_mean_it的类型错误, 应为bool')
            yes_i_really_mean_it_validator = ceph_argparse.CephBool(strings = '')
            yes_i_really_mean_it_validator.valid(str(yes_i_really_mean_it))
            cmd['yes_i_really_mean_it'] = yes_i_really_mean_it

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_purge_subprocess(self, id, force = False, yes_i_really_mean_it = False): # 使用subprocess
        '''
        彻底删除OSD (等价于依次执行了 "ceph osd crush remove"、"ceph auth del" 和 "ceph osd rm")
        :param id: int, 满足CephOsdName, 实际满足CephInt(range = '0'), OSD的ID
        :param force: bool, 满足CephBool(strings = ''), 用于强制操作, 不指定时默认为False以防止敏感操作被误触发
        :param yes_i_really_mean_it: bool, 满足CephBool(strings = ''), 用于确认敏感操作, 不指定时默认为False以防止敏感操作被误触发
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['ceph', 'osd', 'purge']

            if not isinstance(id, int):
                return TypeError('变量id的类型错误, 应为int')
            id_validator = ceph_argparse.CephInt(range = '0')
            id_validator.valid(str(id))
            cmd.append(str(id))

            if force is not False:
                if not isinstance(force, bool):
                    return TypeError('变量force的类型错误, 应为bool')
                force_validator = ceph_argparse.CephBool(strings = '')
                force_validator.valid(str(force))
                cmd.append('--force')
		    
            if yes_i_really_mean_it is not False:
                if not isinstance(yes_i_really_mean_it, bool):
                    return TypeError('变量yes_i_really_mean_it的类型错误, 应为bool')
                yes_i_really_mean_it_validator = ceph_argparse.CephBool(strings = '')
                yes_i_really_mean_it_validator.valid(str(yes_i_really_mean_it))
                cmd.append('--yes_i_really_mean_it')

            result = ['','']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e
        finally:
            self._close()

    def osd_rm(self, ids):
        '''
        删除OSD
        :param ids: list, 允许多个, 元素为str, 有效输入范围为1个或多个OSD的ID, 或者 = ['all'], ['any']
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd rm', 'format': 'json'}

        if not isinstance(ids, list):
            return TypeError('变量ids的类型错误, 应为list')
        for s in ids:
            if not isinstance(s, str):
                return TypeError('变量ids的元素类型错误, 应为str')
        cmd['ids'] = ids

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_stat(self):
        '''
        获取OSD的总体情况, 包括数量和up/in/down/out等状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd stat', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_tree(self, epoch = None):
        '''
        获取OSD树状列表
        :param epoch: int, 满足CephInt(range = '0'), 版本号, 不指定时默认为最新版本
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd tree', 'format': 'json'}

        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError('变量epoch的类型错误, 应为int')
            epoch_validator = ceph_argparse.CephInt(range = '0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def osd_utilization(self):
        '''
        获取OSD总体利用率
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'osd utilization', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph pg deep-scrub/repair/scrub

    def pg_deep_scrub(self, pgid): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于deep以及scrubbing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间
        '''
        深度刷新某个PG
        :param pgid: str, 满足CephPgid(), PG的ID, 格式为 'X.Y', 其中X为存储池的ID, Y为PG在存储池内的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg deep-scrub', 'format': 'json'}

        if not isinstance(pgid, str):
            return TypeError('变量pgid的类型错误, 应为str')
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd['pgid'] = pgid

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_repair(self, pgid): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于repairing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间, 可以体现repair进度或成功的是scrub error以及pg inconsistent的告警数量减少
        '''
        修复某个PG
        :param pgid: str, 满足CephPgid(), PG的ID, 格式为 'X.Y', 其中X为存储池的ID, Y为PG在存储池内的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg repair', 'format': 'json'}

        if not isinstance(pgid, str):
            return TypeError('变量pgid的类型错误, 应为str')
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd['pgid'] = pgid

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_scrub(self, pgid): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于scrubbing状态, 无法查询进度, 该操作的完成时间随操作对象的数据量变化, 可能需要执行很长时间
        '''
        刷新某个PG
        :param pgid: str, 满足CephPgid(), PG的ID, 格式为 'X.Y', 其中X为存储池的ID, Y为PG在存储池内的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg scrub', 'format': 'json'}

        if not isinstance(pgid, str):
            return TypeError('变量pgid的类型错误, 应为str')
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd['pgid'] = pgid

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph pg dump

    def pg_dump(self, dumpcontents = None):
        '''
        获取可读的PG map
        :param dumpcontents: list, 允许多个, 元素为str, 满足CephChoices(strings = 'all|summary|sum|delta|pools|osds|pgs|pgs_brief')
            指定dump的内容, 不指定时默认为 'all' (作用于所有内容)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg dump', 'format': 'json'}

        if dumpcontents is not None:
            if not isinstance(dumpcontents, list):
                return TypeError('变量dumpcontents的类型错误, 应为list')
            dumpcontents_validator = ceph_argparse.CephChoices(strings = 'all|summary|sum|delta|pools|osds|pgs|pgs_brief')
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd['dumpcontents'] = dumpcontents

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_dump_json(self, dumpcontents = None): # 部分完成测试, dumpcontents参数不起作用, 与官方封装好的Linux命令表现一致, 实际执行时都是['all']
        '''
        获取可读的PG map, 以json显示
        :param dumpcontents: list, 允许多个, 元素为str, 满足CephChoices(strings = 'all|summary|sum|pools|osds|pgs')
            指定dump的内容, 不指定时默认为 'all' (作用于所有内容)
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg dump_json', 'format': 'json'}

        if dumpcontents is not None:
            if not isinstance(dumpcontents, list):
                return TypeError('变量dumpcontents的类型错误, 应为list')
            dumpcontents_validator = ceph_argparse.CephChoices(strings = 'all|summary|sum|pools|osds|pgs')
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd['dumpcontents'] = dumpcontents

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_dump_pools_json(self):
        '''
        获取PG map中与池有关的部分, 以json显示
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg dump_pools_json', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_dump_stuck(self, stuckops = None):
        '''
        获取卡住 (有错误状态) 的PG map
        :param stuckops: list, 允许多个, 元素为str, 满足CephChoices(strings = 'inactive|unclean|stale|undersized|degraded')
            指定错误状态, 不指定时默认作用于所有错误状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg dump_stuck', 'format': 'json'}

        if stuckops is not None:
            if not isinstance(stuckops, list):
                return TypeError('变量stuckops的类型错误, 应为list')
            stuckops_validator = ceph_argparse.CephChoices(strings = 'inactive|unclean|stale|undersized|degraded')
            for s in stuckops:
                stuckops_validator.valid(s)
            cmd['stuckops'] = stuckops

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph pg ls

    def pg_ls(self, pool = None, states = None):
        '''
        列出PG信息
        :param pool: int, 满足CephInt(range = ''), 存储池ID, 不指定时默认作用于所有存储池
        :param states: list, 允许多个, 满足CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            指定状态, 不指定时默认作用于所有状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg ls', 'format': 'json'}

        if pool is not None:
            if not isinstance(pool, int):
                return TypeError('变量pool的类型错误, 应为int')
            pool_validator = ceph_argparse.CephInt(range = '')
            pool_validator.valid(str(pool))
            cmd['pool'] = pool

        if states is not None:
            if not isinstance(states, list):
                return TypeError('变量states的类型错误, 应为list')
            states_validator = ceph_argparse.CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_ls_by_osd(self, osd, pool = None, states = None): # 部分完成测试, osd参数不起作用, 输出均为所有OSD的池
        '''
        列出某个OSD的PG信息
        :param osd: str, 满足CephOsdName(), OSD名称
        :param pool: int, 满足CephInt(range = ''), 存储池ID, 不指定时默认作用于所有存储池
        :param states: list, 允许多个, 满足CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            指定状态, 不指定时默认作用于所有状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg ls-by-osd', 'format': 'json'}

        if not isinstance(osd, str):
            return TypeError('变量osd的类型错误, 应为str')
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd['OSD'] = osd # 为啥OSD是要大写才行？？？？OMG！

        if pool is not None:
            if not isinstance(pool, int):
                return TypeError('变量pool的类型错误, 应为int')
            pool_validator = ceph_argparse.CephInt(range = '')
            pool_validator.valid(str(pool))
            cmd['pool'] = pool

        if states is not None:
            if not isinstance(states, list):
                return TypeError('变量states的类型错误, 应为list')
            states_validator = ceph_argparse.CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_ls_by_pool(self, poolstr, states = None):
        '''
        列出某个池的PG信息
        :param poolstr: str, 存储池名称
        :param states: list, 允许多个, 满足CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            指定状态, 不指定时默认作用于所有状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg ls-by-pool', 'format': 'json'}

        if not isinstance(poolstr, str):
            return TypeError('变量poolstr的类型错误, 应为str')
        cmd['poolstr'] = poolstr

        if states is not None:
            if not isinstance(states, list):
                return TypeError('变量states的类型错误, 应为list')
            states_validator = ceph_argparse.CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_ls_by_primary(self, osd, pool = None, states = None): # 部分完成测试, osd参数不起作用, 输出均为所有OSD的池
        '''
        列出某个primary OSD的PG
        :param osd: str, 满足CephOsdName(), OSD名称
        :param pool: int, 满足CephInt(range = ''), 存储池ID, 不指定时默认作用于所有存储池
        :param states: list, 允许多个, 满足CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            指定状态, 不指定时默认作用于所有状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg ls-by-primary', 'format': 'json'}

        if not isinstance(osd, str):
            return TypeError('变量osd的类型错误, 应为str')
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd['OSD'] = osd # 为啥OSD是要大写才行？？？？OMG！

        if pool is not None:
            if not isinstance(pool, int):
                return TypeError('变量pool的类型错误, 应为int')
            pool_validator = ceph_argparse.CephInt(range = '')
            pool_validator.valid(str(pool))
            cmd['pool'] = pool

        if states is not None:
            if not isinstance(states, list):
                return TypeError('变量states的类型错误, 应为list')
            states_validator = ceph_argparse.CephChoices(strings = 'stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error')
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph pg others

    def pg_getmap(self):
        '''
        获取二进制的PG map
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg getmap', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_map(self, pgid):
        '''
        获取某个PG的OSD映射
        :param pgid: str, 满足CephPgid(), PG的ID, 格式为 'X.Y', 其中X为存储池的ID, Y为PG在存储池内的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg map', 'format': 'json'}

        if not isinstance(pgid, str):
            return TypeError('变量pgid的类型错误, 应为str')
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd['pgid'] = pgid

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_repeer(self, pgid): # 返回内容仅为提交操作的提示, 可在集群状态或PG状态中查看哪些PG处于repeering状态, 无法查询进度, 该操作的完成时间一般很短
        '''
        repeer某个PG
        :param pgid: str, 满足CephPgid(), PG的ID, 格式为 'X.Y', 其中X为存储池的ID, Y为PG在存储池内的ID
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg repeer', 'format': 'json'}

        if not isinstance(pgid, str):
            return TypeError('变量pgid的类型错误, 应为str')
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd['pgid'] = pgid

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def pg_stat(self):
        '''
        获取PG的总体状态, 如active、undersized、degraded、clean以及存储使用情况和实时读写
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'pg stat', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    # ceph others

    def deamon_config_show_subprocess(self, daemon, host = None, port = 22, user = 'root'): # 使用subprocess
        '''
        查看指定守护进程的配置
        :param daemon: str, 满足CephName()或<type>为 "auth", 指定目标, 可以是守护进程或PG, 格式为 '<type>.<name>'
            <type>: 守护进程类型, 有效输入范围为 "auth", "mon", "osd", "mds", "mgr", "client"
            <name>: 本机守护进程名称, 对于osd而言是ID, 对于其他类型而言是名称, 均可以设置为 "*" 表示作用于所有同类型守护进程
        :param host: str, 执行本函数操作的主机名称或IP地址, 如为None（默认值）则代表在本机执行；如非None, 由于ssh不支持在命令中直接加入登录密码, 故请尽可能保证当前主机对远程主机已配置SSH免密登录
        :param port: int, 如指定在远程主机执行, 且远程主机的SSH端口号不为默认的22, 则启用此参数
        :param user: str, 如指定在远程主机执行, 需指定远程主机的用户, 默认为'root'
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = []

            if host is not None:
                if not isinstance(host, str):
                    return TypeError('变量host的类型错误, 应为str')
                unreachable = subprocess.Popen(['ping', host, '-c', '2'], stdout = subprocess.PIPE, stderr = subprocess.STDOUT).wait()
                if unreachable:
                    return [unreachable.wait(), unreachable.communicate()[0]]
                cmd.append('ssh')
                if port != 22:
                    if not isinstance(port, int):
                        return TypeError('变量port的类型错误, 应为int')
                    cmd.append('-p')
                    cmd.append(str(port))
                cmd.append(user+'@'+host)

            cmd.append('ceph')
            cmd.append('daemon')

            if not isinstance(daemon, str):
                return TypeError('变量daemon的类型错误, 应为str')
            daemon_split = daemon.split('.')
            if daemon_split[0] is not 'auth':
                daemon_validator = ceph_argparse.CephName()
                daemon_validator.valid(daemon)
            cmd.append(daemon)

            cmd.append('config')
            cmd.append('show')

            result = ['','']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e
        finally:
            self._close()

    def health(self, detail = None):
        '''
        获取集群健康状态
        :param detail: str, 满足CephChoices(strings = 'detail')
            'detail' 表示显示详细信息, 不指定时默认不启用该参数
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'health', 'format': 'json'}

        if detail is not None:
            if not isinstance(detail, str):
                return TypeError('变量detail的类型错误, 应为str')
            detail_validator = ceph_argparse.CephChoices(strings = 'detail')
            detail_validator.valid(detail)
            cmd['detail'] = detail

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def node_ls(self, type = None):
        '''
        获取Ceph节点信息
        :param type: str, 满足CephChoices(strings = 'all|osd|mon|mds|mgr')
            指定节点类型, 默认为 'all'
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'node ls', 'format': 'json'}

        if type is not None:
            if not isinstance(type, str):
                return TypeError('变量type的类型错误, 应为str')
            type_validator = ceph_argparse.CephChoices(strings = 'all|osd|mon|mds|mgr')
            type_validator.valid(type)
            cmd['type'] = type

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def status(self):
        '''
        获取Ceph集群状态
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'status', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def tell(self, target, args): # 未完成测试, args参数无法被识别
        '''
        向指定的目标发送命令
        :param target: str, 满足CephName(), 指定目标, 可以是守护进程或PG, 格式为 '<type>.<name>'
            <type>:
                1. 目标为守护进程时, 为守护进程类型, 有效输入范围为 "osd", "mon", "client", "mds", "mgr"
                2. 目标为PG时, 为PG所在的存储池ID
            <name>:
                1. 目标为守护进程时, 为守护进程名称, 对于osd而言是ID, 对于其他类型而言是名称, 均可以设置为 "*" 表示作用于所有同类型守护进程
                2. 目标为PG时, 为PG在存储池内的ID
        :param args: list, 允许多个, 元素为str, 参数内容
            用例1: 查看PG信息: ['query']
            用例2: 参数注入: ['injectargs', '--<arg>', '<value>']
                <arg>为参数名称
                <value>为参数值
                可以通过成对增加 '--<arg>' 和 '<value>' 的方式同时设置多个参数
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'tell', 'format': 'json'}

        if not isinstance(target, str):
            return TypeError('变量target的类型错误, 应为str')
        target_validator = ceph_argparse.CephName()
        target_validator.valid(target)
        cmd['target'] = target

        if not isinstance(args, list):
            return TypeError('变量args的类型错误, 应为list')
        for s in args:
            if not isinstance(s, str):
                return TypeError('变量args的元素类型错误, 应为str')
        cmd['args'] = args

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def tell_subprocess(self, target, args): # 使用subprocess
        '''
        向指定的目标发送命令
        :param target: str, 满足CephName(), 指定目标, 可以是守护进程或PG, 格式为 '<type>.<name>'
            <type>:
                1. 目标为守护进程时, 为守护进程类型, 有效输入范围为 "osd", "mon", "client", "mds", "mgr"
                2. 目标为PG时, 为PG所在的存储池ID
            <name>:
                1. 目标为守护进程时, 为守护进程名称, 对于osd而言是ID, 对于其他类型而言是名称, 均可以设置为 "*" 表示作用于所有同类型守护进程
                2. 目标为PG时, 为PG在存储池内的ID
        :param args: list, 允许多个, 元素为str, 参数内容
            用例1: 查看PG信息: ['query']
            用例2: 参数注入: ['injectargs', '--<arg>', '<value>']
                <arg>为参数名称
                <value>为参数值
                可以通过成对增加 '--<arg>' 和 '<value>' 的方式同时设置多个参数
        :return: 执行成功时返回列表[返回值, 输出文本], 返回值为0代表执行成功且无报错, 返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['ceph', 'tell']

            if not isinstance(target, str):
                return TypeError('变量target的类型错误, 应为str')
            target_split = target.split('.')
            if not target_split[0].isdigit():
                target_validator = ceph_argparse.CephName()
                target_validator.valid(target)
            cmd.append(target)

            if not isinstance(args, list):
                return TypeError('变量args的类型错误, 应为list')
            for s in args:
                if not isinstance(s, str):
                    return TypeError('变量args的元素类型错误, 应为str')
                cmd.append(s)

            result = ['','']
            run = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            result[1] = run.communicate()[0]
            result[0] = run.returncode
            return result
        except Exception as e:
            raise e
        finally:
            self._close()

    def version(self):
        '''
        获取Ceph版本信息
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'version', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

    def versions(self):
        '''
        获取Ceph各组件版本信息
        :return: tuple, (int ret, str outbuf, str outs), json格式
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: RADOS引起的问题描述
        '''
        cmd = {'prefix': 'versions', 'format': 'json'}

        result = self.run_ceph_command(cmd, inbuf = '')
        return result

# 实例化Ceph对象
if __name__ == '__main__':

    ceph = Ceph()

    arg1 = 'test_ec_pool'
    arg2 = 32
    arg3 = 32
    arg4 = 'erasure'
    arg5 = 'default'
    arg6 = ['plugin = jerasure', 'k = 4', 'm = 2', 'technique = liber8tion', 'crush-failure-domain = osd']
    result = ceph.osd_pool_create(arg1, arg2, arg3, arg4, arg5)
    print(result)
    print(type(result))
    for s in result:
        print(type(s))

    # json.tool格式化输出
    if isinstance(result, tuple):
        with open('output.txt', 'w') as file:
            file.write(result[1])
        with open('output.json', 'w') as file:
            file.write(subprocess.Popen(['python', '-m', 'json.tool', 'output.txt'], stdout = subprocess.PIPE, stderr = subprocess.STDOUT).communicate()[0])

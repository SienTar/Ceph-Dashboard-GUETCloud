# -*- coding: UTF-8 -*-
import rados
import ceph_argparse
import json
import six
import os
from enum import Enum


class StatusCodeEnum(Enum):
    CEPH_OK = (0, 'Success')  #成功
    CEPH_ERROR = (-1, 'Error')  #错误
    CEPH_SERVER_ERR = (500, 'Server Exception')   #服务器异常

    CEPH_THROTTLING_ERR = (4001, 'Frequent Visits')    #访问过于频繁
    CEPH_NECESSARY_PARAM_ERR = (4002, 'Missing Required Parameter')   #缺少必传参数
    CEPH_USER_ERR = (4003, 'User name error')   #用户名错误
    CEPH_PWD_ERR = (4004, 'Password error')  #密码错误
    CEPH_CPWD_ERR = (4005, 'Password inconsistency')   #密码不一致
    CEPH_MOBILE_ERR = (4006, 'Mobile number error')   #手机号错误
    CEPH_SMS_CODE_ERR = (4007, 'Incorrect SMS verification code')   #短信验证码有误
    CEPH_SESSION_ERR = (4008, 'User not logged in')    #用户未登录

    CEPH_DB_ERR = (5000, 'Data error')  #数据错误
    CEPH_NODATA_ERR = (5001, 'No Data')    #无数据
    CEPH_PARAM_ERR = (5002, 'Parameter Error')   #参数错误

    @property
    def code(self):
        """获取状态码"""
        return self.value[0]

    @property
    def message(self):
        """获取状态码信息"""
        return self.value[1]
    
class CephError(Exception):
    """
    运行Ceph命令时出现的错误产生的异常

    :param cmd: 发生错误的cmd
    :param msg: 错误的解释
    """

    def __init__(self, cmd, msg):
        self.cmd = cmd
        self.msg = msg


class Ceph():
    def __init__(self):
        try:
            self.__cluster = rados.Rados(conffile='')
        except TypeError as e:
            print('参数验证错误: {}'.format(e))
            raise e
        print("创建了集群句柄")
        
        try:
            self.__cluster.connect()
        except Exception as e:
            print("链接错误: {}".format(e))
            raise e
        finally:
            print("成功连接集群")
    
    def run_ceph_command(self,cmd,inbuf):
        try:
            result = self.__cluster.mon_command(json.dumps(cmd), inbuf = inbuf)
            if result[0] is not 0:
                print(result)
                raise CephError(cmd=cmd, msg=os.strerror(abs(result[0])))
            return result
        except rados.Error as e:
            raise e
    
    # Ceph集群管理
    def get_health(self):
        '''
        获取集群健康状态
        
        :return: (string outbuf)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "health", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   #return tuple (int ret, string outbuf, string outs)
        health = json.loads(result[1])
        return health['status']
    
    def get_health_detail(self):
        '''
        获取集群健康详情
        
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "health", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def get_crash(self):
        '''
        查看进程崩溃信息
        
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash ls", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def get_crash_info(self, crash_id):
        '''
        查看某个崩溃信息
        
        :param crash_id: string, 崩溃信息的ID，如'2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash info ", "crash_id": crash_id, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def crash_archive(self, crash_id):
        '''
        将某一个崩溃守护进程crash信息进行存档
        
        :param crash_id: string, 崩溃信息的ID，如'2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash info ", "crash_id": crash_id, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def crash_archive_all(self):
        '''
        将所有崩溃守护进程进行存档
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash archive-all", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
        
         
    def get_pool_stats(self):
        '''
        获取池的状态
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd pool stats", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    # PG管理
    def pg_stat(self):
        '''
        获取PG的总体状态，如active、undersized、degraded、clean以及存储使用情况和实时读写
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_getmap(self):
        '''
        获取二进制的PG map
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg getmap", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_dump(self,dumpcontents=None):
        '''
        获取可读的PG map
        
        :param dumpcontents: list, 有效范围=["all","summary","sum","delta","pools","osds","pgs","pgs_brief"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump", "format": "json"}
        if dumpcontents is not None:
            dumpcontents_validator = ceph_argparse.CephChoices(strings="all|summary|sum|delta|pools|osds|pgs|pgs_brief")
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd["dumpcontents"] = dumpcontents
        result = self.run_ceph_command(cmd, inbuf='')
        return result
        
    def pg_dump_json(self, dumpcontents=None):
        '''
        获取可读的PG map，以json显示
        
        :param dumpcontents: list, 有效范围=["all","summary","sum","pools","osds","pgs"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump_json", "format": "json"}
        if dumpcontents is not None:
            dumpcontents_validator = ceph_argparse.CephChoices(strings="all|summary|sum|pools|osds|pgs")
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd['dumpcontents'] = dumpcontents
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_dump_pools_json(self):
        '''
        获取pg池信息，以json显示
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump_pools_json", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_dump_stuck(self, stuckops=None):
        '''
        显示有错误信息的pgs
        
        :param stuckops: list, 错误有效范围=["inactive","unclean","stale","undersized","degraded"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump_stuck", "format": "json"}
        if stuckops is not None:
            stuckops_validator = ceph_argparse.CephChoices(
                strings="inactive|unclean|stale|undersized|degraded")
            for s in stuckops:
                stuckops_validator.valid(s)
            cmd['stuckops'] = stuckops
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_ls_by_pool(self, poolstr, states=None):
        '''
        列出某个池的PG信息
        
        :param poolstr: six.string_types
        :param states: list, 有效范围=["active","clean","down","replay","splitting","scrubbing","scrubq","degraded","inconsistent","peering","repair","recovering","backfill_wait","incomplete","stale","remapped","deep_scrub","backfill","backfill_toofull","recovery_wait","undersized","activating","peered"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        poolstr_validator = ceph_argparse.CephString(goodchars="")
        poolstr_validator.valid(poolstr)
        cmd = {"prefix": "pg ls-by-pool", "poolstr": poolstr,"format": "json"}
        if states is not None:
            states_validator = ceph_argparse.CephChoices(strings = "active|clean|down|replay|splitting|scrubbing|scrubq|degraded|inconsistent|peering|repair|recovering|backfill_wait|incomplete|stale|remapped|deep_scrub|backfill|backfill_toofull|recovery_wait|undersized|activating|peered")
            for s in states:
                states_validator.valid(s)
            cmd["states"] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_ls_by_primary(self, osd, pool=None, states=None):
        '''
        列出某个primary OSD的PG
        
        :param osd: six.string_types
        :param pool: int
        :param states: list, 有效范围=["active","clean","down","replay","splitting","scrubbing","scrubq","degraded","inconsistent","peering","repair","recovering","backfill_wait","incomplete","stale","remapped","deep_scrub","backfill","backfill_toofull","recovery_wait","undersized","activating","peered"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd = {"prefix": "pg ls-by-primary", "OSD": osd, "pool": 1,"format": "json"}  #为啥OSD是要大写才行？？？？OMG！
        if pool is not None:
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(pool)
            cmd["pool"] = pool

        if states is not None:
            states_validator = ceph_argparse.CephChoices(
                strings=
                "active|clean|down|replay|splitting|scrubbing|scrubq|degraded|inconsistent|peering|repair|recovering|backfill_wait|incomplete|stale|remapped|deep_scrub|backfill|backfill_toofull|recovery_wait|undersized|activating|peered")
            for s in states:
                states_validator.valid(s)
            cmd["states"] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_ls_by_osd(self, osd, pool=None, states=None):
        '''
        列出某个OSD的PG
        
        :param osd: six.string_types
        :param pool: int
        :param states: list, 有效范围=["active","clean","down","replay","splitting","scrubbing","scrubq","degraded","inconsistent","peering","repair","recovering","backfill_wait","incomplete","stale","remapped","deep_scrub","backfill","backfill_toofull","recovery_wait","undersized","activating","peered"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd = {"prefix": "pg ls-by-osd", "OSD": osd,"format": "json"}
        if states is not None:
            states_validator = ceph_argparse.CephChoices(
                strings=
                "active|clean|down|replay|splitting|scrubbing|scrubq|degraded|inconsistent|peering|repair|recovering|backfill_wait|incomplete|stale|remapped|deep_scrub|backfill|backfill_toofull|recovery_wait|undersized|activating|peered")
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        if pool is not None:
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(pool)
            cmd['pool'] = pool
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_ls(self, pool=None, states=None):
        '''
        获取PG信息
        
        :param pool: int
        :param states: list, 有效范围=["active","clean","down","replay","splitting","scrubbing","scrubq","degraded","inconsistent","peering","repair","recovering","backfill_wait","incomplete","stale","remapped","deep_scrub","backfill","backfill_toofull","recovery_wait","undersized","activating","peered"]，允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg ls", "format": "json"}
        if states is not None:
            states_validator = ceph_argparse.CephChoices(
                strings=
                "active|clean|down|replay|splitting|scrubbing|scrubq|degraded|inconsistent|peering|repair|recovering|backfill_wait|incomplete|stale|remapped|deep_scrub|backfill|backfill_toofull|recovery_wait|undersized|activating|peered")
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states

        if pool is not None:
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(pool)
            cmd['pool'] = pool
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_map(self, pgid):
        '''
        获取某个PG的OSD映射
        
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg map", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_scrub(self, pgid):
        '''
        刷新某个PG
        
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg scrub", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_deep_scrub(self, pgid):
        '''
        深度刷新某个PG
        
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg deep-scrub", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_repair(self, pgid):
        '''
        修复某个PG
        
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg repair", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    #osd管理
    def osd_stat(self):
        '''
        获取OSD的总体情况，包括数量、up/in/down/out等状态
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_dump(self, epoch=None):
        '''
        获取OSD的总体情况，如命令ceph osd dump
        
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if epoch is not None:
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(epoch)
            cmd['epoch'] = epoch
        cmd = {"prefix": "osd dump", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tree(self, epoch=None):
        '''
        获取osd tree，如命令ceph osd tree
        
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if epoch is not None:
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(epoch)
            cmd['epoch'] = epoch
        cmd = {"prefix": "osd tree", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_ls(self, epoch=None):
        '''
        列出有效osd的ID，如命令ceph osd ls
        
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if epoch is not None:
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(epoch)
            cmd['epoch'] = epoch
        cmd = {"prefix": "osd ls", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_getmap(self, epoch=None):
        '''
        获取二进制的OSD map
        
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if epoch is not None:
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(epoch)
            cmd['epoch'] = epoch
        cmd = {"prefix": "osd getmap", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_getcrushmap(self, epoch=None):
        '''
        获取二进制的CRUSH map
        
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if epoch is not None:
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(epoch)
            cmd['epoch'] = epoch
        cmd = {"prefix": "osd getcrushmap", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_perf(self):
        '''
        获取OSD性能统计
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd perf", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_blocked_by(self):
        '''
        获取阻塞的OSD
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd blocked-by", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_getmaxosd(self):
        '''
        获取最大的OSD ID
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd getmaxosd", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_find(self, id):
        '''
        获取指定OSD ID的定位信息，如服务器、IP等信息
        
        :param id: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd find", "id": id, "format": "json"}
        print(cmd)
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_metadata(self, id=None):
        '''
        获取指定OSD ID的元数据信息（默认全部OSD）
        
        :param id: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd metadata", "format": "json"}
        if id is not None:
            cmd['id'] = id
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_map(self, object, pool, nspace=None):
        '''
        获取池中指定object的PG
        
        :param object: six.string_types
        :param pool: six.string_types
        :param nspace: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        if not isinstance(object, six.string_types):
            raise TypeError("object is not a String")
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        cmd = {"prefix": "osd map", "object": object, "format": "json"}
        if nspace is not None:
            nspace_validator = ceph_argparse.CephString(goodchars="")
            nspace_validator.valid(nspace)
            cmd['nspace'] = nspace
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_scrub(self, osd):
        '''
        刷新指定OSD
        
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(osd)
        cmd = {"prefix": "osd scrub", "who": osd, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_deep_scrub(self, osd):
        '''
        深度刷新指定OSD
        
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(osd)
        cmd = {"prefix": "osd deep-scrub", "who": osd, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_repair(self, osd):
        '''
        修复指定OSD
        
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(osd)
        cmd = {"prefix": "osd repair", "who": osd, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    
    def osd_lspools(self, auid=None):
        '''
        获取存储池的基本信息
        
        :param auid: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd lspools", "format": "json"}
        if auid is not None:
            auid_validator = ceph_argparse.CephInt(range='')
            auid_validator.valid(auid)
            cmd['auid'] = auid
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_rule_list(self):
        '''
        获取crush rule的基本信息
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd crush rule list", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_crush_rule_dump(self, name=None):
        '''
        获取指定crush rule的信息（默认全部），包括副本数、故障域等
        
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd crush rule dump", "format": "json"}
        if name is not None:
            name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
            name_validator.valid(name)
            cmd['name'] = name
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_dump(self):
        '''
        获取crush map的全部信息,包括集群拓扑结构以及rule
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd crush dump", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_add_bucket(self, name, type):
        '''
        添加一个无父母的bucket
        
        :param name: six.string_types
        :param type: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        type_validator = ceph_argparse.CephString(goodchars="")
        type_validator.valid(type)
        cmd = {"prefix": "osd crush add-bucket", "name": name, "type": type, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_rename_bucket(self, dstname, srcname):
        '''
        重命名bucket
        
        :param dstname: six.string_types
        :param srcname: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        dstname_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        dstname_validator.valid(dstname)
        srcname_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        srcname_validator.valid(srcname)
        cmd = {"prefix": "osd crush rename-bucket", "dstname": dstname, "srcname": srcname, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight_all(self):
        '''
        重新计算权重
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd crush reweight-all", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight(self, weight, name):
        '''
        调整自身权重
        
        :param weight: float
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        weight_validator = ceph_argparse.CephFloat(range='0')
        weight_validator.valid(weight)
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        cmd = {"prefix": "osd crush reweight", "weight": weight, "name": name, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight_subtree(self, weight, name):
        '''
        调整自身以及子树权重
        
        :param weight: float
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        weight_validator = ceph_argparse.CephFloat(range='0')
        weight_validator.valid(weight)
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        cmd = {"prefix": "osd crush reweight-subtree", "weight": weight, "name": name, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_pause(self):
        '''
        设置OSD停止读写
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd pause", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_unpause(self):
        '''
        设置OSD可以读写
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "osd unpause", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_set(self, key):
        '''
        设置OSD属性
        
        :param key: list, 有效属性=["full","pause","noup","nodown","noout","noin","nobackfill","norebalance","norecover","noscrub","nodeep-scrub","notieragent","sortbitwise"]
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        key_validator = ceph_argparse.CephChoices(
            strings=
            "full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|sortbitwise")
        for s in key:
            key_validator.valid(s)
        cmd = {"prefix": "osd set", "key": key, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_unset(self, key):
        '''
        取消设置OSD属性
        
        :param key: list, 有效属性=["full","pause","noup","nodown","noout","noin","nobackfill","norebalance","norecover","noscrub","nodeep-scrub","notieragent","sortbitwise"]
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        key_validator = ceph_argparse.CephChoices(
            strings=
            "full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|sortbitwise")
        for s in key:
            key_validator.valid(s)
        cmd = {"prefix": "osd unset", "key": key, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_down(self, ids):
        '''
        设置OSD down
        
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd down", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_out(self, ids):
        '''
        设置OSD out
        
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd out", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_in(self, ids):
        '''
        设置OSD in
        
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd in", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_rm(self, ids):
        '''
        设置OSD rm
        
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd rm", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight(self, id, weight):
        '''
        设置OSD reweight
        
        :param ids: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        id_validator = ceph_argparse.CephInt(range='0')
        id_validator.valid(id)
        weight_validator = ceph_argparse.CephFloat(range='0|1')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd reweight", "id": id, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_primary_affinity(self, id, weight):
        '''
        设置OSD primary_affinity
        
        :param ids: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        id_validator = ceph_argparse.CephOsdName()
        id_validator.valid(id)
        weight_validator = ceph_argparse.CephFloat(range='0|1')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd primary-affinity", "id": id, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_pool_stats(self, name=None):
        '''
        获取存储池的实时状态
        
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd pool stats", "format": "json"}
        if name is not None:
            name_validator = ceph_argparse.CephString(goodchars="")
            name_validator.valid(name)
            cmd['name'] = name
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_utilization(self):
        '''
        获取OSD总体利用率
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd utilization", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight_by_utilization(self,
                                    oload=None,
                                    max_osds=None,
                                    no_increasing=None,
                                    max_change=None):
        '''
        根据存储利用率调整OSD reweight
        
        :param oload: int
        :param max_osds: int
        :param no_increasing: list
        :param max_change: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd reweight-by-utilization", "format": "json"}
        if oload is not None:
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(oload)
            cmd['oload'] = oload

        if max_osds is not None:
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(max_osds)
            cmd['max_osds'] = max_osds

        if no_increasing is not None:
            no_increasing_validator = ceph_argparse.CephChoices(
                strings="--no-increasing")
            for s in no_increasing:
                no_increasing_validator.valid(s)
            cmd['no_increasing'] = no_increasing

        if max_change is not None:
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_test_reweight_by_utilization(self,
                                         max_osds=None,
                                         max_change=None,
                                         no_increasing=None,
                                         oload=None):
        '''
        测试：根据存储利用率调整OSD reweight
        
        :param oload: int
        :param max_osds: int
        :param no_increasing: list
        :param max_change: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd test-reweight-by-utilization", "format": "json"}
        if max_osds is not None:
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(max_osds)
            cmd['max_osds'] = max_osds

        if max_change is not None:
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if no_increasing is not None:
            no_increasing_validator = ceph_argparse.CephChoices(
                strings="--no-increasing")
            for s in no_increasing:
                no_increasing_validator.valid(s)
            cmd['no_increasing'] = no_increasing

        if oload is not None:
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(oload)
            cmd['oload'] = oload
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight_by_pg(self,
                           max_osds=None,
                           max_change=None,
                           oload=None,
                           pools=None):
        '''
        根据PG调整OSD reweight
        
        :param max_osds: int
        :param max_change: float
        :param oload: int
        :param pools: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd reweight-by-pg", "format": "json"}
        if max_osds is not None:
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(max_osds)
            cmd['max_osds'] = max_osds

        if max_change is not None:
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if oload is not None:
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(oload)
            cmd['oload'] = oload

        if pools is not None:
            if not isinstance(pools, six.string_types):
                raise TypeError("pools is not a String")
            cmd['pools'] = pools
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_test_reweight_by_pg(self,
                                max_change=None,
                                max_osds=None,
                                pools=None,
                                oload=None):
        '''
        测试：根据PG调整OSD reweight
        
        :param max_osds: int
        :param max_change: float
        :param oload: int
        :param pools: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd test-reweight-by-pg", "format": "json"}
        if max_change is not None:
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change

        if max_osds is not None:
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(max_osds)
            cmd['max_osds'] = max_osds

        if pools is not None:
            if not isinstance(pools, six.string_types):
                raise TypeError("pools is not a String")
            cmd['pools'] = pools

        if oload is not None:
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(oload)
            cmd['oload'] = oload
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_df(self, output_method=None):
        '''
        获取OSD的信息，如命令ceph osd df
        
        :param output_method: list, 有效参数=["plain","tree"]
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "osd df", "format": "json"}
        if output_method is not None:
            output_method_validator = ceph_argparse.CephChoices(
                strings="plain|tree")
            for s in output_method:
                output_method_validator.valid(s)
            cmd['output_method'] = output_method
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    #pool管理
    def osd_tier_add(self, tierpool, pool, force_nonempty=None):
        '''
        设置Cache Tier
        
        :param tierpool: six.string_types
        :param pool: six.string_types
        :param force_nonempty: list, 有效参数= ["--force-nonempty"]
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        if not isinstance(tierpool, six.string_types):
            raise TypeError("tierpool is not a String")
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        cmd = {"prefix": "osd tier add", "tierpool": tierpool, "pool": pool, "format": "json"}
        if force_nonempty is not None:
            force_nonempty_validator = ceph_argparse.CephChoices(
                strings="--force-nonempty")
            for s in force_nonempty:
                force_nonempty_validator.valid(s)
            cmd['force_nonempty'] = force_nonempty
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_remove(self, tierpool, pool):
        '''
        移除Cache Tier的设置
        
        :param tierpool: six.string_types
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        if not isinstance(tierpool, six.string_types):
            raise TypeError("tierpool is not a String")
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        cmd = {"prefix": "osd tier remove", "tierpool": tierpool, "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_cache_mode(self, pool, mode, sure=None):
        '''
        设置Cachr Tier的模式
        
        :param pool: six.string_types
        :param mode: list, 有效参数 = ["none","writeback","forward","readonly","readforward","proxy","readproxy"] 
        :param sure: list 有效参数 = ["--yes-i-really-mean-it"] 
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        mode_validator = ceph_argparse.CephChoices(
            strings=
            "none|writeback|forward|readonly|readforward|proxy|readproxy")
        for s in mode:
            mode_validator.valid(s)
        cmd = {"prefix": "osd tier cache-mode", "pool": pool, "mode": mode, "format": "json"}
        if sure is not None:
            sure_validator = ceph_argparse.CephChoices(
                strings="--yes-i-really-mean-it")
            for s in sure:
                sure_validator.valid(s)
            cmd['sure'] = sure
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_set_overlay(self, overlaypool, pool):
        '''
        添加覆盖池
        
        :param overlaypool: six.string_types
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        if not isinstance(overlaypool, six.string_types):
            raise TypeError("overlaypool is not a String")
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        cmd = {"prefix": "osd tier set-overlay", "overlaypool": overlaypool, "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_remove_overlay(self, pool):
        '''
        移出覆盖池
        
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        cmd = {"prefix": "osd tier remove-overlay", "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_add_cache(self, size, pool, tierpool):
        '''
        添加指定大小的缓存池
        
        :param size: int
        :param pool: six.string_types
        :param tierpool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        size_validator = ceph_argparse.CephInt(range='0')
        size_validator.valid(size)
        if not isinstance(pool, six.string_types):
            raise TypeError("pool is not a String")
        if not isinstance(tierpool, six.string_types):
            raise TypeError("tierpool is not a String")
        cmd = {"prefix": "osd tier add-cache", "size": size, "pool": pool, "tierpool": tierpool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    #MON管理
    def version(self):
        '''
        获取Ceph 版本
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "version", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def node_ls(self, type=None):
        '''
        获取Ceph 节点信息
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "node ls", "format": "json"}
        if type is not None:
            type_validator = ceph_argparse.CephChoices(
                strings="all|osd|mon|mds")
            for s in type:
                type_validator.valid(s)
            cmd['type'] = type
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def mon_stat(self):
        '''
        获取Mon 节点信息
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "mon stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    
    #权限管理
    def auth_export(self, entity=None):
        '''
        为组件写入密钥环，如果未给定，则写入主密钥环
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "auth export", "format": "json"}
        if entity is not None:
            entity_validator = ceph_argparse.CephString(goodchars="")
            entity_validator.valid(entity)
            cmd['entity'] = entity
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def auth_list(self):
        '''
        列表身份验证状态
        
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
    
        cmd = {"prefix": "auth list", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result 
    
#实例化Ceph对象
ceph = Ceph()  
args = "replicated_rule"
print(ceph.pg_stat())

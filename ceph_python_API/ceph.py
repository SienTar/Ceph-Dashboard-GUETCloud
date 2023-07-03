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
    def get_health(self): # 已完成测试
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
    
    def get_health_detail(self): # 已完成测试
        '''
        获取集群健康详情
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "health", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def get_crash(self): # 已完成测试
        '''
        查看进程崩溃信息
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash ls", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def get_crash_info(self, crash_id): # 未完成测试, 暂时没有可用的crash_id
        '''
        查看某个崩溃信息
        :param crash_id: string, 崩溃信息的ID, 如'2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: json,(int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(crash_id, string):
            return TypeError("变量crash_id的类型错误, 应为string")
        cmd = {"prefix": "crash info ", "crash_id": crash_id, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def crash_archive(self, crash_id): # 未完成测试, 暂时没有可用的crash_id
        '''
        将某一个崩溃守护进程crash信息进行存档
        :param crash_id: string, 崩溃信息的ID, 如'2022-04-22T00:53:30.164344Z_ce493a00-60bf-4114-bb47-6246ebaa4237'
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(crash_id, string):
            return TypeError("变量crash_id的类型错误, 应为string")
        cmd = {"prefix": "crash info ", "crash_id": crash_id, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def crash_archive_all(self): # 已完成测试
        '''
        将所有崩溃守护进程进行存档
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "crash archive-all", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
        
         
    def get_pool_stats(self): # 已完成测试
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
    def pg_stat(self): # 已完成测试
        '''
        获取PG的总体状态, 如active、undersized、degraded、clean以及存储使用情况和实时读写
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_getmap(self): # 已完成测试
        '''
        获取二进制的PG map
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg getmap", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_dump(self,dumpcontents=None): # 已完成测试
        '''
        获取可读的PG map
        :param dumpcontents: list, 有效范围=["all","summary","sum","delta","pools","osds","pgs","pgs_brief"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "pg dump", "format": "json"}
        if dumpcontents is not None:
            if not isinstance(dumpcontents, list):
                return TypeError("变量dumpcontents的类型错误, 应为list")
            dumpcontents_validator = ceph_argparse.CephChoices(strings="all|summary|sum|delta|pools|osds|pgs|pgs_brief")
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd["dumpcontents"] = dumpcontents
        result = self.run_ceph_command(cmd, inbuf='')
        return result
        
    def pg_dump_json(self, dumpcontents=None): # 已完成测试, dumpcontents参数不起作用, 与官方封装好的Linux命令表现一致, 实际执行时都是["all"]
        '''
        获取可读的PG map, 以json显示
        :param dumpcontents: list, 有效范围=["all","summary","sum","pools","osds","pgs"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "pg dump_json", "format": "json"}
        if dumpcontents is not None:
            if not isinstance(dumpcontents, list):
                return TypeError("变量dumpcontents的类型错误, 应为list")
            dumpcontents_validator = ceph_argparse.CephChoices(strings="all|summary|sum|pools|osds|pgs")
            for s in dumpcontents:
                dumpcontents_validator.valid(s)
            cmd['dumpcontents'] = dumpcontents
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_dump_pools_json(self): # 已完成测试
        '''
        获取PG map中与池有关的部分, 以json显示
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump_pools_json", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_dump_stuck(self, stuckops=None): # 已完成测试
        '''
        显示有错误信息的pgs
        :param stuckops: list, 错误有效范围=["inactive","unclean","stale","undersized","degraded"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg dump_stuck", "format": "json"}
        if stuckops is not None:
            if not isinstance(stuckops, list):
                return TypeError("变量stuckops的类型错误, 应为list")
            stuckops_validator = ceph_argparse.CephChoices(strings="inactive|unclean|stale|undersized|degraded")
            for s in stuckops:
                stuckops_validator.valid(s)
            cmd['stuckops'] = stuckops
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_ls_by_pool(self, poolstr, states=None): # 已完成测试
        '''
        列出某个池的PG信息
        :param poolstr: six.string_types
        :param states: list, 有效范围=["stale","creating","active","activating","clean","recovery_wait","recovery_toofull","recovering","forced_recovery","down","recovery_unfound","backfill_unfound","undersized","degraded","remapped","premerge","scrubbing","deep","inconsistent","peering","repair","backfill_wait","backfilling","forced_backfill","backfill_toofull","incomplete","peered","snaptrim","snaptrim_wait","snaptrim_error"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(poolstr, six.string_types):
            return TypeError("变量poolstr的类型错误, 应为six.string_types")
        poolstr_validator = ceph_argparse.CephString(goodchars="")
        poolstr_validator.valid(poolstr)
        cmd = {"prefix": "pg ls-by-pool", "poolstr": poolstr,"format": "json"}
        if states is not None:
            if not isinstance(states, list):
                return TypeError("变量states的类型错误, 应为list")
            states_validator = ceph_argparse.CephChoices(strings="stale+creating+active+activating+clean+recovery_wait+recovery_toofull+recovering+forced_recovery+down+recovery_unfound+backfill_unfound+undersized+degraded+remapped+premerge+scrubbing+deep+inconsistent+peering+repair+backfill_wait+backfilling+forced_backfill+backfill_toofull+incomplete+peered+snaptrim+snaptrim_wait+snaptrim_error")
            for s in states:
                states_validator.valid(s)
            cmd["states"] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_ls_by_primary(self, osd, pool=None, states=None): # 部分完成测试, osd不起作用, 输出均为所有OSD的池
        '''
        列出某个primary OSD的PG
        :param osd: six.string_types
        :param pool: int
        :param states: list, 有效范围=["stale","creating","active","activating","clean","recovery_wait","recovery_toofull","recovering","forced_recovery","down","recovery_unfound","backfill_unfound","undersized","degraded","remapped","premerge","scrubbing","deep","inconsistent","peering","repair","backfill_wait","backfilling","forced_backfill","backfill_toofull","incomplete","peered","snaptrim","snaptrim_wait","snaptrim_error"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(osd, six.string_types):
            return TypeError("变量osd的类型错误, 应为six.string_types")
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd = {"prefix": "pg ls-by-primary", "OSD": osd, "format": "json"}  #为啥OSD是要大写才行？？？？OMG！
        if pool is not None:
            if not isinstance(pool, int):
                return TypeError("变量pool的类型错误, 应为int")
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(str(pool))
            cmd["pool"] = pool
        if states is not None:
            if not isinstance(states, list):
                return TypeError("变量states的类型错误, 应为list")
            states_validator = ceph_argparse.CephChoices(strings="stale+creating+active+activating+clean+recovery_wait+recovery_toofull+recovering+forced_recovery+down+recovery_unfound+backfill_unfound+undersized+degraded+remapped+premerge+scrubbing+deep+inconsistent+peering+repair+backfill_wait+backfilling+forced_backfill+backfill_toofull+incomplete+peered+snaptrim+snaptrim_wait+snaptrim_error")
            for s in states:
                states_validator.valid(s)
            cmd["states"] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result

    def pg_ls_by_osd(self, osd, pool=None, states=None):  # 部分完成测试, osd不起作用, 输出均为所有OSD的池
        '''
        列出某个OSD的PG
        :param osd: six.string_types
        :param pool: int
        :param states: list, 有效范围=["stale","creating","active","activating","clean","recovery_wait","recovery_toofull","recovering","forced_recovery","down","recovery_unfound","backfill_unfound","undersized","degraded","remapped","premerge","scrubbing","deep","inconsistent","peering","repair","backfill_wait","backfilling","forced_backfill","backfill_toofull","incomplete","peered","snaptrim","snaptrim_wait","snaptrim_error"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(osd, six.string_types):
            return TypeError("变量osd的类型错误, 应为six.string_types")
        osd_validator = ceph_argparse.CephOsdName()
        osd_validator.valid(osd)
        cmd = {"prefix": "pg ls-by-osd", "OSD": osd,"format": "json"}
        if pool is not None:
            if not isinstance(pool, int):
                return TypeError("变量pool的类型错误, 应为int")
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(str(pool))
            cmd['pool'] = int(pool)
        if states is not None:
            if not isinstance(states, list):
                return TypeError("变量states的类型错误, 应为list")
            states_validator = ceph_argparse.CephChoices(strings="stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error")
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_ls(self, pool=None, states=None): # 已完成测试
        '''
        列出PG
        :param pool: int
        :param states: list, 有效范围=["stale","creating","active","activating","clean","recovery_wait","recovery_toofull","recovering","forced_recovery","down","recovery_unfound","backfill_unfound","undersized","degraded","remapped","premerge","scrubbing","deep","inconsistent","peering","repair","backfill_wait","backfilling","forced_backfill","backfill_toofull","incomplete","peered","snaptrim","snaptrim_wait","snaptrim_error"], 允许多个
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        
        cmd = {"prefix": "pg ls", "format": "json"}
        if pool is not None:
            if not isinstance(pool, int):
                return TypeError("变量pool的类型错误, 应为int")
            pool_validator = ceph_argparse.CephInt(range='')
            pool_validator.valid(str(pool))
            cmd['pool'] = pool
        if states is not None:
            if not isinstance(states, list):
                return TypeError("变量states的类型错误, 应为list")
            states_validator = ceph_argparse.CephChoices(strings="stale|creating|active|activating|clean|recovery_wait|recovery_toofull|recovering|forced_recovery|down|recovery_unfound|backfill_unfound|undersized|degraded|remapped|premerge|scrubbing|deep|inconsistent|peering|repair|backfill_wait|backfilling|forced_backfill|backfill_toofull|incomplete|peered|snaptrim|snaptrim_wait|snaptrim_error")
            for s in states:
                states_validator.valid(s)
            cmd['states'] = states
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_map(self, pgid): # 已完成测试
        '''
        获取某个PG的OSD映射
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pgid, six.string_types):
            return TypeError("变量pgid的类型错误, 应为six.string_types")
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
        if not isinstance(pgid, six.string_types):
            return TypeError("变量pgid的类型错误, 应为six.string_types")
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg scrub", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_deep_scrub(self, pgid): # 已完成测试
        '''
        深度刷新某个PG
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pgid, six.string_types):
            return TypeError("变量pgid的类型错误, 应为six.string_types")
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg deep-scrub", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_repair(self, pgid): # 已完成测试
        '''
        修复某个PG
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pgid, six.string_types):
            return TypeError("变量pgid的类型错误, 应为six.string_types")
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg repair", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    def pg_repeer(self, pgid): # 已完成测试
        '''
        repeer某个PG
        :param pgid: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pgid, six.string_types):
            return TypeError("变量pgid的类型错误, 应为six.string_types")
        pgid_validator = ceph_argparse.CephPgid()
        pgid_validator.valid(pgid)
        cmd = {"prefix": "pg repeer", "pgid": pgid, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')
        return result
    
    # OSD管理
    def osd_stat(self): # 已完成测试
        '''
        获取OSD的总体情况, 包括数量、up/in/down/out等状态
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_dump(self, epoch=None): # 已完成测试
        '''
        获取OSD的总体情况, 如命令ceph osd dump
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd dump", "format": "json"}
        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError("变量epoch的类型错误, 应为int")
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tree(self, epoch=None): # 已完成测试
        '''
        获取osd tree, 如命令ceph osd tree
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd tree", "format": "json"}
        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError("变量epoch的类型错误, 应为int")
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_ls(self, epoch=None): # 已完成测试
        '''
        列出有效osd的ID, 如命令ceph osd ls
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd ls", "format": "json"}
        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError("变量epoch的类型错误, 应为int")
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = int(epoch)
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_getmap(self, epoch=None): # 已完成测试
        '''
        获取二进制的OSD map
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd getmap", "format": "json"}
        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError("变量epoch的类型错误, 应为int")
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = int(epoch)
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_getcrushmap(self, epoch=None): # 已完成测试
        '''
        获取二进制的CRUSH map
        :param epoch: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd getcrushmap", "format": "json"}
        if epoch is not None:
            if not isinstance(epoch, int):
                return TypeError("变量epoch的类型错误, 应为int")
            epoch_validator = ceph_argparse.CephInt(range='0')
            epoch_validator.valid(str(epoch))
            cmd['epoch'] = epoch
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_perf(self): # 已完成测试
        '''
        获取OSD性能统计
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd perf", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_blocked_by(self): # 已完成测试
        '''
        获取阻塞的OSD
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd blocked-by", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_getmaxosd(self): # 已完成测试
        '''
        获取最大的OSD ID
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd getmaxosd", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_find(self, id): # 已完成测试
        '''
        获取指定OSD ID的定位信息, 如服务器、IP等信息
        :param id: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(id, int):
            return TypeError("变量id的类型错误, 应为int")
        id_validator = ceph_argparse.CephInt(range='0')
        id_validator.valid(str(id))
        cmd = {"prefix": "osd find", "id": id, "format": "json"}
        print(cmd)
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_metadata(self, id=None): # 已完成测试
        '''
        获取指定OSD ID的元数据信息（默认全部OSD）
        :param id: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd metadata", "format": "json"}
        if id is not None:
            if not isinstance(id, int):
                return TypeError("变量id的类型错误, 应为int")
            id_validator = ceph_argparse.CephInt(range='0')
            id_validator.valid(str(id))
            cmd['id'] = id
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_map(self, pool, object, nspace=None): # 部分完成测试, nspace未测试
        '''
        获取池中指定object的PG
        :param object: six.string_types
        :param pool: six.string_types
        :param nspace: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        if not isinstance(object, six.string_types):
            return TypeError("变量object的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd map", "pool":pool, "object": object, "format": "json"}
        if nspace is not None:
            if not isinstance(nspace, six.string_types):
                return TypeError("变量nspace的类型错误, 应为six.string_types")
            nspace_validator = ceph_argparse.CephString(goodchars="")
            nspace_validator.valid(nspace)
            cmd['nspace'] = nspace
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_scrub(self, who): # 已完成测试
        '''
        刷新指定OSD
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(who, six.string_types):
            return TypeError("变量who的类型错误, 应为six.string_types")
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(who)
        cmd = {"prefix": "osd scrub", "who": who, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_deep_scrub(self, who): # 已完成测试
        '''
        深度刷新指定OSD
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(who, six.string_types):
            return TypeError("变量who的类型错误, 应为six.string_types")
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(who)
        cmd = {"prefix": "osd deep-scrub", "who": who, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_repair(self, who): # 已完成测试
        '''
        修复指定OSD
        
        :param osd: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(who, six.string_types):
            return TypeError("变量who的类型错误, 应为six.string_types")
        who_validator = ceph_argparse.CephString(goodchars="")
        who_validator.valid(who)
        cmd = {"prefix": "osd repair", "who": who, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_lspools(self, auid=None): # 部分完成测试, auid未测试
        '''
        获取存储池的基本信息
        :param auid: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd lspools", "format": "json"}
        if auid is not None:
            if not isinstance(auid, int):
                return TypeError("变量auid的类型错误, 应为int")
            auid_validator = ceph_argparse.CephInt(range='')
            auid_validator.valid(str(auid))
            cmd['auid'] = auid
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_rule_list(self): # 已完成测试
        '''
        获取crush rule的基本信息
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd crush rule list", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result

    def osd_crush_rule_dump(self, name=None): # 已完成测试
        '''
        获取指定crush rule的信息（默认全部）, 包括副本数、故障域等
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd crush rule dump", "format": "json"}
        if name is not None:
            if not isinstance(name, six.string_types):
                return TypeError("变量name的类型错误, 应为six.string_types")
            name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
            name_validator.valid(name)
            cmd['name'] = name
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_dump(self): # 已完成测试
        '''
        获取crush map的全部信息,包括集群拓扑结构以及rule
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd crush dump", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_add_bucket(self, name, type): # 已完成测试
        '''
        添加一个无父母的bucket
        :param name: six.string_types
        :param type: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(name, six.string_types):
            return TypeError("变量name的类型错误, 应为six.string_types")
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        if not isinstance(type, six.string_types):
            return TypeError("变量type的类型错误, 应为six.string_types")
        type_validator = ceph_argparse.CephString(goodchars="")
        type_validator.valid(type)
        cmd = {"prefix": "osd crush add-bucket", "name": name, "type": type, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_rm(self, name): # 已完成测试
        '''
        删除一个bucket
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(name, six.string_types):
            return TypeError("变量name的类型错误, 应为six.string_types")
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        cmd = {"prefix": "osd crush rm", "name": name, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_rename_bucket(self, srcname, dstname): # 已完成测试
        '''
        重命名bucket
        :param dstname: six.string_types
        :param srcname: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(dstname, six.string_types):
            return TypeError("变量dstname的类型错误, 应为six.string_types")
        dstname_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        dstname_validator.valid(dstname)
        if not isinstance(srcname, six.string_types):
            return TypeError("变量srcname的类型错误, 应为six.string_types")
        srcname_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        srcname_validator.valid(srcname)
        cmd = {"prefix": "osd crush rename-bucket", "srcname": srcname, "dstname": dstname, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight_all(self): # 已完成测试
        '''
        重新计算权重
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd crush reweight-all", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight(self, name, weight): # 已完成测试
        '''
        调整OSD权重（WEIGHT）
        :param name: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(name, six.string_types):
            return TypeError("变量name的类型错误, 应为six.string_types")
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        if not isinstance(weight, float):
            return TypeError("变量weight的类型错误, 应为float")
        weight_validator = ceph_argparse.CephFloat(range='0')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd crush reweight", "name": name, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_crush_reweight_subtree(self, name, weight): # 已完成测试
        '''
        调整自身以及子树权重
        :param name: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(name, six.string_types):
            return TypeError("变量name的类型错误, 应为six.string_types")
        name_validator = ceph_argparse.CephString(goodchars="A-Za-z0-9-_.")
        name_validator.valid(name)
        if not isinstance(weight, float):
            return TypeError("变量weight的类型错误, 应为float")
        weight_validator = ceph_argparse.CephFloat(range='0')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd crush reweight-subtree", "name": name, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_pause(self): # 已完成测试
        '''
        设置OSD停止读写
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd pause", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_unpause(self): # 已完成测试
        '''
        设置OSD可以读写
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd unpause", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_set(self, key): # 已完成测试
        '''
        设置OSD属性（标志位）
        :param key: string, 有效属性="full","pause","noup","nodown","noout","noin","nobackfill","norebalance","norecover","noscrub","nodeep-scrub","notieragent","nosnaptrim","pglog_hardlimit"
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(key, str):
            return TypeError("变量key的类型错误, 应为string")
        key_validator = ceph_argparse.CephChoices(strings="full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim|pglog_hardlimit")
        key_validator.valid(key)
        cmd = {"prefix": "osd set", "key": key, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_unset(self, key): # 已完成测试
        '''
        取消设置OSD属性（标志位）
        :param key: string, 有效属性="full","pause","noup","nodown","noout","noin","nobackfill","norebalance","norecover","noscrub","nodeep-scrub","notieragent","nosnaptrim"
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(key, str):
            return TypeError("变量key的类型错误, 应为string")
        key_validator = ceph_argparse.CephChoices(strings="full|pause|noup|nodown|noout|noin|nobackfill|norebalance|norecover|noscrub|nodeep-scrub|notieragent|nosnaptrim")
        key_validator.valid(key)
        cmd = {"prefix": "osd unset", "key": key, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_down(self, ids): # 未完成测试, 报错CephError
        '''
        设置OSD down
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(ids, six.string_types):
            return TypeError("变量ids的类型错误, 应为six.string_types")
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd down", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_out(self, ids): # 未完成测试, 报错CephError
        '''
        设置OSD out
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(ids, six.string_types):
            return TypeError("变量ids的类型错误, 应为six.string_types")
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd out", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_in(self, ids): # 未完成测试, 报错CephError
        '''
        设置OSD in
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(ids, six.string_types):
            return TypeError("变量ids的类型错误, 应为six.string_types")
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd in", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_rm(self, ids): # 未完成测试, 报错CephError
        '''
        设置OSD rm
        :param ids: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(ids, six.string_types):
            return TypeError("变量ids的类型错误, 应为six.string_types")
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(ids)
        cmd = {"prefix": "osd rm", "ids": ids, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight(self, id, weight): # 未完成测试, 报错CephError
        '''
        设置OSD reweight
        :param id: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(id, six.string_types):
            return TypeError("变量id的类型错误, 应为six.string_types")
        ids_validator = ceph_argparse.CephString(goodchars="")
        ids_validator.valid(id)
        if not isinstance(weight, float):
            return TypeError("变量weight的类型错误, 应为float")
        weight_validator = ceph_argparse.CephFloat(range='0|1')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd reweight", "id": id, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_primary_affinity(self, id, weight): # 未完成测试, 报错CephError
        '''
        设置OSD primary_affinity
        
        :param id: six.string_types
        :param weight: float
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(id, six.string_types):
            return TypeError("变量id的类型错误, 应为six.string_types")
        id_validator = ceph_argparse.CephOsdName()
        id_validator.valid(id)
        if not isinstance(weight, float):
            return TypeError("变量weight的类型错误, 应为float")
        weight_validator = ceph_argparse.CephFloat(range='0|1')
        weight_validator.valid(weight)
        cmd = {"prefix": "osd primary-affinity", "id": id, "weight": weight, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_pool_stats(self, name=None): # 部分完成测试, name不生效, 输出均为所有池状态
        '''
        获取存储池的实时状态
        :param name: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd pool stats", "format": "json"}
        if name is not None:
            if not isinstance(name, six.string_types):
                return TypeError("变量name的类型错误, 应为six.string_types")
            name_validator = ceph_argparse.CephString(goodchars="")
            name_validator.valid(name)
            cmd['name'] = name
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_utilization(self): # 已完成测试
        '''
        获取OSD总体利用率
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd utilization", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight_by_utilization(self, oload=None, max_change=None, max_osds=None, no_increasing=None): # 已完成测试
        '''
        根据存储利用率调整OSD reweight
        :param oload: int
        :param max_change: float
        :param max_osds: int
        :param no_increasing: string
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd reweight-by-utilization", "format": "json"}
        if oload is not None:
            if not isinstance(oload, int):
                return TypeError("变量oload的类型错误, 应为int")
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload
        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError("变量max_change的类型错误, 应为float")
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change
        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError("变量max_osds的类型错误, 应为int")
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds
        if no_increasing is not None:
            if not isinstance(no_increasing, str):
                return TypeError("变量no_increasing的类型错误, 应为string")
            no_increasing_validator = ceph_argparse.CephChoices(strings="--no-increasing")
            no_increasing_validator.valid(no_increasing)
            cmd['no_increasing'] = no_increasing
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_test_reweight_by_utilization(self, oload=None, max_change=None, max_osds=None, no_increasing=None): # 已完成测试
        '''
        根据存储利用率调整OSD reweight, 仅输出测试结果, 不实际进行调整
        :param oload: int
        :param max_change: float
        :param max_osds: int
        :param no_increasing: string
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd test-reweight-by-utilization", "format": "json"}
        if oload is not None:
            if not isinstance(oload, int):
                return TypeError("变量oload的类型错误, 应为int")
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload
        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError("变量max_change的类型错误, 应为float")
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change
        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError("变量max_osds的类型错误, 应为int")
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds
        if no_increasing is not None:
            if not isinstance(no_increasing, str):
                return TypeError("变量no_increasing的类型错误, 应为string")
            no_increasing_validator = ceph_argparse.CephChoices(strings="--no-increasing")
            no_increasing_validator.valid(no_increasing)
            cmd['no_increasing'] = no_increasing
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_reweight_by_pg(self, oload=None, max_change=None, max_osds=None, pools=None): # 部分完成测试, 运行成功, 但返回值不为0
        '''
        根据PG调整OSD reweight
        :param oload: int
        :param max_change: float
        :param max_osds: int
        :param pools: list
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd reweight-by-pg", "format": "json"}
        if oload is not None:
            if not isinstance(oload, int):
                return TypeError("变量oload的类型错误, 应为int")
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload
        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError("变量max_change的类型错误, 应为float")
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change
        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError("变量max_osds的类型错误, 应为int")
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds
        if pools is not None:
            if not isinstance(pools, list):
                return TypeError("变量pools的类型错误, 应为list")
            cmd['pools'] = pools
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_test_reweight_by_pg(self, oload=None, max_change=None, max_osds=None, pools=None): # 部分完成测试, 运行成功, 但返回值不为0
        '''
        根据PG调整OSD reweight, 仅输出测试结果, 不实际进行调整
        :param oload: int
        :param max_change: float
        :param max_osds: int
        :param pools: list
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd test-reweight-by-pg", "format": "json"}
        if oload is not None:
            if not isinstance(oload, int):
                return TypeError("变量oload的类型错误, 应为int")
            oload_validator = ceph_argparse.CephInt(range='')
            oload_validator.valid(str(oload))
            cmd['oload'] = oload
        if max_change is not None:
            if not isinstance(max_change, float):
                return TypeError("变量max_change的类型错误, 应为float")
            max_change_validator = ceph_argparse.CephFloat(range='')
            max_change_validator.valid(max_change)
            cmd['max_change'] = max_change
        if max_osds is not None:
            if not isinstance(max_osds, int):
                return TypeError("变量max_osds的类型错误, 应为int")
            max_osds_validator = ceph_argparse.CephInt(range='')
            max_osds_validator.valid(str(max_osds))
            cmd['max_osds'] = max_osds
        if pools is not None:
            if not isinstance(pools, list):
                return TypeError("变量pools的类型错误, 应为list")
            cmd['pools'] = pools
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_df(self, output_method=None): # 已完成测试
        '''
        获取OSD的信息, 如命令ceph osd df
        :param output_method: string, 有效参数="plain","tree"
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "osd df", "format": "json"}
        if output_method is not None:
            if not isinstance(output_method, str):
                return TypeError("变量output_method的类型错误, 应为string")
            output_method_validator = ceph_argparse.CephChoices(strings="plain|tree")
            output_method_validator.valid(output_method)
            cmd['output_method'] = output_method
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    # 存储池管理
    def osd_tier_add(self, pool, tierpool, force_nonempty=None): # 已完成测试
        '''
        设置Cache Tier
        :param tierpool: six.string_types
        :param pool: six.string_types
        :param force_nonempty: string, 有效参数= ["--force-nonempty"]
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        if not isinstance(tierpool, six.string_types):
            return TypeError("变量tierpool的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd tier add", "tierpool": tierpool, "pool": pool, "format": "json"}
        if force_nonempty is not None:
            if not isinstance(tierpool, str):
                return TypeError("变量tierpool的类型错误, 应为string")
            force_nonempty_validator = ceph_argparse.CephChoices(strings="--force-nonempty")
            force_nonempty_validator.valid(force_nonempty)
            cmd['force_nonempty'] = force_nonempty
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_remove(self, pool, tierpool): # 已完成测试
        '''
        移除Cache Tier的设置
        :param tierpool: six.string_types
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        if not isinstance(tierpool, six.string_types):
            return TypeError("变量tierpool的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd tier remove", "tierpool": tierpool, "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_cache_mode(self, mode, pool, sure=None): # 已完成测试
        '''
        设置Cachr Tier的模式
        :param mode: string, 有效参数 = "none","writeback","forward","readonly","readforward","proxy","readproxy"
        :param pool: six.string_types
        :param sure: string 有效参数 = "--yes-i-really-mean-it"
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(mode, str):
            return TypeError("变量mode的类型错误, 应为string")
        mode_validator = ceph_argparse.CephChoices(strings="none|writeback|forward|readonly|readforward|proxy|readproxy")
        mode_validator.valid(mode)
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd tier cache-mode", "pool": pool, "mode": mode, "format": "json"}
        if sure is not None:
            sure_validator = ceph_argparse.CephChoices(strings="--yes-i-really-mean-it")
            sure_validator.valid(sure)
            cmd['sure'] = sure
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_set_overlay(self, pool, overlaypool): # 已完成测试
        '''
        添加覆盖池
        :param overlaypool: six.string_types
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(overlaypool, six.string_types):
            return TypeError("变量overlaypool的类型错误, 应为six.string_types")
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd tier set-overlay", "overlaypool": overlaypool, "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_remove_overlay(self, pool): # 已完成测试
        '''
        移除覆盖池
        :param pool: six.string_types
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        cmd = {"prefix": "osd tier remove-overlay", "pool": pool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def osd_tier_add_cache(self, pool, tierpool, size): # 已完成测试
        '''
        添加指定大小的缓存池
        :param pool: six.string_types
        :param tierpool: six.string_types
        :param size: int
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        if not isinstance(pool, six.string_types):
            return TypeError("变量pool的类型错误, 应为six.string_types")
        if not isinstance(tierpool, six.string_types):
            return TypeError("变量tierpool的类型错误, 应为six.string_types")
        if not isinstance(size, int):
            return TypeError("变量size的类型错误, 应为int")
        size_validator = ceph_argparse.CephInt(range='0')
        size_validator.valid(str(size))
        cmd = {"prefix": "osd tier add-cache", "size": size, "pool": pool, "tierpool": tierpool, "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    # MON管理
    def version(self): # 已完成测试
        '''
        获取Ceph版本
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "version", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def node_ls(self, type=None): # 已完成测试
        '''
        获取Ceph节点信息
        :param type: string, 有效参数 = "all","osd","mon","mds","mgr"
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "node ls", "format": "json"}
        if type is not None:
            if not isinstance(type, str):
                return TypeError("变量type的类型错误, 应为string")
            type_validator = ceph_argparse.CephChoices(strings="all|osd|mon|mds|mgr")
            type_validator.valid(type)
            cmd['type'] = type
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def mon_stat(self): # 已完成测试
        '''
        获取MON节点信息
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "mon stat", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    # 权限管理
    def auth_export(self, entity=None): # 部分完成测试, entity未测试
        '''
        为组件写入密钥环, 如果未给定, 则写入主密钥环
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "auth export", "format": "json"}
        if entity is not None:
            if not isinstance(entity, str):
                return TypeError("变量entity的类型错误, 应为string")
            entity_validator = ceph_argparse.CephString(goodchars="")
            entity_validator.valid(entity)
            cmd['entity'] = entity
        result = self.run_ceph_command(cmd, inbuf='')   
        return result
    
    def auth_list(self): # 已完成测试
        '''
        列出身份验证状态
        :return: json, (int ret, string outbuf, string outs)
        :raise CephError: 执行错误时引发CephError
        :raise rados.Error: Rados引起的问题描述
        '''
        cmd = {"prefix": "auth list", "format": "json"}
        result = self.run_ceph_command(cmd, inbuf='')   
        return result 
    
#实例化Ceph对象
ceph = Ceph()  
arg1 = "mgr"
arg2 = "tier_cache_pool"
arg3 = 4294967296
arg4 = "plain"
print(ceph.auth_export())

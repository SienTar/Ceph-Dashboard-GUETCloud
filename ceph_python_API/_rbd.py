# -*- coding: UTF-8 -*-
import rados
import rbd
import ceph_argparse
import subprocess

class _RBD():
    
    def __init__(self, pool):
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
        
        self.ioctx = []
        for p in pool:
            try:
                self.ioctx.append(self.cluster.open_ioctx(p))
            except Exception as e:
                print('绑定存储池错误: {}'.format(e))
                raise e
            print('成功绑定存储池: {}'.format(p))
        
        print self.ioctx[0]
        
        try:
            self.rbd_inst = rbd.RBD()
        except Exception as e:
            print('rbd.RBD实例化错误: {}'.format(e))
            raise e
        print('成功实例化rbd.RBD')
        
    def _close(self):
        for i in self.ioctx:
            i.close()
        self.cluster.shutdown()
    
    def create(self, name, size): # 使用rbd
        '''
        创建RBD镜像
        :param ioctx (rados.Ioctx) -- 用于执行RBD镜像操作的上下文，指定了本函数执行所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :param name (str) -- 创建的RBD镜像名称
        :param size (int) -- 创建的RBD镜像容量，单位为字节
        :return: 执行成功时返回列表[0, None]
        :raise rados.Error: Rados引起的问题描述，包含ImageExists, TypeError, InvalidArgument, FunctionNotSupported
        '''
        try:
            if not isinstance(name, str):
                return TypeError('变量name的类型错误, 应为str')
                
            if not isinstance(size, int):
                return TypeError('变量size的类型错误, 应为int')
            size_validator = ceph_argparse.CephInt(range = '0')
            size_validator.valid(str(size))
            
            result = self.rbd_inst.create(self.ioctx[0], name, size)
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def clone(self, p_name, p_snapname, c_name): # 使用rbd，在该函数执行前使用_RBD(pool)初始化时，其输入的pool中的pool[0]、pool[1]分别对应p_ioctx、c_ioctx的存储池
        '''
        创建RBD镜像
        :param p_ioctx (rados.Ioctx[0]) -- 用于执行RBD镜像操作的上下文，指定了父RBD镜像所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :param p_name (str) -- 父RBD镜像名称
        :param p_snapname (int) -- 父RBD镜像快照名称
        :param c_ioctx (rados.Ioctx[1]) -- 用于执行RBD镜像操作的上下文，指定了子RBD镜像所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :param c_name (str) -- 子RBD镜像名称
        :return: 执行成功时返回列表[0, None]
        :raise rados.Error: Rados引起的问题描述，包含TypeError, InvalidArgument, ImageExists, FunctionNotSupported, ArgumentOutOfRange
        '''
        try:
            if not isinstance(p_name, str):
                return TypeError('变量p_name的类型错误, 应为str')
            
            if not isinstance(p_snapname, str):
                return TypeError('变量p_snapname的类型错误, 应为str')
            
            if not isinstance(c_name, str):
                return TypeError('变量c_name的类型错误, 应为str')
            
            result = self.rbd_inst.clone(self.ioctx[0], p_name, p_snapname, self.ioctx[1], c_name)
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def feature_disable(self, pool, image, features): # 使用subprocess
        '''
        停用RBD镜像的特性
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param features (list) -- RBD特性列表，允许多个，有效输入范围范围 = ['layering', 'striping', 'exclusive-lock', 'object-map', 'fast-diff', 'deep-flatten', 'journaling']
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'feature', 'disable']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            if not isinstance(features, list):
                return TypeError('变量features的类型错误, 应为list')
            for s in features:
                features_validator = ceph_argparse.CephChoices(strings = 'layering|striping|exclusive-lock|object-map|fast-diff|deep-flatten|journaling')
                features_validator.valid(s)
                cmd.append(s)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def feature_enable(self, pool, image, features): # 使用subprocess
        '''
        启用RBD镜像的特性
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param features (list) -- RBD特性列表，允许多个，有效输入范围 = ['layering', 'striping', 'exclusive-lock', 'object-map', 'fast-diff', 'deep-flatten', 'journaling']
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'feature', 'enable']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            if not isinstance(features, list):
                return TypeError('变量features的类型错误, 应为list')
            for s in features:
                features_validator = ceph_argparse.CephChoices(strings = 'layering|striping|exclusive-lock|object-map|fast-diff|deep-flatten|journaling')
                features_validator.valid(s)
                cmd.append(s)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def flatten(self, pool, image): # 使用subprocess，该函数的输出有进度显示，可能会处理较长时间
        '''
        挂载RBD镜像
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'flatten']
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def info(self, pool, image): # 使用subprocess
        '''
        查看RBD镜像信息
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'info']
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def list(self): # 使用rbd
        '''
        列出RBD镜像名称
        :param ioctx (rados.Ioctx) -- 用于执行RBD镜像操作的上下文，指定了本函数执行所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :return: 执行成功时返回列表[0, RBD镜像列表]
        :raise rados.Error: Rados引起的问题描述
        '''
        try:
            result = self.rbd_inst.list(self.ioctx[0])
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def list2(self): # 使用rbd
        '''
        遍历RADOS存储池中的RBD镜像
        :param ioctx (rados.Ioctx) -- 用于执行RBD镜像操作的上下文，指定了本函数执行所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :return: 执行成功时返回列表[0, ImageIterator]
        :raise rados.Error: Rados引起的问题描述
        '''
        try:
            result = self.rbd_inst.list2(self.ioctx[0])
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def map(self, pool, image): # 使用subprocess
        '''
        挂载RBD镜像
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'map']
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def remove(self, name, on_progress = None): # 使用rbd
        '''
        删除RBD镜像
        :param ioctx (rados.Ioctx) -- 用于执行RBD镜像操作的上下文，指定了本函数执行所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :param name (str) -- 删除的RBD镜像名称
        :param on_progress (回调函数) -- 可选的进度回调函数
        :return: 执行成功时返回列表[0, None]
        :raise rados.Error: Rados引起的问题描述，包含ImageNotFound, ImageBusy, ImageHasSnapshots
        '''
        try:
            if not isinstance(name, str):
                return TypeError('变量name的类型错误, 应为str')
            
            if on_progress is not None:
                pass # 暂时没搞清楚怎么调用回调函数
            
            result = self.rbd_inst.remove(self.ioctx[0], name, on_progress)
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def rename(self, src, dest): # 使用rbd
        '''
        修改RBD镜像名称
        :param ioctx (rados.Ioctx) -- 用于执行RBD镜像操作的上下文，指定了本函数执行所在的RADOS存储池，该参数已经在_RBD类初始化时创建，并已本函数中调用，无相关报错时无需手动干预
        :param src (str) -- RBD镜像当前名称
        :param dest (str) -- RBD镜像新名称
        :return: 执行成功时返回列表[0, None]
        :raise rados.Error: Rados引起的问题描述，包含ImageNotFound, ImageExists
        '''
        try:
            if not isinstance(src, str):
                return TypeError('变量src的类型错误, 应为str')
            
            if not isinstance(dest, str):
                return TypeError('变量dest的类型错误, 应为str')
            
            result = self.rbd_inst.rename(self.ioctx[0], src, dest)
            return [0, result]
        except rados.Error as e:
            raise e
        finally:
            self._close()
    
    def resize(self, pool, image, size, unit='B', allow_shrink = None): # 使用subprocess，该函数的输出有进度显示，可能会处理较长时间
        '''
        调整RBD镜像容量
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param size (int) -- 调整后的RBD镜像容量（注意，不是变化量，是目标量)
        :param size (str) -- 容量单位，只接受大写，有效输入范围 = 'B', 'K', 'M', 'G', 'T', 'P', 'E'
        :param allow_shrink (str) -- 允许缩容，有效输入范围 = '--allow-shrink'
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'resize']
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            if not isinstance(size, int):
                return TypeError('变量size的类型错误, 应为int')
            size_validator = ceph_argparse.CephInt(range = '0')
            size_validator.valid(str(size))
            if not isinstance(unit, str):
                return TypeError('变量unit的类型错误, 应为str')
            unit_validator = ceph_argparse.CephChoices(strings = 'B|K|M|G|T|P|E')
            unit_validator.valid(unit)
            cmd.append('--size')
            cmd.append(str(size) + unit)
            
            if allow_shrink is not None:
                allow_shrink_validator = ceph_argparse.CephChoices(strings = '--allow-shrink')
                allow_shrink_validator.valid(allow_shrink)
                cmd.append(allow_shrink)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def showmapped(self): # 使用subprocess
        '''
        查看RBD镜像挂载状态
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'showmapped']
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_create(self, pool, image, snap): # 使用subprocess
        '''
        创建RBD镜像快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param snap (str) -- 快照名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'create']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            if not isinstance(snap, str):
                return TypeError('变量snap的类型错误, 应为str')
            cmd.append(pool+'/'+image+'@'+snap)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_ls(self, pool, image): # 使用subprocess
        '''
        列出RBD镜像快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'ls']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_protect(self, pool, image, snap): # 使用subprocess
        '''
        删除RBD镜像快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param snap (str) -- 快照名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'protect']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            if not isinstance(snap, str):
                return TypeError('变量snap的类型错误, 应为str')
            cmd.append(pool+'/'+image+'@'+snap)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_purge(self, pool, image): # 使用subprocess，该函数的输出有进度显示，可能会处理较长时间
        '''
        删除RBD镜像所有快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'purge']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_rm(self, pool, image, snap): # 使用subprocess，该函数的输出有进度显示，可能会处理较长时间
        '''
        删除RBD镜像快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param snap (str) -- 快照名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'rm']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            if not isinstance(snap, str):
                return TypeError('变量snap的类型错误, 应为str')
            cmd.append(pool+'/'+image+'@'+snap)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_rollback(self, pool, image, snap): # 使用subprocess，该函数的输出有进度显示，可能会处理较长时间
        '''
        回滚RBD镜像到指定快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param snap (str) -- 快照名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'rollback']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            if not isinstance(snap, str):
                return TypeError('变量snap的类型错误, 应为str')
            cmd.append(pool+'/'+image+'@'+snap)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def snap_unprotect(self, pool, image, snap): # 使用subprocess
        '''
        删除RBD镜像快照
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :param snap (str) -- 快照名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'snap', 'unprotect']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            if not isinstance(snap, str):
                return TypeError('变量snap的类型错误, 应为str')
            cmd.append(pool+'/'+image+'@'+snap)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def status(self, pool, image): # 使用subprocess
        '''
        查看RBD镜像状态
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'status']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()
    
    def unmap(self, pool, image): # 使用subprocess
        '''
        卸载RBD镜像
        :param pool (str) -- RADOS存储池名称
        :param image (str) -- RBD镜像名称
        :return: 执行成功时返回列表[返回值, 输出文本]，返回值为0代表执行成功且无报错，返回值非0代表执行成功但有报错
        :raise Exception: 问题描述
        '''
        try:
            cmd = ['rbd', 'unmap']
            
            if not isinstance(pool, str):
                return TypeError('变量pool的类型错误, 应为str')
            if not isinstance(image, str):
                return TypeError('变量image的类型错误, 应为str')
            cmd.append(pool+'/'+image)
            
            result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            return [result.wait(), result.communicate()[0]]
        except Exception as e:
            raise e
        finally:
            self._close()

# 实例化RBD对象
if __name__ == '__main__':
    
    pool = ['testpool', 'testpool2'] # 集群内已经存在的存储池名称
    _rbd = _RBD(pool)
    
    arg1 = 'testpool'
    arg2 = 'testrbd2'
    arg3 = 'snapshot1'
    arg4 = 'M'
    arg5 = '--allow-shrink'
    result = _rbd.snap_unprotect(arg1, arg2, arg3)
    print(result)
    print(type(result))
    
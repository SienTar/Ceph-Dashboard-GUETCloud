# Ceph Python API
## 测试说明
### 测试准备
将`ceph_python_API`目录放入一个Ceph 14.2.22集群的任意一个MON节点, 例如放置在`/root`下
### 测试`_ceph.py`
1. 修改`_ceph.py`主函数的测试用例和参数
1. 执行`_ceph.py`
```
# 进入测试目录
[root@localhost ~]# cd /root/ceph_python_API

# 执行脚本
[root@localhost ceph_python_API]# python _ceph.py
```
### 测试`_rbd.py`
- 测试方法同`_ceph.py`
### 测试`_ceph_volume.py`
- 测试方法同`_ceph.py`
## 其他事项
1. 使用`subprocess`实现的函数已经在函数定义行注释, 搜索关键词 "**使用subprocess**"
1. 异步操作的函数已在函数定义行注释, 搜索关键词 "**异步操作**"
1. 仅用于给后台提交异步操作的函数已在函数定义行注释, 搜索关键词 "**提交操作**"
1. `Features_and_APIs.xlsx`为功能列表与API对照表
1. `ceph_argparse.py`从Ceph 14.2.22源码`/src/pybind`中提取, 当前为官方原版, 未进行修改
1. `_ceph.py_unfinished.py`仅用于记录`_ceph.py`的未完成测试项, 不可执行, 也不可在其他代码中*import*, 后续待`_ceph.py`测试完成, 可能会删除该文件
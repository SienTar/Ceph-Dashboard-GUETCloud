# Ceph Python API
## 测试准备
将`ceph_python_API`目录放入一个Ceph 14.2.22集群的任意一个MON节点，例如放置在`/root`下
## 测试ceph.py
1. 修改`ceph.py`主函数的测试用例和参数
2. 执行`ceph.py`
```
# 进入测试目录
[root@localhost ~]# cd /root/ceph_python_API

# 执行脚本
[root@localhost ceph_python_API]# python ceph.py
```
## 测试_rbd.py
1. 修改`_rbd.py`主函数的存储池名、测试用例和参数
2. 执行`_rbd.py`
```
# 进入测试目录
[root@localhost ~]# cd /root/ceph_python_API

# 执行脚本
[root@localhost ceph_python_API]# python _rbd.py
```
## 其他事项
1. `ceph_argparse.py`从Ceph 14.2.22源码`/src/pybind`中提取，当前为官方原版，未进行修改
2. `ceph.py_unfinished.py`仅用于记录`ceph.py`的未完成测试项，不可执行，也不可在其他代码中*import*，后续待`ceph.py`测试完成，可能会删除该文件
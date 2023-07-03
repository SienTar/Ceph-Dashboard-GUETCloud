# Ceph Python API
1. 将`ceph_python_API`目录放入一个Ceph 14.2.22集群的任意一个MON节点，例如放置在`/root`下
2. 修改`ceph.py`结尾的测试用例和参数
3. 执行`ceph.py`
```
[root@localhost ~]# cd /root/ceph_python_API
[root@localhost ceph_python_API]# python ceph.py
```
- 注：`ceph.py_untested.py`仅用于记录`ceph.py`的未完成测试项，不可执行以及在其他代码中*import*，后续待`ceph.py`测试完成，可能会删除该文件
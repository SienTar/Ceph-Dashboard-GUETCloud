def crash_info(self, id): # 部分完成测试, 因暂时没有可用的id, 目前为止无法测出返回值为0的结果
def crash_archive(self, id): # 部分完成测试, 因暂时没有可用的id, 目前为止无法测出返回值为0的结果
def pg_ls_by_primary(self, osd, pool=None, states=None): # 部分完成测试, osd不起作用, 输出均为所有OSD的池
def pg_ls_by_osd(self, osd, pool=None, states=None):  # 部分完成测试, osd不起作用, 输出均为所有OSD的池
def osd_map(self, pool, object, nspace=None): # 部分完成测试, nspace未测试
def osd_lspools(self, auid=None): # 部分完成测试, auid未测试
def osd_pool_stats(self, name=None): # 部分完成测试, name不生效, 输出均为所有池状态
def osd_reweight_by_pg(self, oload=None, max_change=None, max_osds=None, pools=None): # 部分完成测试, 运行成功, 但返回值不为0
def osd_test_reweight_by_pg(self, oload=None, max_change=None, max_osds=None, pools=None): # 部分完成测试, 运行成功, 但返回值不为0
def auth_export(self, entity=None): # 部分完成测试, entity未测试

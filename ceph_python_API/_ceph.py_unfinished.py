def crash_info(self, id): # 部分完成测试, 因暂时没有可用的崩溃信息ID, 目前为止无法测出返回值为0的结果
def crash_archive(self, id): # 部分完成测试, 因暂时没有可用的崩溃信息ID, 目前为止无法测出返回值为0的结果
def osd_crush_remove(self, name, ancestor = None): # 部分完成测试, ancestor参数未测试
def osd_crush_rm(self, name, ancestor = None): # 部分完成测试, ancestor参数未测试
def osd_test_reweight_by_pg(self, oload = None, max_change = None, max_osds = None, pools = None): # 部分完成测试, 运行成功, 但返回值不为0
def osd_map(self, pool, object, nspace = None): # 部分完成测试, nspace未测试
def osd_purge(self, id, force = False, yes_i_really_mean_it = False): # 未完成测试, Ceph无法识别id参数, 整型、字符串、整型列表和字符串列表均无法识别
def pg_dump_json(self, dumpcontents = None): # 部分完成测试, dumpcontents参数不起作用, 与官方封装好的Linux命令表现一致, 实际执行时都是['all']
def pg_ls_by_osd(self, osd, pool = None, states = None): # 部分完成测试, osd参数不起作用, 输出均为所有OSD的池
def pg_ls_by_primary(self, osd, pool = None, states = None): # 部分完成测试, osd参数不起作用, 输出均为所有OSD的池
def tell(self, target, args): # 未完成测试, args参数无法被识别
import os
import argparse
from Can_dir import Traversal_Curr_Dir,Creat_cfgIf_file, Parse_file,Creat_cfgExt_file, Creat_cfg_c_file, Get_classify_all_files
from Can_dir import Get_cannum, Get_cannum_canname, check
if check("PyQt5"):
    from can_view import *

opt = None
opt_parser = None

def parser_options():
    global opt
    global opt_parser
    opt_parser = argparse.ArgumentParser()

    opt_parser.add_argument('-t', action='store', dest='task_Period',
                                 default ='5', help='t=5 --> Task Period = 5 (ms) [default Task Period = 5 (ms)]')

    opt_parser.add_argument('-v', action='store', dest='qt_view',
                                 default ='disable', help='v=enable --> This will open qt interface')

    opt = opt_parser.parse_args()
    return True


if __name__ == '__main__':
    # get arg
    parser_options()
    # 解析文件
    Parse_file()
    # 生成 canIl_CfgInt.h
    Traversal_Curr_Dir()
    #生成 CanIl_CfgIf.h
    Creat_cfgIf_file()
    # 生成CanIl_CfgExt.h
    Creat_cfgExt_file()
    # 生成CanIl_Cfg.c
    Creat_cfg_c_file(opt.task_Period)
    print("[Info] All done!\n")
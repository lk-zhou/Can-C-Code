"""
***************************************************************************
* @file  dir.py
* @brief 此文件用于遍历文件夹及创建文件夹
***************************************************************************
* @author            gdpu.zhou@outlook.com
* @version           1.0.0
* @date              2023.3.14
* @copyright         (C) Copyright
*
*                    Contents and presentations are protected world-wide.
*                    Any kind of using, copying etc. is prohibited without prior permission.
*                    All rights - incl. industrial property rights - are reserved.
*
***************************************************************************
"""

import os
import re
from file_op import *
from dbc import *
from wirte_message import *
from datetime import datetime
import numpy as np

# 所有dbc file name
Allfile = []
# 所有节点
nodes = []
# 所有can
can_names = []
# 节点名字所代表的index
node_name_index = 0
# 节点名字所代表的index
can_name_index = 1
dbc_index = 1
min_rx_msg_id = 0
max_rx_msg_id = 1
can_nums = []
cannum_canname = {}
cannum_nodes = {}
classify_all_files = []
message_singals_key_value = {}
classify_all_files_rx_min_max = []

find_tx = []
num_can = {}
order_can = []
SIGNAL_PATTERN = re.compile(r"""\${0,2}SG_\${1,2}(?P<signal_name>.*?)\${1}(?P<gourps_name>\w?)(?P<group_id>\d{0,10})\${0,1}:\${1,2}(?P<start_bit>[0-9]{1,2})\|(?P<len>[0-9]{1,2})@(?P<singal_type>[0-1])(?P<type>[+-])\${1,2}\((?P<factor>.*),(?P<offset>.*)\)\${1,2}\[(?P<max>.*)\|(?P<min>.*)\]\${1,2}"(?P<uint>.*)"\${1,2}(?P<node>.*)""")
MESSAGE_PATTERN = re.compile(r"""BO_(?P<message_id>[0-9]{1,20})(?P<message_name>.*):(?P<message_len>[0-9]{1})(?P<transmitter>.*)""")
PERIOD_PATTERN = re.compile(r"""BA_\${0,1}\"GenMsgCycleTime\"\${0,1}BO_\${0,3}(?P<message_id>[0-9]{1,20})\${0,2}(?P<period>\d{0,100000});.*""")
BO_SIMBOL = 'BO_'
SG_SIMBOL = 'SG_'
BA_SIMBOL = 'BA_'
BU_SIMBOL = 'BU_'
CM_SIMBOL = 'CM_ '
RX_TYPE = "Rx"  # only rx
TX_TYPE = "Tx"  # only tx
BOTH_TYPE = "Both"  # tx and rx
CAN_NAME = "can"
CAN_PERIOD = "GenMsgCycleTime"
CAN_PERIOD_NOT_USE = "GenMsgCycleTimeFast"
INT_SIMBOL = "INT"
DBC = '.dbc'
TARGET_DIR = "cfg"
TARGET_FILE = ["CanIl_CfgInt.h","CanIl_CfgIf.h","CanIl_CfgExt.h","CanIl_Cfg.c"]

BA_SPECIAL_SIG_LIST = []

path = os.getcwd()

"""
    判断当前文件路径是否有指定文件或文件夹
    @param name: 需要检测的文件或文件夹名
    @param path: 需要检测的文件或文件夹所在的路径,当path=None时默认使用当前路径检测
    @return: True/False 当检测的文件或文件夹所在的路径下有目标文件或文件夹时返回Ture,
            当检测的文件或文件夹所在的路径下没有有目标文件或文件夹时返回False
"""
def isexist(name:str, path=None) -> bool:
   
    if path is None:
        path = os.getcwd()
    if os.path.exists(path + '/' + name):
        print("[Info] Under the path: "+path+name+" is exist")
        return True
    else:
        if (os.path.exists(path)):
            print("[Warning] Under the path: "+path+name+" is not exist")
        else:
            print("[Warning] This path could not be found: " + path + '\n')
        return False

"""
   创建文件夹
"""
def mkdir(target:str):
	os.makedirs(target)            #makedirs 创建文件时如果路径不存在会创建这个路径
	print("[Info] ---  new folder...  ---")
	print("[Info] ---  OK  ---")


# 在需要分组的消息列表中找到最大、最小Rx，以及 判断是否有需要 Tx的消息
# 双指针查找。因为此时order_files_list列表为有序.(从小到大)
def find_max_and_min_name_in_list(order_files_list:list,need_group_flag=False) -> list:
    i = 0
    j = len(order_files_list) - 1
    min_name = ""
    max_name = ""
    flag2 = False
    while i <= j:
        # No found on this loop
        if ((order_files_list[i].tx_rx == order_files_list[j].tx_rx == "") or \
            (order_files_list[i].tx_rx == order_files_list[j].tx_rx == TX_TYPE)):
            if (order_files_list[i].tx_rx == order_files_list[j].tx_rx == TX_TYPE):
                flag2 = True
            i += 1
            j -= 1
            continue

        # found the min and max rx message
        elif ((order_files_list[i].tx_rx == RX_TYPE and order_files_list[j].tx_rx == BOTH_TYPE) or \
              (order_files_list[i].tx_rx == BOTH_TYPE and order_files_list[j].tx_rx == RX_TYPE) or \
                (order_files_list[i].tx_rx == BOTH_TYPE == order_files_list[j].tx_rx == BOTH_TYPE) or \
                (order_files_list[i].tx_rx == order_files_list[j].tx_rx == RX_TYPE)):
            if need_group_flag == True:
                if min_name == "":
                    min_name = order_files_list[i].name+"_Group"+str(order_files_list[i].groups_id[0])
                if max_name == "":
                    lens = len(order_files_list[j].groups_id) - 1
                    max_name = order_files_list[j].name+"_Group"+str(order_files_list[j].groups_id[lens])
            else:
                if min_name == "":
                    min_name = order_files_list[i].name
                if max_name == "":
                    max_name = order_files_list[j].name
            if (order_files_list[i].tx_rx == BOTH_TYPE or order_files_list[j].tx_rx == BOTH_TYPE):
                flag2 = True
            break

        # found the max rx and this file may have tx message
        elif ((order_files_list[i].tx_rx == TX_TYPE or order_files_list[i].tx_rx == "") and
                (order_files_list[j].tx_rx == BOTH_TYPE or \
                    order_files_list[j].tx_rx == RX_TYPE)):
            if need_group_flag == True:
                if max_name == "":
                    lens = len(order_files_list[j].groups_id) - 1
                    max_name = order_files_list[j].name+"_Group"+str(order_files_list[j].groups_id[lens])
            else:
                if max_name == "":
                    max_name = order_files_list[j].name
            if (order_files_list[i].tx_rx == TX_TYPE):
                flag2 = True
            i += 1
            continue

        # found the min rx and this file may have tx message
        elif ((order_files_list[i].tx_rx == RX_TYPE or order_files_list[i].tx_rx == BOTH_TYPE) and \
                (order_files_list[j].tx_rx == TX_TYPE or order_files_list[j].tx_rx == "")):
            if need_group_flag == True:
                if min_name == "":
                    min_name = order_files_list[i].name+"_Group"+str(order_files_list[i].groups_id[0])
            else:
                min_name = order_files_list[i].name
            if (order_files_list[j].tx_rx == TX_TYPE):
                flag2 = True
            j -= 1
            continue

        else:
            print("[Error] Unkonw type name :%s type %s\t name: %s type %s" % \
                  (order_files_list[i].name, order_files_list[i].tx_rx, order_files_list[j].name, order_files_list[j].tx_rx))

    return [max_name,min_name,flag2]

group_singal_list = []
group_singal_id_list = []
inconclusive_singal_list = []
g_group = []
g_groups = []
"""
    此函数用于解析文件
"""
def Parse_file():

    special_sig_file = file_op(path+"/special_signal.txt")
    ret = special_sig_file.open()
    if (ret > 0):
        while True:
            special = special_sig_file.readline()
            if (None != special):
                BA_SPECIAL_SIG_LIST.append(str(special.rstrip('\n')))
                continue
            else:
                break
    temp_dict = {}
    temp_dict2 = {}
    temp_dict3 = {}
    global g_groups
    i = 0
    # 获取所有的dbc文件
    for root, dirs, files in os.walk(path+"/dbc"):
        for single_file in files:
            if os.path.splitext(single_file)[dbc_index] == DBC:
                Allfile.append(single_file)

    # 获取文件名中的节点以及can名
    for single_file in Allfile:
        nodes.append(single_file.split('_')[node_name_index])
        can_names.append(single_file.split('_')[can_name_index])

    # 将can的id 与 文件进行初步映射
    for i in range(len(can_names)):
        if can_names[i][len(CAN_NAME)].isdigit():
            can_nums.append(can_names[i][len(CAN_NAME)])
            temp_dict[can_nums[i]] = Allfile[i]
            temp_dict2[can_nums[i]] = nodes[i]
            temp_dict3[can_nums[i]] = can_names[i]


    # 从小到大进行排序
    can_nums.sort()

    # 将can id 与 文件进行顺序映射
    for i in range(len(temp_dict)):
        cannum_canname[can_nums[i]] = temp_dict[can_nums[i]]
        cannum_nodes[can_nums[i]] = temp_dict2[can_nums[i]]
        num_can[can_nums[i]] = temp_dict3[can_nums[i]]
    print(can_nums)
    print(cannum_canname)
    aaaaa = 0
    # 遍历读取文件并解析dbc文件中的msg
    count = 0
    for i in can_nums:
        classify_singel_file = []
        singal_file_rx_min_max = []
        message_id_list = []
        group_message_id_list = []
        group_message_id_message = {}
        group_classify_singel_file = []
        message_id_message = {}
        count += 1
        single_open_file = file_op(path+'/dbc/'+cannum_canname[i])
        ret = single_open_file.open()
        if ret < 0:
            print("[Error] can not open %s" % cannum_canname[i])
        while True:
            line = single_open_file.readline()
            if line is None:
                break

            # 找到了单个消息
            if BO_SIMBOL in line and BA_SIMBOL not in line and BU_SIMBOL not in line and CM_SIMBOL not in line:
                group_singal_list.clear()
                group_singal_id_list.clear()
                inconclusive_singal_list.clear()
                g_group.clear()
                g_groups.clear()
                need_pop = False
                aaaaa += 1
                result = MESSAGE_PATTERN.match(line.replace(" ",""))
                # print(result)
                if result == None:
                    print("This format no match:"+line.replace(" ",""))
                message_id = result.group('message_id')
                message_name = result.group('message_name')
                message_len = result.group('message_len')
                transmitter = result.group('transmitter')
                # print(message_id)
                # print(message_len)
                # print(transmitter)
                # print(cannum_nodes[i])
                # print("-------------------------------------")
                singal_message = Message(int(message_id), int(message_len), str(message_name), str(transmitter),cannum_nodes[i])
                # print(singal_message)
                message_id_list.append(int(singal_message.id))
                # 继续往下读取,读取信号：
                # print("------------aaaaa----------")
                while True:
                    line = single_open_file.readline()
                    # 如果当前行不为空 并且 当前行不是空行：
                    if line is not None and line not in ["\n","\r\n"]:
                        # 如果当前行是信号所在行：
                        if SG_SIMBOL in line and (BA_SIMBOL not in line or (BA_SIMBOL in line and any(sig in line for sig in BA_SPECIAL_SIG_LIST)))\
                            and (CM_SIMBOL not in line):
                            # print(line.replace(" ","$"))
                            result_2 = SIGNAL_PATTERN.match(line.replace(" ","$"))
                            if result_2 is not None:
                                # print("正则匹配成功.\n")
                                singal_name = result_2.group('signal_name')         # 信号名
                                singal_start_bit = result_2.group('start_bit')      # 起始位
                                singal_len = result_2.group('len')                  # 数据长度
                                singal_type = result_2.group('singal_type')         # Intel/motorola
                                singal_byte_type = result_2.group('type')           # 无符号还是有符号
                                singal_uint = result_2.group('uint')                # 单位
                                singal_node = result_2.group('node')                # 接收节点
                                singal_group_id = result_2.group('group_id')        # 分组id
                                singal_group_name = result_2.group('gourps_name')   # 分组名

                                # print(singal_name)
                                # 如果有这消息的这个信号的接收节点是当前dbc文件所定义的节点，那么该报文为接收报文
                                if singal_message.tx_rx == "" and cannum_nodes[i] in singal_node:
                                    singal_message.tx_rx = "Rx"
                                if singal_message.tx_rx == "Tx" and cannum_nodes[i] in singal_node:
                                    singal_message.tx_rx = "Both"

                                single_singal = Signal(singal_name,singal_start_bit,singal_len,singal_type,singal_uint,singal_node,singal_byte_type,singal_group_id)
                                # 读到需要分组的信号但不是需要分组信号的共有信号
                                if singal_group_id != "" and singal_group_name != "":
                                    if singal_message.need_group == False:
                                        singal_message.need_group = True
                                    if len(message_id_list) > 0:
                                        if need_pop == False:
                                            message_id_list.pop()
                                            need_pop = True

                                    # 读取到当前需要分组的消息的新的需要分组的信号
                                    if int(singal_group_id) not in group_singal_id_list and len(group_singal_list) > 0:
                                        # print("read new group singal : %s group_id = %d\n" % (singal_name, int(singal_group_id)))
                                        s = []
                                        s += group_singal_list
                                        group_message_id_list.append(singal_message.id)
                                        singal_message.groups.append(copy.deepcopy(s))
                                        group_singal_id_list.append(int(singal_group_id))
                                        group_singal_list.clear()
                                        group_singal_list.append(single_singal)
                                        # 继续读下一行
                                        continue

                                    # 读取到需要分组的消息的第一个信号
                                    if len(group_singal_id_list) == 0:
                                        # print("read frist one singal : %s group_id = %d\n" % (singal_name, int(singal_group_id)))
                                        group_singal_id_list.append(int(singal_group_id))
                                        group_singal_list.append(single_singal)
                                        #继续读下一行
                                        continue
                                    # 如果当前的信号的信号id 在信号id列表中，那么直接将当前信号加入到信号列表
                                    if int(singal_group_id) in group_singal_id_list:
                                        # print("read same group id singal = %s, group_id = %s\n" % (singal_name, singal_group_id))
                                        group_singal_list.append(single_singal)
                                        # 继续读下一行
                                        continue

                                # 模棱两可的信号
                                else:
                                    if singal_group_name == "M":
                                        singal_message.M_groups.append(single_singal)
                                    # print(single_singal.name)
                                    inconclusive_singal_list.append(single_singal)
                                    # 继续读下一行
                                    continue

                            else:
                                print(line.replace(" ","$"))
                                print("[Error] 正则匹配失败,请检查正则表达式是否正确.\n")
                    else:
                        if singal_message.need_group == True:
                            s = []
                            s = singal_message.both_need + inconclusive_singal_list
                            singal_message.both_need = s

                            s = []
                            s = group_message_id_list
                            singal_message.groups_id = s
            
                        else:
                            s = []
                            s = singal_message.signals + inconclusive_singal_list
                            singal_message.signals = s
                        break

                if singal_message.need_group == False:
                    # 根据单个消息中的信号进行排序(起始位置排序)
                    singal_message.sort()
                    if (0 != len(singal_message.signals) and (singal_message.name != "" and singal_message.name != "Vector__XXX" and singal_message.tx_rx != "")):
                        message_id_message[int(singal_message.id)] = singal_message
                        # 此时单个消息中的所有信号均为有序
                        classify_singel_file.append(singal_message)
                    else:
                        message_id_list.remove(int(singal_message.id))
                else:
                    #print(group_singal_id_list)
                    s = []
                    s += group_singal_id_list
                    singal_message.groups_id = s
                    # 将共有信号，加入到每个信号分组中
                    singal_message.groups.append(group_singal_list)
                    j = 0
                    while j < len(singal_message.groups):
                        s = []
                        s = singal_message.groups[j] + singal_message.both_need
                        singal_message.groups[j] = s
                        j += 1

                    # 将需要分类的信号id and 需要分组的信号的信号列表 翻转
                    if ((0 != len(singal_message.groups)) and (singal_message.name != "" and singal_message.name != "Vector__XXX") and singal_message.tx_rx != ""):
                        group_message_id_message[int(singal_message.id)] = singal_message
                        group_classify_singel_file.append(singal_message)
                    else:
                        group_singal_id_list.remove(int(singal_message.id))

            # 判断该报文是否是周期报文，并且获取其周期
            if BA_SIMBOL in line and BO_SIMBOL in line and CAN_PERIOD in line and INT_SIMBOL not in line and CAN_PERIOD_NOT_USE \
                not in line:
                result = PERIOD_PATTERN.match(line.replace(" ","$"))
                if result == None:
                    print("Unkown singal"+line.replace(" ","$"))
                msg_id = result.group('message_id')
                period = result.group('period')
                for msg in group_classify_singel_file:
                    if msg.id == int(msg_id):
                        msg.is_period = True
                        msg.period = int(period)
                for msg in classify_singel_file:
                    if msg.id == int(msg_id):
                        msg.is_period = True
                        msg.period = int(period)

        # 针对不需要分组的消息进行排序
        message_id_list.sort()      
        j = 0
        while j < len(message_id_message):
            classify_singel_file[j] = message_id_message[message_id_list[j]]
            j += 1

        # 针对需要分组的消息进行排序
        group_message_id_list.sort()
        j = 0
        while j < len(group_message_id_message):
            group_classify_singel_file[j] = group_message_id_message[group_message_id_list[j]]
            j += 1

        group_min_and_max_name_list = []
        min_and_max_name_list = []

        # 此dbc文件全都需要分组
        if len(classify_singel_file) == 0:
            group_min_and_max_name_list =  find_max_and_min_name_in_list(group_classify_singel_file,True)
            find_tx.append(group_min_and_max_name_list[2])
            singal_file_rx_min_max.append(group_min_and_max_name_list[1])
            singal_file_rx_min_max.append(group_min_and_max_name_list[0])
            classify_all_files_rx_min_max.append(singal_file_rx_min_max)
            classify_all_files.append(group_classify_singel_file)
            print(1)

        # 此dbc文件全都不需要分组
        elif len(group_classify_singel_file) == 0:
            min_and_max_name_list = find_max_and_min_name_in_list(classify_singel_file,False)
            find_tx.append(min_and_max_name_list[2])
            singal_file_rx_min_max.append(min_and_max_name_list[1])
            singal_file_rx_min_max.append(min_and_max_name_list[0])
            classify_all_files_rx_min_max.append(singal_file_rx_min_max)
            classify_all_files.append(classify_singel_file)

        # 此dbc文件存在需要分组的消息
        else:
            group_min_and_max_name_list = find_max_and_min_name_in_list(group_classify_singel_file,True)
            min_and_max_name_list = find_max_and_min_name_in_list(classify_singel_file,False)

            if group_min_and_max_name_list[2] == min_and_max_name_list[2]:
                find_tx.append(group_min_and_max_name_list[2])
            else:
                if group_min_and_max_name_list[2] == True:
                    find_tx.append(group_min_and_max_name_list[2])
                else:
                    find_tx.append(min_and_max_name_list[2])
            singal_file_rx_min_max.append(min_and_max_name_list[1])
            if group_min_and_max_name_list[1] != "":
                singal_file_rx_min_max.append(group_min_and_max_name_list[1])
            else:
                singal_file_rx_min_max.append(min_and_max_name_list[0])
            classify_all_files_rx_min_max.append(singal_file_rx_min_max)
            classify_all_files.append(classify_singel_file+group_classify_singel_file)


    # i = 0
    # while i < len(classify_all_files):
    #     j = 0
    #     print("--------------------------")
    #     while j < len(classify_all_files[i]):
    #         if classify_all_files[i][j].need_group == True:
    #             print(classify_all_files[i][j].name)
    #             for ar_list in classify_all_files[i][j].groups:
    #                 print("bbbbbbbbbbbbbbbbbbbbbbbbbbbb_1")
    #                 for ar in ar_list:
    #                     print(ar.name)
    #                     print(ar.group_id)
    #                 print("bbbbbbbbbbbbbbbbbbbbbbbbbbbb_2")
    #         j += 1
    #     i += 1

    # <<<<< DO NOT REMOVE !!!!! >>>>>
    # print(cannum_canname)
    # print(Allfile)
    # print(can_nums)
    # print(can_names)
    # print(cannum_nodes)
    # print(num_can)
    # print(nodes)
    # print(classify_all_files_rx_min_max)
    # print(find_tx)
    for nums in can_nums:
        order_can.append(num_can[nums])


    # 生成文件
def Traversal_Curr_Dir():
    # 判断目标文件夹是否存在
    if isexist(TARGET_DIR) == False:
        mkdir(path+"/"+TARGET_DIR)

    # 尝试打开目标文件
    target = file_op(path+"/"+TARGET_DIR+"/"+TARGET_FILE[0], True)
    ret = target.open()
    if ret == False:
        print("[Warning] NO such file:"+TARGET_FILE[0])
        print("[Info] Creat file:"+TARGET_FILE[0])
        os.mknod(path+"/"+TARGET_DIR+"/"+TARGET_FILE[0])
    ret = target.open()
    if ret == True:
        # print(num_can)
        write_message(target,can_nums,classify_all_files_rx_min_max,min_rx_msg_id,max_rx_msg_id,TARGET_FILE[0],num_can) 


"""
    通过Traversal_Curr_Dir()函数解析结果,生成 CanIl_CfgIf.h 到 cfg/
"""
def Creat_cfgIf_file():
    if isexist(TARGET_DIR) == False:
        mkdir(path+"/"+TARGET_DIR)

    # 尝试打开目标文件
    target = file_op(path+"/"+TARGET_DIR+"/"+TARGET_FILE[1], True)
    ret = target.open()
    if ret == False:
        print("[Warning] No such file:"+TARGET_FILE[1])
        print("[Info] Creat file:"+TARGET_FILE[1])
        os.mknod(path+"/"+TARGET_DIR+"/"+TARGET_FILE[1])
    ret = target.open()
    if ret == True:
        # print(find_tx)
        creat_cancfg(target,TARGET_FILE[1],can_nums,find_tx,num_can)

"""
    生成CanIl_CfgExt.h
"""
def Creat_cfgExt_file():
    if isexist(TARGET_DIR) == False:
        mkdir(path+"/"+TARGET_DIR)

    # 尝试打开目标文件
    target = file_op(path+"/"+TARGET_DIR+"/"+TARGET_FILE[2], True)
    ret = target.open()
    if ret == False:
        print("[Warning] No such file:"+TARGET_FILE[2])
        print("[Info] Creat file:"+TARGET_FILE[2])
        os.mknod(path+"/"+TARGET_DIR+"/"+TARGET_FILE[2])
    ret = target.open()
    if ret == True:
        Write_cfgext_message(target,TARGET_FILE[2], classify_all_files, can_nums, num_can, order_can)

"""
    生成CanIl_Cfg.c文件
"""
def Creat_cfg_c_file(task_Period):
    if isexist(TARGET_DIR) == False:
        mkdir(path+"/"+TARGET_DIR)

    # 尝试打开目标文件
    target = file_op(path+"/"+TARGET_DIR+"/"+TARGET_FILE[3], True)
    ret = target.open()
    if ret == False:
        print("[Warning] No such file:"+TARGET_FILE[3])
        print("[Info] Creat file:"+TARGET_FILE[3])
        os.mknod(path+"/"+TARGET_DIR+"/"+TARGET_FILE[3])
    ret = target.open()
    if ret == True:
        Write_cfg_c_message(target,TARGET_FILE, classify_all_files, can_nums, num_can, order_can, task_Period)

def Get_classify_all_files():
    return classify_all_files

def Get_cannum_canname():
    return cannum_canname

def Get_cannum():
    return can_nums
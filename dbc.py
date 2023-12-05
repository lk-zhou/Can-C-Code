"""
***************************************************************************
* @file  dir.py
* @brief 此文件用于定义 信号、消息
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
import numpy as np
import copy
LINE_NUM = 8
Txmsg_count = 0
Rxmsg_count = 0
Txmsg_data_count = 0
Rxmsg_data_count = 0
# 这里定义每一行的起始位
round_up = [7,15,23,31,39,47,55,63]
right_shift = [8,16,24,32,40,48,56]
singed_list = [8,16,32,64]
unsinged_list = [8,16,32,64]
format_list = ["Motorola","Intel"]
g_flag = False
groups_name = "Group"
g_flag_rx = False
message = """
/*!
* @brief Enum for Tx msg type.
*/
typedef enum
{
	CANIL_TX_TYPE_VISIBLE = 0,	/* Visible like CE, HS Periodical Msg. */
	CANIL_TX_TYPE_HIDDEN		/* Invisible like Test Msg. */
}CanIl_TtxMsgType;

/*!
* @brief Enum for all CAN channels.
*/
typedef enum
{
	CANIL_RX_DIAG_TRUE = 0,	/* Rx message would be diagnosed against checksum or rolling counter, etc. */
	CANIL_RX_DIAG_FALSE		/* Rx message would NOT be diagnosed. */
}CanIl_TrxMsgDiagStatus;

"""
enum_header = """
/*!
* @brief Enum for all CAN channels.
*/
typedef enum
{
    /* CanIl_TcanChannel: Code Generation starts here.*/
"""
enum_end = """
}CanIl_TcanChannel;

"""
# 切片函数
def cut_list(list_input):
    temp = []
    result = []
    i = 0
    j = i+1
    while j <= len(list_input)-1:
        if list_input[j] == list_input[i]:
            temp.append(list_input[i])
        else:
            temp.append(list_input[i])
            result.append(temp)
            temp = []
        i += 1
        j += 1
    temp.append(list_input[j - 1])
    result.append(temp)
    return result

class Signal:

    def __init__(self,name,start_bit,len,align,uint,node,bittypes,group_id):
        self.name = name                #   信号名
        self.sbit = start_bit           #   信号起始bit
        self.len = len                  #   信号总长度
        # 如果当前信号的长度，是8的倍数，则不需要特殊处理，
        # 否则需要特殊处理
        if (24 != int(self.len) and (int(self.len) % 8) == 0):
            self.is_bit_8_time = True
        else:
            self.is_bit_8_time = False
        self.align = align              #   数据对其模式: 0--Motorola， 1--Intel
        self.sign = bittypes            #   "+"  --无符号数据，"-" : --有符号数据
        self.mul = -1                   #   scale
        self.offset = -1
        self.unit = uint                #   单位
        self.max = -1
        self.min = -1
        self.small_name = name            #   保持最初状态的名字
        self.receivers = node           #   接收处理此信号的节点，同样可以不指明，写为Vector__XXX
        self.get_rx_map = {}            #   此map用于需要跨字节存储时，需要对字节低位\高位，与左\右 移位的映射
        self.heightest_bits = 0
        self.need_cross_byte = False    #   是否需要跨字节存储
        self.cut_off_count = 0          #   表示这个信号的存储需要截断多少次
        self.cut_off_list = []          #   存储这个被截断的名称
        self.intel_less_list = []       #   存储intel格式的每个“分段位的长度”
        self.if_done = False
        if group_id !=  "":
            self.group_id = int(group_id)
        else:
            self.group_id = -1
        # 有符号
        if self.sign == "-":
            for sign_ in singed_list:
                if int(self.len) <= sign_:
                    self.bits = sign_
                    self.byte = "sint"+str(sign_)
                    if (64 == sign_):
                        self.byte_64_ = True
                    else:
                        self.byte_64_ = False
                    break
            self.struct = "sint8"
            self.struct_for_need_cross_byte = "uint8"
        # 无符号
        if self.sign == "+":
            for sign_ in unsinged_list:
                if int(self.len) <= sign_:
                    self.bits = sign_
                    self.byte = "uint"+str(sign_)
                    if (64 == sign_):
                        self.byte_64_ = True
                    else:
                        self.byte_64_ = False
                    break
            self.struct = "uint8"
            self.struct_for_need_cross_byte = "uint8"
        self.values = []            #信号可取的值的列表

class Message:

    def __init__(self, message_id, message_len, message_name, emitter, node=""):
        self.curr_file_node = node
        self.id = message_id            #   消息ID
        self.name = message_name        #   消息名字
        self.emitter = emitter          #   发出该消息的网络节点，标识为Vector__XXX时未指明具体节点
        if emitter == node:
            self.tx_rx = "Tx"
        else:
            self.tx_rx = ""
        self.signals = []               #   消息中的信号,这里存储的是不需要分组的信号集合[信号1，信号2，信号3，信号4]
        self.no_need_group_64_layout = []    #   不需要分组时,64为长度布局
        self.no_need_group_64_layout_without_sign = []  #   不需要分组时，不带符号的64位长度
        self.groups = []                #   这里存储的是需要分组的信号集合[[信号，信号2，信号3],[信号1',信号2',信号3']]
        self.groups_id = []             #   这里存放的是分组id [组id9,组id8,组id7.....,组id0]从大到小排序(从dbc文件中读取的顺序决定)
        # 映射关系:
        # [      组id_n,       组id_n-1,          组id_n-2..., 组id_0 ]
        #         \            \                   \           \
        #          \            \                   \           \
        # [ [信号,信号2,信号3],   [信号1',信号2',信号3'], ......,   [信号1'',信号2'',信号3'']]
        #           \                   \                               \
        #            \                   \                               \
        # [  [ 64位长度布局1],       [64为长度布局2],...........,      [64为长度布局3]  ]

        self.need_group_64_layout = []       #   需要分组时,每一个分组的64位长度布局
        self.need_group_64_layout_without_sign = []     #   需要分组时，带符号的64位长度
        self.group_ordered = False      #   是否已经排序了，在后续操作中，如何判断当前已经排序了，那么就直接不用再排序了
        self.M_groups = []              #   需要分组信号中，带有M字段的信号，作为repeat msg使用，在CanIl_Cfg.c中会用到。
        self.list_repeat_message_name = ""
        self.is_period = False          #   是否是周期报文
        self.period = 0                 #   该报文的周期
        self.both_need = []             #   这里存放的是所有分组信号集合中共有信号
        self.need_group = False         #   这个消息是否需要进行分组
        self.both = False
        self.both_data_struct = False
        self.parsed = False
        self.need_group_parsed = False
        self.struct_writed = False
        self.union_writed = False

    def sort(self):
        temp = {}
        temp2 = []
        if self.signals != []:
            start_bit = []
            for ar in self.signals:
                # 先将起始位全部加入到start_bit
                start_bit.append(int(ar.sbit))
                # 将起始位 与 ar 作映射
                temp[int(ar.sbit)] = ar
            # 将start_bit 从小到大排序
            start_bit.sort()
            for id in start_bit:
                temp2.append(temp[id])
        self.signals = temp2

    # 排序原理与上面sort()一致
    def group_sort(self):
        if self.group_ordered == False:
            self.group_ordered = True
            if len(self.groups_id) > 0 and len(self.groups) > 0:
                self.groups_id.reverse()
                self.groups.reverse()
                if len(self.groups_id) != len(self.groups):
                    print("[Error] 需要分组的id 与 信号分组 大小不一致")
                    # print(self.name)
                    # print(self.groups_id)
                    # print(len(self.groups))
                    # for ar_list in self.groups:
                    #     print(ar_list[0].group_id)
                    return
                else:
                    i = 0
                    while i < len(self.groups):
                        start_bit = []
                        temp = {}
                        temp2 = []
                        for ar in self.groups[i]:
                            start_bit.append(int(ar.sbit))
                            temp[int(ar.sbit)] = ar
                        start_bit.sort()
                        for id in start_bit:
                            temp2.append(temp[id])
                        self.groups[i] = temp2
                        i += 1

    @staticmethod
    def pares_intel(message:'Message', ar_list:(list), group: (bool)):

        if True == message.need_group_parsed:
                return

        if (group == False):
            if True == message.parsed:
                return
            else:
                message.parsed = True

        #   存放最终结果
        bitmap_result = []
        #   填充一个长度为64，元素初始值均为‘0’的一维数组
        bitmap = []
        i = 0
        while i < 64:
            bitmap.append('0')
            i += 1

        #   将这个消息的所有的信号，按照起始位置已经长度
        for ar in ar_list:
            j = 0
            while j < int(ar.len):
                bitmap[int(ar.sbit)+j] = ar.name
                j += 1

        if 1 == int(ar.align):
            #   如果是intel格式，将其转换为8*8的矩阵
            #   元素有原来的numpy.srt_对象 转换为 python.str对象
            bitmap = np.array(bitmap, dtype=np.str_).reshape(8,8).astype(str)
            bitmap = bitmap.astype(str)
            bitmap = bitmap.tolist()

            #  按照相同元素进行切片处理
            i = 0
            while i < len(bitmap):
                bitmap_result.append(cut_list(bitmap[i]))
                i += 1

            if group :
                message.need_group_64_layout_without_sign.append(copy.deepcopy(bitmap_result))
            else:
                message.no_need_group_64_layout_without_sign = copy.deepcopy(bitmap_result)

            #   遍历所有得信号列表
            for ar in ar_list:
                #   切割次数
                ar.cut_off_count = 0
                i = 0
                while i < len(bitmap_result):
                    j = 0
                    while j < len(bitmap_result[i]):
                        #   这个条件下，此信号不需要被跨字节存储
                        if ('0' not in bitmap_result[i][j]) and (ar.name in bitmap_result[i][j]) and (int(ar.len) == len(bitmap_result[i][j])):
                            k = 0
                            while k < len(bitmap_result[i][j]):
                                bitmap_result[i][j][k] = ar.struct+" "+ar.name
                                k += 1
                        #   此条件下，此信号需要被跨字节存储
                        if ('0' not in bitmap_result[i][j] and (ar.name in bitmap_result[i][j]) and (int(ar.len) != len(bitmap_result[i][j]))):
                            # 此时len(bitmap_result[i][j]) 表示这个信号 在这个字节中占用多少位
                            ar.intel_less_list.append(len(bitmap_result[i][j]))
                            if ar.need_cross_byte == False:
                                    ar.need_cross_byte = True
                            k = 0
                            while k < len(bitmap_result[i][j]):
                                bitmap_result[i][j][k] = ar.struct_for_need_cross_byte+" "+ar.name+"_"+str(ar.cut_off_count)
                                message.no_need_group_64_layout_without_sign[i][j][k] = \
                                    ar.name+"_"+str(ar.cut_off_count)
                                k += 1
                            # 如果ar需要被切三次存储，那么ar.cut_off_list = [ar.name_0, ar.name_1, ar.name_2]
                            ar.cut_off_list.append(ar.name+"_"+str(ar.cut_off_count))
                            ar.cut_off_count += 1
                        j += 1
                    i += 1
            return copy.deepcopy(bitmap_result)

    @staticmethod
    def pares_motorola(message:'Message' ,ar_list:(list), group:(bool)):

        if True == message.need_group_parsed:
                return

        if (group == False):
            if True == message.parsed:
                return
            else:
                message.parsed = True

        result_map = []
        bitmaps = []
        i = 0
        while i < 64:
            bitmaps.append('0')
            i += 1

        index = 0
        for ar in ar_list:
            #   z找到ar.sbit所在行的最高位,得到其index
            for up in round_up:
                if int(ar.sbit) <= up:
                    index = round_up.index(up)
                    break
            # 如果从ar.len 如果比从ar.sbit到其所在行的最低位小（说明这个从ar.sbit到其所在行最低位之间就可以填完这个信号）
            # 8 - (round_up[index]-ar.sbit) 得到的就是从ar.sbit到其最低位之间的空余位数
            if int(ar.len) <= (LINE_NUM - (round_up[index]-int(ar.sbit))):
                ar.need_cross_byte = False
                j = 0
                while j < int(ar.len):
                    bitmaps[int(ar.sbit)-j] = ar.struct+" "+ar.name
                    j += 1
            else:
                # 在这个条件中，这个信号需要跨行填充
                ar.need_cross_byte = True

                loop = 0
                start_list = []
                less_list = []
                # 首先将ar.sbit加入起始位列表
                start_list.append(int(ar.sbit))  #start_list[0] = 5
                # 将ar.sbit到该行最低位之间的空余行加入其中
                less_list.append(LINE_NUM-(round_up[index]-int(ar.sbit))) # less_list[0] = 6
                # 将ar.len 剩余的位数赋值给 less
                less = int(ar.len) - (LINE_NUM-(round_up[index]-int(ar.sbit)))
                if less > 0:
                    if (less % LINE_NUM) != 0:
                        # 剩下的数不是 8 的整数倍，说明需要 less / 8 + 1 行 才能填满
                        loop = less / LINE_NUM + 1              # 9/8 + 1 = 2
                        num = less % LINE_NUM                   # 最后一行填多少？填9%8的余数。9%8 = 1
                        i = 0
                        while i <= loop - 2:                    # 这里减2的原因是：第一次填和最后一次填都已经确认了，仅需记录中间的即可。i <= 2-2
                            less_list.append(LINE_NUM)          # less_list[1] = 8
                            i += 1
                        less_list.append(num)                   # less_list[2] = 1
                    else:
                        # 如果剩下的数是 8 整数倍，那么说明剩下的位数 需要 less/8 行 即可填满
                        loop = less / LINE_NUM
                        i = 0
                        while i < loop:
                            less_list.append(LINE_NUM)
                            i += 1

                    i = 1
                    while i <= loop:
                        start_list.append(round_up[index+i])
                        i += 1

                    # 如果需要单独debug单一行，那么将此注释打开
                    # print(start_list)
                    # print(less_list)
                    # print(ar.name)
                    # print(len(bitmaps))

                    #   需要切割多少次，即：len(start_list)的长度
                    ar.cut_off_count = len(start_list)

                    #   分别从每次切割的最高位开始，
                    #   往低位开始填
                    i = 0
                    while i < len(start_list):
                        sbit = int(start_list[i])
                        count = int(less_list[i])
                        while count > 0:
                                bitmaps[sbit] = ar.struct_for_need_cross_byte+" "+ar.name+"_"+str(i)
                                sbit -= 1
                                count -= 1
                        i += 1

                    # 找到该信号的最高位占几位
                    ar.heightest_bits = less_list[i-1]
                    less_list_copy = []
                    less_list_copy = copy.deepcopy(less_list)
                    less_list_copy.append(0)
                    arr = np.array(less_list_copy)

                    # 求 左右移位的列表
                    i = 0
                    c = []
                    sum = 0
                    while i < len(arr):
                        temp = 0
                        j = i+1
                        while j < len(arr):
                            temp += arr[j]
                            j += 1
                        sum = copy.deepcopy(temp)
                        c.append(sum)
                        i += 1
                    c.pop()

                    #   求得每一个跨行信号所需要的移位字典
                    i = 0
                    while i < len(start_list):
                        ar.get_rx_map[ar.name+"_"+str(i)] = c[i]
                        i += 1
                    # print(ar.get_rx_map)
                else:
                    print("[Error]!!!Please check!!\n")

        #装换为 8*8 的数组 （根据canoe 上的layout大小生成）
        bitmaps = np.array(bitmaps, dtype=np.str_).reshape(8,8).astype(str)
        bitmaps = bitmaps.astype(str)
        bitmaps = bitmaps.tolist()
        i = 0
        while i < len(bitmaps):
            result_map.append(cut_list(bitmaps[i]))
            i += 1

        return result_map

    def self_parse_self(self):

        if False == self.need_group:
            if 1 == int(self.signals[0].align):
                self.sort()
                result = None
                result = Message.pares_intel(self, self.signals, False)
                if None != result:
                    self.no_need_group_64_layout = copy.deepcopy(result)

            if 0 == int(self.signals[0].align):
                self.sort()
                result = None
                result = Message.pares_motorola(self, self.signals, False)
                if None != result:
                    self.no_need_group_64_layout = copy.deepcopy(result)

        if True == self.need_group:
            if 1 == int (self.groups[0][0].align):
                if (len(self.groups_id) == len(self.groups)):
                    self.group_sort()
                    i = 0
                    while i < len(self.groups_id):
                        result = None
                        result = Message.pares_intel(self, self.groups[i], True)
                        if None != result:
                            self.need_group_64_layout.append(result)
                        i += 1
                    self.need_group_parsed = True
                else:
                    print("分组信号与分组id长度不同, message:[%s]\n" % (self.name))
                # print("--------------------------------------")
                # print("name = %s" % (self.name))
                # print(self.need_group_64_layout)
            if 0 == int(self.groups[0][0].align):
                if (len(self.groups_id) == len(self.groups)):
                    self.group_sort()
                    i = 0
                    while i < len(self.groups_id):
                        result = None
                        result = Message.pares_motorola(self, self.groups[i], True)
                        if None != result:
                            self.need_group_64_layout.append(result)
                        i += 1
                    self.need_group_parsed = True
                else:
                    print("分组信号与分组id长度不同, message:[%s]\n" % (self.name))
                # print("--------------------------------------")
                # print("name = %s" % (self.name))
                # print("groups_id = %s" % (len(self.groups)))
                # print("Groups = %d" % (len(self.groups_id)))
                # print(self.need_group_64_layout)

    def wirte_tx_rx(self,target=None,can_name="",dir="Tx", types="define", order_can_list=None):
        global g_flag
        global g_flag_rx
        global Txmsg_count
        global Rxmsg_count
        global Txmsg_data_count
        global Rxmsg_data_count

        self.self_parse_self()

        if target != None:
            unused = 0
            count = 0
            # ar 为一行
            # 写入宏定义
            if (self.tx_rx == dir or self.tx_rx == "Both") and ("Tx" == dir) and types == "define":
                # print(self.name)
                if self.need_group == False:
                    for ar in self.signals:
                        if ar.need_cross_byte == False:
                            target.write("/*  MsgNo: %s\n" % (Txmsg_count))
                            target.write("\tMsgid: 0x%X\n" % (self.id))
                            target.write("\tDir: %s\n" % (self.tx_rx))
                            target.write("\tMsgid(dec): %d\n" % (self.id))
                            target.write("\tMsgName: %s\n" % (self.name))
                            target.write("\tSigName: %s\n" % (ar.name))
                            target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                            target.write("*/\n")
                            target.write("#define CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"(c) \\\n")
                            target.write("{\\\n")
                            target.write("\tCanIlIf_SuspendAllInterrupts(); \\\n")
                            target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.name+" = (c); \\\n")
                            target.write("\tCanIlIf_ResumeAllInterrupts(); \\\n")
                            target.write("}\n\n")
                            Txmsg_count += 1
                else:
                    i = 0
                    while i < len(self.groups_id):
                        for ar in self.groups[i]:
                            if ar.need_cross_byte == False:
                                target.write("/*  MsgNo: %s\n" % (Txmsg_count))
                                target.write("\tMsgid: 0x%X\n" % (self.id))
                                target.write("\tDir: %s\n" % (self.tx_rx))
                                target.write("\tMsgid(dec): %d\n" % (self.id))
                                target.write("\tMsgName: %s\n" % (self.name+"_Group"+str(self.groups_id[i])))
                                target.write("\tSigName: %s\n" % (ar.name))
                                target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                                target.write("*/\n")
                                target.write("#define CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.name+"(c) \\\n")
                                target.write("{\\\n")
                                target.write("\tCanIlIf_SuspendAllInterrupts(); \\\n")
                                target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+"."+ \
                                            self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+"."+ar.name+" = (c); \\\n")
                                target.write("\tCanIlIf_ResumeAllInterrupts(); \\\n")
                                target.write("}\n\n")
                                Txmsg_count += 1
                        i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and ("Rx" == dir) and types == "define":
                if self.need_group == False:
                    for ar in self.signals:
                        if ar.need_cross_byte == False:
                            target.write("/*  MsgNo: %s\n" % (Rxmsg_count))
                            target.write("\tMsgid: 0x%X\n" % (self.id))
                            target.write("\tMsgid(dec): %d\n" % (self.id))
                            target.write("\tMsgName: %s\n" % (self.name))
                            target.write("\tSigName: %s\n" % (ar.name))
                            target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                            target.write("*/\n")
                            target.write("#define CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"()\t\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.name+"\n\n")
                            Rxmsg_count += 1

                else:
                    i = 0
                    while i < len(self.groups_id):
                        if len(self.groups) == len(self.groups_id):
                            for ar in self.groups[i]:
                                if ar.need_cross_byte == False:
                                    target.write("/*  MsgNo: %s\n" % (Rxmsg_count))
                                    target.write("\tMsgid: 0x%X\n" % (self.id))
                                    target.write("\tMsgid(dec): %d\n" % (self.id))
                                    target.write("\tMsgName: %s\n" % (self.name+"_Group"+str(self.groups_id[i])))
                                    target.write("\tSigName: %s\n" % (ar.name))
                                    target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                                    target.write("*/\n")
                                    target.write("#define CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.name+"()\t\t"+ \
                                                dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+"."+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+"."+ar.name+"\n\n")
                                    Rxmsg_count += 1
                        i += 1    

            # 写入结构体
            if (self.tx_rx == dir or self.tx_rx == "Both") and types == "struct":
                # print(self.name)
                # print(self.need_group)
                if True == self.struct_writed:
                    return
                self.struct_writed = True

                if self.need_group == False:
                    target.write("/* Dir: %s\n" % (self.tx_rx))
                    if dir == "Rx" or dir == "Both":
                        target.write("   MsgNo: %d\n" % (Rxmsg_count))
                    else:
                        target.write("   MsgNo: %d\n" % (Txmsg_count))
                    target.write("   MsgName: %s\n" % (self.name))
                    target.write("   MsgId: 0x%X\n" % (self.id))
                    target.write("   MsgId(dec): %d\n" % (self.id))
                    target.write("   Transmitter: %s\n" % (self.emitter))
                    target.write("   NetWork: %s\n" % (can_name))
                    target.write("   Format: %s\n" % (format_list[int(self.signals[0].align)]))
                    target.write("   DLC: %d\n" % (LINE_NUM))
                    target.write("*/\n")
                    target.write("typedef struct\n")
                    target.write("{\n")
                    for ar in self.no_need_group_64_layout:
                        target.write("\n\t/* Byte No: "+str(count)+" (bit 0 -> bit 7) */\n")
                        for br in ar:
                            if '0' in br or None in br:
                                target.write("\tuint8 unused_"+str(unused)+": "+str(len(br))+";\n")
                                unused += 1
                            else:
                                target.write("\t"+str(br[0])+": "+str(len(br))+";\n")
                        count += 1
                    target.write("\n} CanIl_TmsgSt_"+can_name+"_"+self.name+";\n\n")

                else:
                    if len(self.groups) > 0:
                        i = 0
                        while i < len(self.groups_id):
                            target.write("/* Dir: %s\n" % (dir))
                            if dir == "Rx":
                                target.write("   MsgNo: %d\n" % (Rxmsg_count-1))
                            else:
                                target.write("   MsgNo: %d\n" % (Txmsg_count-1))
                            target.write("   MsgName: %s\n" % (self.name+"_Group"+str(self.groups_id[i])))
                            target.write("   MsgId: 0x%X\n" % (self.id))
                            target.write("   MsgId(dec): %d\n" % (self.id))
                            target.write("   Transmitter: %s\n" % (self.emitter))
                            target.write("   NetWork: %s\n" % (can_name))
                            target.write("   Format: %s\n" % (format_list[int(self.groups[0][0].align)]))
                            target.write("   DLC: %d\n" % (LINE_NUM))
                            target.write("*/\n")
                            target.write("typedef struct\n")
                            target.write("{\n")
                            count = 0
                            unused = 0
                            for ar in self.need_group_64_layout[i]:
                                target.write("\n\t/* Byte No: "+str(count)+" (bit 0 -> bit 7) */\n")
                                for br in ar:
                                    if '0' in br:
                                        target.write("\tuint8 unused_"+str(unused)+": "+str(len(br))+";\n")
                                        unused += 1
                                    else:
                                        target.write("\t"+br[0]+": "+str(len(br))+";\n")
                                count += 1
                            target.write("\n} CanIl_TmsgSt_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+";\n\n")
                            i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and types == "data_struct":
                if True == self.union_writed:
                    return
                self.union_writed = True
                if self.need_group == False:
                    target.write("/* Dir: %s\n" % (self.tx_rx))
                    if dir == "Rx":
                        target.write("   MsgNo: %d\n" % (Rxmsg_data_count-1))
                    else:
                        target.write("   MsgNo: %d\n" % (Txmsg_data_count-1))

                    target.write("   MsgName: %s\n" % (self.name))
                    target.write("   MsgId: 0x%X\n" % (self.id))
                    target.write("   MsgId(dec): %d\n" % (self.id))
                    target.write("   Transmitter: %s\n" % (self.emitter))
                    target.write("   NetWork: %s\n" % (can_name))
                    target.write("   Format: %s\n" % (format_list[int(self.signals[0].align)]))
                    target.write("   DLC: %d\n" % (LINE_NUM))
                    target.write("*/\n")
                    target.write("typedef union\n")
                    target.write("{\n")
                    target.write("\tuint8 data_array[8];\n")
                    target.write("\tCanIl_TmsgSt_"+can_name+"_"+self.name+" "+self.name.upper()+";\n")
                    target.write("}CanIl_TmsgUn_"+can_name+"_"+self.name+";\n\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        target.write("/* Dir: %s\n" % (dir))
                        if dir == "Rx":
                            target.write("   MsgNo: %d\n" % (Rxmsg_data_count-1))
                        else:
                            target.write("   MsgNo: %d\n" % (Txmsg_data_count-1))

                        target.write("   MsgName: %s\n" % (self.name+"_Group"+str(self.groups_id[i])))
                        target.write("   MsgId: 0x%X\n" % (self.id))
                        target.write("   MsgId(dec): %d\n" % (self.id))
                        target.write("   Transmitter: %s\n" % (self.emitter))
                        target.write("   NetWork: %s\n" % (can_name))
                        target.write("   Format: %s\n" % (format_list[int(self.groups[0][0].align)]))
                        target.write("   DLC: %d\n" % (LINE_NUM))
                        target.write("*/\n")
                        target.write("typedef union\n")
                        target.write("{\n")
                        target.write("\tuint8 data_array[8];\n")
                        target.write("\tCanIl_TmsgSt_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" "+self.name.upper()+ \
                                    "_"+groups_name.upper()+str(self.groups_id[i])+";\n")
                        target.write("}CanIl_TmsgUn_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+";\n\n")
                        i += 1

            # 写入枚举
            if types == "Channel_enum":
                if order_can_list != None:
                    target.write(message)
                    target.write(enum_header)
                    flag = False
                    for can in order_can_list:
                        if flag == False:
                            flag = True
                            target.write("\tCANIL_CHN_ID_"+can+" = 0,\n")
                        else:
                            target.write("\tCANIL_CHN_ID_"+can+",\n")
                    target.write("\tCANIL_CHN_ID_NUM")
                    target.write(enum_end)
            # 写入can tx message 枚举
            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Tx" and types == "can_message_enum":
                if self.need_group == False:
                    if self.tx_rx == "Tx" or self.tx_rx == "Both":
                        if g_flag == False:
                            target.write("\tCANIL_MSG_IL_ID_TX_PE_"+can_name+"_"+self.name+" = 0,\n")
                            g_flag = True
                        else:
                            target.write("\tCANIL_MSG_IL_ID_TX_PE_"+can_name+"_"+self.name+",\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        if self.tx_rx == "Tx" or self.tx_rx == "Both":
                            if g_flag == False:
                                target.write("\tCANIL_MSG_IL_ID_TX_PE_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" = 0,\n")
                                g_flag = True
                            else:
                                target.write("\tCANIL_MSG_IL_ID_TX_PE_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+",\n")
                        i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Rx" and types == "can_message_enum":
                if self.need_group == False:
                    if self.tx_rx == "Rx" or self.tx_rx == "Both":
                        if g_flag_rx == False:
                            target.write("\tCANIL_MSG_IL_ID_RX_PE_"+can_name+"_"+self.name+" = 0,\n")
                            g_flag_rx = True
                        else:
                            target.write("\tCANIL_MSG_IL_ID_RX_PE_"+can_name+"_"+self.name+",\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        if self.tx_rx == "Rx" or self.tx_rx == "Both":
                            if g_flag_rx == False:
                                target.write("\tCANIL_MSG_IL_ID_RX_PE_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" = 0,\n")
                                g_flag_rx = True
                            else:
                                target.write("\tCANIL_MSG_IL_ID_RX_PE_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+",\n")
                        i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Tx":
                if types == "extern_int":
                    if self.need_group == False :
                        target.write("extern CanIl_TmsgUn_"+can_name+"_"+self.name+" "+dir.upper()+"_"+can_name+"_"+self.name.upper()+";\n")
                    else:
                        i = 0
                        while i < len(self.groups_id):
                            target.write("extern CanIl_TmsgUn_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" "+\
                                        dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+";\n")
                            i += 1

                if types == "extern_int_back":
                    if self.need_group == False :
                        target.write("/*  MsgId: %s\n" % (hex(int(self.id)).upper()))
                        target.write("\tDir: %s\n" % (self.tx_rx))
                        target.write("\tMsgName : %s\n" % (self.name))
                        target.write("\tFormat: %s\n" % (format_list[int(self.signals[0].align)]))
                        target.write("*/\n")
                        target.write("CanIl_TmsgUn_"+can_name+"_"+self.name+" "+dir.upper()+"_"+can_name+"_"+self.name.upper()+";\n\n")
                    else:
                        i = 0
                        while i < len(self.groups_id):
                            target.write("/*  MsgId: %s\n" % (hex(int(self.id)).upper()))
                            target.write("\tDir: %s\n" % (self.tx_rx))
                            target.write("\tMsgName : %s\n" % (self.name))
                            target.write("\tFormat: %s\n" % (format_list[int(self.groups[0][0].align)]))
                            target.write("*/\n")
                            target.write("CanIl_TmsgUn_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" "+\
                                        dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+";\n\n")
                            i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Rx":
                if types == "extern_int":
                    if self.need_group == False:
                        target.write("extern CanIl_TmsgUn_"+can_name+"_"+self.name+" "+dir.upper()+"_"+can_name+"_"+self.name.upper()+";\n")
                    else:
                        i = 0
                        while i < len(self.groups_id):
                            target.write("extern CanIl_TmsgUn_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" "+\
                                        dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+";\n")
                            i += 1

                if types == "extern_int_back":
                    if self.need_group == False:
                        target.write("/*  MsgId: %s\n" % (hex(int(self.id)).upper()))
                        target.write("\tDir: %s\n" % (self.tx_rx))
                        target.write("\tMsgName : %s\n" % (self.name))
                        target.write("\tFormat: %s\n" % (format_list[int(self.signals[0].align)]))
                        target.write("*/\n")
                        target.write("CanIl_TmsgUn_"+can_name+"_"+self.name+" "+dir.upper()+"_"+can_name+"_"+self.name.upper()+";\n\n")
                    else:
                        i = 0
                        while i < len(self.groups_id):
                            target.write("/*  MsgId: %s\n" % (hex(int(self.id)).upper()))
                            target.write("\tDir: %s\n" % (self.tx_rx))
                            target.write("\tMsgName : %s\n" % (self.name))
                            target.write("\tFormat: %s\n" % (format_list[int(self.groups[0][0].align)]))
                            target.write("*/\n")
                            target.write("CanIl_TmsgUn_"+can_name+"_"+self.name+"_Group"+str(self.groups_id[i])+" "+\
                                        dir.upper()+"_"+can_name+"_"+self.name.upper()+"_"+groups_name.upper()+str(self.groups_id[i])+";\n\n")
                            i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Tx" and types == "extern_tx_int":
                if self.need_group == False:
                    for ar in self.signals:
                        if ar.need_cross_byte == True:
                            if ar.byte_64_ == False:
                                target.write("extern void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"("+ar.byte+" sigData);\n")
                            else:
                                target.write("extern void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"(uint8* sigData);\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        for ar_list in self.groups:
                            for ar in ar_list:
                                if ar.need_cross_byte == True:
                                    target.write("extern void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.small_name+"("+ar.byte+" sigData);\n")
                        i += 1
    

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Tx" and types == "extern_tx_int_back":
                if self.need_group == False:
                    for ar in self.signals:
                        if ar.need_cross_byte == True and ar.byte_64_ == False:
                            target.write("/*  Msg_id: %s\n" % (hex(int(self.id)).upper()))
                            target.write("\tMsg_name: %s\n" % (self.name))
                            target.write("\tSigName: %s\n" % (ar.name))
                            target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                            target.write("*/\n")
                            target.write("void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.small_name+"("+ar.byte+" sigData)\n")
                            target.write("{\n")
                            target.write("\tCanIlIf_SuspendAllInterrupts();\n")
                            #   针对Motorola格式：
                            if int(ar.align) == 0:
                                for key, value in ar.get_rx_map.items():
                                    if value != 0:
                                        target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+key+" = (uint8)((sigData) >> "+str(value)+");\n")
                                    else:
                                        k = 0
                                        sum = 0
                                        while k < ar.heightest_bits:
                                            sum |= 1 << k
                                            k += 1
                                        sum = bin(sum)[2:]
                                        sum = '0x{:02X}'.format(int(sum,2))
                                        target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+key+" = "+" ((uint8) (sigData & "+sum+"));\n")
                            else:
                                if int(ar.cut_off_count) <= 2:
                                    k = 0
                                    sum = 0
                                    while k < ar.intel_less_list[0]:
                                        sum |= 1 << k
                                        k += 1
                                    sum = bin(sum)[2:]
                                    sum = '0x{:02X}'.format(int(sum,2))
                                    target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[0]+" = "+" ((uint8) (sigData & "+sum+"));\n")
                                    target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[1]+" = (uint8)((sigData) >> "+str(ar.intel_less_list[0])+");\n")
                                else:
                                    z = 0
                                    while z < int(ar.cut_off_count):
                                        if z == 0:
                                            k = 0
                                            sum = 0
                                            while k < ar.intel_less_list[0]:
                                                sum |= 1 << k
                                                k += 1
                                            sum = bin(sum)[2:]
                                            sum = '0x{:02X}'.format(int(sum,2))
                                            target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[0]+" = "+" ((uint8) (sigData & "+sum+"));\n")
                                        else:
                                            q = 0
                                            sum = 0
                                            while q < z:
                                                sum += ar.intel_less_list[q]
                                                q += 1
                                            target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[z]+" = (uint8)((sigData) >> "+str(sum)+");\n")
                                        z += 1
                            target.write("\tCanIlIf_ResumeAllInterrupts();\n")
                            target.write("};\n\n")

                        if ar.need_cross_byte == True and ar.byte_64_ == True:
                            target.write("/*  Msg_id: %s\n" % (hex(int(self.id)).upper()))
                            target.write("\tMsg_name: %s\n" % (self.name))
                            target.write("\tSigName: %s\n" % (ar.name))
                            target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                            target.write("*/\n")
                            target.write("void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.small_name+"(uint8* sigData)\n")
                            target.write("{\n")
                            target.write("\tCanIlIf_SuspendAllInterrupts();\n")
                            # 针对motorola 格式
                            if int(ar.align) == 0:
                                count_temp = len(ar.get_rx_map) - 1
                                for key, value in ar.get_rx_map.items():
                                    if value != 0:
                                        target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+key+" = (sigData["+str(count_temp)+"]);\n")
                                        count_temp -= 1
                                    else:
                                        target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+key+" = (sigData["+str(count_temp)+"]);\n")
                            else:
                                z = int(ar.cut_off_count) - 1
                                while z >= 0:
                                    target.write("\t"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[z]+" = (sigData["+str(z)+"]);\n")
                                    z -= 1
                            target.write("\tCanIlIf_ResumeAllInterrupts();\n")
                            target.write("};\n\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        for ar_list in self.groups:
                            for ar in ar_list:
                                if ar.need_cross_byte == True:
                                    target.write("/*  Msg_id: %s\n" % (hex(int(self.id)).upper()))
                                    target.write("\tMsg_name: %s\n" % (self.name))
                                    target.write("\tSigName: %s\n" % (ar.name))
                                    target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                                    target.write("*/\n")
                                    target.write("void CanIlPutTx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.small_name+"("+ar.byte+" sigData)\n")
                                    target.write("{\n")
                                    target.write("\tCanIlIf_SuspendAllInterrupts();\n")
                                    if int(ar.align) == 0:
                                        k = 0
                                        k_len = int(ar.cut_off_count) - 2
                                        while k < int(ar.cut_off_count):
                                            if k < int(ar.cut_off_count) - 1:
                                                target.write("\t"+dir.upper()+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+self.name.upper()+"_GROUP"+str(self.groups_id[i])+\
                                                            "."+ar.small_name+"_"+str(k)+" = "+"(uint8)((sigData >> "+str(right_shift[k_len])+"));\n")
                                                k_len -= 1
                                            if k == int(ar.cut_off_count) - 1:
                                                j = 0
                                                sum = 0
                                                while j < ar.heightest_bits:
                                                    sum |= 1 << j
                                                    j += 1
                                                sum = bin(sum)[2:]
                                                sum = '0x{:02X}'.format(int(sum,2))
                                                target.write("\t"+dir.upper()+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+\
                                                            self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+ar.small_name+"_"+str(k)+" = "+" ((uint8) (sigData & "+sum+"));\n")
                                            k += 1
                                        target.write("\tCanIlIf_ResumeAllInterrupts();\n")
                                        target.write("};\n\n")
                                    else:
                                        if int(ar.cut_off_count) <= 2:
                                            k = 0
                                            sum = 0
                                            while k < ar.intel_less_list[0]:
                                                sum |= 1 << k
                                                k += 1
                                            sum = bin(sum)[2:]
                                            sum = '0x{:02X}'.format(int(sum,2))
                                            target.write("\t"+dir.upper()+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[0]+" = "+" ((uint8) (sigData & "+sum+"));\n")
                                            target.write("\t"+dir.upper()+"_"+self.name.upper()+"."+self.name.upper()+"."+ar.cut_off_list[1]+" = (uint8)((sigData) >> "+str(ar.intel_less_list[0])+");\n")
                                        else:
                                            z = 0
                                            while z < int(ar.cut_off_count):
                                                if z == 0:
                                                    k = 0
                                                    sum = 0
                                                    while k < ar.intel_less_list[0]:
                                                        sum |= 1 << k
                                                        k += 1
                                                    sum = bin(sum)[2:]
                                                    sum = '0x{:02X}'.format(int(sum,2))
                                                    target.write("\t"+dir.upper()+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+self.name.upper()+"_GROUP"+str(self.groups_id[i])+\
                                                    "."+ar.cut_off_list[0]+" = "+" ((uint8) (sigData & "+sum+"));\n")
                                                else:
                                                    q = 0
                                                    sum = 0
                                                    while q < z:
                                                        sum += ar.intel_less_list[q]
                                                        q += 1
                                                    target.write("\t"+dir.upper()+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+\
                                                                 "."+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+ar.cut_off_list[z]+" = (uint8)((sigData) >> "+sum+");\n")
                                                z += 1
                        i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Rx" and types == "extern_rx_int":
                if self.need_group == False:
                    for ar in self.signals:
                        if ar.need_cross_byte == True:
                            target.write("extern "+ar.byte+" CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"(void);\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        for ar_list in self.groups:
                            for ar in ar_list:
                                if ar.need_cross_byte == True:
                                    target.write("extern "+ar.byte+" CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.name+"(void);\n")
                                    
                        i += 1

            if (self.tx_rx == dir or self.tx_rx == "Both") and dir == "Rx" and types == "extern_rx_int_back":
                if self.need_group == False:
                    for ar in self.signals:
                        ar_flag = False
                        ar2_flag = False
                        if ar.need_cross_byte == True:
                            target.write("/*  Msg_id: %s\n" % (hex(int(self.id)).upper()))
                            target.write("\tMsg_name: %s\n" % (self.name))
                            target.write("\tSigName: %s\n" % (ar.name))
                            target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                            target.write("*/\n")
                            target.write(ar.byte+" CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"(void)\n")
                            target.write("{\n")
                            target.write("\t"+ar.byte+" rc = 0;\n")
                            target.write("\tCanIlIf_SuspendAllInterrupts();\n")
                            if int(ar.align) == 0:
                                for key, value in ar.get_rx_map.items():
                                    if value != 0:
                                        target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                    "."+self.name.upper()+"."+key+") << "+str(value)+");\n")
                                    else:
                                        k = 0
                                        sum = 0
                                        while k < ar.heightest_bits:
                                            sum |= 1 << k
                                            k += 1
                                        sum = bin(sum)[2:]
                                        sum = '0x{:02X}'.format(int(sum,2))
                                        target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                        "."+self.name.upper()+"."+key+") & "+sum+");\n")

                                if ((ar.is_bit_8_time == False and ar.sign == '-') or (ar.sign == '-' and int(ar.len) == 24)):
                                    ar_flag = True
                            else:
                                # print(ar.name)
                                # print(ar.cut_off_count)
                                # print(ar.intel_less_list)
                                # print(ar.cut_off_list)
                                # print("-------------------------------")
                                if ar.cut_off_count <= 2:
                                    k = 0
                                    sum = 0
                                    while k < int(ar.intel_less_list[0]):
                                        sum |= 1 << k
                                        k += 1
                                    sum  = bin(sum)[2:]
                                    sum  = '0x{:02X}'.format(int(sum,2))
                                    target.write("\trc = ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                 "."+self.name.upper()+"."+ar.cut_off_list[0]+") & "+sum+");\n")
                                    target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                 "."+self.name.upper()+"."+ar.cut_off_list[1]+") << "+str(ar.intel_less_list[0])+");\n")
                                else:
                                    k = 0
                                    while k < int(ar.cut_off_count):
                                        if k == 0:
                                            y = 0
                                            sum = 0
                                            while y < int(ar.intel_less_list[0]):
                                                sum |= 1 << y
                                                y += 1
                                            sum = bin(sum)[2:]
                                            sum = sum  = '0x{:02X}'.format(int(sum,2))
                                            target.write("\trc = ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                 "."+self.name.upper()+"."+ar.cut_off_list[k]+") & "+sum+");\n")
                                        else:
                                            p = 0
                                            sum = 0
                                            while p < k:
                                                sum += ar.intel_less_list[p]
                                                p += 1
                                            # print(len(ar.cut_off_list))
                                            # print("\t")
                                            # print(ar.cut_off_list[0])
                                            target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+\
                                                 "."+self.name.upper()+"."+ar.cut_off_list[k]+") << "+str(sum)+");\n")
                                        k += 1
                                    if ((ar.is_bit_8_time == False and ar.sign == '-') or (ar.sign == '-' and int(ar.len) == 24)):
                                        ar2_flag = True
                            target.write("\tCanIlIf_ResumeAllInterrupts();\n")
                            if (ar2_flag or ar_flag):
                                shift_value = 1 << (int(ar.len) -1)
                                shift_value = hex(shift_value)
                                target.write("\n\tif(rc & "+shift_value+")\n")
                                target.write("\t{\n")
                                a = (1 << int(ar.bits))-1
                                b = (1 << int(ar.len))-1
                                target.write("\t\trc |= "+hex(a ^ b)+";\n")
                                target.write("\t}\n")
                            target.write("\treturn rc;\n")
                            target.write("};\n\n")
                else:
                    i = 0
                    while i < len(self.groups_id):
                        for ar_list in self.groups:
                            for ar in ar_list:
                                if ar.need_cross_byte == True:
                                    # target.write("extern "+ar.byte+" CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Group"+str(self.groups_id[i])+"_Sig_"+ar.name+"(void);\n")
                                    target.write("/*  Msg_id: %s\n" % (hex(int(self.id)).upper()))
                                    target.write("\tMsg_name: %s\n" % (self.name))
                                    target.write("\tSigName: %s\n" % (ar.name))
                                    target.write("\tFormat: %s\n" % (format_list[int(ar.align)]))
                                    target.write("*/\n")
                                    target.write(ar.byte+" CanIlGetRx_Net_"+can_name+"_Msg_"+self.name+"_Sig_"+ar.name+"(void)\n")
                                    target.write("{\n")
                                    target.write("\t"+ar.byte+" rc = 0;\n")
                                    target.write("\tCanIlIf_SuspendAllInterrupts();\n")
                                    for key, value in ar.get_rx_map.items():
                                        if value != 0:
                                            target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+\
                                                         "."+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+key+") << "+str(value)+");\n")
                                        else:
                                            k = 0
                                            sum = 0
                                            while k < ar.heightest_bits:
                                                sum |= 1 << k
                                                k += 1
                                            sum = bin(sum)[2:]
                                            sum = '0x{:02X}'.format(int(sum,2))
                                            target.write("\trc |= ((("+ar.byte+")"+dir.upper()+"_"+can_name+"_"+self.name.upper()+"_GROUP"+str(self.groups_id[i])+\
                                                         "."+self.name.upper()+"_GROUP"+str(self.groups_id[i])+"."+key+") & "+sum+");\n")
                                    if ((ar.is_bit_8_time == False and ar.sign == '-') or (ar.sign == '-' and int(ar.len) == 24)):
                                        shift_value = 1 << (int(ar.len) -1)
                                        shift_value = hex(shift_value)
                                        target.write("\n\tif(rc & "+shift_value+")\n")
                                        target.write("\t{\n")
                                        a = (1 << int(ar.bits))-1
                                        b = (1 << int(ar.len))-1
                                        target.write("\t\trc |= "+hex(a ^ b)+";\n")
                                        target.write("\t}\n")
                                    target.write("\tCanIlIf_ResumeAllInterrupts();\n")
                                    target.write("\treturn rc;\n")
                                    target.write("};\n\n")
                        i += 1

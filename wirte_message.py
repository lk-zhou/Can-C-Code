import os
from datetime import datetime

header = """
/*!
***************************************************************************
"""

header2 = """
***************************************************************************
* @author            gdpu.zhou@outlook.com
* @version           1.0.0
* @date              2023.03.15
"""

header3 = """
* @copyright         (C) Copyright
*
*                    Contents and presentations are protected world-wide.
*                    Any kind of using, copying etc. is prohibited without prior permission.
*                    All rights - incl. industrial property rights - are reserved.
*
* @starthistory
* @revision{         1.0.0, Eason Zhou, Initial version.}
* @endhistory
***************************************************************************
*/

"""

message = """
/*!
* @brief struct for repeat CAN message.
*/
typedef struct
{
	uint16 RptMsgID;
	uint8 RptMsgMask;
	uint8 RptMsgOffset;

}CanIl_RepeatMsgMaskInfo;

typedef struct
{
	uint8 NumberOfRptMsg;
	CanIl_RepeatMsgMaskInfo * RptMsgMaskInfo;

}CanIl_CanMsgRptCfg;

/*!
* @brief Enum for Rx timeout handling mode.
*/
typedef enum
{
	CANIL_RX_TM_USE_DEFAULT = 0,
	CANIL_RX_TM_KEEP_LAST
}CanIl_TrxTimeoutMode;

/*!
* @brief Enum for Tx Msg Schedule Type.
*/
typedef enum
{
	CANIL_TX_SCH_TYPE_OS = 0,
	CANIL_TX_SCH_TYPE_ISR
}CanIl_TtxSchType;

/*!
* @brief Attributes for Periodical Tx CAN Message.
*/
typedef struct
{
	uint16 msgId;                                /* CAN Message ID. */
	CanIl_TtxMsgType  msgType;                   /* Tx msg type. */
	CanIl_TtxSchType  schType;                   /* Tx msg schedule type. */
	CanIl_TcanChannel chn;                       /* which CAN channel this message belongs to. */
	uint8  dlc;                                  /* data lenth. */
	uint16 period;                               /* unit is (times value of scheduling period of CanIl_TxTask()). */
	uint8  offset;                               /* unit is (times value of scheduling period of CanIl_TxTask()). */
	boolean periodFixed;                         /* Whethter period and offset are fixed or changable to period2/offset2. */
	uint16 period2;                              /* unit is (times value of scheduling period2 of CanIl_TxTask()). */
	uint8  offset2;                              /* unit is (times value of scheduling offset2 of CanIl_TxTask()). */
	uint8 inGlobalRamIndex;                      /* For whether this frame is shared by CPU1 and CPU2.*/
	uint8 isCANFDFrame;                          /* whether this frame is CANFD or CAN.*/
	uint8  initValue[8];                         /* Initial value to transmit. */
	uint8  *pilBuf;                              /* pointer to message 8 bytes data buffer of IL layer. */

}CanIl_TpeTxMsgAttr;

/*!
* @brief Attributes for Periodical Rx CAN Message.
*/
typedef struct
{
	uint16 msgId;                                /* CAN Message ID. */
	CanIl_TcanChannel chn;                       /* which CAN channel this message belongs to. */
	CanIl_TrxMsgDiagStatus diagStatus;           /* message would be diagnosed or not. */
	uint8  dlc;                                  /* data length. */
	CanIl_TrxTimeoutMode  timeoutMode;           /* Mode for Rx timeout handling. */
	uint16 timeoutDuration;                      /* How long shall message be regarded as timeout for non-reception. */
	uint8 inGlobalRamIndex;                      /* For whether this frame is shared by CPU1 and CPU2.*/
	uint8  defaultValue[8];                      /* Default value for reception timeout. */
	uint8  *pilBuf;                              /* pointer to message 8 bytes data buffer of IL layer. */

}CanIl_TpeRxMsgAttr;

/*
***************************************************************************
* External variables declaration
****************************************************************************
*/
extern const CanIl_CanMsgRptCfg CanMsgRptCfg[CANIL_TOTAL_CAN_NETWORK_NUM] ;

extern const CanIl_TpeTxMsgAttr CanIl_CyclicTxMsgAttrTable[CANIL_MSG_IL_ID_TX_PE_NUM];

extern const CanIl_TpeRxMsgAttr CanIl_CyclicRxMsgAttrTable[CANIL_MSG_IL_ID_RX_PE_NUM];
"""

can_tx_message_header = """
/*!
* @brief IL Ids defines for all periodical Tx CAN message.
*/
typedef enum
{
/* CanIl_TpeTxMsgIlId: Code Generation starts here.*/

"""
can_tx_message_end = """
    CANIL_MSG_IL_ID_TX_PE_NUM
}CanIl_TpeTxMsgIlId;

"""

can_rx_message_header = """
/*!
* @brief IL Ids defines for all periodical Rx CAN message.
*/
typedef enum
{
/* CanIl_TpeTxMsgIlId: Code Generation starts here.*/

"""
can_rx_message_end = """
    CANIL_MSG_IL_ID_RX_PE_NUM
}CanIl_TpeRxMsgIlId;

"""

can_tx_extern_message_header = """
/*
****************************************************************************
* External variables declaration
****************************************************************************
*/
/* External variables declaration(TxMsg): Code Generation starts here.*/
"""

can_rx_extern_message_header = """
/* External variables declaration(RxMsg): Code Generation starts here.*/
"""

can_tx_extern_int_header = """
/*
****************************************************************************
* External routines declaration
****************************************************************************
*/
/* External routines declaration(IlPut): Code Generation starts here.*/
"""

can_rx_extern_int_header = """
/* External routines declaration(IlGet): Code Generation starts here.*/
"""

start_message = "#define\t\tCANIL_START_RX_MSG_OF_NETWORK_CHANNEL_ID_"
end_message  = "#define\t\tCANIL_END_RX_MSG_OF_NETWORK_CHANNEL_ID_"
note = "/* The start and end Rx message Ids for Can network Id "
pe_messgae = "CANIL_MSG_IL_ID_RX_PE_"
def write_message(target,can_nums,classify_all_files_rx_min_max,min_rx_msg_id,max_rx_msg_id,file,num_can):
    target.write(header)
    target.write("* @file  "+file+"\n")
    target.write("* @brief Internal configuration header file for CanIl module.\n")
    target.write("*\n")
    target.write(header2)
    data = datetime.now()
    target.write("* @CodeGenDate       "+data.strftime("%Y-%m-%d %H : %M : %S")+"\n")
    target.write(header3)
    target.write("\n")
    target.write("#ifndef CANIL_CFGINT_H\n")
    target.write("#define CANIL_CFGINT_H\n\n")
    target.write("#ifdef __cplusplus\n")
    target.write("extern \"C\" {\n")
    target.write("#endif\n")
    target.write("\n\n")
    target.write("/* Total CAN network Id number: Code Generation starts here.*/\n")
    target.write("#define CANIL_TOTAL_CAN_NETWORK_NUM       "+str(len(can_nums))+"U\n")
    target.write("\n"+"/* The start and end Rx message Il name of each CAN network Id: Code Generation starts here.*/\n")
    target.write("\n")
    i = 0
    count = 0
    while i < len(can_nums):
        if classify_all_files_rx_min_max[i][min_rx_msg_id] != "" and classify_all_files_rx_min_max[i][min_rx_msg_id] != "":
            target.write(note+str(count+1)+" ("+num_can[can_nums[i]]+") */\n")
            target.write(start_message+str(can_nums[i])+"\t\t"+pe_messgae+num_can[can_nums[i]]+"_"+classify_all_files_rx_min_max[i][min_rx_msg_id]+"\n")
            target.write(end_message+(str(can_nums[i]))+"\t\t"+pe_messgae+num_can[can_nums[i]]+"_"+classify_all_files_rx_min_max[i][max_rx_msg_id]+"\n")
            target.write("\n")
            count += 1
        i += 1

    target.write(message)
    target.write("\n\n\n")
    target.write("#ifdef __cplusplus\n")
    target.write("}\n")
    target.write("#endif  /* __cplusplus */\n\n")
    target.write("#endif /* CANIL_CFGINT_H */")
    target.write("\n")


message_s2 = """
/* Type mapping */
#define CanIlIf_FrameType                    Can_FrameType
#define CanIlIf_TXFrameType                  Can_FrameType
#define CanIlIf_TXFrameTypeOnlyCAN           Can_FrameType
"""

message_s = """
/* Other Functions: Code Generation starts here.*/
/* Once the specified test message is received, this function would be called. */
#define CanIlIf_TestEnabledMsgCallback()

/* Callback function just before data preparation for CAN Tx. */
#define CanIlIf_Ntf_BeforePrepareTxMsgData(txMsgIlId)

/* Callback function just after a successful transmission of CAN message. */
#define CanIlIf_Ntf_AfterSuccessfulTxMsg(txMsgIlId)

/* Required interface to suspend all interrupts. */
#define CanIlIf_SuspendAllInterrupts()		            Irq_SuspendAllInt()

/* Required interface to resume all interrupts. */
#define CanIlIf_ResumeAllInterrupts()		            Irq_ResumeAllInt()

/* Once the rx msg with diag atrribute "TRUE" is received, this function would be called. */
#define CanIlIf_Ntf_DiagRxMsgBeReceived(rxMsgIlId)		CanDiag_DiagRxMsgReceived((rxMsgIlId))


"""

def creat_cancfg(target,file,can_nums,find_tx,num_can):
    target.write(header)
    target.write("* @file  "+file+"\n")
    target.write("* @brief Required interface related header file for CanIl module.\n")
    target.write("*\n")
    target.write(header2)
    data = datetime.now()
    target.write("* @CodeGenDate       "+data.strftime("%Y-%m-%d %H : %M : %S")+"\n")
    target.write(header3)
    target.write("\n")
    target.write("#ifndef CANIL_CFGIF_H\n")
    target.write("#define CANIL_CFGIF_H\n\n")
    target.write("#ifdef __cplusplus\n")
    target.write("extern \"C\" {\n")
    target.write("#endif\n")
    target.write("\n\n")

    target.write(message_s2)
    target.write("\n")
    target.write("/* Service mapping */\n")
    target.write("/* CAN Tx Driver Functions: Code Generation starts here.*/\n")
    i = 0
    j = 0
    for nums in can_nums:
        if find_tx[i]:
            target.write("/* CAN Network Id: "+str(nums)+" for\t"+num_can[nums]+" */\n")
            target.write("#define CanIlIf_TxMsgCanNetId"+str(nums)+"(BufId, pMsgBuf)\t\t\t"+num_can[nums]+"_TxBuf((BufId), (pMsgBuf))\n")
            j += 1
            target.write("\n")
        i += 1
    target.write(message_s)
    target.write("#ifdef __cplusplus\n")
    target.write("}\n")
    target.write("#endif  /* __cplusplus */\n\n")
    target.write("#endif /* CANIL_CFGIF_H */")
    target.write("\n")

def Write_cfgext_message(target, file, classify_all_files, can_nums, num_can, order_can):
    target.write(header)
    target.write("* @file  "+file+"\n")
    target.write("* @brief Required interface related header file for CanIl module.\n")
    target.write("*\n")
    target.write(header2)
    data = datetime.now()
    target.write("* @CodeGenDate       "+data.strftime("%Y-%m-%d %H : %M : %S")+"\n")
    target.write(header3)
    target.write("\n")
    target.write("#ifndef CANIL_CFGEXT_H\n")
    target.write("#define CANIL_CFGEXT_H\n\n")
    target.write("#ifdef __cplusplus\n")
    target.write("extern \"C\" {\n")
    target.write("#endif\n")
    target.write("\n\n")

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","define")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","define")
            j += 1
        i += 1

    # channel 的定义，仅需要定义一次，所以，这里仅调用一次即可
    classify_all_files[0][0].wirte_tx_rx(target,"","", types="Channel_enum",order_can_list = order_can)

    target.write(can_tx_message_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx",types="can_message_enum")
            j += 1
        i += 1
    target.write(can_tx_message_end)

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","struct")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","data_struct")
            j += 1
        i += 1

    target.write(can_rx_message_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","can_message_enum")
            j += 1
        i += 1
    target.write(can_rx_message_end)

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","struct")
            j += 1
        i += 1


    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","data_struct")
            j += 1
        i += 1

    target.write(can_tx_extern_message_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","extern_int")
            j += 1
        i += 1

    target.write("\n")

    target.write(can_rx_extern_message_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","extern_int")
            j += 1
        i += 1

    target.write("\n")

    target.write(can_tx_extern_int_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","extern_tx_int")
            j += 1
        i += 1

    target.write("\n")

    target.write(can_rx_extern_int_header)
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","extern_rx_int")
            j += 1
        i += 1
    target.write("\n")
    target.write("#ifdef __cplusplus\n")
    target.write("}\n")
    target.write("#endif /* __cplusplus */\n\n")
    target.write("#endif /* CANIL_CFGEXT_H */")
    target.write("\n")

def Write_cfg_c_message(target, files, classify_all_files, can_nums, num_can, order_can, task_Period):
    target.write(header)
    target.write("* @file  "+files[3]+"\n")
    target.write("* @brief Configuration Implementation file for CanIl module.\n")
    target.write("*\n")
    target.write(header2)
    data = datetime.now()
    target.write("* @CodeGenDate       "+data.strftime("%Y-%m-%d %H : %M : %S")+"\n")
    target.write(header3)
    target.write("#include \"Std_Types.h\"\n")
    target.write("#include \"CanIl.h\"\n")
    i = 0
    while i < len(files) - 2:
        target.write("#include "+"\""+files[i]+"\"\n")
        i +=1

    can_repeat_message = []
    i = 0
    while i < len(classify_all_files):
        j = 0
        count = 0
        flag = False
        can_repeat_message.append("\t{0, (CanIl_RepeatMsgMaskInfo *)0x00000000ul},\n")
        while j < len(classify_all_files[i]):
            if len(classify_all_files[i][j].M_groups) > 0:
                if len(classify_all_files[i][j].M_groups) >= 2:
                    print("[Error] check the dbc error\n")
                    return
                else:
                    if flag == False:
                        target.write("\n/*CAN ID list for repeat message*/")
                        classify_all_files[i][j].list_repeat_message_name = "CanIlRptMsgMaskInfo_Ch"+can_nums[i]
                        can_repeat_message[i] = "\t{1, (CanIl_RepeatMsgMaskInfo *)&"+"CanIlRptMsgMaskInfo_Ch"+can_nums[i]+"["+str(count)+"]"+"},\n"
                        target.write("\nconst CanIl_RepeatMsgMaskInfo CanIlRptMsgMaskInfo_Ch"+can_nums[i]+"["+str(count+1)+"]"+" = \n")
                        target.write("{\n")
                        flag = True
                    singal = classify_all_files[i][j].M_groups[0]
                    sbit = int(singal.sbit)
                    lens = int(singal.len)
                    a = []
                    z = 0
                    while z < 64:
                        a.append('0')
                        z += 1
                    while int(lens) > 0:
                        a[sbit] = '1'
                        sbit -= 1
                        lens -= 1
                    s = ""
                    a.reverse()
                    z = 0
                    while z < 64:
                        s += a[z]
                        z += 1
                    s = "".join(list(s))
                    target.write("\t{"+str(hex(int(classify_all_files[i][j].id)))+"u,\t"+'0x{:02X}'.format(int(s,2))+"u,\t\t0u"+"},\n")
            j += 1
        if j == len(classify_all_files[i]) and flag == True:
            target.write("};\n")
        i += 1

    target.write("\n")

    target.write("/*CAN repeat message configuration*/")
    target.write("\nconst CanIl_CanMsgRptCfg CanMsgRptCfg"+"[CANIL_TOTAL_CAN_NETWORK_NUM]"+" = \n")
    target.write("{\n")
    i = 0
    while i < len(classify_all_files):
        target.write(can_repeat_message[i])
        i += 1
    target.write("};\n")

    target.write("\n")

    target.write("\n\n/*v Beginning of Tx Messages definition. v*/\n\n")
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","extern_int_back")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Both","extern_int_back")
            j += 1
        i += 1

    init_message = "{\t0x00,\t0x00,\t0x00,\t0x00,\t0x00,\t0x00,\t0x00,\t0x00}"
    target.write("/* External variable definition(TxMsgTable): Code Generation starts here.*/\n")
    target.write("/* Msg ID ,\t\t\tMsg Purpose Type,\t\t\tMsg Schedule Type,\t\t\tChannel Id,\t\t\tDlc,\t\t\tPeriod,\t\t\tOffset,\t\t\tPeriodFixed,\t\t\tPeriod2,\t\t\tOffset2,\t\t\tGlobal RAM index,\t\t\tCANFD Frame,\t\t\tInitial value of bytes,\t\t\t\t\tpointer to msg IL data buffer.*/\n")
    target.write("const CanIl_TpeTxMsgAttr CanIl_CyclicTxMsgAttrTable[CANIL_MSG_IL_ID_TX_PE_NUM] = \n")
    target.write("{\n")
    tx_count_no_group = 0
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            if classify_all_files[i][j].is_period == True:
                period_t = int(classify_all_files[i][j].period) // int(task_Period)
                period = str(period_t)+"U"
            else:
                period = "0U"

            if (classify_all_files[i][j].tx_rx == "Tx" or classify_all_files[i][j].tx_rx == "Both" ) and classify_all_files[i][j].need_group == False:
                target.write("\t{ 0x"+hex(classify_all_files[i][j].id)[2:].upper()+"U"+\
                             ",\tCANIL_TX_TYPE_VISIBLE"+",\tCANIL_TX_SCH_TYPE_OS"+",\t\t\tCANIL_CHN_ID_"+\
                             order_can[i]+",\t\t\t8U"+",\t\t\t\t"+period+",\t\t\t\t"+str(tx_count_no_group%10)+",\t\t\t\tTRUE"+",\t\t\t\t\t\t4U"+",\t\t\t\t\t0U"+\
                             ",\t\t\t\t\t\t255U"+",\t\t\t\t\t\t0U  ,"+init_message+",\t((uint8*)(&"+"TX_"+num_can[can_nums[i]]+"_"+classify_all_files[i][j].name.upper()+\
                             "."+classify_all_files[i][j].name.upper()+"))"+" },\n")
                tx_count_no_group += 1
            if (classify_all_files[i][j].tx_rx == "Tx" or classify_all_files[i][j].tx_rx == "Both" )and classify_all_files[i][j].need_group == True:
                z = 0
                while z < len(classify_all_files[i][j].groups_id):
                    target.write("\t{ 0x"+hex(classify_all_files[i][j].id)[2:].upper()+"U"+\
                                 ",\tCANIL_TX_TYPE_VISIBLE"+",\tCANIL_TX_SCH_TYPE_OS"+",\t\t\tCANIL_CHN_ID_"+\
                                 order_can[i]+",\t\t\t8U"+",\t\t\t\t"+period+",\t\t\t\t"+str(z%10)+",\t\t\t\tTRUE"+",\t\t\t\t\t\t4U"+",\t\t\t\t\t0U"+\
                                 ",\t\t\t\t\t\t255U"+",\t\t\t\t\t\t0U  ,"+init_message+",\t((uint8*)(&"+"TX_"+num_can[can_nums[i]]+"_"+classify_all_files[i][j].name.upper()+\
                                 "_GROUP"+str(classify_all_files[i][j].groups_id[z])+"."+classify_all_files[i][j].name.upper()+\
                                 "_GROUP"+str(classify_all_files[i][j].groups_id[z])+"))"+" },\n")
                    z += 1
            j += 1
        i += 1
    target.write("};\n")
    target.write("\n/*^ End of Tx Messages definition. ^*/\n")

    target.write("\n\n/*v Beginning of Rx Messages definition. v*/\n\n")
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","extern_int_back")
            j += 1
        i += 1
    
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Both","extern_int_back")
            j += 1
        i += 1

    target.write("/* External variable definition(RxMsgTable): Code Generation starts here.*/\n")
    target.write("/* Msg ID,\t\tChannel Id,\t\t\tDiagStatus,\t\t\t\t\tDlc,\t\t\t\t\tTimeout Mode,\t\t\t\t\tTimeout Period,\t\t\t\t\tGlobal RAM index,\t\t\t\t\tDefault value of bytes,\t\t\t\t\tpointer to msg IL data buffer.*/\n")
    target.write("const CanIl_TpeRxMsgAttr CanIl_CyclicRxMsgAttrTable[CANIL_MSG_IL_ID_RX_PE_NUM] = \n")
    target.write("{\n")
    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            if classify_all_files[i][j].is_period == True:
                period_t = int(classify_all_files[i][j].period) // int(task_Period)
                period = str(period_t)+"U"
            else:
                period = "0U"

            if (classify_all_files[i][j].tx_rx == "Rx" or classify_all_files[i][j].tx_rx == "Both") and classify_all_files[i][j].need_group == False:
                target.write("\t{ 0x"+hex(classify_all_files[i][j].id)[2:].upper()+"U"+\
                             ",\tCANIL_CHN_ID_"+order_can[i]+",\t\tCANIL_RX_DIAG_FALSE"+",\t\t\t8U"+",\t\t\tCANIL_RX_TM_KEEP_LAST"+",\t\t\t\t"+period+",\t\t\t\t\t\t\t255U,\t\t"+init_message+",\t((uint8*)(&"+"RX_"+num_can[can_nums[i]]+"_"+classify_all_files[i][j].name.upper()+\
                             "."+classify_all_files[i][j].name.upper()+"))"+" },\n")
            if (classify_all_files[i][j].tx_rx == "Rx" or classify_all_files[i][j].tx_rx == "Both") and classify_all_files[i][j].need_group == True:
                z = 0
                while z < len(classify_all_files[i][j].groups_id):
                    target.write("\t{ 0x"+hex(classify_all_files[i][j].id)[2:].upper()+"U"+\
                                ",\tCANIL_CHN_ID_"+order_can[i]+",\t\tCANIL_RX_DIAG_FALSE"+",\t\t\t8U"+",\t\t\tCANIL_RX_TM_KEEP_LAST"+",\t\t\t\t"+period+",\t\t\t\t\t\t\t255U,\t\t"+init_message+",\t((uint8*)(&"+"RX_"+num_can[can_nums[i]]+"_"+classify_all_files[i][j].name.upper()+\
                                 "_GROUP"+str(classify_all_files[i][j].groups_id[z])+"."+classify_all_files[i][j].name.upper()+\
                                 "_GROUP"+str(classify_all_files[i][j].groups_id[z])+"))"+" },\n")
                    z += 1
            j += 1
        i += 1
    target.write("};\n")
    target.write("\n/*^ End of Rx Messages definition. ^*/\n")

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Rx","extern_rx_int_back")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Both","extern_rx_int_back")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Tx","extern_tx_int_back")
            j += 1
        i += 1

    i = 0
    while i < len(classify_all_files):
        j = 0
        while j < len(classify_all_files[i]):
            classify_all_files[i][j].wirte_tx_rx(target,num_can[can_nums[i]],"Both","extern_tx_int_back")
            j += 1
        i += 1
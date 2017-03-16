# coding:utf-8
# designer:Zhoulang
import os
from mod_config import get_config
import _mssql
from wechatpy.enterprise import WeChatClient
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.enterprise.client.api import WeChatMessage
from wechatpy.enterprise.client.api import WeChatMedia

wxset = {'host': get_config("wx", "host"), 'database': get_config("wx", "database"), 'user': get_config("wx", "user"),
         'pwd': get_config("wx", "pwd"), 'port': get_config("wx", "port"), 'customstr': get_config("wx", "customstr"),
         'Secret': get_config("wx", "Secret"), 'TOKEN': get_config("wx", "TOKEN"),
         'EncodingAESKey': get_config("wx", "EncodingAESKey"), 'CorpId': get_config("wx", "CorpId"),
         'agent_id': get_config("wx", "agent_id"), 'tm': get_config("wx", "tm"),
         'msg_limit': get_config("wx", "msg_limit")}

df_p = os.path.dirname(os.path.realpath(__file__)) + '\\config.py'
root_url = ''
# 数据库连接
try:
    conn = _mssql.connect(server=wxset['host'], user=wxset['user'], port=wxset['port'],
                          password=wxset['pwd'], database=wxset['database'], charset='utf8')
except _mssql.MssqlDatabaseException:
    print("数据库连接错误！")

try:
    client = WeChatClient(wxset['CorpId'], wxset['Secret'])
except InvalidCorpIdException as e:
    print("wx client出错: %s" % e)

try:
    wechatmessage = WeChatMessage(client)
except InvalidCorpIdException as e:
    print("wx message出错: %s" % e)

try:
    wechatmedia = WeChatMedia(client)
except InvalidCorpIdException as e:
    print("wx media出错: %s" % e)

dic_sql = {
    # 更新提醒记录状态语句
    'up_flag': "UPDATE [wxtx] SET [flag] = '1' WHERE [id] IN %s ",
    # 查询待发送语句
    'sl_000': '''
    SELECT 	[wxtx].[cDate],
		[wxtx].[context],
		wxtx.pic,
		wxtx.fh,
		wxtx.p_des,
		[wxtx].[flag] ,
		[wxtx].[id],
		wxtx.tp,
		[wxtx].[toAgent],
		[wxtxl].[账号]
    From [wxtx],[wxtxl]
    WHERE [wxtx].[toUser] = [wxtxl].[姓名]
    and isnull(wxtx.flag,'') = ''
    ''',
    # 查询文本提醒语句
    'sl_001': '''
    SELECT 	[wxtx].[cDate],
		[wxtx].[context],
		[wxtx].[flag] ,
		[wxtx].[id],
		[wxtx].[toAgent],
		[wxtxl].[账号]
    From [wxtx],[wxtxl]
    WHERE [wxtx].[toUser] = [wxtxl].[姓名]
    and isnull(wxtx.flag,'') = ''
    and isnull(pic,'')=''
	and ISNULL(fh, '')=''
    ''' ,
    # 查询图文语句
    'sl_002': '''
    SELECT
		[wxtx].[cDate],
		[wxtx].[context],
		[wxtx].[flag] ,
		[wxtx].[id],
		[wxtx].[toAgent],
		[wxtxl].[账号]
    From [wxtx],[wxtxl]
    WHERE [wxtx].[toUser] = [wxtxl].[姓名]
    and isnull(wxtx.flag,'') = ''
    AND isnull([pic],'') <>''
    and isnull(context,'')<>''
    and ISNULL(fh, '')=''
    ''',
    # 查询自定义查询语句
    'sl_003': "SELECT cmd,cmdstr,[参数个数],[格式提醒],[权限] FROM [dbo].[wxcx] where cmd = %s",

    # 查询待发送图片、文件语句,可替代sl_001语句
    'sl_004': """
SELECT f.fileType,
(isnull(f.folderPath,'')+f.RelaFolder+f.PhyFileName) AS path,
w.flag,
w.toUser,
w.toAgent,
w.content,
w.id,
w.pic,
w.fh,
w.p_des,
w.tp,
t.[账号]

FROM
dbo.ES_v_CaseLink AS f
RIGHT JOIN dbo.wxtx AS w ON w.ExcelServerRCID = f.rcId ,
dbo.wxtxl AS t
WHERE
isnull(w.flag,'') = '' AND
w.toUser = t.[姓名]""",

}

ftime = "%Y-%m-%d %H:%M:%S"

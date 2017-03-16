# coding:utf-8
# designer:Zhoulang
import time
import re
import math
from config import *

ids = []


# 发送主动消息函数
def wx_tx():
    while True:
        try:
            conn.execute_query(dic_sql['sl_004'])
            null = ['', None]
            print('%s %s :微信扫描中--->' % (time.strftime(ftime, time.localtime()), wxset['customstr']))
            for rw in conn:
                # 发送文本消息
                if rw['tp'] == '文本消息':
                    if wechatmessage.send_text(rw['toAgent'], rw['账号'], rw['content']).get('errmsg') == 'ok':
                        wait_ids(rw['id'])
                # 发送图片消息
                elif rw['tp'] == '图片消息':
                    # 发送图片消息,需要先上传临时素材获取media_id，然后在发送
                    try:
                        with open(rw['path']) as f:
                            md_id = wechatmedia.upload('image', f)
                            if wechatmessage.send_image(rw['toAgent'], rw['账号'], md_id.get('media_id')).get('errmsg') == 'ok':
                                wait_ids(rw['id'])
                    except Exception as e:
                        print(e)

                # 发送图文消息
                elif rw['tp'] == '图文消息':
                    pic_url = root_url+'wxtx/<id>'
                    if rw['pic'] not in null:
                        try:
                            with open(rw['path']) as f:
                                pic_url = wechatmedia.upload_mass_image(f)
                        except Exception as e:
                            print(e)
                    # TODO url暂时写死
                    my_article = [{'title': rw['context'], 'description': rw['p_des'],
                       'image': pic_url, 'url': root_url+'wxtx/<id>'}]
                    if wechatmessage.send_articles(rw['toAgent'], rw['账号'], my_article).get('errmsg') == 'ok':
                        wait_ids(rw['id'])
                # 发送文件消息
                elif rw['tp'] == '文件消息':
                    try:
                        with open(rw['path']) as f:
                            md_id = wechatmedia.upload('file', f)
                            if md_id.get('media_id') != '':
                                if wechatmessage.send_file(rw['toAgent'], rw['账号'], md_id.get('media_id')).get('errmsg') == 'ok':
                                    wait_ids(rw['id'])
                    except Exception as e:
                        print(e)
        except Exception as e:
            print(e)
        finally:
            if len(ids) == 0:
                pass
            else:
                conn.execute_query(dic_sql['up_flag'], (tuple(ids),))
            time.sleep(int(wxset['tm']))


def wait_ids(i):
    print('id:', i, ' 发送成功！')
    ids.append(i)


def pd_msg(tp, content):
    # 用户发送的文本消息
    if tp == 'text':
        if re.findall('\?|\？', content, re.X) and re.findall('[0-9]{4}', content, re.X):
            # 从数据库中匹配命令提示
            sql = "SELECT [格式提醒] FROM [dbo].[wxcx] where cmd = %s "
            conn.execute_query(sql, re.findall('[0-9]{4}', content, re.X)[0])
            s = [r for r in conn][0]['格式提醒']

        elif re.findall('\?|\？', content, re.X):
            sql = "SELECT cmdname as [命令] FROM [dbo].[wxcx] ORDER BY cmd ASC"

            conn.execute_query(sql)

            s = []
            for rw in conn:
                d = {k: v for k, v in rw.items() if isinstance(k, str) == True}
                d_sort = sorted(d.items(), key=lambda item: item[0])
                s.append(d_sort)
            s = wxset['customstr']+'\n【微信命令说明】\n 命令: ? -->获取帮助；\n 命令: ?4位数字(?2001) -->' \
                '获取当前命令的帮助；\n ↓↓↓命令清单如下↓↓↓ \n' + ls_to_str(s)
        else:
            if re.findall('p', content, re.I):
                i = re.split('p', content, re.I)[-1]
                s = wxset['customstr']+'\n↓↓↓查询结果如下↓↓↓ \n' + ls_to_str(db_super_query(content), int(i))
            else:
                ls = ls_to_str(db_super_query(content))
                if isinstance(ls, list):
                    s = ls
                else:
                    s = wxset['customstr']+'\n↓↓↓查询结果如下↓↓↓ \n' + ls
    # 用户发送的图片消息
    elif tp == 'image':
        pass
    else:
        s = '请输入正确的文本信息.'
    return s


# 加工msg消息，返回查询字典
def jg_msg(msg):
    ls_msg = re.split('\W', msg, 1, re.X)
    if ls_msg:
        sql = "SELECT cmd,cmdstr,[参数个数],[格式提醒],[权限] FROM [dbo].[wxcx] where cmd = %s"
        conn.execute_query(sql, ls_msg[0])
        ds1 = []
        for r in conn:
            ds1.append(r)
        ds = ds1[0]
        ds['content'] = re.split(',|，', ls_msg[1], 1, re.X)[0]
        # print('ds', ds)
        return ds


# 数据库自定义查询 s:sql查询语句字典,返回一个列表
def db_super_query(s):
    cmd = jg_msg(s).get('cmd')
    cmdstr = jg_msg(s).get('cmdstr')
    content = jg_msg(s).get('content')
    print('cmdstr:', cmdstr)
    print('content:', content)

    conn.execute_query(cmdstr, content)
    custom_ls = []
    for rw in conn:
        # print(rw)
        d = {k: v for k, v in rw.items() if isinstance(k, str) == True}
        d_sort = sorted(d.items(), key=lambda item: item[0])
        custom_ls.append(d_sort)
    # print('custom_ls1:', custom_ls1)
    if custom_ls:
        return custom_ls
    else:
        custom_ls = [[('格式提醒', '\n'+jg_msg(s).get('格式提醒'))]]
        return custom_ls


# 列表转换成文本 d:查询页数,10条/页,默认第一页,列表内容太多时会自动返回列表,用图文进行回复
def ls_to_str(ls, d=1):
    # print('len(ls):', len(ls))

    if wxset["msg_limit"] == '1':
        s1 = ''
        s = ''
        for l in ls:
            s = ''
            for l2 in l:
                s = s + str(l2[0]) + ': ' + str(l2[1]) + '\n'
            s1 += '\n' + s
        print('len s1:', len(s1))
        if len(s1) > 2000:
            # TODO 图文回复-->list
            return ls
        else:

            if len(s1) < 1300:
                print('s1<1300:', len(s1))
                return s1
            else:
                if d == 1:
                    ls2 = ls[:10]
                else:
                    ls2 = ls[(d-1)*10:d*10+1]
                s1 = ''
                for l in ls2:
                    s = ''
                    for l2 in l:
                        s = s + str(l2[0]) + ': ' + str(l2[1]) + '\n'
                    s1 += '\n' + s
                print('s1>1300:', len(s1))
                return s1 + '\n[第 ' + str(d) + '页/共 ' + str(math.ceil(len(ls)/10)) + ' 页]'

    else:
        return ls

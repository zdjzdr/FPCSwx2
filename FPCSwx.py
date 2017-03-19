from flask import Flask, request, abort, render_template, flash, url_for, redirect
from mod_config import set_config
from config import *
from wechatpy.enterprise import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.enterprise import create_reply, parse_message
from FPCSdb import wx_tx, pd_msg, db_super_query, events_upimage
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
import threading
import collections

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'fpcs#welcomeyou'


class setForm(FlaskForm):
    fld_host = StringField("数据库地址：", validators=[DataRequired()])
    fld_database = StringField("数据库名称：", validators=[DataRequired()])
    fld_user = StringField("数据库用户：", validators=[DataRequired()])
    fld_pwd = PasswordField("数据库密码：", validators=[DataRequired()])
    fld_port = StringField("数据库端口(默认:1433)：", validators=[DataRequired()], default=1433)
    fld_customstr = StringField("微信自定义提醒语句：", default="[FPCS系统提醒]")
    fld_secret = StringField("微信Secret：", validators=[DataRequired()])
    fld_token = StringField("微信TOKEN：", validators=[DataRequired()])
    fld_aeskey = StringField("微信EncodingAESKey：")
    fld_corpid = StringField("微信CorpId：", validators=[DataRequired()])
    fld_agent_id = StringField("微信应用ID（默认：0)：", default=0, validators=[DataRequired()], description="默认为0，即 企业小助手")
    fld_tm = StringField("微信提醒间隔时间(秒)：", default=60, validators=[DataRequired()])
    fld_limit = StringField("消息是否分页显示：", default=1, description="两个选项[0:不分页；1：分页,默认为：1]")
    submit = SubmitField("保存配置")


# wx消息(回复)处理函数
# (c:加解密函数 r:post过来的内容 s:sinnature t:timesatmp n: nonce)
def rep(c, r, s, t, n):
    try:
        # 解密消息
        msg_xml = c.decrypt_message(r, s, t, n)
        print("msg_xml:", msg_xml)
    except (InvalidSignatureException, InvalidCorpIdException):
        abort(403)
    # XML---> Dic
    msg = parse_message(msg_xml)
    print("解密后的msg:", msg)
    reply = ""
    if msg.type == 'text':
        # 回复消息
        print('msg.content:', msg.content)
        reps = pd_msg(msg.type, msg.content)
        # 如果返回的是一个列表用图文回复
        if isinstance(reps, list):
            articles = [{'title': '>>>点击查看更多内容>>>',
                         'description': '当前查询的内容过多，请点击下面的【查看原文】...',
                         'url': request.url_root + 'morerep?content=' + msg.content
                         }]
            reply = create_reply(articles, msg)
        else:
            reply = create_reply(reps, msg)
            # 事件消息处理
    elif msg.type == 'event':
        # 图片上传事件
        reply = create_reply(events_upimage(msg), msg)
    elif msg.type == 'image':
        if msg.media_id:
            response = wechatmedia.download(msg.media_id)
            with open('test.jpg', 'wb') as f:
                for chunk in response.iter_content(2048):
                    f.write(chunk)
                print("文件保存成功！")
    # 加密消息
    return c.encrypt_message(reply, n, t)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/cfg', methods=['GET', 'POST'])
def cfg():
    form = setForm()
    if request.method == 'GET':
        form.fld_host.data = wxset['host']
        form.fld_user.data = wxset['user']
        form.fld_pwd.data = wxset['pwd']
        form.fld_database.data = wxset['database']
        form.fld_port.data = wxset['port']
        form.fld_corpid.data = wxset['CorpId']
        form.fld_secret.data = wxset['Secret']
        form.fld_aeskey.data = wxset['EncodingAESKey']
        form.fld_token.data = wxset['TOKEN']
        form.fld_agent_id.data = wxset['agent_id']
        form.fld_limit.data = wxset['msg_limit']
        form.fld_tm.data = wxset['tm']
        form.fld_customstr.data = wxset["customstr"]
    else:
        if form.validate_on_submit():
            wx_dic = {'host': form.fld_host.data, 'database': form.fld_database.data,
                      'user': form.fld_user.data, 'pwd': form.fld_pwd.data, 'port': form.fld_port.data,
                      'customstr': form.fld_customstr.data, 'Secret': form.fld_secret.data,
                      'TOKEN': form.fld_token.data,
                      'EncodingAESKey': form.fld_aeskey.data, 'CorpId': form.fld_corpid.data,
                      'agent_id': form.fld_agent_id.data, 'tm': form.fld_tm.data, 'msg_limit': form.fld_limit.data}

            set_config('wx', wx_dic)
            flash("保存配置文件成功！请重新运行服务器。", 'success')
    return render_template('cfg.html', form=form)


@app.route('/morehelp')
def morehelp():
    sql = "SELECT cmd as 命令,SUBSTRING(cmdname,7,500) as [命令名称] ,格式提醒 as 示例 FROM [dbo].[wxcx] ORDER BY cmd ASC"
    conn.execute_query(sql)
    # rw = [r for r in conn]
    # print(conn)
    # print('rw:', rw)
    return render_template('morehelp.html', conn=conn)


@app.route('/morerep', methods=['GET', 'POST'])
def morerep():
    if request.method == 'GET':
        content = request.args.get('content')
        ls = db_super_query(content)
        ds = []
        if ls:
            for d in ls:
                dic1 = collections.OrderedDict()
                for d2 in d:
                    dic1[d2[0]] = d2[1]
                ds.append(dic1)
    return render_template('morerep.html', ds=ds)


@app.route('/wechat', methods=['GET', 'POST'])
def wx():
    sinnature = request.args.get('msg_signature', '')
    timesatmp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')
    crypto = WeChatCrypto(wxset['TOKEN'], wxset['EncodingAESKey'], wxset['CorpId'])
    if request.method == 'GET':
        echo_str = request.args.get('echostr', '')
        try:
            # 验证URL有效性
            echo_str = crypto.check_signature(sinnature, timesatmp, nonce, echo_str)
        except InvalidSignatureException:
            abort(403)
        return echo_str
    else:

        return rep(crypto, request.data, sinnature, timesatmp, nonce)


if __name__ == '__main__':
    # t = threading.Thread(target=wx_tx)
    # t.start()
    app.run(debug=True)

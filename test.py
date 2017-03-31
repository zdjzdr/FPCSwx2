def send_message(data, signature, timesatmp, nonce):
	# ①解密消息
	msg_xml = crypto.decrypt_message(data, signature, timesatmp, nonce)
	# ②xml2Dict
	msg = parse_message(msg_xml)
	# ③调用消息处理函数,返回待发送的数据
	reps = pd_msg(msg.type, msg.content)
	# ④根据返回的数据类型决定发送的数据格式（文本消息或者图文消息）
	# ⑤调用回复函数
	reply = create_reply('hhah', msg)
	# ⑥待回复的消息加密发送
	return crypto.encrypt_message(reply, nonce, timesatmp)

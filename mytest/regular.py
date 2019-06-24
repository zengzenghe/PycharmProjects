import re
reg_str = '<.*?>'
sent = """<img src="https://mmbiz.qpic.cn/mmbiz_gif/8I0xSIL7mRF140bmxFLuRnHia0UXwqzNMbpVswH72Z5G7B1eJAnxE6MMcxfEoJ5TprbECFnxAwIuXeRvRicMic8Pg/640?wx_fmt=gif" align="center"/>
<img src="https://mmbiz.qpic.cn/mmbiz_png/kYOOKdXmicxlCpJZsIINmHiaiawo7KbIgff4ibVP3RSY7dnKqU1qdCKibXYhKHKT6QrbiaSnJOx2k6MyY6AALiaL6Q1bA/640?" align="center"/>"""
sent = re.sub(reg_str, '', sent)
print(sent)
# coding:GB18030

"""
��http://life.main.com/xingming.asp��ַ���������Ա������Զ��ύ��������ȡ���ҳ���еķ������

Created on 2016��10��23��

@author: crazyant.net
""" 

import urllib
import urllib2
from bs4 import BeautifulSoup 
import re
import sys
import threading
import time
import threadpool

# from main import user_config
# from main import sys_config
import user_config
import sys_config

reload(sys) 
sys.setdefaultencoding("GB18030")

curr_idx = 0
all_count = 0
fout = None

def get_name_postfixs():
    """�����Ƿ�ʹ�õ��ֺ��û����õ��Ա��������ȡ���е������б�"""

    target_name_postfixs = set()
    
    # �Ƿ��е�������
    has_limit_word = False
    limit_word = user_config.setting["limit_world"]
    if limit_word is not None and len(limit_word) > 0:
        has_limit_word = True
        
    if has_limit_word:
        if user_config.setting["sex"] == "��":
            fpath_input = sys_config.FPATH_DICTFILE_BOYS_SINGLE
        elif user_config.setting["sex"] == "Ů":
            fpath_input = sys_config.FPATH_DICTFILE_GIRLS_SINGLE
        
        print "has limit word, fpath=%s" % fpath_input
        
        for line in open(fpath_input):
                iter_name = str(line).strip()
                target_name_postfixs.add("%s%s" % (limit_word, iter_name))
    else:
        if user_config.setting["sex"] == "��":
            fpath_input = sys_config.FPATH_DICTFILE_BOYS_DOUBLE
        elif user_config.setting["sex"] == "Ů":
            fpath_input = sys_config.FPATH_DICTFILE_GIRLS_DOUBLE

        for line in open(fpath_input):
                iter_name = str(line).strip()
                target_name_postfixs.add(iter_name)
    
    return target_name_postfixs


def compute_name_score(name_postfix):
    """���ýӿڣ�ִ�м��㣬���ؽ��"""

    result_data = {}
    params = {}
    
    # �������ͣ�0��ʾ������1��ʾũ��
    params['data_type'] = "0"
    params['year'] = "%s" % str(user_config.setting["year"])
    params['month'] = "%s" % str(user_config.setting["month"])
    params['day'] = "%s" % str(user_config.setting["day"])
    params['hour'] = "%s" % str(user_config.setting["hour"])
    params['minute'] = "%s" % str(user_config.setting["minute"])
    params['pid'] = "%s" % str(user_config.setting["area_province"])
    params['cid'] = "%s" % str(user_config.setting["area_region"])
    # ϲ�����У�0��ʾ�Զ�������1��ʾ�Զ�ϲ����
    params['wxxy'] = "0"
    params['xing'] = "%s" % (user_config.setting["name_prefix"])
    params['ming'] = name_postfix
    # ��ʾŮ��1��ʾ��
    if user_config.setting["sex"] == "��":
        params['sex'] = "1"
    else:
        params['sex'] = "0"
        
    params['act'] = "submit"
    params['isbz'] = "1"
    
    # for k, v in params.items():
    #    print k, v
    
    post_data = urllib.urlencode(params)
    req = urllib2.urlopen(sys_config.REQUEST_URL, post_data)
    content = req.read()
    
    soup = BeautifulSoup(content, 'html.parser', from_encoding="GB18030")
    full_name = get_full_name(name_postfix)
    
    # print soup.find(string=re.compile(u"�����������"))
    for node in soup.find_all("div", class_="chaxun_b"):
        node_cont = node.get_text()
        if u'�����������' in node_cont:
            name_wuge = node.find(string=re.compile(u"�����������"))
            result_data['wuge_score'] = name_wuge.next_sibling.b.get_text()
        
        if u'������������' in node_cont:
            name_wuge = node.find(string=re.compile(u"������������"))
            result_data['bazi_score'] = name_wuge.next_sibling.b.get_text()
    
    result_data['total_score'] = float(result_data['wuge_score']) + float(result_data['bazi_score'])
    result_data['full_name'] = full_name
    return result_data
    

def compute_and_writefile(name_postfix):
    try:
        global fout
        name_data = compute_name_score(name_postfix)
        write_to_file(fout, name_data)
    except Exception as e:
        print 'error, ', e, name_postfix

def get_full_name(name_postfix):
    return "%s%s" % ((user_config.setting["name_prefix"]), name_postfix)


lock = threading.Lock()
def write_to_file(fout, name_data):
    lock.acquire()
    global curr_idx, all_count
    curr_idx += 1
    print "%d/%d" % (curr_idx, all_count),
    print "\t".join((name_data['full_name'],
                     "������������=" + str(name_data['bazi_score']),
                     "�����������=" + str(name_data['wuge_score']),
                     "�ܷ�=" + str(name_data['total_score'])
                     ))
    fout.write(name_data['full_name'] + "\t" 
               + str(name_data['bazi_score']) + "\t" 
               + str(name_data['wuge_score']) + "\t" 
               + str(name_data['total_score']) + "\n")
    lock.release()

def process(output_fpath):
    """���㲢�ҽ����������ļ�"""

    global fout
    # ����ļ�·��
    fout = open(output_fpath, "w")
    # ������п��õ������б�
    all_name_postfixs = get_name_postfixs()
    
    global all_count
    all_count = len(all_name_postfixs)
     
    pool = threadpool.ThreadPool(50) 
    requests = threadpool.makeRequests(compute_and_writefile, all_name_postfixs) 
    [pool.putRequest(req) for req in requests] 
    pool.wait()  

    fout.flush()
    fout.close()


if __name__ == "__main__":
    print "begin................................"
    output_fpath = "./outputs/%s" % user_config.setting["output_fname"]
    process(output_fpath)
    print "over................................"


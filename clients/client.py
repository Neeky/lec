#! /usr/bin/env python3
#! -*- encoding: utf8 -*-

import configparser,argparse,requests,bs4,json,logging,sys,os
logging.basicConfig(level = logging.INFO)

def listLogFile(path='./'):
    for filename in os.listdir(path):
        name = os.path.join(path,filename)
        if os.path.isfile(name):
            yield name

def sysbenchLogParser(file_full_path):
    logging.info("start parser {}".format(file_full_path))
    file_name = os.path.basename(file_full_path)
    file_name = file_name.replace('.log','')
    #oltp_update_index#autocommit#0#1
    oltp,variable_name,vairable_value,parallels = file_name.split('#')
    #logging.info("oltp={} variable_name={} vairable_value={} parallels={}".format(oltp,variable_name,vairable_value,parallels))
    with open(file_full_path) as log_file:
        for line in log_file:
            if 'transactions:' in line:
                *_,transactions = line.split('(')
                transactions,*_ = transactions.split('per')
                transactions = int(float(transactions))
            if 'queries:' in line:
                *_,queries = line.split('(')
                queries,*_ = queries.split('per')
                queries = int(float(queries))
    tps = transactions + queries
    #logging.info("tps={}".format(tps))
    result = {'oltp_name':oltp,'parallels':parallels,'scores':tps,
            'variable_name':variable_name,'variable_value':vairable_value}
    logging.info("{}".format(result))
    return result

def tableKVS(vks):
    """表格化打印命令行
    """
    for k,v in vks.items():
        logging.info("{0:>20s} = {1:<60s}".format(k,v))

def submitData(data):
    session = requests.Session()
    r = session.get(data['target_url'])
    soup = bs4.BeautifulSoup(r.text,'html.parser')
    csrfmiddlewaretoken = soup.find('input',type='hidden')
    token=csrfmiddlewaretoken['value']
    data.update({'csrfmiddlewaretoken':token})
    r = session.post(data['target_url'],data=data)
    logging.info('提交动作执行完成')

def hardwareCreate(args):
    """创建hardware对象
    """
    logging.info("进入hardware对象创建流程")
    logging.info("准备读取配置文件 {}".format(args.defaults_file))
    config = configparser.ConfigParser()
    config.read(args.defaults_file)
    hardware = dict(config['hardware'])
    hardware.update({'target_url':config['default']['hardwarecreate']})
    #打印hardware中的内容
    tableKVS(hardware)
    #准备提交数据
    logging.info('准备将数据提交到 {0}'.format(hardware['target_url']))
    submitData(hardware)
    #session = requests.Session()
    #r = session.get(hardware['target_url'])
    #soup = bs4.BeautifulSoup(r.text,'html.parser')
    #csrfmiddlewaretoken = soup.find('input',type='hidden')
    #token=csrfmiddlewaretoken['value']
    #hardware.update({'csrfmiddlewaretoken':token})
    #r = session.post(hardware['target_url'],data=hardware)
    #logging.info('提交动作执行完成'.format(hardware['target_url']))

def softwareCreate(args):
    """创建software对象
    """    
    logging.info("进入software对象创建流程")
    logging.info("准备读取配置文件 {}".format(args.defaults_file))
    config = configparser.ConfigParser()
    config.read(args.defaults_file)
    software = dict(config['software'])
    software.update({'hardware_name':config['hardware']['name']})
    software.update({'target_url':config['default']['softwarecreate']})
    tableKVS(software)
    logging.info('准备将数据提交到 {0}'.format(software['target_url']))
    submitData(software)

def softwareScoreCreate(args):
    """
    """
    logging.info("进入software对象创建流程")
    logging.info("准备读取配置文件 {}".format(args.defaults_file))
    config = configparser.ConfigParser()
    config.read(args.defaults_file)
    softwarescore={}
    softwarescore['hardware_name']=config['hardware']['name']
    softwarescore['mysql_release']=config['software']['mysql_release']
    softwarescore['target_url']=config['default']['softwarescorecreate']
    for filename in listLogFile(args.log_path):
        data={}
        data.update(softwarescore)
        try:
            result = sysbenchLogParser(filename)
        except Exception as e:
            logging.info('解析sysbench的日志出错')
            logging.error(e)
            raise SystemExit()

        data.update({'threads':result['parallels'],'scores':result['scores']})
        submitData(data)
        
argsToFun={
    'hardware-create':hardwareCreate,
    'software-create':softwareCreate,
    'softwarescore-create':softwareScoreCreate
}

if __name__=="__main__":
    logging.info('准备进行命令行参数处理')
    parser=argparse.ArgumentParser()
    parser.add_argument('--defaults-file',default='sqlpy.cnf',help='默认配置文件./sqlpy.cnf')
    parser.add_argument('--log-path',default='/Users/jianglexing/Desktop/mysql-5.7.22',help='sysbench 日志文件所保存的路径')
    parser.add_argument('action',choices=('hardware-create','software-create','softwarescore-create'))
    args=parser.parse_args()

    #打印相关命令行参数
    logging.info('命令行参数信息如下')
    tableKVS(args.__dict__)

    #根据action的值执行操作
    argsToFun[args.action](args)


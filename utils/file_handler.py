from langchain_core.documents.base import Document
import os,hashlib
from utils.logger_handler import logger
from langchain_community.document_loaders import TextLoader


def get_file_md5_hex(filepath:str):
    '''获取文件的16进制字符串'''
    if not os.path.exists(filepath):
        logger.error(f"[md5计算]文件{filepath}不存在")
        return
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]路径{filepath}不是文件")
        return
    
    md5_obj=hashlib.md5()
    chunk_size=4096 #避免文件过大
    try:
        with open(filepath,'rb') as f:  #以二进制方式读文件，简化编码步骤
            while chunk :=f.read(chunk_size):
                md5_obj.update(chunk)
                '''
                chunk=f.read(chunk_size)
                while chunk:
                    md5_obj.update(chunk)
                    chunk=f.read(chunk_size)
                '''
            md5_hex=md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None


def listdir_with_allowed_type(path:str,allowed_types:tuple[str]):
    '''获取文件夹内的文件列表'''
    files=[]

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return allowed_types
    
    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path,f))

    return tuple(files)


def txt_loader(filepath:str)->list[Document]:
    return TextLoader(filepath, encoding='utf-8').load()

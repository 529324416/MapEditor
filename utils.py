import os
import time
import copy
import json
import queue

def read(filepath:str) -> str:
    '''以文本的形式读取一个文件的所有信息'''

    with open(filepath, "r", encoding='utf-8') as f:
        return f.read()

def save(cnt:str, filepath:str) -> None:
    '''存储文本到指定的文件夹'''

    with open(filepath, "w", encoding='utf-8') as f:
        f.write(cnt)

def save_json(obj:dict, filepath:str) -> None:
    '''存储一个dict到指定的JSON文件中'''

    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(obj, f)

def now():
    '''以默认的格式[hh:mm:ss]获取当前的时间信息'''

    t = time.localtime()
    return f"{t[3]}:{t[4]}:{t[5]}"

def clearFolder(folder:str, clear=True):
    '''删除文件夹下所有的文件'''

    for file in os.listdir(folder):
        path = f"{folder}/{file}"
        if os.path.isfile(path):
            os.remove(path)
        else:
            clearFolder(path, True)
    if clear:
        os.rmdir(folder)

def parseNameFromPath(path:str,sep='/'):
    '''从path解析出文件名'''

    try:
        return path.split(sep)[-1].split('.')[0]
    except:
        return path


class Counter:
    '''计数器'''

    def __init__(self, entry=0):
        self._id = entry
        self._queue = queue.Queue()

    @property
    def json(self):
        '''将计数器存储为JSON数据'''

        _queue = copy.copy(self._queue)
        recycleList = list()
        for i in range(_queue.qsize()):
            recycleList.append(_queue.get())

        # while _queue.not_empty:
        #     recycleList.append(_queue.get())
        return {
            "currentId":self._id,
            "recycleList":recycleList
        }


    @property
    def next_id(self):
        '''获取下一个id'''

        if self._queue.empty():
            buf = self._id
            self._id += 1
            return buf
        return self._queue.get()

    def recycle(self, _id):
        '''回收一个id'''

        self._queue.put(_id)

if __name__ == '__main__':

    print(parseNameFromPath("./test.png"))
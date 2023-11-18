import os,shutil
import pdb
import zipfile

# 判断是否是文件和判断文件是否存在
def isfile_exist(file_path):
    if not os.path.isfile(file_path):
        print("It's not a file or no such file exist ! %s" % file_path)
        return False
    else:
        return True


# 修改指定目录下的文件类型名，将excel后缀名修改为.zip
def change_file_name(file_path, new_type='.zip'):
    # 
    if not isfile_exist(file_path):
        return ''

    extend = os.path.splitext(file_path)[1]  # 获取文件拓展名
    if extend != '.xlsx' and extend != '.xls':
        print("It's not a excel file! %s" % file_path)
        return False

    file_name = os.path.basename(file_path)  # 获取文件名
    new_name = str(file_name.split('.')[0]) + new_type  # 新的文件名，命名为：xxx.zip

    dir_path = os.path.dirname(file_path)  # 获取文件所在目录
    new_path = os.path.join(dir_path, new_name)  # 新的文件路径
    if os.path.exists(new_path):
        os.remove(new_path)

    os.rename(file_path, new_path)  # 保存新文件，旧文件会替换掉

    return new_path  # 返回新的文件路径，压缩包


# 解压文件
def unzip_file(zipfile_path):
    
    if not isfile_exist(zipfile_path):
        return False

    if os.path.splitext(zipfile_path)[1] != '.zip':
        print("It's not a zip file! %s" % zipfile_path)
        return False

    file_zip = zipfile.ZipFile(zipfile_path, 'r')
    file_name = os.path.basename(zipfile_path)  # 获取文件名
    # 获取文件所在目录
    zipdir = os.path.join(os.path.dirname(zipfile_path), str(file_name.split('.')[0]))
    for files in file_zip.namelist():
        file_zip.extract(files, os.path.join(zipfile_path, zipdir))  # 解压到指定文件目录

    file_zip.close()
    return True


# 读取解压后的文件夹，打印图片路径
def read_img(zipfile_path,img_path):
    # 
    if not isfile_exist(zipfile_path):
        return False
    dir_path = os.path.dirname(zipfile_path)  # 获取文件所在目录
    file_name = os.path.basename(zipfile_path)  # 获取文件名
    unzip_dir = os.path.join(dir_path, str(file_name.split('.')[0]))
    # excel变成压缩包解压后，excel中的图片在media目录
    pic_dir = 'xl' + os.sep + 'media'
    pic_path = os.path.join(dir_path, str(file_name.split('.')[0]), pic_dir)

    file_list = os.listdir(pic_path)
    for file in file_list:
        filepath = os.path.join(pic_path, file)
        # print(filepath,img_path)
        # 复制文件 
        if os.path.isfile(os.path.join(img_path, os.path.basename(filepath))):
            os.remove(os.path.join(img_path, os.path.basename(filepath)))
        
        shutil.move(filepath,img_path)
    # 删除压缩文件
    # os.unlink(zipfile_path)
    # 删除解压后的文件
    shutil.rmtree(unzip_dir)


# 还原文件名
def revert_dir(zipfile_path):
    extend = os.path.splitext(zipfile_path)[1]  # 获取文件拓展名
    if extend != '.zip':
        print("It's not a zip file! %s" % zipfile_path)
        return False

    file_name = os.path.basename(zipfile_path)  # 获取文件名
    new_name = str(file_name.split('.')[0]) + '.xlsx'  # 新的文件名，命名为：xxx.xlsx

    dir_path = os.path.dirname(zipfile_path)  # 获取文件所在目录
    new_path = os.path.join(dir_path, new_name)  # 新的文件路径
    if os.path.exists(new_path):
        os.remove(new_path)

    os.rename(zipfile_path, new_path)  # 保存新文件，旧文件会替换掉

    return new_path  # 返回新的文件路径，压缩包


# 提取图片，并保存
def compenent(excel_file_path,img_path):
    # 返回图片地址
    zip_file_path = change_file_name(excel_file_path) 
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    if zip_file_path != '':
        
        unzip_msg = unzip_file(zip_file_path)
        if unzip_msg:
            read_img(zip_file_path,img_path)
    revert_dir(zip_file_path)
    return img_path


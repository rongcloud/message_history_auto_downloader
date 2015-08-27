    # message_history_auto_downloader
    自动下载聊天历史记录到本地服务器的任务脚本。
    
    使用说明：
    1、执行环境：linux系统
    2、在脚本所在目录下，创建并编辑app_info.ini文件，添加如下三行：
        [info]
        rongcloud_app_key=您的App-key
        rongcloud_app_secret=您的App-secret
    3、添加计划任务（使用linux自带的crontab服务），自动下载聊天记录，这里假设为root用户，设置方法如下：
         echo "0 * * * * python 脚本所在目录/history_message_download.py 脚本所在目录 > /dev/null 2>&1" >> /var/spool/cron/root（redhat系统）
      或 echo "0 * * * * python 脚本所在目录/history_message_download.py 脚本所在目录 > /dev/null 2>&1" >> /var/spool/cron/crontabs/root（ubuntu系统）
    4、由于消息存挡的时间关系，此脚本每小时自动执行一次，每次下载的消息是一个小时前的数据，
       举例：现在15:00 =< time < 16:00，那么下载的消息为13:00-14:00的一个小时的历史消息。
    5、消息自动存档至脚本所在目录。

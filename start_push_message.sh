 
python spider/piyao_spider.py 
python app/scraper/spiders/weibo_search.py
python app/scripts/migrate_data.py 
python send_message.py --username user1 --now --limit 5
# python send_message.py  --now
# 向指定用户推送
#python send_message.py --username user1 --now

# 向所有用户推送
#python send_message.py --all-users --now

# 向订阅用户推送（默认）
#python send_message.py --now

# 启动定时推送给指定用户
#python send_message.py --username user1

# 启动定时推送给所有用户
#python send_message.py --all-users
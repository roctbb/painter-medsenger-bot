sudo pip3 install -r requirements.txt
sudo cp painter.ini /etc/uwsgi/apps/
sudo cp agents_painter.conf /etc/supervisor/conf.d/
sudo cp agents_painter_nginx.conf /etc/nginx/sites-enabled/
sudo supervisorctl update
sudo systemctl restart nginx
sudo certbot --nginx -d painter.ai.medsenger.ru
